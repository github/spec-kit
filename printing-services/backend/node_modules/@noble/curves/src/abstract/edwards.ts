/*! noble-curves - MIT License (c) 2022 Paul Miller (paulmillr.com) */
// Twisted Edwards curve. The formula is: ax² + y² = 1 + dx²y²
import { mod } from './modular.js';
import * as ut from './utils.js';
import { ensureBytes, FHash, Hex } from './utils.js';
import { Group, GroupConstructor, wNAF, BasicCurve, validateBasic, AffinePoint } from './curve.js';

// Be friendly to bad ECMAScript parsers by not using bigint literals
// prettier-ignore
const _0n = BigInt(0), _1n = BigInt(1), _2n = BigInt(2), _8n = BigInt(8);

// Edwards curves must declare params a & d.
export type CurveType = BasicCurve<bigint> & {
  a: bigint; // curve param a
  d: bigint; // curve param d
  hash: FHash; // Hashing
  randomBytes: (bytesLength?: number) => Uint8Array; // CSPRNG
  adjustScalarBytes?: (bytes: Uint8Array) => Uint8Array; // clears bits to get valid field elemtn
  domain?: (data: Uint8Array, ctx: Uint8Array, phflag: boolean) => Uint8Array; // Used for hashing
  uvRatio?: (u: bigint, v: bigint) => { isValid: boolean; value: bigint }; // Ratio √(u/v)
  prehash?: FHash; // RFC 8032 pre-hashing of messages to sign() / verify()
  mapToCurve?: (scalar: bigint[]) => AffinePoint<bigint>; // for hash-to-curve standard
};

// verification rule is either zip215 or rfc8032 / nist186-5. Consult fromHex:
const VERIFY_DEFAULT = { zip215: true };

function validateOpts(curve: CurveType) {
  const opts = validateBasic(curve);
  ut.validateObject(
    curve,
    {
      hash: 'function',
      a: 'bigint',
      d: 'bigint',
      randomBytes: 'function',
    },
    {
      adjustScalarBytes: 'function',
      domain: 'function',
      uvRatio: 'function',
      mapToCurve: 'function',
    }
  );
  // Set defaults
  return Object.freeze({ ...opts } as const);
}

// Instance of Extended Point with coordinates in X, Y, Z, T
export interface ExtPointType extends Group<ExtPointType> {
  readonly ex: bigint;
  readonly ey: bigint;
  readonly ez: bigint;
  readonly et: bigint;
  get x(): bigint;
  get y(): bigint;
  assertValidity(): void;
  multiply(scalar: bigint): ExtPointType;
  multiplyUnsafe(scalar: bigint): ExtPointType;
  isSmallOrder(): boolean;
  isTorsionFree(): boolean;
  clearCofactor(): ExtPointType;
  toAffine(iz?: bigint): AffinePoint<bigint>;
  toRawBytes(isCompressed?: boolean): Uint8Array;
  toHex(isCompressed?: boolean): string;
}
// Static methods of Extended Point with coordinates in X, Y, Z, T
export interface ExtPointConstructor extends GroupConstructor<ExtPointType> {
  new (x: bigint, y: bigint, z: bigint, t: bigint): ExtPointType;
  fromAffine(p: AffinePoint<bigint>): ExtPointType;
  fromHex(hex: Hex): ExtPointType;
  fromPrivateKey(privateKey: Hex): ExtPointType;
}

export type CurveFn = {
  CURVE: ReturnType<typeof validateOpts>;
  getPublicKey: (privateKey: Hex) => Uint8Array;
  sign: (message: Hex, privateKey: Hex, options?: { context?: Hex }) => Uint8Array;
  verify: (
    sig: Hex,
    message: Hex,
    publicKey: Hex,
    options?: { context?: Hex; zip215: boolean }
  ) => boolean;
  ExtendedPoint: ExtPointConstructor;
  utils: {
    randomPrivateKey: () => Uint8Array;
    getExtendedPublicKey: (key: Hex) => {
      head: Uint8Array;
      prefix: Uint8Array;
      scalar: bigint;
      point: ExtPointType;
      pointBytes: Uint8Array;
    };
  };
};

