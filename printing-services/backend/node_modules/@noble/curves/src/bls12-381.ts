/*! noble-curves - MIT License (c) 2022 Paul Miller (paulmillr.com) */

// bls12-381 pairing-friendly Barreto-Lynn-Scott elliptic curve construction allows to:
// - Construct zk-SNARKs at the 128-bit security
// - Use threshold signatures, which allows a user to sign lots of messages with one signature and
//   verify them swiftly in a batch, using Boneh-Lynn-Shacham signature scheme.
//
// The library uses G1 for public keys and G2 for signatures. Support for G1 signatures is planned.
// Compatible with Algorand, Chia, Dfinity, Ethereum, FIL, Zcash. Matches specs
// [pairing-curves-11](https://tools.ietf.org/html/draft-irtf-cfrg-pairing-friendly-curves-11),
// [bls-sigs-04](https:/cfrg-hash-to/tools.ietf.org/html/draft-irtf-cfrg-bls-signature-04),
// [hash-to-curve-12](https://tools.ietf.org/html/draft-irtf--curve-12).
//
// ### Summary
// 1. BLS Relies on Bilinear Pairing (expensive)
// 2. Private Keys: 32 bytes
// 3. Public Keys: 48 bytes: 381 bit affine x coordinate, encoded into 48 big-endian bytes.
// 4. Signatures: 96 bytes: two 381 bit integers (affine x coordinate), encoded into two 48 big-endian byte arrays.
//     - The signature is a point on the G2 subgroup, which is defined over a finite field
//     with elements twice as big as the G1 curve (G2 is over Fp2 rather than Fp. Fp2 is analogous to the complex numbers).
// 5. The 12 stands for the Embedding degree.
//
// ### Formulas
// - `P = pk x G` - public keys
// - `S = pk x H(m)` - signing
// - `e(P, H(m)) == e(G, S)` - verification using pairings
// - `e(G, S) = e(G, SUM(n)(Si)) = MUL(n)(e(G, Si))` - signature aggregation
// Filecoin uses little endian byte arrays for private keys -
// so ensure to reverse byte order if you'll use it with FIL.
import { sha256 } from '@noble/hashes/sha256';
import { randomBytes } from '@noble/hashes/utils';
import { bls, CurveFn } from './abstract/bls.js';
import * as mod from './abstract/modular.js';
import {
  concatBytes as concatB,
  ensureBytes,
  numberToBytesBE,
  bytesToNumberBE,
  bitLen,
  bitSet,
  bitGet,
  Hex,
  bitMask,
  bytesToHex,
} from './abstract/utils.js';
// Types
import {
  ProjPointType,
  ProjConstructor,
  mapToCurveSimpleSWU,
  AffinePoint,
} from './abstract/weierstrass.js';
import { isogenyMap } from './abstract/hash-to-curve.js';

// Be friendly to bad ECMAScript parsers by not using bigint literals
// prettier-ignore
const _0n = BigInt(0), _1n = BigInt(1), _2n = BigInt(2), _3n = BigInt(3), _4n = BigInt(4);
// prettier-ignore
const _8n = BigInt(8), _16n = BigInt(16);

// CURVE FIELDS
// Finite field over p.
const Fp_raw = BigInt(
  '0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaab'
);
const Fp = mod.Field(Fp_raw);
type Fp = bigint;
// Finite field over r.
// This particular field is not used anywhere in bls12-381, but it is still useful.
const Fr = mod.Field(BigInt('0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001'));

// Fp₂ over complex plane
type BigintTuple = [bigint, bigint];
type Fp2 = { c0: bigint; c1: bigint };
const Fp2Add = ({ c0, c1 }: Fp2, { c0: r0, c1: r1 }: Fp2) => ({
  c0: Fp.add(c0, r0),
  c1: Fp.add(c1, r1),
});
const Fp2Subtract = ({ c0, c1 }: Fp2, { c0: r0, c1: r1 }: Fp2) => ({
  c0: Fp.sub(c0, r0),
  c1: Fp.sub(c1, r1),
});
const Fp2Multiply = ({ c0, c1 }: Fp2, rhs: Fp2) => {
  if (typeof rhs === 'bigint') return { c0: Fp.mul(c0, rhs), c1: Fp.mul(c1, rhs) };
  // (a+bi)(c+di) = (ac−bd) + (ad+bc)i
  const { c0: r0, c1: r1 } = rhs;
  let t1 = Fp.mul(c0, r0); // c0 * o0
  let t2 = Fp.mul(c1, r1); // c1 * o1
  // (T1 - T2) + ((c0 + c1) * (r0 + r1) - (T1 + T2))*i
  const o0 = Fp.sub(t1, t2);
  const o1 = Fp.sub(Fp.mul(Fp.add(c0, c1), Fp.add(r0, r1)), Fp.add(t1, t2));
  return { c0: o0, c1: o1 };
};
const Fp2Square = ({ c0, c1 }: Fp2) => {
  const a = Fp.add(c0, c1);
  const b = Fp.sub(c0, c1);
  const c = Fp.add(c0, c0);
  return { c0: Fp.mul(a, b), c1: Fp.mul(c, c1) };
};
type Fp2Utils = {
  fromBigTuple: (tuple: BigintTuple | bigint[]) => Fp2;
  reim: (num: Fp2) => { re: bigint; im: bigint };
  mulByNonresidue: (num: Fp2) => Fp2;
  multiplyByB: (num: Fp2) => Fp2;
  frobeniusMap(num: Fp2, power: number): Fp2;
};
// G2 is the order-q subgroup of E2(Fp²) : y² = x³+4(1+√−1),
// where Fp2 is Fp[√−1]/(x2+1). #E2(Fp2 ) = h2q, where
// G² - 1
// h2q
// NOTE: ORDER was wrong!
const FP2_ORDER = Fp_raw * Fp_raw;

const Fp2: mod.IField<Fp2> & Fp2Utils = {
  ORDER: FP2_ORDER,
  BITS: bitLen(FP2_ORDER),
  BYTES: Math.ceil(bitLen(FP2_ORDER) / 8),
  MASK: bitMask(bitLen(FP2_ORDER)),
  ZERO: { c0: Fp.ZERO, c1: Fp.ZERO },
  ONE: { c0: Fp.ONE, c1: Fp.ZERO },
  create: (num) => num,
  isValid: ({ c0, c1 }) => typeof c0 === 'bigint' && typeof c1 === 'bigint',
  is0: ({ c0, c1 }) => Fp.is0(c0) && Fp.is0(c1),
  eql: ({ c0, c1 }: Fp2, { c0: r0, c1: r1 }: Fp2) => Fp.eql(c0, r0) && Fp.eql(c1, r1),
  neg: ({ c0, c1 }) => ({ c0: Fp.neg(c0), c1: Fp.neg(c1) }),
  pow: (num, power) => mod.FpPow(Fp2, num, power),
  invertBatch: (nums) => mod.FpInvertBatch(Fp2, nums),
  // Normalized
  add: Fp2Add,
  sub: Fp2Subtract,
  mul: Fp2Multiply,
  sqr: Fp2Square,
  // NonNormalized stuff
  addN: Fp2Add,
  subN: Fp2Subtract,
  mulN: Fp2Multiply,
  sqrN: Fp2Square,
  // Why inversion for bigint inside Fp instead of Fp2? it is even used in that context?
  div: (lhs, rhs) => Fp2.mul(lhs, typeof rhs === 'bigint' ? Fp.inv(Fp.create(rhs)) : Fp2.inv(rhs)),
  inv: ({ c0: a, c1: b }) => {
    // We wish to find the multiplicative inverse of a nonzero
    // element a + bu in Fp2. We leverage an identity
    //
    // (a + bu)(a - bu) = a² + b²
    //
    // which holds because u² = -1. This can be rewritten as
    //
    // (a + bu)(a - bu)/(a² + b²) = 1
    //
    // because a² + b² = 0 has no nonzero solutions for (a, b).
    // This gives that (a - bu)/(a² + b²) is the inverse
    // of (a + bu). Importantly, this can be computing using
    // only a single inversion in Fp.
    const factor = Fp.inv(Fp.create(a * a + b * b));
    return { c0: Fp.mul(factor, Fp.create(a)), c1: Fp.mul(factor, Fp.create(-b)) };
  },
  sqrt: (num) => {
    if (Fp2.eql(num, Fp2.ZERO)) return Fp2.ZERO; // Algo doesn't handles this case
    // TODO: Optimize this line. It's extremely slow.
    // Speeding this up would boost aggregateSignatures.
    // https://eprint.iacr.org/2012/685.pdf applicable?
    // https://github.com/zkcrypto/bls12_381/blob/080eaa74ec0e394377caa1ba302c8c121df08b07/src/fp2.rs#L250
    // https://github.com/supranational/blst/blob/aae0c7d70b799ac269ff5edf29d8191dbd357876/src/exp2.c#L1
    // Inspired by https://github.com/dalek-cryptography/curve25519-dalek/blob/17698df9d4c834204f83a3574143abacb4fc81a5/src/field.rs#L99
    const candidateSqrt = Fp2.pow(num, (Fp2.ORDER + _8n) / _16n);
    const check = Fp2.div(Fp2.sqr(candidateSqrt), num); // candidateSqrt.square().div(this);
    const R = FP2_ROOTS_OF_UNITY;
    const divisor = [R[0], R[2], R[4], R[6]].find((r) => Fp2.eql(r, check));
    if (!divisor) throw new Error('No root');
    const index = R.indexOf(divisor);
    const root = R[index / 2];
    if (!root) throw new Error('Invalid root');
    const x1 = Fp2.div(candidateSqrt, root);
    const x2 = Fp2.neg(x1);
    const { re: re1, im: im1 } = Fp2.reim(x1);
    const { re: re2, im: im2 } = Fp2.reim(x2);
    if (im1 > im2 || (im1 === im2 && re1 > re2)) return x1;
    return x2;
  },
  // Same as sgn0_m_eq_2 in RFC 9380
  isOdd: (x: Fp2) => {
    const { re: x0, im: x1 } = Fp2.reim(x);
    const sign_0 = x0 % _2n;
    const zero_0 = x0 === _0n;
    const sign_1 = x1 % _2n;
    return BigInt(sign_0 || (zero_0 && sign_1)) == _1n;
  },
  // Bytes util
  fromBytes(b: Uint8Array): Fp2 {
    if (b.length !== Fp2.BYTES) throw new Error(`fromBytes wrong length=${b.length}`);
    return { c0: Fp.fromBytes(b.subarray(0, Fp.BYTES)), c1: Fp.fromBytes(b.subarray(Fp.BYTES)) };
  },
  toBytes: ({ c0, c1 }) => concatB(Fp.toBytes(c0), Fp.toBytes(c1)),
  cmov: ({ c0, c1 }, { c0: r0, c1: r1 }, c) => ({
    c0: Fp.cmov(c0, r0, c),
    c1: Fp.cmov(c1, r1, c),
  }),
  // Specific utils
  // toString() {
  //   return `Fp2(${this.c0} + ${this.c1}×i)`;
  // }
  reim: ({ c0, c1 }) => ({ re: c0, im: c1 }),
  // multiply by u + 1
  mulByNonresidue: ({ c0, c1 }) => ({ c0: Fp.sub(c0, c1), c1: Fp.add(c0, c1) }),
  multiplyByB: ({ c0, c1 }) => {
    let t0 = Fp.mul(c0, _4n); // 4 * c0
    let t1 = Fp.mul(c1, _4n); // 4 * c1
    // (T0-T1) + (T0+T1)*i
    return { c0: Fp.sub(t0, t1), c1: Fp.add(t0, t1) };
  },
  fromBigTuple: (tuple: BigintTuple | bigint[]) => {
    if (tuple.length !== 2) throw new Error('Invalid tuple');
    const fps = tuple.map((n) => Fp.create(n)) as [Fp, Fp];
    return { c0: fps[0], c1: fps[1] };
  },
  frobeniusMap: ({ c0, c1 }, power: number): Fp2 => ({
    c0,
    c1: Fp.mul(c1, FP2_FROBENIUS_COEFFICIENTS[power % 2]),
  }),
};
// Finite extension field over irreducible polynominal.
// Fp(u) / (u² - β) where β = -1
const FP2_FROBENIUS_COEFFICIENTS = [
  BigInt('0x1'),
  BigInt(
    '0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaaa'
  ),
].map((item) => Fp.create(item));

