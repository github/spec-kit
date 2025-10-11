"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.recoverAddress = exports.computeAddress = void 0;
const index_js_1 = require("../address/index.js");
const index_js_2 = require("../crypto/index.js");
/**
 *  Returns the address for the %%key%%.
 *
 *  The key may be any standard form of public key or a private key.
 */
function computeAddress(key) {
    let pubkey;
    if (typeof (key) === "string") {
        pubkey = index_js_2.SigningKey.computePublicKey(key, false);
    }
    else {
        pubkey = key.publicKey;
    }
    return (0, index_js_1.getAddress)((0, index_js_2.keccak256)("0x" + pubkey.substring(4)).substring(26));
}
exports.computeAddress = computeAddress;
/**
 *  Returns the recovered address for the private key that was
 *  used to sign %%digest%% that resulted in %%signature%%.
 */
function recoverAddress(digest, signature) {
    return computeAddress(index_js_2.SigningKey.recoverPublicKey(digest, signature));
}
exports.recoverAddress = recoverAddress;
//# sourceMappingURL=address.js.map