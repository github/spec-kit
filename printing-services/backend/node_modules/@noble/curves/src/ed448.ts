/*! noble-curves - MIT License (c) 2022 Paul Miller (paulmillr.com) */
import { shake256 } from '@noble/hashes/sha3';
import { concatBytes, randomBytes, utf8ToBytes, wrapConstructor } from '@noble/hashes/utils';
import { ExtPointType, twistedEdwards } from './abstract/edwards.js';
import { mod, pow2, Field, isNegativeLE } from './abstract/modular.js';
import { montgomery } from './abstract/montgomery.js';
import { createHasher, htfBasicOpts, expand_message_xof } from './abstract/hash-to-curve.js';
import {
  bytesToHex,
  bytesToNumberLE,
  ensureBytes,
  equalBytes,
  Hex,
  numberToBytesLE,
} from './abstract/utils.js';
import { AffinePoint } from './abstract/curve.js';

/**
 * Edwards448 (not Ed448-Goldilocks) curve with following addons:
 * - X448 ECDH
 * - Decaf cofactor elimination
 * - Elligator hash-to-group / point indistinguishability
 * Conforms to RFC 8032 https://www.rfc-editor.org/rfc/rfc8032.html#section-5.2
 */

const shake256_114 = wrapConstructor(() => shake256.create({ dkLen: 114 }));
const shake256_64 = wrapConstructor(() => shake256.create({ dkLen: 64 }));
const ed448P = BigInt(
  '726838724295606890549323807888004534353641360687318060281490199180612328166730772686396383698676545930088884461843637361053498018365439'
);

// prettier-ignore
const _1n = BigInt(1), _2n = BigInt(2), _3n = BigInt(3), _4n = BigInt(4), _11n = BigInt(11);
// prettier-ignore
const _22n = BigInt(22), _44n = BigInt(44), _88n = BigInt(88), _223n = BigInt(223);

// powPminus3div4 calculates z = x^k mod p, where k = (p-3)/4.
// Used for efficient square root calculation.
// ((P-3)/4).toString(2) would produce bits [223x 1, 0, 222x 1]
function ed448_pow_Pminus3div4(x: bigint): bigint {
  const P = ed448P;
  const b2 = (x * x * x) % P;
  const b3 = (b2 * b2 * x) % P;
  const b6 = (pow2(b3, _3n, P) * b3) % P;
  const b9 = (pow2(b6, _3n, P) * b3) % P;
  const b11 = (pow2(b9, _2n, P) * b2) % P;
  const b22 = (pow2(b11, _11n, P) * b11) % P;
  const b44 = (pow2(b22, _22n, P) * b22) % P;
  const b88 = (pow2(b44, _44n, P) * b44) % P;
  const b176 = (pow2(b88, _88n, P) * b88) % P;
  const b220 = (pow2(b176, _44n, P) * b44) % P;
  const b222 = (pow2(b220, _2n, P) * b2) % P;
  const b223 = (pow2(b222, _1n, P) * x) % P;
  return (pow2(b223, _223n, P) * b222) % P;
}

function adjustScalarBytes(bytes: Uint8Array): Uint8Array {
  // Section 5: Likewise, for X448, set the two least significant bits of the first byte to 0, and the most
  // significant bit of the last byte to 1.
  bytes[0] &= 252; // 0b11111100
  // and the most significant bit of the last byte to 1.
  bytes[55] |= 128; // 0b10000000
  // NOTE: is is NOOP for 56 bytes scalars (X25519/X448)
  bytes[56] = 0; // Byte outside of group (456 buts vs 448 bits)
  return bytes;
}

// Constant-time ratio of u to v. Allows to combine inversion and square root u/√v.
// Uses algo from RFC8032 5.1.3.
function uvRatio(u: bigint, v: bigint): { isValid: boolean; value: bigint } {
  const P = ed448P;
  // https://www.rfc-editor.org/rfc/rfc8032#section-5.2.3
  // To compute the square root of (u/v), the first step is to compute the
  //   candidate root x = (u/v)^((p+1)/4).  This can be done using the
  // following trick, to use a single modular powering for both the
  // inversion of v and the square root:
  // x = (u/v)^((p+1)/4)   = u³v(u⁵v³)^((p-3)/4)   (mod p)
  const u2v = mod(u * u * v, P); // u²v
  const u3v = mod(u2v * u, P); // u³v
  const u5v3 = mod(u3v * u2v * v, P); // u⁵v³
  const root = ed448_pow_Pminus3div4(u5v3);
  const x = mod(u3v * root, P);
  // Verify that root is exists
  const x2 = mod(x * x, P); // x²
  // If vx² = u, the recovered x-coordinate is x.  Otherwise, no
  // square root exists, and the decoding fails.
  return { isValid: mod(x2 * v, P) === u, value: x };
}