// For Fp2 roots of unity.
const rv1 = BigInt(
  '0x6af0e0437ff400b6831e36d6bd17ffe48395dabc2d3435e77f76e17009241c5ee67992f72ec05f4c81084fbede3cc09'
);
// const ev1 =
//   BigInt('0x699be3b8c6870965e5bf892ad5d2cc7b0e85a117402dfd83b7f4a947e02d978498255a2aaec0ac627b5afbdf1bf1c90');
// const ev2 =
//   BigInt('0x8157cd83046453f5dd0972b6e3949e4288020b5b8a9cc99ca07e27089a2ce2436d965026adad3ef7baba37f2183e9b5');
// const ev3 =
//   BigInt('0xab1c2ffdd6c253ca155231eb3e71ba044fd562f6f72bc5bad5ec46a0b7a3b0247cf08ce6c6317f40edbc653a72dee17');
// const ev4 =
//   BigInt('0xaa404866706722864480885d68ad0ccac1967c7544b447873cc37e0181271e006df72162a3d3e0287bf597fbf7f8fc1');

// Eighth roots of unity, used for computing square roots in Fp2.
// To verify or re-calculate:
// Array(8).fill(new Fp2([1n, 1n])).map((fp2, k) => fp2.pow(Fp2.ORDER * BigInt(k) / 8n))
const FP2_ROOTS_OF_UNITY = [
  [_1n, _0n],
  [rv1, -rv1],
  [_0n, _1n],
  [rv1, rv1],
  [-_1n, _0n],
  [-rv1, rv1],
  [_0n, -_1n],
  [-rv1, -rv1],
].map((pair) => Fp2.fromBigTuple(pair));
// eta values, used for computing sqrt(g(X1(t)))
// const FP2_ETAs = [
//   [ev1, ev2],
//   [-ev2, ev1],
//   [ev3, ev4],
//   [-ev4, ev3],
// ].map((pair) => Fp2.fromBigTuple(pair));

// Finite extension field over irreducible polynominal.
// Fp2(v) / (v³ - ξ) where ξ = u + 1
type BigintSix = [bigint, bigint, bigint, bigint, bigint, bigint];
type Fp6 = { c0: Fp2; c1: Fp2; c2: Fp2 };
const Fp6Add = ({ c0, c1, c2 }: Fp6, { c0: r0, c1: r1, c2: r2 }: Fp6) => ({
  c0: Fp2.add(c0, r0),
  c1: Fp2.add(c1, r1),
  c2: Fp2.add(c2, r2),
});
const Fp6Subtract = ({ c0, c1, c2 }: Fp6, { c0: r0, c1: r1, c2: r2 }: Fp6) => ({
  c0: Fp2.sub(c0, r0),
  c1: Fp2.sub(c1, r1),
  c2: Fp2.sub(c2, r2),
});
const Fp6Multiply = ({ c0, c1, c2 }: Fp6, rhs: Fp6 | bigint) => {
  if (typeof rhs === 'bigint') {
    return {
      c0: Fp2.mul(c0, rhs),
      c1: Fp2.mul(c1, rhs),
      c2: Fp2.mul(c2, rhs),
    };
  }
  const { c0: r0, c1: r1, c2: r2 } = rhs;
  const t0 = Fp2.mul(c0, r0); // c0 * o0
  const t1 = Fp2.mul(c1, r1); // c1 * o1
  const t2 = Fp2.mul(c2, r2); // c2 * o2
  return {
    // t0 + (c1 + c2) * (r1 * r2) - (T1 + T2) * (u + 1)
    c0: Fp2.add(
      t0,
      Fp2.mulByNonresidue(Fp2.sub(Fp2.mul(Fp2.add(c1, c2), Fp2.add(r1, r2)), Fp2.add(t1, t2)))
    ),
    // (c0 + c1) * (r0 + r1) - (T0 + T1) + T2 * (u + 1)
    c1: Fp2.add(
      Fp2.sub(Fp2.mul(Fp2.add(c0, c1), Fp2.add(r0, r1)), Fp2.add(t0, t1)),
      Fp2.mulByNonresidue(t2)
    ),
    // T1 + (c0 + c2) * (r0 + r2) - T0 + T2
    c2: Fp2.sub(Fp2.add(t1, Fp2.mul(Fp2.add(c0, c2), Fp2.add(r0, r2))), Fp2.add(t0, t2)),
  };
};
const Fp6Square = ({ c0, c1, c2 }: Fp6) => {
  let t0 = Fp2.sqr(c0); // c0²
  let t1 = Fp2.mul(Fp2.mul(c0, c1), _2n); // 2 * c0 * c1
  let t3 = Fp2.mul(Fp2.mul(c1, c2), _2n); // 2 * c1 * c2
  let t4 = Fp2.sqr(c2); // c2²
  return {
    c0: Fp2.add(Fp2.mulByNonresidue(t3), t0), // T3 * (u + 1) + T0
    c1: Fp2.add(Fp2.mulByNonresidue(t4), t1), // T4 * (u + 1) + T1
    // T1 + (c0 - c1 + c2)² + T3 - T0 - T4
    c2: Fp2.sub(Fp2.sub(Fp2.add(Fp2.add(t1, Fp2.sqr(Fp2.add(Fp2.sub(c0, c1), c2))), t3), t0), t4),
  };
};
type Fp6Utils = {
  fromBigSix: (tuple: BigintSix) => Fp6;
  mulByNonresidue: (num: Fp6) => Fp6;
  frobeniusMap(num: Fp6, power: number): Fp6;
  multiplyBy1(num: Fp6, b1: Fp2): Fp6;
  multiplyBy01(num: Fp6, b0: Fp2, b1: Fp2): Fp6;
  multiplyByFp2(lhs: Fp6, rhs: Fp2): Fp6;
};

