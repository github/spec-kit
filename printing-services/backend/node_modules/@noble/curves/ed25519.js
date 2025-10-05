"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.hash_to_ristretto255 = exports.hashToRistretto255 = exports.RistrettoPoint = exports.encodeToCurve = exports.hashToCurve = exports.edwardsToMontgomeryPriv = exports.edwardsToMontgomery = exports.edwardsToMontgomeryPub = exports.x25519 = exports.ed25519ph = exports.ed25519ctx = exports.ed25519 = exports.ED25519_TORSION_SUBGROUP = void 0;
/*! noble-curves - MIT License (c) 2022 Paul Miller (paulmillr.com) */
const sha512_1 = require("@noble/hashes/sha512");
const utils_1 = require("@noble/hashes/utils");
const edwards_js_1 = require("./abstract/edwards.js");
const montgomery_js_1 = require("./abstract/montgomery.js");
const modular_js_1 = require("./abstract/modular.js");
const utils_js_1 = require("./abstract/utils.js");
const hash_to_curve_js_1 = require("./abstract/hash-to-curve.js");
/**
 * ed25519 Twisted Edwards curve with following addons:
 * - X25519 ECDH
 * - Ristretto cofactor elimination
 * - Elligator hash-to-group / point indistinguishability
 */
const ED25519_P = BigInt('57896044618658097711785492504343953926634992332820282019728792003956564819949');
// √(-1) aka √(a) aka 2^((p-1)/4)
const ED25519_SQRT_M1 = BigInt('19681161376707505956807079304988542015446066515923890162744021073123829784752');
// prettier-ignore
const _0n = BigInt(0), _1n = BigInt(1), _2n = BigInt(2), _5n = BigInt(5);
// prettier-ignore
const _10n = BigInt(10), _20n = BigInt(20), _40n = BigInt(40), _80n = BigInt(80);
function ed25519_pow_2_252_3(x) {
    const P = ED25519_P;
    const x2 = (x * x) % P;
    const b2 = (x2 * x) % P; // x^3, 11
    const b4 = ((0, modular_js_1.pow2)(b2, _2n, P) * b2) % P; // x^15, 1111
    const b5 = ((0, modular_js_1.pow2)(b4, _1n, P) * x) % P; // x^31
    const b10 = ((0, modular_js_1.pow2)(b5, _5n, P) * b5) % P;
    const b20 = ((0, modular_js_1.pow2)(b10, _10n, P) * b10) % P;
    const b40 = ((0, modular_js_1.pow2)(b20, _20n, P) * b20) % P;
    const b80 = ((0, modular_js_1.pow2)(b40, _40n, P) * b40) % P;
    const b160 = ((0, modular_js_1.pow2)(b80, _80n, P) * b80) % P;
    const b240 = ((0, modular_js_1.pow2)(b160, _80n, P) * b80) % P;
    const b250 = ((0, modular_js_1.pow2)(b240, _10n, P) * b10) % P;
    const pow_p_5_8 = ((0, modular_js_1.pow2)(b250, _2n, P) * x) % P;
    // ^ To pow to (p+3)/8, multiply it by x.
    return { pow_p_5_8, b2 };
}
function adjustScalarBytes(bytes) {
    // Section 5: For X25519, in order to decode 32 random bytes as an integer scalar,
    // set the three least significant bits of the first byte
    bytes[0] &= 248; // 0b1111_1000
    // and the most significant bit of the last to zero,
    bytes[31] &= 127; // 0b0111_1111
    // set the second most significant bit of the last byte to 1
    bytes[31] |= 64; // 0b0100_0000
    return bytes;
}
// sqrt(u/v)
function uvRatio(u, v) {
    const P = ED25519_P;
    const v3 = (0, modular_js_1.mod)(v * v * v, P); // v³
    const v7 = (0, modular_js_1.mod)(v3 * v3 * v, P); // v⁷
    // (p+3)/8 and (p-5)/8
    const pow = ed25519_pow_2_252_3(u * v7).pow_p_5_8;
    let x = (0, modular_js_1.mod)(u * v3 * pow, P); // (uv³)(uv⁷)^(p-5)/8
    const vx2 = (0, modular_js_1.mod)(v * x * x, P); // vx²
    const root1 = x; // First root candidate
    const root2 = (0, modular_js_1.mod)(x * ED25519_SQRT_M1, P); // Second root candidate
    const useRoot1 = vx2 === u; // If vx² = u (mod p), x is a square root
    const useRoot2 = vx2 === (0, modular_js_1.mod)(-u, P); // If vx² = -u, set x <-- x * 2^((p-1)/4)
    const noRoot = vx2 === (0, modular_js_1.mod)(-u * ED25519_SQRT_M1, P); // There is no valid root, vx² = -u√(-1)
    if (useRoot1)
        x = root1;
    if (useRoot2 || noRoot)
        x = root2; // We return root2 anyway, for const-time
    if ((0, modular_js_1.isNegativeLE)(x, P))
        x = (0, modular_js_1.mod)(-x, P);
    return { isValid: useRoot1 || useRoot2, value: x };
}
// Just in case
exports.ED25519_TORSION_SUBGROUP = [
    '0100000000000000000000000000000000000000000000000000000000000000',
    'c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a',
    '0000000000000000000000000000000000000000000000000000000000000080',
    '26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05',
    'ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f',
    '26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85',
    '0000000000000000000000000000000000000000000000000000000000000000',
    'c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa',
];
const Fp = (0, modular_js_1.Field)(ED25519_P, undefined, true);
const ed25519Defaults = {
    // Param: a
    a: BigInt(-1),
    // d is equal to -121665/121666 over finite field.
    // Negative number is P - number, and division is invert(number, P)
    d: BigInt('37095705934669439343138083508754565189542113879843219016388785533085940283555'),
    // Finite field 𝔽p over which we'll do calculations; 2n**255n - 19n
    Fp,
    // Subgroup order: how many points curve has
    // 2n**252n + 27742317777372353535851937790883648493n;
    n: BigInt('7237005577332262213973186563042994240857116359379907606001950938285454250989'),
    // Cofactor
    h: BigInt(8),
    // Base point (x, y) aka generator point
    Gx: BigInt('15112221349535400772501151409588531511454012693041857206046113283949847762202'),
    Gy: BigInt('46316835694926478169428394003475163141307993866256225615783033603165251855960'),
    hash: sha512_1.sha512,
    randomBytes: utils_1.randomBytes,
    adjustScalarBytes,
    // dom2
    // Ratio of u to v. Allows us to combine inversion and square root. Uses algo from RFC8032 5.1.3.
    // Constant-time, u/√v
    uvRatio,
};
exports.ed25519 = (0, edwards_js_1.twistedEdwards)(ed25519Defaults);
function ed25519_domain(data, ctx, phflag) {
    if (ctx.length > 255)
        throw new Error('Context is too big');
    return (0, utils_1.concatBytes)((0, utils_1.utf8ToBytes)('SigEd25519 no Ed25519 collisions'), new Uint8Array([phflag ? 1 : 0, ctx.length]), ctx, data);
}
exports.ed25519ctx = (0, edwards_js_1.twistedEdwards)({
    ...ed25519Defaults,
    domain: ed25519_domain,
});
exports.ed25519ph = (0, edwards_js_1.twistedEdwards)({
    ...ed25519Defaults,
    domain: ed25519_domain,
    prehash: sha512_1.sha512,
});
exports.x25519 = (() => (0, montgomery_js_1.montgomery)({
    P: ED25519_P,
    a: BigInt(486662),
    montgomeryBits: 255,
    nByteLength: 32,
    Gu: BigInt(9),
    powPminus2: (x) => {
        const P = ED25519_P;
        // x^(p-2) aka x^(2^255-21)
        const { pow_p_5_8, b2 } = ed25519_pow_2_252_3(x);
        return (0, modular_js_1.mod)((0, modular_js_1.pow2)(pow_p_5_8, BigInt(3), P) * b2, P);
    },
    adjustScalarBytes,
    randomBytes: utils_1.randomBytes,
}))();
/**
 * Converts ed25519 public key to x25519 public key. Uses formula:
 * * `(u, v) = ((1+y)/(1-y), sqrt(-486664)*u/x)`
 * * `(x, y) = (sqrt(-486664)*u/v, (u-1)/(u+1))`
 * @example
 *   const someonesPub = ed25519.getPublicKey(ed25519.utils.randomPrivateKey());
 *   const aPriv = x25519.utils.randomPrivateKey();
 *   x25519.getSharedSecret(aPriv, edwardsToMontgomeryPub(someonesPub))
 */