const Fp = Field(ed448P, 456, true);

const ED448_DEF = {
  // Param: a
  a: BigInt(1),
  // -39081. Negative number is P - number
  d: BigInt(
    '726838724295606890549323807888004534353641360687318060281490199180612328166730772686396383698676545930088884461843637361053498018326358'
  ),
  // Finite field 𝔽p over which we'll do calculations; 2n**448n - 2n**224n - 1n
  Fp,
  // Subgroup order: how many points curve has;
  // 2n**446n - 13818066809895115352007386748515426880336692474882178609894547503885n
  n: BigInt(
    '181709681073901722637330951972001133588410340171829515070372549795146003961539585716195755291692375963310293709091662304773755859649779'
  ),
  nBitLength: 456,
  // Cofactor
  h: BigInt(4),
  // Base point (x, y) aka generator point
  Gx: BigInt(
    '224580040295924300187604334099896036246789641632564134246125461686950415467406032909029192869357953282578032075146446173674602635247710'
  ),
  Gy: BigInt(
    '298819210078481492676017930443930673437544040154080242095928241372331506189835876003536878655418784733982303233503462500531545062832660'
  ),
  // SHAKE256(dom4(phflag,context)||x, 114)
  hash: shake256_114,
  randomBytes,
  adjustScalarBytes,
  // dom4
  domain: (data: Uint8Array, ctx: Uint8Array, phflag: boolean) => {
    if (ctx.length > 255) throw new Error(`Context is too big: ${ctx.length}`);
    return concatBytes(
      utf8ToBytes('SigEd448'),
      new Uint8Array([phflag ? 1 : 0, ctx.length]),
      ctx,
      data
    );
  },
  uvRatio,
} as const;

export const ed448 = /* @__PURE__ */ twistedEdwards(ED448_DEF);
// NOTE: there is no ed448ctx, since ed448 supports ctx by default
export const ed448ph = /* @__PURE__ */ twistedEdwards({ ...ED448_DEF, prehash: shake256_64 });

export const x448 = /* @__PURE__ */ (() =>
  montgomery({
    a: BigInt(156326),
    montgomeryBits: 448,
    nByteLength: 57,
    P: ed448P,
    Gu: BigInt(5),
    powPminus2: (x: bigint): bigint => {
      const P = ed448P;
      const Pminus3div4 = ed448_pow_Pminus3div4(x);
      const Pminus3 = pow2(Pminus3div4, BigInt(2), P);
      return mod(Pminus3 * x, P); // Pminus3 * x = Pminus2
    },
    adjustScalarBytes,
    randomBytes,
  }))();

/**
 * Converts edwards448 public key to x448 public key. Uses formula:
 * * `(u, v) = ((y-1)/(y+1), sqrt(156324)*u/x)`
 * * `(x, y) = (sqrt(156324)*u/v, (1+u)/(1-u))`
 * @example
 *   const aPub = ed448.getPublicKey(utils.randomPrivateKey());
 *   x448.getSharedSecret(edwardsToMontgomery(aPub), edwardsToMontgomery(someonesPub))
 */
export function edwardsToMontgomeryPub(edwardsPub: string | Uint8Array): Uint8Array {
  const { y } = ed448.ExtendedPoint.fromHex(edwardsPub);
  const _1n = BigInt(1);
  return Fp.toBytes(Fp.create((y - _1n) * Fp.inv(y + _1n)));
}
export const edwardsToMontgomery = edwardsToMontgomeryPub; // deprecated