const Fp6: mod.IField<Fp6> & Fp6Utils = {
  ORDER: Fp2.ORDER, // TODO: unused, but need to verify
  BITS: 3 * Fp2.BITS,
  BYTES: 3 * Fp2.BYTES,
  MASK: bitMask(3 * Fp2.BITS),
  ZERO: { c0: Fp2.ZERO, c1: Fp2.ZERO, c2: Fp2.ZERO },
  ONE: { c0: Fp2.ONE, c1: Fp2.ZERO, c2: Fp2.ZERO },
  create: (num) => num,
  isValid: ({ c0, c1, c2 }) => Fp2.isValid(c0) && Fp2.isValid(c1) && Fp2.isValid(c2),
  is0: ({ c0, c1, c2 }) => Fp2.is0(c0) && Fp2.is0(c1) && Fp2.is0(c2),
  neg: ({ c0, c1, c2 }) => ({ c0: Fp2.neg(c0), c1: Fp2.neg(c1), c2: Fp2.neg(c2) }),
  eql: ({ c0, c1, c2 }, { c0: r0, c1: r1, c2: r2 }) =>
    Fp2.eql(c0, r0) && Fp2.eql(c1, r1) && Fp2.eql(c2, r2),
  sqrt: () => {
    throw new Error('Not implemented');
  },
  // Do we need division by bigint at all? Should be done via order:
  div: (lhs, rhs) => Fp6.mul(lhs, typeof rhs === 'bigint' ? Fp.inv(Fp.create(rhs)) : Fp6.inv(rhs)),
  pow: (num, power) => mod.FpPow(Fp6, num, power),
  invertBatch: (nums) => mod.FpInvertBatch(Fp6, nums),
  // Normalized
  add: Fp6Add,
  sub: Fp6Subtract,
  mul: Fp6Multiply,
  sqr: Fp6Square,
  // NonNormalized stuff
  addN: Fp6Add,
  subN: Fp6Subtract,
  mulN: Fp6Multiply,
  sqrN: Fp6Square,

  inv: ({ c0, c1, c2 }) => {
    let t0 = Fp2.sub(Fp2.sqr(c0), Fp2.mulByNonresidue(Fp2.mul(c2, c1))); // c0² - c2 * c1 * (u + 1)
    let t1 = Fp2.sub(Fp2.mulByNonresidue(Fp2.sqr(c2)), Fp2.mul(c0, c1)); // c2² * (u + 1) - c0 * c1
    let t2 = Fp2.sub(Fp2.sqr(c1), Fp2.mul(c0, c2)); // c1² - c0 * c2
    // 1/(((c2 * T1 + c1 * T2) * v) + c0 * T0)
    let t4 = Fp2.inv(
      Fp2.add(Fp2.mulByNonresidue(Fp2.add(Fp2.mul(c2, t1), Fp2.mul(c1, t2))), Fp2.mul(c0, t0))
    );
    return { c0: Fp2.mul(t4, t0), c1: Fp2.mul(t4, t1), c2: Fp2.mul(t4, t2) };
  },
  // Bytes utils
  fromBytes: (b: Uint8Array): Fp6 => {
    if (b.length !== Fp6.BYTES) throw new Error(`fromBytes wrong length=${b.length}`);
    return {
      c0: Fp2.fromBytes(b.subarray(0, Fp2.BYTES)),
      c1: Fp2.fromBytes(b.subarray(Fp2.BYTES, 2 * Fp2.BYTES)),
      c2: Fp2.fromBytes(b.subarray(2 * Fp2.BYTES)),
    };
  },
  toBytes: ({ c0, c1, c2 }): Uint8Array =>
    concatB(Fp2.toBytes(c0), Fp2.toBytes(c1), Fp2.toBytes(c2)),
  cmov: ({ c0, c1, c2 }: Fp6, { c0: r0, c1: r1, c2: r2 }: Fp6, c) => ({
    c0: Fp2.cmov(c0, r0, c),
    c1: Fp2.cmov(c1, r1, c),
    c2: Fp2.cmov(c2, r2, c),
  }),
  // Utils
  //   fromTriple(triple: [Fp2, Fp2, Fp2]) {
  //     return new Fp6(...triple);
  //   }
  //   toString() {
  //     return `Fp6(${this.c0} + ${this.c1} * v, ${this.c2} * v^2)`;
  //   }
  fromBigSix: (t: BigintSix): Fp6 => {
    if (!Array.isArray(t) || t.length !== 6) throw new Error('Invalid Fp6 usage');
    return {
      c0: Fp2.fromBigTuple(t.slice(0, 2)),
      c1: Fp2.fromBigTuple(t.slice(2, 4)),
      c2: Fp2.fromBigTuple(t.slice(4, 6)),
    };
  },
  frobeniusMap: ({ c0, c1, c2 }, power: number) => ({
    c0: Fp2.frobeniusMap(c0, power),
    c1: Fp2.mul(Fp2.frobeniusMap(c1, power), FP6_FROBENIUS_COEFFICIENTS_1[power % 6]),
    c2: Fp2.mul(Fp2.frobeniusMap(c2, power), FP6_FROBENIUS_COEFFICIENTS_2[power % 6]),
  }),
  mulByNonresidue: ({ c0, c1, c2 }) => ({ c0: Fp2.mulByNonresidue(c2), c1: c0, c2: c1 }),

  // Sparse multiplication
  multiplyBy1: ({ c0, c1, c2 }, b1: Fp2): Fp6 => ({
    c0: Fp2.mulByNonresidue(Fp2.mul(c2, b1)),
    c1: Fp2.mul(c0, b1),
    c2: Fp2.mul(c1, b1),
  }),
  // Sparse multiplication
  multiplyBy01({ c0, c1, c2 }, b0: Fp2, b1: Fp2): Fp6 {
    let t0 = Fp2.mul(c0, b0); // c0 * b0
    let t1 = Fp2.mul(c1, b1); // c1 * b1
    return {
      // ((c1 + c2) * b1 - T1) * (u + 1) + T0
      c0: Fp2.add(Fp2.mulByNonresidue(Fp2.sub(Fp2.mul(Fp2.add(c1, c2), b1), t1)), t0),
      // (b0 + b1) * (c0 + c1) - T0 - T1
      c1: Fp2.sub(Fp2.sub(Fp2.mul(Fp2.add(b0, b1), Fp2.add(c0, c1)), t0), t1),
      // (c0 + c2) * b0 - T0 + T1
      c2: Fp2.add(Fp2.sub(Fp2.mul(Fp2.add(c0, c2), b0), t0), t1),
    };
  },

  multiplyByFp2: ({ c0, c1, c2 }, rhs: Fp2): Fp6 => ({
    c0: Fp2.mul(c0, rhs),
    c1: Fp2.mul(c1, rhs),
    c2: Fp2.mul(c2, rhs),
  }),
};

const FP6_FROBENIUS_COEFFICIENTS_1 = [
  [BigInt('0x1'), BigInt('0x0')],
  [
    BigInt('0x0'),
    BigInt(
      '0x1a0111ea397fe699ec02408663d4de85aa0d857d89759ad4897d29650fb85f9b409427eb4f49fffd8bfd00000000aaac'
    ),
  ],
  [
    BigInt(
      '0x00000000000000005f19672fdf76ce51ba69c6076a0f77eaddb3a93be6f89688de17d813620a00022e01fffffffefffe'
    ),
    BigInt('0x0'),
  ],
  [BigInt('0x0'), BigInt('0x1')],
  [
    BigInt(
      '0x1a0111ea397fe699ec02408663d4de85aa0d857d89759ad4897d29650fb85f9b409427eb4f49fffd8bfd00000000aaac'
    ),
    BigInt('0x0'),
  ],
  [
    BigInt('0x0'),
    BigInt(
      '0x00000000000000005f19672fdf76ce51ba69c6076a0f77eaddb3a93be6f89688de17d813620a00022e01fffffffefffe'
    ),
  ],
].map((pair) => Fp2.fromBigTuple(pair));
const FP6_FROBENIUS_COEFFICIENTS_2 = [
  [BigInt('0x1'), BigInt('0x0')],
  [
    BigInt(
      '0x1a0111ea397fe699ec02408663d4de85aa0d857d89759ad4897d29650fb85f9b409427eb4f49fffd8bfd00000000aaad'
    ),
    BigInt('0x0'),
  ],
  [
    BigInt(
      '0x1a0111ea397fe699ec02408663d4de85aa0d857d89759ad4897d29650fb85f9b409427eb4f49fffd8bfd00000000aaac'
    ),
    BigInt('0x0'),
  ],
  [
    BigInt(
      '0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaaa'
    ),
    BigInt('0x0'),
  ],
  [
    BigInt(
      '0x00000000000000005f19672fdf76ce51ba69c6076a0f77eaddb3a93be6f89688de17d813620a00022e01fffffffefffe'
    ),
    BigInt('0x0'),
  ],
  [
    BigInt(
      '0x00000000000000005f19672fdf76ce51ba69c6076a0f77eaddb3a93be6f89688de17d813620a00022e01fffffffeffff'
    ),
    BigInt('0x0'),
  ],
].map((pair) => Fp2.fromBigTuple(pair));

// Finite extension field over irreducible polynominal.
// Fp₁₂ = Fp₆² => Fp₂³
// Fp₆(w) / (w² - γ) where γ = v
type Fp12 = { c0: Fp6; c1: Fp6 };
// The BLS parameter x for BLS12-381
const BLS_X = BigInt('0xd201000000010000');
const BLS_X_LEN = bitLen(BLS_X);

// prettier-ignore
type BigintTwelve = [
    bigint, bigint, bigint, bigint, bigint, bigint,
    bigint, bigint, bigint, bigint, bigint, bigint
  ];
const Fp12Add = ({ c0, c1 }: Fp12, { c0: r0, c1: r1 }: Fp12) => ({
  c0: Fp6.add(c0, r0),
  c1: Fp6.add(c1, r1),
});
const Fp12Subtract = ({ c0, c1 }: Fp12, { c0: r0, c1: r1 }: Fp12) => ({
  c0: Fp6.sub(c0, r0),
  c1: Fp6.sub(c1, r1),
});
const Fp12Multiply = ({ c0, c1 }: Fp12, rhs: Fp12 | bigint) => {
  if (typeof rhs === 'bigint') return { c0: Fp6.mul(c0, rhs), c1: Fp6.mul(c1, rhs) };
  let { c0: r0, c1: r1 } = rhs;
  let t1 = Fp6.mul(c0, r0); // c0 * r0
  let t2 = Fp6.mul(c1, r1); // c1 * r1
  return {
    c0: Fp6.add(t1, Fp6.mulByNonresidue(t2)), // T1 + T2 * v
    // (c0 + c1) * (r0 + r1) - (T1 + T2)
    c1: Fp6.sub(Fp6.mul(Fp6.add(c0, c1), Fp6.add(r0, r1)), Fp6.add(t1, t2)),
  };
};
const Fp12Square = ({ c0, c1 }: Fp12) => {
  let ab = Fp6.mul(c0, c1); // c0 * c1
  return {
    // (c1 * v + c0) * (c0 + c1) - AB - AB * v
    c0: Fp6.sub(
      Fp6.sub(Fp6.mul(Fp6.add(Fp6.mulByNonresidue(c1), c0), Fp6.add(c0, c1)), ab),
      Fp6.mulByNonresidue(ab)
    ),
    c1: Fp6.add(ab, ab),
  }; // AB + AB
};
function Fp4Square(a: Fp2, b: Fp2): { first: Fp2; second: Fp2 } {
  const a2 = Fp2.sqr(a);
  const b2 = Fp2.sqr(b);
  return {
    first: Fp2.add(Fp2.mulByNonresidue(b2), a2), // b² * Nonresidue + a²
    second: Fp2.sub(Fp2.sub(Fp2.sqr(Fp2.add(a, b)), a2), b2), // (a + b)² - a² - b²
  };
}
type Fp12Utils = {
  fromBigTwelve: (t: BigintTwelve) => Fp12;
  frobeniusMap(num: Fp12, power: number): Fp12;
  multiplyBy014(num: Fp12, o0: Fp2, o1: Fp2, o4: Fp2): Fp12;
  multiplyByFp2(lhs: Fp12, rhs: Fp2): Fp12;
  conjugate(num: Fp12): Fp12;
  finalExponentiate(num: Fp12): Fp12;
  _cyclotomicSquare(num: Fp12): Fp12;
  _cyclotomicExp(num: Fp12, n: bigint): Fp12;
};

