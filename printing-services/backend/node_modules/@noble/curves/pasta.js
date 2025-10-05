"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.vesta = exports.pallas = exports.q = exports.p = void 0;
/*! noble-curves - MIT License (c) 2022 Paul Miller (paulmillr.com) */
const sha256_1 = require("@noble/hashes/sha256");
const weierstrass_js_1 = require("./abstract/weierstrass.js");
const _shortw_utils_js_1 = require("./_shortw_utils.js");
const mod = require("./abstract/modular.js");
exports.p = BigInt('0x40000000000000000000000000000000224698fc094cf91b992d30ed00000001');
exports.q = BigInt('0x40000000000000000000000000000000224698fc0994a8dd8c46eb2100000001');
// https://neuromancer.sk/std/other/Pallas
exports.pallas = (0, weierstrass_js_1.weierstrass)({
    a: BigInt(0),
    b: BigInt(5),
    Fp: mod.Field(exports.p),
    n: exports.q,
    Gx: mod.mod(BigInt(-1), exports.p),
    Gy: BigInt(2),
    h: BigInt(1),
    ...(0, _shortw_utils_js_1.getHash)(sha256_1.sha256),
});
// https://neuromancer.sk/std/other/Vesta
exports.vesta = (0, weierstrass_js_1.weierstrass)({
    a: BigInt(0),
    b: BigInt(5),
    Fp: mod.Field(exports.q),
    n: exports.p,
    Gx: mod.mod(BigInt(-1), exports.q),
    Gy: BigInt(2),
    h: BigInt(1),
    ...(0, _shortw_utils_js_1.getHash)(sha256_1.sha256),
});
//# sourceMappingURL=pasta.js.map