// Hash To Curve Elligator2 Map
const ELL2_C1 = (Fp.ORDER - BigInt(3)) / BigInt(4); // 1. c1 = (q - 3) / 4         # Integer arithmetic
const ELL2_J = BigInt(156326);
function map_to_curve_elligator2_curve448(u: bigint) {
  let tv1 = Fp.sqr(u); // 1.  tv1 = u^2
  let e1 = Fp.eql(tv1, Fp.ONE); // 2.   e1 = tv1 == 1
  tv1 = Fp.cmov(tv1, Fp.ZERO, e1); // 3.  tv1 = CMOV(tv1, 0, e1)  # If Z * u^2 == -1, set tv1 = 0
  let xd = Fp.sub(Fp.ONE, tv1); // 4.   xd = 1 - tv1
  let x1n = Fp.neg(ELL2_J); // 5.  x1n = -J
  let tv2 = Fp.sqr(xd); // 6.  tv2 = xd^2
  let gxd = Fp.mul(tv2, xd); // 7.  gxd = tv2 * xd          # gxd = xd^3
  let gx1 = Fp.mul(tv1, Fp.neg(ELL2_J)); // 8.  gx1 = -J * tv1          # x1n + J * xd
  gx1 = Fp.mul(gx1, x1n); // 9.  gx1 = gx1 * x1n         # x1n^2 + J * x1n * xd
  gx1 = Fp.add(gx1, tv2); // 10. gx1 = gx1 + tv2         # x1n^2 + J * x1n * xd + xd^2
  gx1 = Fp.mul(gx1, x1n); // 11. gx1 = gx1 * x1n         # x1n^3 + J * x1n^2 * xd + x1n * xd^2
  let tv3 = Fp.sqr(gxd); // 12. tv3 = gxd^2
  tv2 = Fp.mul(gx1, gxd); // 13. tv2 = gx1 * gxd         # gx1 * gxd
  tv3 = Fp.mul(tv3, tv2); // 14. tv3 = tv3 * tv2         # gx1 * gxd^3
  let y1 = Fp.pow(tv3, ELL2_C1); // 15.  y1 = tv3^c1            # (gx1 * gxd^3)^((p - 3) / 4)
  y1 = Fp.mul(y1, tv2); // 16.  y1 = y1 * tv2          # gx1 * gxd * (gx1 * gxd^3)^((p - 3) / 4)
  let x2n = Fp.mul(x1n, Fp.neg(tv1)); // 17. x2n = -tv1 * x1n        # x2 = x2n / xd = -1 * u^2 * x1n / xd
  let y2 = Fp.mul(y1, u); // 18.  y2 = y1 * u
  y2 = Fp.cmov(y2, Fp.ZERO, e1); // 19.  y2 = CMOV(y2, 0, e1)
  tv2 = Fp.sqr(y1); // 20. tv2 = y1^2
  tv2 = Fp.mul(tv2, gxd); // 21. tv2 = tv2 * gxd
  let e2 = Fp.eql(tv2, gx1); // 22.  e2 = tv2 == gx1
  let xn = Fp.cmov(x2n, x1n, e2); // 23.  xn = CMOV(x2n, x1n, e2)  # If e2, x = x1, else x = x2
  let y = Fp.cmov(y2, y1, e2); // 24.   y = CMOV(y2, y1, e2)    # If e2, y = y1, else y = y2
  let e3 = Fp.isOdd(y); // 25.  e3 = sgn0(y) == 1        # Fix sign of y
  y = Fp.cmov(y, Fp.neg(y), e2 !== e3); // 26.   y = CMOV(y, -y, e2 XOR e3)
  return { xn, xd, yn: y, yd: Fp.ONE }; // 27. return (xn, xd, y, 1)
}
function map_to_curve_elligator2_edwards448(u: bigint) {
  let { xn, xd, yn, yd } = map_to_curve_elligator2_curve448(u); // 1. (xn, xd, yn, yd) = map_to_curve_elligator2_curve448(u)
  let xn2 = Fp.sqr(xn); // 2.  xn2 = xn^2
  let xd2 = Fp.sqr(xd); // 3.  xd2 = xd^2
  let xd4 = Fp.sqr(xd2); // 4.  xd4 = xd2^2
  let yn2 = Fp.sqr(yn); // 5.  yn2 = yn^2
  let yd2 = Fp.sqr(yd); // 6.  yd2 = yd^2
  let xEn = Fp.sub(xn2, xd2); // 7.  xEn = xn2 - xd2
  let tv2 = Fp.sub(xEn, xd2); // 8.  tv2 = xEn - xd2
  xEn = Fp.mul(xEn, xd2); // 9.  xEn = xEn * xd2
  xEn = Fp.mul(xEn, yd); // 10. xEn = xEn * yd
  xEn = Fp.mul(xEn, yn); // 11. xEn = xEn * yn
  xEn = Fp.mul(xEn, _4n); // 12. xEn = xEn * 4
  tv2 = Fp.mul(tv2, xn2); // 13. tv2 = tv2 * xn2
  tv2 = Fp.mul(tv2, yd2); // 14. tv2 = tv2 * yd2
  let tv3 = Fp.mul(yn2, _4n); // 15. tv3 = 4 * yn2
  let tv1 = Fp.add(tv3, yd2); // 16. tv1 = tv3 + yd2
  tv1 = Fp.mul(tv1, xd4); // 17. tv1 = tv1 * xd4
  let xEd = Fp.add(tv1, tv2); // 18. xEd = tv1 + tv2
  tv2 = Fp.mul(tv2, xn); // 19. tv2 = tv2 * xn
  let tv4 = Fp.mul(xn, xd4); // 20. tv4 = xn * xd4
  let yEn = Fp.sub(tv3, yd2); // 21. yEn = tv3 - yd2
  yEn = Fp.mul(yEn, tv4); // 22. yEn = yEn * tv4
  yEn = Fp.sub(yEn, tv2); // 23. yEn = yEn - tv2
  tv1 = Fp.add(xn2, xd2); // 24. tv1 = xn2 + xd2
  tv1 = Fp.mul(tv1, xd2); // 25. tv1 = tv1 * xd2
  tv1 = Fp.mul(tv1, xd); // 26. tv1 = tv1 * xd
  tv1 = Fp.mul(tv1, yn2); // 27. tv1 = tv1 * yn2
  tv1 = Fp.mul(tv1, BigInt(-2)); // 28. tv1 = -2 * tv1
  let yEd = Fp.add(tv2, tv1); // 29. yEd = tv2 + tv1
  tv4 = Fp.mul(tv4, yd2); // 30. tv4 = tv4 * yd2
  yEd = Fp.add(yEd, tv4); // 31. yEd = yEd + tv4
  tv1 = Fp.mul(xEd, yEd); // 32. tv1 = xEd * yEd
  let e = Fp.eql(tv1, Fp.ZERO); // 33.   e = tv1 == 0
  xEn = Fp.cmov(xEn, Fp.ZERO, e); // 34. xEn = CMOV(xEn, 0, e)
  xEd = Fp.cmov(xEd, Fp.ONE, e); // 35. xEd = CMOV(xEd, 1, e)
  yEn = Fp.cmov(yEn, Fp.ONE, e); // 36. yEn = CMOV(yEn, 1, e)
  yEd = Fp.cmov(yEd, Fp.ONE, e); // 37. yEd = CMOV(yEd, 1, e)

  const inv = Fp.invertBatch([xEd, yEd]); // batch division
  return { x: Fp.mul(xEn, inv[0]), y: Fp.mul(yEn, inv[1]) }; // 38. return (xEn, xEd, yEn, yEd)
}