const Fp12: mod.IField<Fp12> & Fp12Utils = {
  ORDER: Fp2.ORDER, // TODO: unused, but need to verify
  BITS: 2 * Fp2.BITS,
  BYTES: 2 * Fp2.BYTES,
  MASK: bitMask(2 * Fp2.BITS),
  ZERO: { c0: Fp6.ZERO, c1: Fp6.ZERO },
  ONE: { c0: Fp6.ONE, c1: Fp6.ZERO },
  create: (num) => num,
  isValid: ({ c0, c1 }) => Fp6.isValid(c0) && Fp6.isValid(c1),
  is0: ({ c0, c1 }) => Fp6.is0(c0) && Fp6.is0(c1),
  neg: ({ c0, c1 }) => ({ c0: Fp6.neg(c0), c1: Fp6.neg(c1) }),
  eql: ({ c0, c1 }, { c0: r0, c1: r1 }) => Fp6.eql(c0, r0) && Fp6.eql(c1, r1),
  sqrt: () => {
    throw new Error('Not implemented');
  },
  inv: ({ c0, c1 }) => {
    let t = Fp6.inv(Fp6.sub(Fp6.sqr(c0), Fp6.mulByNonresidue(Fp6.sqr(c1)))); // 1 / (c0² - c1² * v)
    return { c0: Fp6.mul(c0, t), c1: Fp6.neg(Fp6.mul(c1, t)) }; // ((C0 * T) * T) + (-C1 * T) * w
  },
  div: (lhs, rhs) =>
    Fp12.mul(lhs, typeof rhs === 'bigint' ? Fp.inv(Fp.create(rhs)) : Fp12.inv(rhs)),
  pow: (num, power) => mod.FpPow(Fp12, num, power),
  invertBatch: (nums) => mod.FpInvertBatch(Fp12, nums),
  // Normalized
  add: Fp12Add,
  sub: Fp12Subtract,
  mul: Fp12Multiply,
  sqr: Fp12Square,
  // NonNormalized stuff
  addN: Fp12Add,
  subN: Fp12Subtract,
  mulN: Fp12Multiply,
  sqrN: Fp12Square,

  // Bytes utils
  fromBytes: (b: Uint8Array): Fp12 => {
    if (b.length !== Fp12.BYTES) throw new Error(`fromBytes wrong length=${b.length}`);
    return {
      c0: Fp6.fromBytes(b.subarray(0, Fp6.BYTES)),
      c1: Fp6.fromBytes(b.subarray(Fp6.BYTES)),
    };
  },
  toBytes: ({ c0, c1 }): Uint8Array => concatB(Fp6.toBytes(c0), Fp6.toBytes(c1)),
  cmov: ({ c0, c1 }, { c0: r0, c1: r1 }, c) => ({
    c0: Fp6.cmov(c0, r0, c),
    c1: Fp6.cmov(c1, r1, c),
  }),
  // Utils
  // toString() {
  //   return `Fp12(${this.c0} + ${this.c1} * w)`;
  // },
  // fromTuple(c: [Fp6, Fp6]) {
  //   return new Fp12(...c);
  // }
  fromBigTwelve: (t: BigintTwelve): Fp12 => ({
    c0: Fp6.fromBigSix(t.slice(0, 6) as BigintSix),
    c1: Fp6.fromBigSix(t.slice(6, 12) as BigintSix),
  }),
  // Raises to q**i -th power
  frobeniusMap(lhs, power: number) {
    const r0 = Fp6.frobeniusMap(lhs.c0, power);
    const { c0, c1, c2 } = Fp6.frobeniusMap(lhs.c1, power);
    const coeff = FP12_FROBENIUS_COEFFICIENTS[power % 12];
    return {
      c0: r0,
      c1: Fp6.create({
        c0: Fp2.mul(c0, coeff),
        c1: Fp2.mul(c1, coeff),
        c2: Fp2.mul(c2, coeff),
      }),
    };
  },
  // Sparse multiplication
  multiplyBy014: ({ c0, c1 }, o0: Fp2, o1: Fp2, o4: Fp2) => {
    let t0 = Fp6.multiplyBy01(c0, o0, o1);
    let t1 = Fp6.multiplyBy1(c1, o4);
    return {
      c0: Fp6.add(Fp6.mulByNonresidue(t1), t0), // T1 * v + T0
      // (c1 + c0) * [o0, o1+o4] - T0 - T1
      c1: Fp6.sub(Fp6.sub(Fp6.multiplyBy01(Fp6.add(c1, c0), o0, Fp2.add(o1, o4)), t0), t1),
    };
  },
  multiplyByFp2: ({ c0, c1 }, rhs: Fp2): Fp12 => ({
    c0: Fp6.multiplyByFp2(c0, rhs),
    c1: Fp6.multiplyByFp2(c1, rhs),
  }),
  conjugate: ({ c0, c1 }): Fp12 => ({ c0, c1: Fp6.neg(c1) }),

  // A cyclotomic group is a subgroup of Fp^n defined by
  //   GΦₙ(p) = {α ∈ Fpⁿ : α^Φₙ(p) = 1}
  // The result of any pairing is in a cyclotomic subgroup
  // https://eprint.iacr.org/2009/565.pdf
  _cyclotomicSquare: ({ c0, c1 }): Fp12 => {
    const { c0: c0c0, c1: c0c1, c2: c0c2 } = c0;
    const { c0: c1c0, c1: c1c1, c2: c1c2 } = c1;
    const { first: t3, second: t4 } = Fp4Square(c0c0, c1c1);
    const { first: t5, second: t6 } = Fp4Square(c1c0, c0c2);
    const { first: t7, second: t8 } = Fp4Square(c0c1, c1c2);
    let t9 = Fp2.mulByNonresidue(t8); // T8 * (u + 1)
    return {
      c0: Fp6.create({
        c0: Fp2.add(Fp2.mul(Fp2.sub(t3, c0c0), _2n), t3), // 2 * (T3 - c0c0)  + T3
        c1: Fp2.add(Fp2.mul(Fp2.sub(t5, c0c1), _2n), t5), // 2 * (T5 - c0c1)  + T5
        c2: Fp2.add(Fp2.mul(Fp2.sub(t7, c0c2), _2n), t7),
      }), // 2 * (T7 - c0c2)  + T7
      c1: Fp6.create({
        c0: Fp2.add(Fp2.mul(Fp2.add(t9, c1c0), _2n), t9), // 2 * (T9 + c1c0) + T9
        c1: Fp2.add(Fp2.mul(Fp2.add(t4, c1c1), _2n), t4), // 2 * (T4 + c1c1) + T4
        c2: Fp2.add(Fp2.mul(Fp2.add(t6, c1c2), _2n), t6),
      }),
    }; // 2 * (T6 + c1c2) + T6
  },
  _cyclotomicExp(num, n) {
    let z = Fp12.ONE;
    for (let i = BLS_X_LEN - 1; i >= 0; i--) {
      z = Fp12._cyclotomicSquare(z);
      if (bitGet(n, i)) z = Fp12.mul(z, num);
    }
    return z;
  },
  // https://eprint.iacr.org/2010/354.pdf
  // https://eprint.iacr.org/2009/565.pdf
  finalExponentiate: (num) => {
    const x = BLS_X;
    // this^(q⁶) / this
    const t0 = Fp12.div(Fp12.frobeniusMap(num, 6), num);
    // t0^(q²) * t0
    const t1 = Fp12.mul(Fp12.frobeniusMap(t0, 2), t0);
    const t2 = Fp12.conjugate(Fp12._cyclotomicExp(t1, x));
    const t3 = Fp12.mul(Fp12.conjugate(Fp12._cyclotomicSquare(t1)), t2);
    const t4 = Fp12.conjugate(Fp12._cyclotomicExp(t3, x));
    const t5 = Fp12.conjugate(Fp12._cyclotomicExp(t4, x));
    const t6 = Fp12.mul(Fp12.conjugate(Fp12._cyclotomicExp(t5, x)), Fp12._cyclotomicSquare(t2));
    const t7 = Fp12.conjugate(Fp12._cyclotomicExp(t6, x));
    const t2_t5_pow_q2 = Fp12.frobeniusMap(Fp12.mul(t2, t5), 2);
    const t4_t1_pow_q3 = Fp12.frobeniusMap(Fp12.mul(t4, t1), 3);
    const t6_t1c_pow_q1 = Fp12.frobeniusMap(Fp12.mul(t6, Fp12.conjugate(t1)), 1);
    const t7_t3c_t1 = Fp12.mul(Fp12.mul(t7, Fp12.conjugate(t3)), t1);
    // (t2 * t5)^(q²) * (t4 * t1)^(q³) * (t6 * t1.conj)^(q^1) * t7 * t3.conj * t1
    return Fp12.mul(Fp12.mul(Fp12.mul(t2_t5_pow_q2, t4_t1_pow_q3), t6_t1c_pow_q1), t7_t3c_t1);
  },
};
const FP12_FROBENIUS_COEFFICIENTS = [
  [BigInt('0x1'), BigInt('0x0')],
  [
    BigInt(
      '0x1904d3bf02bb0667c231beb4202c0d1f0fd603fd3cbd5f4f7b2443d784bab9c4f67ea53d63e7813d8d0775ed92235fb8'
    ),
    BigInt(
      '0x00fc3e2b36c4e03288e9e902231f9fb854a14787b6c7b36fec0c8ec971f63c5f282d5ac14d6c7ec22cf78a126ddc4af3'
    ),
  ],
  [
    BigInt(
      '0x00000000000000005f19672fdf76ce51ba69c6076a0f77eaddb3a93be6f89688de17d813620a00022e01fffffffeffff'
    ),
    BigInt('0x0'),
  ],
  [
    BigInt(
      '0x135203e60180a68ee2e9c448d77a2cd91c3dedd930b1cf60ef396489f61eb45e304466cf3e67fa0af1ee7b04121bdea2'
    ),
    BigInt(
      '0x06af0e0437ff400b6831e36d6bd17ffe48395dabc2d3435e77f76e17009241c5ee67992f72ec05f4c81084fbede3cc09'
    ),
  ],
  [
    BigInt(
      '0x00000000000000005f19672fdf76ce51ba69c6076a0f77eaddb3a93be6f89688de17d813620a00022e01fffffffefffe'
    ),
    BigInt('0x0'),
  ],
  [
    BigInt(
      '0x144e4211384586c16bd3ad4afa99cc9170df3560e77982d0db45f3536814f0bd5871c1908bd478cd1ee605167ff82995'
    ),
    BigInt(
      '0x05b2cfd9013a5fd8df47fa6b48b1e045f39816240c0b8fee8beadf4d8e9c0566c63a3e6e257f87329b18fae980078116'
    ),
  ],
  [
    BigInt(
      '0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaaa'
    ),
    BigInt('0x0'),
  ],
  [
    BigInt(
      '0x00fc3e2b36c4e03288e9e902231f9fb854a14787b6c7b36fec0c8ec971f63c5f282d5ac14d6c7ec22cf78a126ddc4af3'
    ),
    BigInt(
      '0x1904d3bf02bb0667c231beb4202c0d1f0fd603fd3cbd5f4f7b2443d784bab9c4f67ea53d63e7813d8d0775ed92235fb8'
    ),
  ],
  [
    BigInt(
      '0x1a0111ea397fe699ec02408663d4de85aa0d857d89759ad4897d29650fb85f9b409427eb4f49fffd8bfd00000000aaac'
    ),
    BigInt('0x0'),
  ],
  [
    BigInt(
      '0x06af0e0437ff400b6831e36d6bd17ffe48395dabc2d3435e77f76e17009241c5ee67992f72ec05f4c81084fbede3cc09'
    ),
    BigInt(
      '0x135203e60180a68ee2e9c448d77a2cd91c3dedd930b1cf60ef396489f61eb45e304466cf3e67fa0af1ee7b04121bdea2'
    ),
  ],
  [
    BigInt(
      '0x1a0111ea397fe699ec02408663d4de85aa0d857d89759ad4897d29650fb85f9b409427eb4f49fffd8bfd00000000aaad'
    ),
    BigInt('0x0'),
  ],
  [
    BigInt(
      '0x05b2cfd9013a5fd8df47fa6b48b1e045f39816240c0b8fee8beadf4d8e9c0566c63a3e6e257f87329b18fae980078116'
    ),
    BigInt(
      '0x144e4211384586c16bd3ad4afa99cc9170df3560e77982d0db45f3536814f0bd5871c1908bd478cd1ee605167ff82995'
    ),
  ],
].map((n) => Fp2.fromBigTuple(n));
// END OF CURVE FIELDS