function edwardsToMontgomeryPub(edwardsPub) {
    const { y } = exports.ed25519.ExtendedPoint.fromHex(edwardsPub);
    const _1n = BigInt(1);
    return Fp.toBytes(Fp.create((_1n + y) * Fp.inv(_1n - y)));
}
exports.edwardsToMontgomeryPub = edwardsToMontgomeryPub;
exports.edwardsToMontgomery = edwardsToMontgomeryPub; // deprecated
/**
 * Converts ed25519 secret key to x25519 secret key.
 * @example
 *   const someonesPub = x25519.getPublicKey(x25519.utils.randomPrivateKey());
 *   const aPriv = ed25519.utils.randomPrivateKey();
 *   x25519.getSharedSecret(edwardsToMontgomeryPriv(aPriv), someonesPub)
 */
function edwardsToMontgomeryPriv(edwardsPriv) {
    const hashed = ed25519Defaults.hash(edwardsPriv.subarray(0, 32));
    return ed25519Defaults.adjustScalarBytes(hashed).subarray(0, 32);
}
exports.edwardsToMontgomeryPriv = edwardsToMontgomeryPriv;
// Hash To Curve Elligator2 Map (NOTE: different from ristretto255 elligator)
// NOTE: very important part is usage of FpSqrtEven for ELL2_C1_EDWARDS, since
// SageMath returns different root first and everything falls apart
const ELL2_C1 = (Fp.ORDER + BigInt(3)) / BigInt(8); // 1. c1 = (q + 3) / 8       # Integer arithmetic
const ELL2_C2 = Fp.pow(_2n, ELL2_C1); // 2. c2 = 2^c1
const ELL2_C3 = Fp.sqrt(Fp.neg(Fp.ONE)); // 3. c3 = sqrt(-1)
const ELL2_C4 = (Fp.ORDER - BigInt(5)) / BigInt(8); // 4. c4 = (q - 5) / 8       # Integer arithmetic
const ELL2_J = BigInt(486662);
// prettier-ignore
function map_to_curve_elligator2_curve25519(u) {
    let tv1 = Fp.sqr(u); //  1.  tv1 = u^2
    tv1 = Fp.mul(tv1, _2n); //  2.  tv1 = 2 * tv1
    let xd = Fp.add(tv1, Fp.ONE); //  3.   xd = tv1 + 1         # Nonzero: -1 is square (mod p), tv1 is not
    let x1n = Fp.neg(ELL2_J); //  4.  x1n = -J              # x1 = x1n / xd = -J / (1 + 2 * u^2)
    let tv2 = Fp.sqr(xd); //  5.  tv2 = xd^2
    let gxd = Fp.mul(tv2, xd); //  6.  gxd = tv2 * xd        # gxd = xd^3
    let gx1 = Fp.mul(tv1, ELL2_J); //  7.  gx1 = J * tv1         # x1n + J * xd
    gx1 = Fp.mul(gx1, x1n); //  8.  gx1 = gx1 * x1n       # x1n^2 + J * x1n * xd
    gx1 = Fp.add(gx1, tv2); //  9.  gx1 = gx1 + tv2       # x1n^2 + J * x1n * xd + xd^2
    gx1 = Fp.mul(gx1, x1n); //  10. gx1 = gx1 * x1n       # x1n^3 + J * x1n^2 * xd + x1n * xd^2
    let tv3 = Fp.sqr(gxd); //  11. tv3 = gxd^2
    tv2 = Fp.sqr(tv3); //  12. tv2 = tv3^2           # gxd^4
    tv3 = Fp.mul(tv3, gxd); //  13. tv3 = tv3 * gxd       # gxd^3
    tv3 = Fp.mul(tv3, gx1); //  14. tv3 = tv3 * gx1       # gx1 * gxd^3
    tv2 = Fp.mul(tv2, tv3); //  15. tv2 = tv2 * tv3       # gx1 * gxd^7
    let y11 = Fp.pow(tv2, ELL2_C4); //  16. y11 = tv2^c4        # (gx1 * gxd^7)^((p - 5) / 8)
    y11 = Fp.mul(y11, tv3); //  17. y11 = y11 * tv3       # gx1*gxd^3*(gx1*gxd^7)^((p-5)/8)
    let y12 = Fp.mul(y11, ELL2_C3); //  18. y12 = y11 * c3
    tv2 = Fp.sqr(y11); //  19. tv2 = y11^2
    tv2 = Fp.mul(tv2, gxd); //  20. tv2 = tv2 * gxd
    let e1 = Fp.eql(tv2, gx1); //  21.  e1 = tv2 == gx1
    let y1 = Fp.cmov(y12, y11, e1); //  22.  y1 = CMOV(y12, y11, e1)  # If g(x1) is square, this is its sqrt
    let x2n = Fp.mul(x1n, tv1); //  23. x2n = x1n * tv1       # x2 = x2n / xd = 2 * u^2 * x1n / xd
    let y21 = Fp.mul(y11, u); //  24. y21 = y11 * u
    y21 = Fp.mul(y21, ELL2_C2); //  25. y21 = y21 * c2
    let y22 = Fp.mul(y21, ELL2_C3); //  26. y22 = y21 * c3
    let gx2 = Fp.mul(gx1, tv1); //  27. gx2 = gx1 * tv1       # g(x2) = gx2 / gxd = 2 * u^2 * g(x1)
    tv2 = Fp.sqr(y21); //  28. tv2 = y21^2
    tv2 = Fp.mul(tv2, gxd); //  29. tv2 = tv2 * gxd
    let e2 = Fp.eql(tv2, gx2); //  30.  e2 = tv2 == gx2
    let y2 = Fp.cmov(y22, y21, e2); //  31.  y2 = CMOV(y22, y21, e2)  # If g(x2) is square, this is its sqrt
    tv2 = Fp.sqr(y1); //  32. tv2 = y1^2
    tv2 = Fp.mul(tv2, gxd); //  33. tv2 = tv2 * gxd
    let e3 = Fp.eql(tv2, gx1); //  34.  e3 = tv2 == gx1
    let xn = Fp.cmov(x2n, x1n, e3); //  35.  xn = CMOV(x2n, x1n, e3)  # If e3, x = x1, else x = x2
    let y = Fp.cmov(y2, y1, e3); //  36.   y = CMOV(y2, y1, e3)    # If e3, y = y1, else y = y2
    let e4 = Fp.isOdd(y); //  37.  e4 = sgn0(y) == 1        # Fix sign of y
    y = Fp.cmov(y, Fp.neg(y), e3 !== e4); //  38.   y = CMOV(y, -y, e3 XOR e4)
    return { xMn: xn, xMd: xd, yMn: y, yMd: _1n }; //  39. return (xn, xd, y, 1)
}
const ELL2_C1_EDWARDS = (0, modular_js_1.FpSqrtEven)(Fp, Fp.neg(BigInt(486664))); // sgn0(c1) MUST equal 0
function map_to_curve_elligator2_edwards25519(u) {
    const { xMn, xMd, yMn, yMd } = map_to_curve_elligator2_curve25519(u); //  1.  (xMn, xMd, yMn, yMd) =
    // map_to_curve_elligator2_curve25519(u)
    let xn = Fp.mul(xMn, yMd); //  2.  xn = xMn * yMd
    xn = Fp.mul(xn, ELL2_C1_EDWARDS); //  3.  xn = xn * c1
    let xd = Fp.mul(xMd, yMn); //  4.  xd = xMd * yMn    # xn / xd = c1 * xM / yM
    let yn = Fp.sub(xMn, xMd); //  5.  yn = xMn - xMd
    let yd = Fp.add(xMn, xMd); //  6.  yd = xMn + xMd    # (n / d - 1) / (n / d + 1) = (n - d) / (n + d)
    let tv1 = Fp.mul(xd, yd); //  7. tv1 = xd * yd
    let e = Fp.eql(tv1, Fp.ZERO); //  8.   e = tv1 == 0
    xn = Fp.cmov(xn, Fp.ZERO, e); //  9.  xn = CMOV(xn, 0, e)
    xd = Fp.cmov(xd, Fp.ONE, e); //  10. xd = CMOV(xd, 1, e)
    yn = Fp.cmov(yn, Fp.ONE, e); //  11. yn = CMOV(yn, 1, e)
    yd = Fp.cmov(yd, Fp.ONE, e); //  12. yd = CMOV(yd, 1, e)
    const inv = Fp.invertBatch([xd, yd]); // batch division
    return { x: Fp.mul(xn, inv[0]), y: Fp.mul(yn, inv[1]) }; //  13. return (xn, xd, yn, yd)
}
const htf = /* @__PURE__ */ (() => (0, hash_to_curve_js_1.createHasher)(exports.ed25519.ExtendedPoint, (scalars) => map_to_curve_elligator2_edwards25519(scalars[0]), {
    DST: 'edwards25519_XMD:SHA-512_ELL2_RO_',
    encodeDST: 'edwards25519_XMD:SHA-512_ELL2_NU_',
    p: Fp.ORDER,
    m: 1,
    k: 128,
    expand: 'xmd',
    hash: sha512_1.sha512,
}))();
exports.hashToCurve = (() => htf.hashToCurve)();
exports.encodeToCurve = (() => htf.encodeToCurve)();
function assertRstPoint(other) {
    if (!(other instanceof RistPoint))
        throw new Error('RistrettoPoint expected');
}
// √(-1) aka √(a) aka 2^((p-1)/4)
const SQRT_M1 = ED25519_SQRT_M1;
// √(ad - 1)
const SQRT_AD_MINUS_ONE = BigInt('25063068953384623474111414158702152701244531502492656460079210482610430750235');
// 1 / √(a-d)
const INVSQRT_A_MINUS_D = BigInt('54469307008909316920995813868745141605393597292927456921205312896311721017578');
// 1-d²
const ONE_MINUS_D_SQ = BigInt('1159843021668779879193775521855586647937357759715417654439879720876111806838');
// (d-1)²
const D_MINUS_ONE_SQ = BigInt('40440834346308536858101042469323190826248399146238708352240133220865137265952');
// Calculates 1/√(number)
const invertSqrt = (number) => uvRatio(_1n, number);
const MAX_255B = BigInt('0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff');
const bytes255ToNumberLE = (bytes) => exports.ed25519.CURVE.Fp.create((0, utils_js_1.bytesToNumberLE)(bytes) & MAX_255B);
// Computes Elligator map for Ristretto
// https://ristretto.group/formulas/elligator.html
function calcElligatorRistrettoMap(r0) {
    const { d } = exports.ed25519.CURVE;
    const P = exports.ed25519.CURVE.Fp.ORDER;
    const mod = exports.ed25519.CURVE.Fp.create;
    const r = mod(SQRT_M1 * r0 * r0); // 1
    const Ns = mod((r + _1n) * ONE_MINUS_D_SQ); // 2
    let c = BigInt(-1); // 3
    const D = mod((c - d * r) * mod(r + d)); // 4
    let { isValid: Ns_D_is_sq, value: s } = uvRatio(Ns, D); // 5
    let s_ = mod(s * r0); // 6
    if (!(0, modular_js_1.isNegativeLE)(s_, P))
        s_ = mod(-s_);
    if (!Ns_D_is_sq)
        s = s_; // 7
    if (!Ns_D_is_sq)
        c = r; // 8
    const Nt = mod(c * (r - _1n) * D_MINUS_ONE_SQ - D); // 9
    const s2 = s * s;
    const W0 = mod((s + s) * D); // 10
    const W1 = mod(Nt * SQRT_AD_MINUS_ONE); // 11
    const W2 = mod(_1n - s2); // 12
    const W3 = mod(_1n + s2); // 13
    return new exports.ed25519.ExtendedPoint(mod(W0 * W3), mod(W2 * W1), mod(W1 * W3), mod(W0 * W2));
}
/**
 * Each ed25519/ExtendedPoint has 8 different equivalent points. This can be
 * a source of bugs for protocols like ring signatures. Ristretto was created to solve this.
 * Ristretto point operates in X:Y:Z:T extended coordinates like ExtendedPoint,
 * but it should work in its own namespace: do not combine those two.
 * https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-ristretto255-decaf448
 */