const htf = /* @__PURE__ */ (() =>
  createHasher(
    ed448.ExtendedPoint,
    (scalars: bigint[]) => map_to_curve_elligator2_edwards448(scalars[0]),
    {
      DST: 'edwards448_XOF:SHAKE256_ELL2_RO_',
      encodeDST: 'edwards448_XOF:SHAKE256_ELL2_NU_',
      p: Fp.ORDER,
      m: 1,
      k: 224,
      expand: 'xof',
      hash: shake256,
    }
  ))();
export const hashToCurve = /* @__PURE__ */ (() => htf.hashToCurve)();
export const encodeToCurve = /* @__PURE__ */ (() => htf.encodeToCurve)();

function assertDcfPoint(other: unknown) {
  if (!(other instanceof DcfPoint)) throw new Error('DecafPoint expected');
}

// 1-d
const ONE_MINUS_D = BigInt('39082');
// 1-2d
const ONE_MINUS_TWO_D = BigInt('78163');
// √(-d)
const SQRT_MINUS_D = BigInt(
  '98944233647732219769177004876929019128417576295529901074099889598043702116001257856802131563896515373927712232092845883226922417596214'
);
// 1 / √(-d)
const INVSQRT_MINUS_D = BigInt(
  '315019913931389607337177038330951043522456072897266928557328499619017160722351061360252776265186336876723201881398623946864393857820716'
);
// Calculates 1/√(number)
const invertSqrt = (number: bigint) => uvRatio(_1n, number);