// HashToCurve

// 3-isogeny map from E' to E https://www.rfc-editor.org/rfc/rfc9380#appendix-E.3
const isogenyMapG2 = isogenyMap(
  Fp2,
  [
    // xNum
    [
      [
        '0x5c759507e8e333ebb5b7a9a47d7ed8532c52d39fd3a042a88b58423c50ae15d5c2638e343d9c71c6238aaaaaaaa97d6',
        '0x5c759507e8e333ebb5b7a9a47d7ed8532c52d39fd3a042a88b58423c50ae15d5c2638e343d9c71c6238aaaaaaaa97d6',
      ],
      [
        '0x0',
        '0x11560bf17baa99bc32126fced787c88f984f87adf7ae0c7f9a208c6b4f20a4181472aaa9cb8d555526a9ffffffffc71a',
      ],
      [
        '0x11560bf17baa99bc32126fced787c88f984f87adf7ae0c7f9a208c6b4f20a4181472aaa9cb8d555526a9ffffffffc71e',
        '0x8ab05f8bdd54cde190937e76bc3e447cc27c3d6fbd7063fcd104635a790520c0a395554e5c6aaaa9354ffffffffe38d',
      ],
      [
        '0x171d6541fa38ccfaed6dea691f5fb614cb14b4e7f4e810aa22d6108f142b85757098e38d0f671c7188e2aaaaaaaa5ed1',
        '0x0',
      ],
    ],
    // xDen
    [
      [
        '0x0',
        '0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaa63',
      ],
      [
        '0xc',
        '0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaa9f',
      ],
      ['0x1', '0x0'], // LAST 1
    ],
    // yNum
    [
      [
        '0x1530477c7ab4113b59a4c18b076d11930f7da5d4a07f649bf54439d87d27e500fc8c25ebf8c92f6812cfc71c71c6d706',
        '0x1530477c7ab4113b59a4c18b076d11930f7da5d4a07f649bf54439d87d27e500fc8c25ebf8c92f6812cfc71c71c6d706',
      ],
      [
        '0x0',
        '0x5c759507e8e333ebb5b7a9a47d7ed8532c52d39fd3a042a88b58423c50ae15d5c2638e343d9c71c6238aaaaaaaa97be',
      ],
      [
        '0x11560bf17baa99bc32126fced787c88f984f87adf7ae0c7f9a208c6b4f20a4181472aaa9cb8d555526a9ffffffffc71c',
        '0x8ab05f8bdd54cde190937e76bc3e447cc27c3d6fbd7063fcd104635a790520c0a395554e5c6aaaa9354ffffffffe38f',
      ],
      [
        '0x124c9ad43b6cf79bfbf7043de3811ad0761b0f37a1e26286b0e977c69aa274524e79097a56dc4bd9e1b371c71c718b10',
        '0x0',
      ],
    ],
    // yDen
    [
      [
        '0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffa8fb',
        '0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffa8fb',
      ],
      [
        '0x0',
        '0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffa9d3',
      ],
      [
        '0x12',
        '0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaa99',
      ],
      ['0x1', '0x0'], // LAST 1
    ],
  ].map((i) => i.map((pair) => Fp2.fromBigTuple(pair.map(BigInt)))) as [Fp2[], Fp2[], Fp2[], Fp2[]]
);
// 11-isogeny map from E' to E
const isogenyMapG1 = isogenyMap(
  Fp,
  [
    // xNum
    [
      '0x11a05f2b1e833340b809101dd99815856b303e88a2d7005ff2627b56cdb4e2c85610c2d5f2e62d6eaeac1662734649b7',
      '0x17294ed3e943ab2f0588bab22147a81c7c17e75b2f6a8417f565e33c70d1e86b4838f2a6f318c356e834eef1b3cb83bb',
      '0xd54005db97678ec1d1048c5d10a9a1bce032473295983e56878e501ec68e25c958c3e3d2a09729fe0179f9dac9edcb0',
      '0x1778e7166fcc6db74e0609d307e55412d7f5e4656a8dbf25f1b33289f1b330835336e25ce3107193c5b388641d9b6861',
      '0xe99726a3199f4436642b4b3e4118e5499db995a1257fb3f086eeb65982fac18985a286f301e77c451154ce9ac8895d9',
      '0x1630c3250d7313ff01d1201bf7a74ab5db3cb17dd952799b9ed3ab9097e68f90a0870d2dcae73d19cd13c1c66f652983',
      '0xd6ed6553fe44d296a3726c38ae652bfb11586264f0f8ce19008e218f9c86b2a8da25128c1052ecaddd7f225a139ed84',
      '0x17b81e7701abdbe2e8743884d1117e53356de5ab275b4db1a682c62ef0f2753339b7c8f8c8f475af9ccb5618e3f0c88e',
      '0x80d3cf1f9a78fc47b90b33563be990dc43b756ce79f5574a2c596c928c5d1de4fa295f296b74e956d71986a8497e317',
      '0x169b1f8e1bcfa7c42e0c37515d138f22dd2ecb803a0c5c99676314baf4bb1b7fa3190b2edc0327797f241067be390c9e',
      '0x10321da079ce07e272d8ec09d2565b0dfa7dccdde6787f96d50af36003b14866f69b771f8c285decca67df3f1605fb7b',
      '0x6e08c248e260e70bd1e962381edee3d31d79d7e22c837bc23c0bf1bc24c6b68c24b1b80b64d391fa9c8ba2e8ba2d229',
    ],
    // xDen
    [
      '0x8ca8d548cff19ae18b2e62f4bd3fa6f01d5ef4ba35b48ba9c9588617fc8ac62b558d681be343df8993cf9fa40d21b1c',
      '0x12561a5deb559c4348b4711298e536367041e8ca0cf0800c0126c2588c48bf5713daa8846cb026e9e5c8276ec82b3bff',
      '0xb2962fe57a3225e8137e629bff2991f6f89416f5a718cd1fca64e00b11aceacd6a3d0967c94fedcfcc239ba5cb83e19',
      '0x3425581a58ae2fec83aafef7c40eb545b08243f16b1655154cca8abc28d6fd04976d5243eecf5c4130de8938dc62cd8',
      '0x13a8e162022914a80a6f1d5f43e7a07dffdfc759a12062bb8d6b44e833b306da9bd29ba81f35781d539d395b3532a21e',
      '0xe7355f8e4e667b955390f7f0506c6e9395735e9ce9cad4d0a43bcef24b8982f7400d24bc4228f11c02df9a29f6304a5',
      '0x772caacf16936190f3e0c63e0596721570f5799af53a1894e2e073062aede9cea73b3538f0de06cec2574496ee84a3a',
      '0x14a7ac2a9d64a8b230b3f5b074cf01996e7f63c21bca68a81996e1cdf9822c580fa5b9489d11e2d311f7d99bbdcc5a5e',
      '0xa10ecf6ada54f825e920b3dafc7a3cce07f8d1d7161366b74100da67f39883503826692abba43704776ec3a79a1d641',
      '0x95fc13ab9e92ad4476d6e3eb3a56680f682b4ee96f7d03776df533978f31c1593174e4b4b7865002d6384d168ecdd0a',
      '0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001', // LAST 1
    ],
    // yNum
    [
      '0x90d97c81ba24ee0259d1f094980dcfa11ad138e48a869522b52af6c956543d3cd0c7aee9b3ba3c2be9845719707bb33',
      '0x134996a104ee5811d51036d776fb46831223e96c254f383d0f906343eb67ad34d6c56711962fa8bfe097e75a2e41c696',
      '0xcc786baa966e66f4a384c86a3b49942552e2d658a31ce2c344be4b91400da7d26d521628b00523b8dfe240c72de1f6',
      '0x1f86376e8981c217898751ad8746757d42aa7b90eeb791c09e4a3ec03251cf9de405aba9ec61deca6355c77b0e5f4cb',
      '0x8cc03fdefe0ff135caf4fe2a21529c4195536fbe3ce50b879833fd221351adc2ee7f8dc099040a841b6daecf2e8fedb',
      '0x16603fca40634b6a2211e11db8f0a6a074a7d0d4afadb7bd76505c3d3ad5544e203f6326c95a807299b23ab13633a5f0',
      '0x4ab0b9bcfac1bbcb2c977d027796b3ce75bb8ca2be184cb5231413c4d634f3747a87ac2460f415ec961f8855fe9d6f2',
      '0x987c8d5333ab86fde9926bd2ca6c674170a05bfe3bdd81ffd038da6c26c842642f64550fedfe935a15e4ca31870fb29',
      '0x9fc4018bd96684be88c9e221e4da1bb8f3abd16679dc26c1e8b6e6a1f20cabe69d65201c78607a360370e577bdba587',
      '0xe1bba7a1186bdb5223abde7ada14a23c42a0ca7915af6fe06985e7ed1e4d43b9b3f7055dd4eba6f2bafaaebca731c30',
      '0x19713e47937cd1be0dfd0b8f1d43fb93cd2fcbcb6caf493fd1183e416389e61031bf3a5cce3fbafce813711ad011c132',
      '0x18b46a908f36f6deb918c143fed2edcc523559b8aaf0c2462e6bfe7f911f643249d9cdf41b44d606ce07c8a4d0074d8e',
      '0xb182cac101b9399d155096004f53f447aa7b12a3426b08ec02710e807b4633f06c851c1919211f20d4c04f00b971ef8',
      '0x245a394ad1eca9b72fc00ae7be315dc757b3b080d4c158013e6632d3c40659cc6cf90ad1c232a6442d9d3f5db980133',
      '0x5c129645e44cf1102a159f748c4a3fc5e673d81d7e86568d9ab0f5d396a7ce46ba1049b6579afb7866b1e715475224b',
      '0x15e6be4e990f03ce4ea50b3b42df2eb5cb181d8f84965a3957add4fa95af01b2b665027efec01c7704b456be69c8b604',
    ],
    // yDen
    [
      '0x16112c4c3a9c98b252181140fad0eae9601a6de578980be6eec3232b5be72e7a07f3688ef60c206d01479253b03663c1',
      '0x1962d75c2381201e1a0cbd6c43c348b885c84ff731c4d59ca4a10356f453e01f78a4260763529e3532f6102c2e49a03d',
      '0x58df3306640da276faaae7d6e8eb15778c4855551ae7f310c35a5dd279cd2eca6757cd636f96f891e2538b53dbf67f2',
      '0x16b7d288798e5395f20d23bf89edb4d1d115c5dbddbcd30e123da489e726af41727364f2c28297ada8d26d98445f5416',
      '0xbe0e079545f43e4b00cc912f8228ddcc6d19c9f0f69bbb0542eda0fc9dec916a20b15dc0fd2ededda39142311a5001d',
      '0x8d9e5297186db2d9fb266eaac783182b70152c65550d881c5ecd87b6f0f5a6449f38db9dfa9cce202c6477faaf9b7ac',
      '0x166007c08a99db2fc3ba8734ace9824b5eecfdfa8d0cf8ef5dd365bc400a0051d5fa9c01a58b1fb93d1a1399126a775c',
      '0x16a3ef08be3ea7ea03bcddfabba6ff6ee5a4375efa1f4fd7feb34fd206357132b920f5b00801dee460ee415a15812ed9',
      '0x1866c8ed336c61231a1be54fd1d74cc4f9fb0ce4c6af5920abc5750c4bf39b4852cfe2f7bb9248836b233d9d55535d4a',
      '0x167a55cda70a6e1cea820597d94a84903216f763e13d87bb5308592e7ea7d4fbc7385ea3d529b35e346ef48bb8913f55',
      '0x4d2f259eea405bd48f010a01ad2911d9c6dd039bb61a6290e591b36e636a5c871a5c29f4f83060400f8b49cba8f6aa8',
      '0xaccbb67481d033ff5852c1e48c50c477f94ff8aefce42d28c0f9a88cea7913516f968986f7ebbea9684b529e2561092',
      '0xad6b9514c767fe3c3613144b45f1496543346d98adf02267d5ceef9a00d9b8693000763e3b90ac11e99b138573345cc',
      '0x2660400eb2e4f3b628bdd0d53cd76f2bf565b94e72927c1cb748df27942480e420517bd8714cc80d1fadc1326ed06f7',
      '0xe0fa1d816ddc03e6b24255e0d7819c171c40f65e273b853324efcd6356caa205ca2f570f13497804415473a1d634b8f',
      '0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001', // LAST 1
    ],
  ].map((i) => i.map((j) => BigInt(j))) as [Fp[], Fp[], Fp[], Fp[]]
);

