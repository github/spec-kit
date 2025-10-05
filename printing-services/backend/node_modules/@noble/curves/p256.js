"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.encodeToCurve = exports.hashToCurve = exports.secp256r1 = exports.p256 = void 0;
/*! noble-curves - MIT License (c) 2022 Paul Miller (paulmillr.com) */
const _shortw_utils_js_1 = require("./_shortw_utils.js");
const sha256_1 = require("@noble/hashes/sha256");
const modular_js_1 = require("./abstract/modular.js");
const weierstrass_js_1 = require("./abstract/weierstrass.js");
const hash_to_curve_js_1 = require("./abstract/hash-to-curve.js");
// NIST secp256r1 aka p256
// https://www.secg.org/sec2-v2.pdf, https://neuromancer.sk/std/nist/P-256
const Fp = (0, modular_js_1.Field)(BigInt('0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff'));
const CURVE_A = Fp.create(BigInt('-3'));
const CURVE_B = BigInt('0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b');
// prettier-ignore
exports.p256 = (0, _shortw_utils_js_1.createCurve)({
    a: CURVE_A,
    b: CURVE_B,
    Fp,
    // Curve order, total count of valid points in the field
    n: BigInt('0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551'),
    // Base (generator) point (x, y)
    Gx: BigInt('0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296'),
    Gy: BigInt('0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5'),
    h: BigInt(1),
    lowS: false,
}, sha256_1.sha256);
exports.secp256r1 = exports.p256;
const mapSWU = /* @__PURE__ */ (() => (0, weierstrass_js_1.mapToCurveSimpleSWU)(Fp, {
    A: CURVE_A,
    B: CURVE_B,
    Z: Fp.create(BigInt('-10')),
}))();
const htf = /* @__PURE__ */ (() => (0, hash_to_curve_js_1.createHasher)(exports.secp256r1.ProjectivePoint, (scalars) => mapSWU(scalars[0]), {
    DST: 'P256_XMD:SHA-256_SSWU_RO_',
    encodeDST: 'P256_XMD:SHA-256_SSWU_NU_',
    p: Fp.ORDER,
    m: 1,
    k: 128,
    expand: 'xmd',
    hash: sha256_1.sha256,
}))();
exports.hashToCurve = (() => htf.hashToCurve)();
exports.encodeToCurve = (() => htf.encodeToCurve)();
//# sourceMappingURL=p256.js.map