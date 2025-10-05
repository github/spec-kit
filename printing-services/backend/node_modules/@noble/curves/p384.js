"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.encodeToCurve = exports.hashToCurve = exports.secp384r1 = exports.p384 = void 0;
/*! noble-curves - MIT License (c) 2022 Paul Miller (paulmillr.com) */
const _shortw_utils_js_1 = require("./_shortw_utils.js");
const sha512_1 = require("@noble/hashes/sha512");
const modular_js_1 = require("./abstract/modular.js");
const weierstrass_js_1 = require("./abstract/weierstrass.js");
const hash_to_curve_js_1 = require("./abstract/hash-to-curve.js");
// NIST secp384r1 aka p384
// https://www.secg.org/sec2-v2.pdf, https://neuromancer.sk/std/nist/P-384
// Field over which we'll do calculations.
// prettier-ignore
const P = BigInt('0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffeffffffff0000000000000000ffffffff');
const Fp = (0, modular_js_1.Field)(P);
const CURVE_A = Fp.create(BigInt('-3'));
// prettier-ignore
const CURVE_B = BigInt('0xb3312fa7e23ee7e4988e056be3f82d19181d9c6efe8141120314088f5013875ac656398d8a2ed19d2a85c8edd3ec2aef');
// prettier-ignore
exports.p384 = (0, _shortw_utils_js_1.createCurve)({
    a: CURVE_A,
    b: CURVE_B,
    Fp,
    // Curve order, total count of valid points in the field.
    n: BigInt('0xffffffffffffffffffffffffffffffffffffffffffffffffc7634d81f4372ddf581a0db248b0a77aecec196accc52973'),
    // Base (generator) point (x, y)
    Gx: BigInt('0xaa87ca22be8b05378eb1c71ef320ad746e1d3b628ba79b9859f741e082542a385502f25dbf55296c3a545e3872760ab7'),
    Gy: BigInt('0x3617de4a96262c6f5d9e98bf9292dc29f8f41dbd289a147ce9da3113b5f0b8c00a60b1ce1d7e819d7a431d7c90ea0e5f'),
    h: BigInt(1),
    lowS: false,
}, sha512_1.sha384);
exports.secp384r1 = exports.p384;
const mapSWU = /* @__PURE__ */ (() => (0, weierstrass_js_1.mapToCurveSimpleSWU)(Fp, {
    A: CURVE_A,
    B: CURVE_B,
    Z: Fp.create(BigInt('-12')),
}))();
const htf = /* @__PURE__ */ (() => (0, hash_to_curve_js_1.createHasher)(exports.secp384r1.ProjectivePoint, (scalars) => mapSWU(scalars[0]), {
    DST: 'P384_XMD:SHA-384_SSWU_RO_',
    encodeDST: 'P384_XMD:SHA-384_SSWU_NU_',
    p: Fp.ORDER,
    m: 1,
    k: 192,
    expand: 'xmd',
    hash: sha512_1.sha384,
}))();
exports.hashToCurve = (() => htf.hashToCurve)();
exports.encodeToCurve = (() => htf.encodeToCurve)();
//# sourceMappingURL=p384.js.map