// SWU Map - Fp2 to G2': y² = x³ + 240i * x + 1012 + 1012i
const G2_SWU = mapToCurveSimpleSWU(Fp2, {
  A: Fp2.create({ c0: Fp.create(_0n), c1: Fp.create(BigInt(240)) }), // A' = 240 * I
  B: Fp2.create({ c0: Fp.create(BigInt(1012)), c1: Fp.create(BigInt(1012)) }), // B' = 1012 * (1 + I)
  Z: Fp2.create({ c0: Fp.create(BigInt(-2)), c1: Fp.create(BigInt(-1)) }), // Z: -(2 + I)
});
// Optimized SWU Map - Fp to G1
const G1_SWU = mapToCurveSimpleSWU(Fp, {
  A: Fp.create(
    BigInt(
      '0x144698a3b8e9433d693a02c96d4982b0ea985383ee66a8d8e8981aefd881ac98936f8da0e0f97f5cf428082d584c1d'
    )
  ),
  B: Fp.create(
    BigInt(
      '0x12e2908d11688030018b12e8753eee3b2016c1f0f24f4070a0b9c14fcef35ef55a23215a316ceaa5d1cc48e98e172be0'
    )
  ),
  Z: Fp.create(BigInt(11)),
});

// Endomorphisms (for fast cofactor clearing)
// Ψ(P) endomorphism
const ut_root = Fp6.create({ c0: Fp2.ZERO, c1: Fp2.ONE, c2: Fp2.ZERO });
const wsq = Fp12.create({ c0: ut_root, c1: Fp6.ZERO });
const wcu = Fp12.create({ c0: Fp6.ZERO, c1: ut_root });
const [wsq_inv, wcu_inv] = Fp12.invertBatch([wsq, wcu]);
function psi(x: Fp2, y: Fp2): [Fp2, Fp2] {
  // Untwist Fp2->Fp12 && frobenius(1) && twist back
  const x2 = Fp12.mul(Fp12.frobeniusMap(Fp12.multiplyByFp2(wsq_inv, x), 1), wsq).c0.c0;
  const y2 = Fp12.mul(Fp12.frobeniusMap(Fp12.multiplyByFp2(wcu_inv, y), 1), wcu).c0.c0;
  return [x2, y2];
}
// Ψ endomorphism
function G2psi(c: ProjConstructor<Fp2>, P: ProjPointType<Fp2>) {
  const affine = P.toAffine();
  const p = psi(affine.x, affine.y);
  return new c(p[0], p[1], Fp2.ONE);
}
// Ψ²(P) endomorphism
// 1 / F2(2)^((p-1)/3) in GF(p²)
const PSI2_C1 = BigInt(
  '0x1a0111ea397fe699ec02408663d4de85aa0d857d89759ad4897d29650fb85f9b409427eb4f49fffd8bfd00000000aaac'
);

