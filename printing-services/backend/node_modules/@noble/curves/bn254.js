"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.bn254 = void 0;
/*! noble-curves - MIT License (c) 2022 Paul Miller (paulmillr.com) */
const sha256_1 = require("@noble/hashes/sha256");
const weierstrass_js_1 = require("./abstract/weierstrass.js");
const _shortw_utils_js_1 = require("./_shortw_utils.js");
const modular_js_1 = require("./abstract/modular.js");
/**
 * bn254 pairing-friendly curve.
 * Previously known as alt_bn_128, when it had 128-bit security.
 * Recent research shown it's weaker, the naming has been adjusted to its prime bit count.
 * https://github.com/zcash/zcash/issues/2502
 */
exports.bn254 = (0, weierstrass_js_1.weierstrass)({
    a: BigInt(0),
    b: BigInt(3),
    Fp: (0, modular_js_1.Field)(BigInt('0x30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd47')),
    n: BigInt('0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001'),
    Gx: BigInt(1),
    Gy: BigInt(2),
    h: BigInt(1),
    ...(0, _shortw_utils_js_1.getHash)(sha256_1.sha256),
});
//# sourceMappingURL=bn254.js.map