class RistPoint {
    // Private property to discourage combining ExtendedPoint + RistrettoPoint
    // Always use Ristretto encoding/decoding instead.
    constructor(ep) {
        this.ep = ep;
    }
    static fromAffine(ap) {
        return new RistPoint(exports.ed25519.ExtendedPoint.fromAffine(ap));
    }
    /**
     * Takes uniform output of 64-byte hash function like sha512 and converts it to `RistrettoPoint`.
     * The hash-to-group operation applies Elligator twice and adds the results.
     * **Note:** this is one-way map, there is no conversion from point to hash.
     * https://ristretto.group/formulas/elligator.html
     * @param hex 64-byte output of a hash function
     */
    static hashToCurve(hex) {
        hex = (0, utils_js_1.ensureBytes)('ristrettoHash', hex, 64);
        const r1 = bytes255ToNumberLE(hex.slice(0, 32));
        const R1 = calcElligatorRistrettoMap(r1);
        const r2 = bytes255ToNumberLE(hex.slice(32, 64));
        const R2 = calcElligatorRistrettoMap(r2);
        return new RistPoint(R1.add(R2));
    }
    /**
     * Converts ristretto-encoded string to ristretto point.
     * https://ristretto.group/formulas/decoding.html
     * @param hex Ristretto-encoded 32 bytes. Not every 32-byte string is valid ristretto encoding
     */
    static fromHex(hex) {
        hex = (0, utils_js_1.ensureBytes)('ristrettoHex', hex, 32);
        const { a, d } = exports.ed25519.CURVE;
        const P = exports.ed25519.CURVE.Fp.ORDER;
        const mod = exports.ed25519.CURVE.Fp.create;
        const emsg = 'RistrettoPoint.fromHex: the hex is not valid encoding of RistrettoPoint';
        const s = bytes255ToNumberLE(hex);
        // 1. Check that s_bytes is the canonical encoding of a field element, or else abort.
        // 3. Check that s is non-negative, or else abort
        if (!(0, utils_js_1.equalBytes)((0, utils_js_1.numberToBytesLE)(s, 32), hex) || (0, modular_js_1.isNegativeLE)(s, P))
            throw new Error(emsg);
        const s2 = mod(s * s);
        const u1 = mod(_1n + a * s2); // 4 (a is -1)
        const u2 = mod(_1n - a * s2); // 5
        const u1_2 = mod(u1 * u1);
        const u2_2 = mod(u2 * u2);
        const v = mod(a * d * u1_2 - u2_2); // 6
        const { isValid, value: I } = invertSqrt(mod(v * u2_2)); // 7
        const Dx = mod(I * u2); // 8
        const Dy = mod(I * Dx * v); // 9
        let x = mod((s + s) * Dx); // 10
        if ((0, modular_js_1.isNegativeLE)(x, P))
            x = mod(-x); // 10
        const y = mod(u1 * Dy); // 11
        const t = mod(x * y); // 12
        if (!isValid || (0, modular_js_1.isNegativeLE)(t, P) || y === _0n)
            throw new Error(emsg);
        return new RistPoint(new exports.ed25519.ExtendedPoint(x, y, _1n, t));
    }
    /**
     * Encodes ristretto point to Uint8Array.
     * https://ristretto.group/formulas/encoding.html
     */
    toRawBytes() {
        let { ex: x, ey: y, ez: z, et: t } = this.ep;
        const P = exports.ed25519.CURVE.Fp.ORDER;
        const mod = exports.ed25519.CURVE.Fp.create;
        const u1 = mod(mod(z + y) * mod(z - y)); // 1
        const u2 = mod(x * y); // 2
        // Square root always exists
        const u2sq = mod(u2 * u2);
        const { value: invsqrt } = invertSqrt(mod(u1 * u2sq)); // 3
        const D1 = mod(invsqrt * u1); // 4
        const D2 = mod(invsqrt * u2); // 5
        const zInv = mod(D1 * D2 * t); // 6
        let D; // 7
        if ((0, modular_js_1.isNegativeLE)(t * zInv, P)) {
            let _x = mod(y * SQRT_M1);
            let _y = mod(x * SQRT_M1);
            x = _x;
            y = _y;
            D = mod(D1 * INVSQRT_A_MINUS_D);
        }
        else {
            D = D2; // 8
        }
        if ((0, modular_js_1.isNegativeLE)(x * zInv, P))
            y = mod(-y); // 9
        let s = mod((z - y) * D); // 10 (check footer's note, no sqrt(-a))
        if ((0, modular_js_1.isNegativeLE)(s, P))
            s = mod(-s);
        return (0, utils_js_1.numberToBytesLE)(s, 32); // 11
    }
    toHex() {
        return (0, utils_js_1.bytesToHex)(this.toRawBytes());
    }
    toString() {
        return this.toHex();
    }
    // Compare one point to another.
    equals(other) {
        assertRstPoint(other);
        const { ex: X1, ey: Y1 } = this.ep;
        const { ex: X2, ey: Y2 } = other.ep;
        const mod = exports.ed25519.CURVE.Fp.create;
        // (x1 * y2 == y1 * x2) | (y1 * y2 == x1 * x2)
        const one = mod(X1 * Y2) === mod(Y1 * X2);
        const two = mod(Y1 * Y2) === mod(X1 * X2);
        return one || two;
    }
    add(other) {
        assertRstPoint(other);
        return new RistPoint(this.ep.add(other.ep));
    }
    subtract(other) {
        assertRstPoint(other);
        return new RistPoint(this.ep.subtract(other.ep));
    }
    multiply(scalar) {
        return new RistPoint(this.ep.multiply(scalar));
    }
    multiplyUnsafe(scalar) {
        return new RistPoint(this.ep.multiplyUnsafe(scalar));
    }
}
exports.RistrettoPoint = (() => {
    if (!RistPoint.BASE)
        RistPoint.BASE = new RistPoint(exports.ed25519.ExtendedPoint.BASE);
    if (!RistPoint.ZERO)
        RistPoint.ZERO = new RistPoint(exports.ed25519.ExtendedPoint.ZERO);
    return RistPoint;
})();
// Hashing to ristretto255. https://www.rfc-editor.org/rfc/rfc9380#appendix-B
const hashToRistretto255 = (msg, options) => {
    const d = options.DST;
    const DST = typeof d === 'string' ? (0, utils_1.utf8ToBytes)(d) : d;
    const uniform_bytes = (0, hash_to_curve_js_1.expand_message_xmd)(msg, DST, 64, sha512_1.sha512);
    const P = RistPoint.hashToCurve(uniform_bytes);
    return P;
};
exports.hashToRistretto255 = hashToRistretto255;
exports.hash_to_ristretto255 = exports.hashToRistretto255; // legacy
//# sourceMappingURL=ed25519.js.map