function psi2(x: Fp2, y: Fp2): [Fp2, Fp2] {
  return [Fp2.mul(x, PSI2_C1), Fp2.neg(y)];
}
function G2psi2(c: ProjConstructor<Fp2>, P: ProjPointType<Fp2>) {
  const affine = P.toAffine();
  const p = psi2(affine.x, affine.y);
  return new c(p[0], p[1], Fp2.ONE);
}

// Default hash_to_field options are for hash to G2.
//
// Parameter definitions are in section 5.3 of the spec unless otherwise noted.
// Parameter values come from section 8.8.2 of the spec.
// https://www.rfc-editor.org/rfc/rfc9380#section-8.8.2
//
// Base field F is GF(p^m)
// p = 0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaab
// m = 2 (or 1 for G1 see section 8.8.1)
// k = 128
const htfDefaults = Object.freeze({
  // DST: a domain separation tag
  // defined in section 2.2.5
  // Use utils.getDSTLabel(), utils.setDSTLabel(value)
  DST: 'BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_NUL_',
  encodeDST: 'BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_NUL_',
  // p: the characteristic of F
  //    where F is a finite field of characteristic p and order q = p^m
  p: Fp.ORDER,
  // m: the extension degree of F, m >= 1
  //     where F is a finite field of characteristic p and order q = p^m
  m: 2,
  // k: the target security level for the suite in bits
  // defined in section 5.1
  k: 128,
  // option to use a message that has already been processed by
  // expand_message_xmd
  expand: 'xmd',
  // Hash functions for: expand_message_xmd is appropriate for use with a
  // wide range of hash functions, including SHA-2, SHA-3, BLAKE2, and others.
  // BBS+ uses blake2: https://github.com/hyperledger/aries-framework-go/issues/2247
  hash: sha256,
} as const);

// Encoding utils
// Point on G1 curve: (x, y)
const C_BIT_POS = Fp.BITS; // C_bit, compression bit for serialization flag
const I_BIT_POS = Fp.BITS + 1; // I_bit, point-at-infinity bit for serialization flag
const S_BIT_POS = Fp.BITS + 2; // S_bit, sign bit for serialization flag
// Compressed point of infinity
const COMPRESSED_ZERO = Fp.toBytes(bitSet(bitSet(_0n, I_BIT_POS, true), S_BIT_POS, true)); // set compressed & point-at-infinity bits

function signatureG2ToRawBytes(point: ProjPointType<Fp2>) {
  // NOTE: by some reasons it was missed in bls12-381, looks like bug
  point.assertValidity();
  const len = Fp.BYTES;
  if (point.equals(bls12_381.G2.ProjectivePoint.ZERO))
    return concatB(COMPRESSED_ZERO, numberToBytesBE(_0n, len));
  const { x, y } = point.toAffine();
  const { re: x0, im: x1 } = Fp2.reim(x);
  const { re: y0, im: y1 } = Fp2.reim(y);
  const tmp = y1 > _0n ? y1 * _2n : y0 * _2n;
  const aflag1 = Boolean((tmp / Fp.ORDER) & _1n);
  const z1 = bitSet(bitSet(x1, 381, aflag1), S_BIT_POS, true);
  const z2 = x0;
  return concatB(numberToBytesBE(z1, len), numberToBytesBE(z2, len));
}