const MAX_448B = BigInt(
  '0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
);
const bytes448ToNumberLE = (bytes: Uint8Array) =>
  ed448.CURVE.Fp.create(bytesToNumberLE(bytes) & MAX_448B);

type ExtendedPoint = ExtPointType;

// Computes Elligator map for Decaf
// https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-ristretto255-decaf448-07#name-element-derivation-2
function calcElligatorDecafMap(r0: bigint): ExtendedPoint {
  const { d } = ed448.CURVE;
  const P = ed448.CURVE.Fp.ORDER;
  const mod = ed448.CURVE.Fp.create;

  const r = mod(-(r0 * r0)); // 1
  const u0 = mod(d * (r - _1n)); // 2
  const u1 = mod((u0 + _1n) * (u0 - r)); // 3

  const { isValid: was_square, value: v } = uvRatio(ONE_MINUS_TWO_D, mod((r + _1n) * u1)); // 4

  let v_prime = v; // 5
  if (!was_square) v_prime = mod(r0 * v);

  let sgn = _1n; // 6
  if (!was_square) sgn = mod(-_1n);

  const s = mod(v_prime * (r + _1n)); // 7
  let s_abs = s;
  if (isNegativeLE(s, P)) s_abs = mod(-s);

  const s2 = s * s;
  const W0 = mod(s_abs * _2n); // 8
  const W1 = mod(s2 + _1n); // 9
  const W2 = mod(s2 - _1n); // 10
  const W3 = mod(v_prime * s * (r - _1n) * ONE_MINUS_TWO_D + sgn); // 11
  return new ed448.ExtendedPoint(mod(W0 * W3), mod(W2 * W1), mod(W1 * W3), mod(W0 * W2));
}

/**
 * Each ed448/ExtendedPoint has 4 different equivalent points. This can be
 * a source of bugs for protocols like ring signatures. Decaf was created to solve this.
 * Decaf point operates in X:Y:Z:T extended coordinates like ExtendedPoint,
 * but it should work in its own namespace: do not combine those two.
 * https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-ristretto255-decaf448
 */
class DcfPoint {
  static BASE: DcfPoint;
  static ZERO: DcfPoint;
  // Private property to discourage combining ExtendedPoint + DecafPoint
  // Always use Decaf encoding/decoding instead.
  constructor(private readonly ep: ExtendedPoint) {}

  static fromAffine(ap: AffinePoint<bigint>) {
    return new DcfPoint(ed448.ExtendedPoint.fromAffine(ap));
  }

  /**
   * Takes uniform output of 112-byte hash function like shake256 and converts it to `DecafPoint`.
   * The hash-to-group operation applies Elligator twice and adds the results.
   * **Note:** this is one-way map, there is no conversion from point to hash.
   * https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-ristretto255-decaf448-07#name-element-derivation-2
   * @param hex 112-byte output of a hash function
   */
  static hashToCurve(hex: Hex): DcfPoint {
    hex = ensureBytes('decafHash', hex, 112);
    const r1 = bytes448ToNumberLE(hex.slice(0, 56));
    const R1 = calcElligatorDecafMap(r1);
    const r2 = bytes448ToNumberLE(hex.slice(56, 112));
    const R2 = calcElligatorDecafMap(r2);
    return new DcfPoint(R1.add(R2));
  }