// It is not generic twisted curve for now, but ed25519/ed448 generic implementation
export function twistedEdwards(curveDef: CurveType): CurveFn {
  const CURVE = validateOpts(curveDef) as ReturnType<typeof validateOpts>;
  const {
    Fp,
    n: CURVE_ORDER,
    prehash: prehash,
    hash: cHash,
    randomBytes,
    nByteLength,
    h: cofactor,
  } = CURVE;
  const MASK = _2n << (BigInt(nByteLength * 8) - _1n);
  const modP = Fp.create; // Function overrides

  // sqrt(u/v)
  const uvRatio =
    CURVE.uvRatio ||
    ((u: bigint, v: bigint) => {
      try {
        return { isValid: true, value: Fp.sqrt(u * Fp.inv(v)) };
      } catch (e) {
        return { isValid: false, value: _0n };
      }
    });
  const adjustScalarBytes = CURVE.adjustScalarBytes || ((bytes: Uint8Array) => bytes); // NOOP
  const domain =
    CURVE.domain ||
    ((data: Uint8Array, ctx: Uint8Array, phflag: boolean) => {
      if (ctx.length || phflag) throw new Error('Contexts/pre-hash are not supported');
      return data;
    }); // NOOP
  const inBig = (n: bigint) => typeof n === 'bigint' && _0n < n; // n in [1..]
  const inRange = (n: bigint, max: bigint) => inBig(n) && inBig(max) && n < max; // n in [1..max-1]
  const in0MaskRange = (n: bigint) => n === _0n || inRange(n, MASK); // n in [0..MASK-1]
  function assertInRange(n: bigint, max: bigint) {
    // n in [1..max-1]
    if (inRange(n, max)) return n;
    throw new Error(`Expected valid scalar < ${max}, got ${typeof n} ${n}`);
  }
  function assertGE0(n: bigint) {
    // n in [0..CURVE_ORDER-1]
    return n === _0n ? n : assertInRange(n, CURVE_ORDER); // GE = prime subgroup, not full group
  }
  const pointPrecomputes = new Map<Point, Point[]>();
  function isPoint(other: unknown) {
    if (!(other instanceof Point)) throw new Error('ExtendedPoint expected');
  }
  // Extended Point works in extended coordinates: (x, y, z, t) ∋ (x=x/z, y=y/z, t=xy).
  // https://en.wikipedia.org/wiki/Twisted_Edwards_curve#Extended_coordinates
  class Point implements ExtPointType {
    static readonly BASE = new Point(CURVE.Gx, CURVE.Gy, _1n, modP(CURVE.Gx * CURVE.Gy));
    static readonly ZERO = new Point(_0n, _1n, _1n, _0n); // 0, 1, 1, 0

    constructor(
      readonly ex: bigint,
      readonly ey: bigint,
      readonly ez: bigint,
      readonly et: bigint
    ) {
      if (!in0MaskRange(ex)) throw new Error('x required');
      if (!in0MaskRange(ey)) throw new Error('y required');
      if (!in0MaskRange(ez)) throw new Error('z required');
      if (!in0MaskRange(et)) throw new Error('t required');
    }

    get x(): bigint {
      return this.toAffine().x;
    }
    get y(): bigint {
      return this.toAffine().y;
    }

    static fromAffine(p: AffinePoint<bigint>): Point {
      if (p instanceof Point) throw new Error('extended point not allowed');
      const { x, y } = p || {};
      if (!in0MaskRange(x) || !in0MaskRange(y)) throw new Error('invalid affine point');
      return new Point(x, y, _1n, modP(x * y));
    }
    static normalizeZ(points: Point[]): Point[] {
      const toInv = Fp.invertBatch(points.map((p) => p.ez));
      return points.map((p, i) => p.toAffine(toInv[i])).map(Point.fromAffine);
    }

    // We calculate precomputes for elliptic curve point multiplication
    // using windowed method. This specifies window size and
    // stores precomputed values. Usually only base point would be precomputed.
    _WINDOW_SIZE?: number;

    // "Private method", don't use it directly
    _setWindowSize(windowSize: number) {
      this._WINDOW_SIZE = windowSize;
      pointPrecomputes.delete(this);
    }
    // Not required for fromHex(), which always creates valid points.
    // Could be useful for fromAffine().
    assertValidity(): void {
      const { a, d } = CURVE;
      if (this.is0()) throw new Error('bad point: ZERO'); // TODO: optimize, with vars below?
      // Equation in affine coordinates: ax² + y² = 1 + dx²y²
      // Equation in projective coordinates (X/Z, Y/Z, Z):  (aX² + Y²)Z² = Z⁴ + dX²Y²
      const { ex: X, ey: Y, ez: Z, et: T } = this;
      const X2 = modP(X * X); // X²
      const Y2 = modP(Y * Y); // Y²
      const Z2 = modP(Z * Z); // Z²
      const Z4 = modP(Z2 * Z2); // Z⁴
      const aX2 = modP(X2 * a); // aX²
      const left = modP(Z2 * modP(aX2 + Y2)); // (aX² + Y²)Z²
      const right = modP(Z4 + modP(d * modP(X2 * Y2))); // Z⁴ + dX²Y²
      if (left !== right) throw new Error('bad point: equation left != right (1)');
      // In Extended coordinates we also have T, which is x*y=T/Z: check X*Y == Z*T
      const XY = modP(X * Y);
      const ZT = modP(Z * T);
      if (XY !== ZT) throw new Error('bad point: equation left != right (2)');
    }

    // Compare one point to another.
    equals(other: Point): boolean {
      isPoint(other);
      const { ex: X1, ey: Y1, ez: Z1 } = this;
      const { ex: X2, ey: Y2, ez: Z2 } = other;
      const X1Z2 = modP(X1 * Z2);
      const X2Z1 = modP(X2 * Z1);
      const Y1Z2 = modP(Y1 * Z2);
      const Y2Z1 = modP(Y2 * Z1);
      return X1Z2 === X2Z1 && Y1Z2 === Y2Z1;
    }

    protected is0(): boolean {
      return this.equals(Point.ZERO);
    }

    negate(): Point {
      // Flips point sign to a negative one (-x, y in affine coords)
      return new Point(modP(-this.ex), this.ey, this.ez, modP(-this.et));
    }

    // Fast algo for doubling Extended Point.
    // https://hyperelliptic.org/EFD/g1p/auto-twisted-extended.html#doubling-dbl-2008-hwcd
    // Cost: 4M + 4S + 1*a + 6add + 1*2.
    double(): Point {
      const { a } = CURVE;
      const { ex: X1, ey: Y1, ez: Z1 } = this;
      const A = modP(X1 * X1); // A = X12
      const B = modP(Y1 * Y1); // B = Y12
      const C = modP(_2n * modP(Z1 * Z1)); // C = 2*Z12
      const D = modP(a * A); // D = a*A
      const x1y1 = X1 + Y1;
      const E = modP(modP(x1y1 * x1y1) - A - B); // E = (X1+Y1)2-A-B
      const G = D + B; // G = D+B
      const F = G - C; // F = G-C
      const H = D - B; // H = D-B
      const X3 = modP(E * F); // X3 = E*F
      const Y3 = modP(G * H); // Y3 = G*H
      const T3 = modP(E * H); // T3 = E*H
      const Z3 = modP(F * G); // Z3 = F*G
      return new Point(X3, Y3, Z3, T3);
    }

    // Fast algo for adding 2 Extended Points.
    // https://hyperelliptic.org/EFD/g1p/auto-twisted-extended.html#addition-add-2008-hwcd
    // Cost: 9M + 1*a + 1*d + 7add.
    add(other: Point) {
      isPoint(other);
      const { a, d } = CURVE;
      const { ex: X1, ey: Y1, ez: Z1, et: T1 } = this;
      const { ex: X2, ey: Y2, ez: Z2, et: T2 } = other;
      // Faster algo for adding 2 Extended Points when curve's a=-1.
      // http://hyperelliptic.org/EFD/g1p/auto-twisted-extended-1.html#addition-add-2008-hwcd-4
      // Cost: 8M + 8add + 2*2.
      // Note: It does not check whether the `other` point is valid.
      if (a === BigInt(-1)) {
        const A = modP((Y1 - X1) * (Y2 + X2));
        const B = modP((Y1 + X1) * (Y2 - X2));
        const F = modP(B - A);
        if (F === _0n) return this.double(); // Same point. Tests say it doesn't affect timing
        const C = modP(Z1 * _2n * T2);
        const D = modP(T1 * _2n * Z2);
        const E = D + C;
        const G = B + A;
        const H = D - C;
        const X3 = modP(E * F);
        const Y3 = modP(G * H);
        const T3 = modP(E * H);
        const Z3 = modP(F * G);
        return new Point(X3, Y3, Z3, T3);
      }
      const A = modP(X1 * X2); // A = X1*X2
      const B = modP(Y1 * Y2); // B = Y1*Y2
      const C = modP(T1 * d * T2); // C = T1*d*T2
      const D = modP(Z1 * Z2); // D = Z1*Z2
      const E = modP((X1 + Y1) * (X2 + Y2) - A - B); // E = (X1+Y1)*(X2+Y2)-A-B
      const F = D - C; // F = D-C
      const G = D + C; // G = D+C
      const H = modP(B - a * A); // H = B-a*A
      const X3 = modP(E * F); // X3 = E*F
      const Y3 = modP(G * H); // Y3 = G*H
      const T3 = modP(E * H); // T3 = E*H
      const Z3 = modP(F * G); // Z3 = F*G

      return new Point(X3, Y3, Z3, T3);
    }

    subtract(other: Point): Point {
      return this.add(other.negate());
    }

    private wNAF(n: bigint): { p: Point; f: Point } {
      return wnaf.wNAFCached(this, pointPrecomputes, n, Point.normalizeZ);
    }

    // Constant-time multiplication.
    multiply(scalar: bigint): Point {
      const { p, f } = this.wNAF(assertInRange(scalar, CURVE_ORDER));
      return Point.normalizeZ([p, f])[0];
    }

    // Non-constant-time multiplication. Uses double-and-add algorithm.
    // It's faster, but should only be used when you don't care about
    // an exposed private key e.g. sig verification.
    // Does NOT allow scalars higher than CURVE.n.
    multiplyUnsafe(scalar: bigint): Point {
      let n = assertGE0(scalar); // 0 <= scalar < CURVE.n
      if (n === _0n) return I;
      if (this.equals(I) || n === _1n) return this;
      if (this.equals(G)) return this.wNAF(n).p;
      return wnaf.unsafeLadder(this, n);
    }

    // Checks if point is of small order.
    // If you add something to small order point, you will have "dirty"
    // point with torsion component.
    // Multiplies point by cofactor and checks if the result is 0.
    isSmallOrder(): boolean {
      return this.multiplyUnsafe(cofactor).is0();
    }

    // Multiplies point by curve order and checks if the result is 0.
    // Returns `false` is the point is dirty.
    isTorsionFree(): boolean {
      return wnaf.unsafeLadder(this, CURVE_ORDER).is0();
    }

    // Converts Extended point to default (x, y) coordinates.
    // Can accept precomputed Z^-1 - for example, from invertBatch.
    toAffine(iz?: bigint): AffinePoint<bigint> {
      const { ex: x, ey: y, ez: z } = this;
      const is0 = this.is0();
      if (iz == null) iz = is0 ? _8n : (Fp.inv(z) as bigint); // 8 was chosen arbitrarily
      const ax = modP(x * iz);
      const ay = modP(y * iz);
      const zz = modP(z * iz);
      if (is0) return { x: _0n, y: _1n };
      if (zz !== _1n) throw new Error('invZ was invalid');
      return { x: ax, y: ay };
    }

    clearCofactor(): Point {
      const { h: cofactor } = CURVE;
      if (cofactor === _1n) return this;
      return this.multiplyUnsafe(cofactor);
    }

    // Converts hash string or Uint8Array to Point.
    // Uses algo from RFC8032 5.1.3.
    static fromHex(hex: Hex, zip215 = false): Point {
      const { d, a } = CURVE;
      const len = Fp.BYTES;
      hex = ensureBytes('pointHex', hex, len); // copy hex to a new array
      const normed = hex.slice(); // copy again, we'll manipulate it
      const lastByte = hex[len - 1]; // select last byte
      normed[len - 1] = lastByte & ~0x80; // clear last bit
      const y = ut.bytesToNumberLE(normed);
      if (y === _0n) {
        // y=0 is allowed
      } else {
        // RFC8032 prohibits >= p, but ZIP215 doesn't
        if (zip215) assertInRange(y, MASK); // zip215=true [1..P-1] (2^255-19-1 for ed25519)
        else assertInRange(y, Fp.ORDER); // zip215=false [1..MASK-1] (2^256-1 for ed25519)
      }

      // Ed25519: x² = (y²-1)/(dy²+1) mod p. Ed448: x² = (y²-1)/(dy²-1) mod p. Generic case:
      // ax²+y²=1+dx²y² => y²-1=dx²y²-ax² => y²-1=x²(dy²-a) => x²=(y²-1)/(dy²-a)
      const y2 = modP(y * y); // denominator is always non-0 mod p.
      const u = modP(y2 - _1n); // u = y² - 1
      const v = modP(d * y2 - a); // v = d y² + 1.
      let { isValid, value: x } = uvRatio(u, v); // √(u/v)
      if (!isValid) throw new Error('Point.fromHex: invalid y coordinate');
      const isXOdd = (x & _1n) === _1n; // There are 2 square roots. Use x_0 bit to select proper
      const isLastByteOdd = (lastByte & 0x80) !== 0; // x_0, last bit
      if (!zip215 && x === _0n && isLastByteOdd)
        // if x=0 and x_0 = 1, fail
        throw new Error('Point.fromHex: x=0 and x_0=1');
      if (isLastByteOdd !== isXOdd) x = modP(-x); // if x_0 != x mod 2, set x = p-x
      return Point.fromAffine({ x, y });
    }
    static fromPrivateKey(privKey: Hex) {
      return getExtendedPublicKey(privKey).point;
    }
    toRawBytes(): Uint8Array {
      const { x, y } = this.toAffine();
      const bytes = ut.numberToBytesLE(y, Fp.BYTES); // each y has 2 x values (x, -y)
      bytes[bytes.length - 1] |= x & _1n ? 0x80 : 0; // when compressing, it's enough to store y
      return bytes; // and use the last byte to encode sign of x
    }
    toHex(): string {
      return ut.bytesToHex(this.toRawBytes()); // Same as toRawBytes, but returns string.
    }
  }
  const { BASE: G, ZERO: I } = Point;
  const wnaf = wNAF(Point, nByteLength * 8);

  function modN(a: bigint) {
    return mod(a, CURVE_ORDER);
  }
  // Little-endian SHA512 with modulo n
  function modN_LE(hash: Uint8Array): bigint {
    return modN(ut.bytesToNumberLE(hash));
  }

  /** Convenience method that creates public key and other stuff. RFC8032 5.1.5 */
  function getExtendedPublicKey(key: Hex) {
    const len = nByteLength;
    key = ensureBytes('private key', key, len);
    // Hash private key with curve's hash function to produce uniformingly random input
    // Check byte lengths: ensure(64, h(ensure(32, key)))
    const hashed = ensureBytes('hashed private key', cHash(key), 2 * len);
    const head = adjustScalarBytes(hashed.slice(0, len)); // clear first half bits, produce FE
    const prefix = hashed.slice(len, 2 * len); // second half is called key prefix (5.1.6)
    const scalar = modN_LE(head); // The actual private scalar
    const point = G.multiply(scalar); // Point on Edwards curve aka public key
    const pointBytes = point.toRawBytes(); // Uint8Array representation
    return { head, prefix, scalar, point, pointBytes };
  }

  // Calculates EdDSA pub key. RFC8032 5.1.5. Privkey is hashed. Use first half with 3 bits cleared
  function getPublicKey(privKey: Hex): Uint8Array {
    return getExtendedPublicKey(privKey).pointBytes;
  }

  // int('LE', SHA512(dom2(F, C) || msgs)) mod N
  function hashDomainToScalar(context: Hex = new Uint8Array(), ...msgs: Uint8Array[]) {
    const msg = ut.concatBytes(...msgs);
    return modN_LE(cHash(domain(msg, ensureBytes('context', context), !!prehash)));
  }

  /** Signs message with privateKey. RFC8032 5.1.6 */
  function sign(msg: Hex, privKey: Hex, options: { context?: Hex } = {}): Uint8Array {
    msg = ensureBytes('message', msg);
    if (prehash) msg = prehash(msg); // for ed25519ph etc.
    const { prefix, scalar, pointBytes } = getExtendedPublicKey(privKey);
    const r = hashDomainToScalar(options.context, prefix, msg); // r = dom2(F, C) || prefix || PH(M)
    const R = G.multiply(r).toRawBytes(); // R = rG
    const k = hashDomainToScalar(options.context, R, pointBytes, msg); // R || A || PH(M)
    const s = modN(r + k * scalar); // S = (r + k * s) mod L
    assertGE0(s); // 0 <= s < l
    const res = ut.concatBytes(R, ut.numberToBytesLE(s, Fp.BYTES));
    return ensureBytes('result', res, nByteLength * 2); // 64-byte signature
  }

  const verifyOpts: { context?: Hex; zip215?: boolean } = VERIFY_DEFAULT;
  function verify(sig: Hex, msg: Hex, publicKey: Hex, options = verifyOpts): boolean {
    const { context, zip215 } = options;
    const len = Fp.BYTES; // Verifies EdDSA signature against message and public key. RFC8032 5.1.7.
    sig = ensureBytes('signature', sig, 2 * len); // An extended group equation is checked.
    msg = ensureBytes('message', msg);
    if (prehash) msg = prehash(msg); // for ed25519ph, etc

    const s = ut.bytesToNumberLE(sig.slice(len, 2 * len));
    // zip215: true is good for consensus-critical apps and allows points < 2^256
    // zip215: false follows RFC8032 / NIST186-5 and restricts points to CURVE.p
    let A, R, SB;
    try {
      A = Point.fromHex(publicKey, zip215);
      R = Point.fromHex(sig.slice(0, len), zip215);
      SB = G.multiplyUnsafe(s); // 0 <= s < l is done inside
    } catch (error) {
      return false;
    }
    if (!zip215 && A.isSmallOrder()) return false;

    const k = hashDomainToScalar(context, R.toRawBytes(), A.toRawBytes(), msg);
    const RkA = R.add(A.multiplyUnsafe(k));
    // [8][S]B = [8]R + [8][k]A'
    return RkA.subtract(SB).clearCofactor().equals(Point.ZERO);
  }

  G._setWindowSize(8); // Enable precomputes. Slows down first publicKey computation by 20ms.

  const utils = {
    getExtendedPublicKey,
    // ed25519 private keys are uniform 32b. No need to check for modulo bias, like in secp256k1.
    randomPrivateKey: (): Uint8Array => randomBytes(Fp.BYTES),

    /**
     * We're doing scalar multiplication (used in getPublicKey etc) with precomputed BASE_POINT
     * values. This slows down first getPublicKey() by milliseconds (see Speed section),
     * but allows to speed-up subsequent getPublicKey() calls up to 20x.
     * @param windowSize 2, 4, 8, 16
     */
    precompute(windowSize = 8, point = Point.BASE): typeof Point.BASE {
      point._setWindowSize(windowSize);
      point.multiply(BigInt(3));
      return point;
    },
  };

  return {
    CURVE,
    getPublicKey,
    sign,
    verify,
    ExtendedPoint: Point,
    utils,
  };
}