// To verify curve parameters, see pairing-friendly-curves spec:
// https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-pairing-friendly-curves-11
// Basic math is done over finite fields over p.
// More complicated math is done over polynominal extension fields.
// To simplify calculations in Fp12, we construct extension tower:
// Fp₁₂ = Fp₆² => Fp₂³
// Fp(u) / (u² - β) where β = -1
// Fp₂(v) / (v³ - ξ) where ξ = u + 1
// Fp₆(w) / (w² - γ) where γ = v
// Here goes constants && point encoding format
export const bls12_381: CurveFn<Fp, Fp2, Fp6, Fp12> = bls({
  // Fields
  fields: {
    Fp,
    Fp2,
    Fp6,
    Fp12,
    Fr,
  },
  // G1 is the order-q subgroup of E1(Fp) : y² = x³ + 4, #E1(Fp) = h1q, where
  // characteristic; z + (z⁴ - z² + 1)(z - 1)²/3
  G1: {
    Fp,
    // cofactor; (z - 1)²/3
    h: BigInt('0x396c8c005555e1568c00aaab0000aaab'),
    // generator's coordinates
    // x = 3685416753713387016781088315183077757961620795782546409894578378688607592378376318836054947676345821548104185464507
    // y = 1339506544944476473020471379941921221584933875938349620426543736416511423956333506472724655353366534992391756441569
    Gx: BigInt(
      '0x17f1d3a73197d7942695638c4fa9ac0fc3688c4f9774b905a14e3a3f171bac586c55e83ff97a1aeffb3af00adb22c6bb'
    ),
    Gy: BigInt(
      '0x08b3f481e3aaa0f1a09e30ed741d8ae4fcf5e095d5d00af600db18cb2c04b3edd03cc744a2888ae40caa232946c5e7e1'
    ),
    a: Fp.ZERO,
    b: _4n,
    htfDefaults: { ...htfDefaults, m: 1 },
    wrapPrivateKey: true,
    allowInfinityPoint: true,
    // Checks is the point resides in prime-order subgroup.
    // point.isTorsionFree() should return true for valid points
    // It returns false for shitty points.
    // https://eprint.iacr.org/2021/1130.pdf
    isTorsionFree: (c, point): boolean => {
      // φ endomorphism
      const cubicRootOfUnityModP = BigInt(
        '0x5f19672fdf76ce51ba69c6076a0f77eaddb3a93be6f89688de17d813620a00022e01fffffffefffe'
      );
      const phi = new c(Fp.mul(point.px, cubicRootOfUnityModP), point.py, point.pz);

      // todo: unroll
      const xP = point.multiplyUnsafe(bls12_381.params.x).negate(); // [x]P
      const u2P = xP.multiplyUnsafe(bls12_381.params.x); // [u2]P
      return u2P.equals(phi);

      // https://eprint.iacr.org/2019/814.pdf
      // (z² − 1)/3
      // const c1 = BigInt('0x396c8c005555e1560000000055555555');
      // const P = this;
      // const S = P.sigma();
      // const Q = S.double();
      // const S2 = S.sigma();
      // // [(z² − 1)/3](2σ(P) − P − σ²(P)) − σ²(P) = O
      // const left = Q.subtract(P).subtract(S2).multiplyUnsafe(c1);
      // const C = left.subtract(S2);
      // return C.isZero();
    },
    // Clear cofactor of G1
    // https://eprint.iacr.org/2019/403
    clearCofactor: (_c, point) => {
      // return this.multiplyUnsafe(CURVE.h);
      return point.multiplyUnsafe(bls12_381.params.x).add(point); // x*P + P
    },
    mapToCurve: (scalars: bigint[]) => {
      const { x, y } = G1_SWU(Fp.create(scalars[0]));
      return isogenyMapG1(x, y);
    },
    fromBytes: (bytes: Uint8Array): AffinePoint<Fp> => {
      bytes = bytes.slice();
      if (bytes.length === 48) {
        // TODO: Fp.bytes
        const P = Fp.ORDER;
        const compressedValue = bytesToNumberBE(bytes);
        const bflag = bitGet(compressedValue, I_BIT_POS);
        // Zero
        if (bflag === _1n) return { x: _0n, y: _0n };
        const x = Fp.create(compressedValue & Fp.MASK);
        const right = Fp.add(Fp.pow(x, _3n), Fp.create(bls12_381.params.G1b)); // y² = x³ + b
        let y = Fp.sqrt(right);
        if (!y) throw new Error('Invalid compressed G1 point');
        const aflag = bitGet(compressedValue, C_BIT_POS);
        if ((y * _2n) / P !== aflag) y = Fp.neg(y);
        return { x: Fp.create(x), y: Fp.create(y) };
      } else if (bytes.length === 96) {
        // Check if the infinity flag is set
        if ((bytes[0] & (1 << 6)) !== 0) return bls12_381.G1.ProjectivePoint.ZERO.toAffine();
        const x = bytesToNumberBE(bytes.subarray(0, Fp.BYTES));
        const y = bytesToNumberBE(bytes.subarray(Fp.BYTES));
        return { x: Fp.create(x), y: Fp.create(y) };
      } else {
        throw new Error('Invalid point G1, expected 48/96 bytes');
      }
    },
    toBytes: (c, point, isCompressed) => {
      const isZero = point.equals(c.ZERO);
      const { x, y } = point.toAffine();
      if (isCompressed) {
        if (isZero) return COMPRESSED_ZERO.slice();
        const P = Fp.ORDER;
        let num;
        num = bitSet(x, C_BIT_POS, Boolean((y * _2n) / P)); // set aflag
        num = bitSet(num, S_BIT_POS, true);
        return numberToBytesBE(num, Fp.BYTES);
      } else {
        if (isZero) {
          // 2x PUBLIC_KEY_LENGTH
          const x = concatB(new Uint8Array([0x40]), new Uint8Array(2 * Fp.BYTES - 1));
          return x;
        } else {
          return concatB(numberToBytesBE(x, Fp.BYTES), numberToBytesBE(y, Fp.BYTES));
        }
      }
    },
  },
  // G2 is the order-q subgroup of E2(Fp²) : y² = x³+4(1+√−1),
  // where Fp2 is Fp[√−1]/(x2+1). #E2(Fp2 ) = h2q, where
  // G² - 1
  // h2q
  G2: {
    Fp: Fp2,
    // cofactor
    h: BigInt(
      '0x5d543a95414e7f1091d50792876a202cd91de4547085abaa68a205b2e5a7ddfa628f1cb4d9e82ef21537e293a6691ae1616ec6e786f0c70cf1c38e31c7238e5'
    ),
    Gx: Fp2.fromBigTuple([
      BigInt(
        '0x024aa2b2f08f0a91260805272dc51051c6e47ad4fa403b02b4510b647ae3d1770bac0326a805bbefd48056c8c121bdb8'
      ),
      BigInt(
        '0x13e02b6052719f607dacd3a088274f65596bd0d09920b61ab5da61bbdc7f5049334cf11213945d57e5ac7d055d042b7e'
      ),
    ]),
    // y =
    // 927553665492332455747201965776037880757740193453592970025027978793976877002675564980949289727957565575433344219582,
    // 1985150602287291935568054521177171638300868978215655730859378665066344726373823718423869104263333984641494340347905
    Gy: Fp2.fromBigTuple([
      BigInt(
        '0x0ce5d527727d6e118cc9cdc6da2e351aadfd9baa8cbdd3a76d429a695160d12c923ac9cc3baca289e193548608b82801'
      ),
      BigInt(
        '0x0606c4a02ea734cc32acd2b02bc28b99cb3e287e85a763af267492ab572e99ab3f370d275cec1da1aaa9075ff05f79be'
      ),
    ]),
    a: Fp2.ZERO,
    b: Fp2.fromBigTuple([_4n, _4n]),
    hEff: BigInt(
      '0xbc69f08f2ee75b3584c6a0ea91b352888e2a8e9145ad7689986ff031508ffe1329c2f178731db956d82bf015d1212b02ec0ec69d7477c1ae954cbc06689f6a359894c0adebbf6b4e8020005aaa95551'
    ),
    htfDefaults: { ...htfDefaults },
    wrapPrivateKey: true,
    allowInfinityPoint: true,
    mapToCurve: (scalars: bigint[]) => {
      const { x, y } = G2_SWU(Fp2.fromBigTuple(scalars));
      return isogenyMapG2(x, y);
    },
    // Checks is the point resides in prime-order subgroup.
    // point.isTorsionFree() should return true for valid points
    // It returns false for shitty points.
    // https://eprint.iacr.org/2021/1130.pdf
    isTorsionFree: (c, P): boolean => {
      return P.multiplyUnsafe(bls12_381.params.x).negate().equals(G2psi(c, P)); // ψ(P) == [u](P)
      // Older version: https://eprint.iacr.org/2019/814.pdf
      // Ψ²(P) => Ψ³(P) => [z]Ψ³(P) where z = -x => [z]Ψ³(P) - Ψ²(P) + P == O
      // return P.psi2().psi().mulNegX().subtract(psi2).add(P).isZero();
    },
    // Maps the point into the prime-order subgroup G2.
    // clear_cofactor_bls12381_g2 from cfrg-hash-to-curve-11
    // https://eprint.iacr.org/2017/419.pdf
    // prettier-ignore
    clearCofactor: (c, P) => {
      const x = bls12_381.params.x;
      let t1 = P.multiplyUnsafe(x).negate();  // [-x]P
      let t2 = G2psi(c, P);                   // Ψ(P)
      let t3 = P.double();                    // 2P
      t3 = G2psi2(c, t3);                     // Ψ²(2P)
      t3 = t3.subtract(t2);                   // Ψ²(2P) - Ψ(P)
      t2 = t1.add(t2);                        // [-x]P + Ψ(P)
      t2 = t2.multiplyUnsafe(x).negate();     // [x²]P - [x]Ψ(P)
      t3 = t3.add(t2);                        // Ψ²(2P) - Ψ(P) + [x²]P - [x]Ψ(P)
      t3 = t3.subtract(t1);                   // Ψ²(2P) - Ψ(P) + [x²]P - [x]Ψ(P) + [x]P
      const Q = t3.subtract(P);               // Ψ²(2P) - Ψ(P) + [x²]P - [x]Ψ(P) + [x]P - 1P
      return Q;                               // [x²-x-1]P + [x-1]Ψ(P) + Ψ²(2P)
    },
    fromBytes: (bytes: Uint8Array): AffinePoint<Fp2> => {
      bytes = bytes.slice();
      const m_byte = bytes[0] & 0xe0;
      if (m_byte === 0x20 || m_byte === 0x60 || m_byte === 0xe0) {
        throw new Error('Invalid encoding flag: ' + m_byte);
      }
      const bitC = m_byte & 0x80; // compression bit
      const bitI = m_byte & 0x40; // point at infinity bit
      const bitS = m_byte & 0x20; // sign bit
      const L = Fp.BYTES;
      const slc = (b: Uint8Array, from: number, to?: number) => bytesToNumberBE(b.slice(from, to));
      if (bytes.length === 96 && bitC) {
        const b = bls12_381.params.G2b;
        const P = Fp.ORDER;

        bytes[0] = bytes[0] & 0x1f; // clear flags
        if (bitI) {
          // check that all bytes are 0
          if (bytes.reduce((p, c) => (p !== 0 ? c + 1 : c), 0) > 0) {
            throw new Error('Invalid compressed G2 point');
          }
          return { x: Fp2.ZERO, y: Fp2.ZERO };
        }
        const x_1 = slc(bytes, 0, L);
        const x_0 = slc(bytes, L, 2 * L);
        const x = Fp2.create({ c0: Fp.create(x_0), c1: Fp.create(x_1) });
        const right = Fp2.add(Fp2.pow(x, _3n), b); // y² = x³ + 4 * (u+1) = x³ + b
        let y = Fp2.sqrt(right);
        const Y_bit = y.c1 === _0n ? (y.c0 * _2n) / P : (y.c1 * _2n) / P ? _1n : _0n;
        y = bitS > 0 && Y_bit > 0 ? y : Fp2.neg(y);
        return { x, y };
      } else if (bytes.length === 192 && !bitC) {
        // Check if the infinity flag is set
        if ((bytes[0] & (1 << 6)) !== 0) {
          return { x: Fp2.ZERO, y: Fp2.ZERO };
        }
        const x1 = slc(bytes, 0, L);
        const x0 = slc(bytes, L, 2 * L);
        const y1 = slc(bytes, 2 * L, 3 * L);
        const y0 = slc(bytes, 3 * L, 4 * L);
        return { x: Fp2.fromBigTuple([x0, x1]), y: Fp2.fromBigTuple([y0, y1]) };
      } else {
        throw new Error('Invalid point G2, expected 96/192 bytes');
      }
    },
    toBytes: (c, point, isCompressed) => {
      const { BYTES: len, ORDER: P } = Fp;
      const isZero = point.equals(c.ZERO);
      const { x, y } = point.toAffine();
      if (isCompressed) {
        if (isZero) return concatB(COMPRESSED_ZERO, numberToBytesBE(_0n, len));
        const flag = Boolean(y.c1 === _0n ? (y.c0 * _2n) / P : (y.c1 * _2n) / P);
        // set compressed & sign bits (looks like different offsets than for G1/Fp?)
        let x_1 = bitSet(x.c1, C_BIT_POS, flag);
        x_1 = bitSet(x_1, S_BIT_POS, true);
        return concatB(numberToBytesBE(x_1, len), numberToBytesBE(x.c0, len));
      } else {
        if (isZero) return concatB(new Uint8Array([0x40]), new Uint8Array(4 * len - 1)); // bytes[0] |= 1 << 6;
        const { re: x0, im: x1 } = Fp2.reim(x);
        const { re: y0, im: y1 } = Fp2.reim(y);
        return concatB(
          numberToBytesBE(x1, len),
          numberToBytesBE(x0, len),
          numberToBytesBE(y1, len),
          numberToBytesBE(y0, len)
        );
      }
    },
    Signature: {
      // TODO: Optimize, it's very slow because of sqrt.
      fromHex(hex: Hex): ProjPointType<Fp2> {
        hex = ensureBytes('signatureHex', hex);
        const P = Fp.ORDER;
        const half = hex.length / 2;
        if (half !== 48 && half !== 96)
          throw new Error('Invalid compressed signature length, must be 96 or 192');
        const z1 = bytesToNumberBE(hex.slice(0, half));
        const z2 = bytesToNumberBE(hex.slice(half));
        // Indicates the infinity point
        const bflag1 = bitGet(z1, I_BIT_POS);
        if (bflag1 === _1n) return bls12_381.G2.ProjectivePoint.ZERO;

        const x1 = Fp.create(z1 & Fp.MASK);
        const x2 = Fp.create(z2);
        const x = Fp2.create({ c0: x2, c1: x1 });
        const y2 = Fp2.add(Fp2.pow(x, _3n), bls12_381.params.G2b); // y² = x³ + 4
        // The slow part
        let y = Fp2.sqrt(y2);
        if (!y) throw new Error('Failed to find a square root');

        // Choose the y whose leftmost bit of the imaginary part is equal to the a_flag1
        // If y1 happens to be zero, then use the bit of y0
        const { re: y0, im: y1 } = Fp2.reim(y);
        const aflag1 = bitGet(z1, 381);
        const isGreater = y1 > _0n && (y1 * _2n) / P !== aflag1;
        const isZero = y1 === _0n && (y0 * _2n) / P !== aflag1;
        if (isGreater || isZero) y = Fp2.neg(y);
        const point = bls12_381.G2.ProjectivePoint.fromAffine({ x, y });
        point.assertValidity();
        return point;
      },
      toRawBytes(point: ProjPointType<Fp2>) {
        return signatureG2ToRawBytes(point);
      },
      toHex(point: ProjPointType<Fp2>) {
        return bytesToHex(signatureG2ToRawBytes(point));
      },
    },
  },
  params: {
    x: BLS_X, // The BLS parameter x for BLS12-381
    r: Fr.ORDER, // order; z⁴ − z² + 1; CURVE.n from other curves
  },
  htfDefaults,
  hash: sha256,
  randomBytes,
});