  /**
   * Converts decaf-encoded string to decaf point.
   * https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-ristretto255-decaf448-07#name-decode-2
   * @param hex Decaf-encoded 56 bytes. Not every 56-byte string is valid decaf encoding
   */
  static fromHex(hex: Hex): DcfPoint {
    hex = ensureBytes('decafHex', hex, 56);
    const { d } = ed448.CURVE;
    const P = ed448.CURVE.Fp.ORDER;
    const mod = ed448.CURVE.Fp.create;
    const emsg = 'DecafPoint.fromHex: the hex is not valid encoding of DecafPoint';
    const s = bytes448ToNumberLE(hex);

    // 1. Check that s_bytes is the canonical encoding of a field element, or else abort.
    // 2. Check that s is non-negative, or else abort
    if (!equalBytes(numberToBytesLE(s, 56), hex) || isNegativeLE(s, P)) throw new Error(emsg);

    const s2 = mod(s * s); // 1
    const u1 = mod(_1n + s2); // 2
    const u1sq = mod(u1 * u1);
    const u2 = mod(u1sq - _4n * d * s2); // 3

    const { isValid, value: invsqrt } = invertSqrt(mod(u2 * u1sq)); // 4

    let u3 = mod((s + s) * invsqrt * u1 * SQRT_MINUS_D); // 5
    if (isNegativeLE(u3, P)) u3 = mod(-u3);

    const x = mod(u3 * invsqrt * u2 * INVSQRT_MINUS_D); // 6
    const y = mod((_1n - s2) * invsqrt * u1); // 7
    const t = mod(x * y); // 8

    if (!isValid) throw new Error(emsg);
    return new DcfPoint(new ed448.ExtendedPoint(x, y, _1n, t));
  }

  /**
   * Encodes decaf point to Uint8Array.
   * https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-ristretto255-decaf448-07#name-encode-2
   */
  toRawBytes(): Uint8Array {
    let { ex: x, ey: _y, ez: z, et: t } = this.ep;
    const P = ed448.CURVE.Fp.ORDER;
    const mod = ed448.CURVE.Fp.create;

    const u1 = mod(mod(x + t) * mod(x - t)); // 1
    const x2 = mod(x * x);
    const { value: invsqrt } = invertSqrt(mod(u1 * ONE_MINUS_D * x2)); // 2

    let ratio = mod(invsqrt * u1 * SQRT_MINUS_D); // 3
    if (isNegativeLE(ratio, P)) ratio = mod(-ratio);

    const u2 = mod(INVSQRT_MINUS_D * ratio * z - t); // 4

    let s = mod(ONE_MINUS_D * invsqrt * x * u2); // 5
    if (isNegativeLE(s, P)) s = mod(-s);

    return numberToBytesLE(s, 56);
  }

  toHex(): string {
    return bytesToHex(this.toRawBytes());
  }

  toString(): string {
    return this.toHex();
  }

  // Compare one point to another.
  // https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-ristretto255-decaf448-07#name-equals-2
  equals(other: DcfPoint): boolean {
    assertDcfPoint(other);
    const { ex: X1, ey: Y1 } = this.ep;
    const { ex: X2, ey: Y2 } = other.ep;
    const mod = ed448.CURVE.Fp.create;
    // (x1 * y2 == y1 * x2)
    return mod(X1 * Y2) === mod(Y1 * X2);
  }

  add(other: DcfPoint): DcfPoint {
    assertDcfPoint(other);
    return new DcfPoint(this.ep.add(other.ep));
  }

  subtract(other: DcfPoint): DcfPoint {
    assertDcfPoint(other);
    return new DcfPoint(this.ep.subtract(other.ep));
  }

  multiply(scalar: bigint): DcfPoint {
    return new DcfPoint(this.ep.multiply(scalar));
  }

  multiplyUnsafe(scalar: bigint): DcfPoint {
    return new DcfPoint(this.ep.multiplyUnsafe(scalar));
  }
}
export const DecafPoint = /* @__PURE__ */ (() => {
  // decaf448 base point is ed448 base x 2
  // https://github.com/dalek-cryptography/curve25519-dalek/blob/59837c6ecff02b77b9d5ff84dbc239d0cf33ef90/vendor/ristretto.sage#L699
  if (!DcfPoint.BASE) DcfPoint.BASE = new DcfPoint(ed448.ExtendedPoint.BASE).multiply(_2n);
  if (!DcfPoint.ZERO) DcfPoint.ZERO = new DcfPoint(ed448.ExtendedPoint.ZERO);
  return DcfPoint;
})();

// Hashing to decaf448. https://www.rfc-editor.org/rfc/rfc9380#appendix-C
export const hashToDecaf448 = (msg: Uint8Array, options: htfBasicOpts) => {
  const d = options.DST;
  const DST = typeof d === 'string' ? utf8ToBytes(d) : d;
  const uniform_bytes = expand_message_xof(msg, DST, 112, 224, shake256);
  const P = DcfPoint.hashToCurve(uniform_bytes);
  return P;
};
export const hash_to_decaf448 = hashToDecaf448; // legacy
