"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.verifyAuthorization = exports.hashAuthorization = void 0;
const index_js_1 = require("../address/index.js");
const index_js_2 = require("../crypto/index.js");
const index_js_3 = require("../transaction/index.js");
const index_js_4 = require("../utils/index.js");
/**
 *  Computes the [[link-eip-7702]] authorization digest to sign.
 */
function hashAuthorization(auth) {
    (0, index_js_4.assertArgument)(typeof (auth.address) === "string", "invalid address for hashAuthorization", "auth.address", auth);
    return (0, index_js_2.keccak256)((0, index_js_4.concat)([
        "0x05", (0, index_js_4.encodeRlp)([
            (auth.chainId != null) ? (0, index_js_4.toBeArray)(auth.chainId) : "0x",
            (0, index_js_1.getAddress)(auth.address),
            (auth.nonce != null) ? (0, index_js_4.toBeArray)(auth.nonce) : "0x",
        ])
    ]));
}
exports.hashAuthorization = hashAuthorization;
/**
 *  Return the address of the private key that produced
 *  the signature %%sig%% during signing for %%message%%.
 */
function verifyAuthorization(auth, sig) {
    return (0, index_js_3.recoverAddress)(hashAuthorization(auth), sig);
}
exports.verifyAuthorization = verifyAuthorization;
//# sourceMappingURL=authorization.js.map