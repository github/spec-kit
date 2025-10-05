"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.verifyMessage = exports.hashMessage = void 0;
const index_js_1 = require("../crypto/index.js");
const index_js_2 = require("../constants/index.js");
const index_js_3 = require("../transaction/index.js");
const index_js_4 = require("../utils/index.js");
/**
 *  Computes the [[link-eip-191]] personal-sign message digest to sign.
 *
 *  This prefixes the message with [[MessagePrefix]] and the decimal length
 *  of %%message%% and computes the [[keccak256]] digest.
 *
 *  If %%message%% is a string, it is converted to its UTF-8 bytes
 *  first. To compute the digest of a [[DataHexString]], it must be converted
 *  to [bytes](getBytes).
 *
 *  @example:
 *    hashMessage("Hello World")
 *    //_result:
 *
 *    // Hashes the SIX (6) string characters, i.e.
 *    // [ "0", "x", "4", "2", "4", "3" ]
 *    hashMessage("0x4243")
 *    //_result:
 *
 *    // Hashes the TWO (2) bytes [ 0x42, 0x43 ]...
 *    hashMessage(getBytes("0x4243"))
 *    //_result:
 *
 *    // ...which is equal to using data
 *    hashMessage(new Uint8Array([ 0x42, 0x43 ]))
 *    //_result:
 *
 */
function hashMessage(message) {
    if (typeof (message) === "string") {
        message = (0, index_js_4.toUtf8Bytes)(message);
    }
    return (0, index_js_1.keccak256)((0, index_js_4.concat)([
        (0, index_js_4.toUtf8Bytes)(index_js_2.MessagePrefix),
        (0, index_js_4.toUtf8Bytes)(String(message.length)),
        message
    ]));
}
exports.hashMessage = hashMessage;
/**
 *  Return the address of the private key that produced
 *  the signature %%sig%% during signing for %%message%%.
 */
function verifyMessage(message, sig) {
    const digest = hashMessage(message);
    return (0, index_js_3.recoverAddress)(digest, sig);
}
exports.verifyMessage = verifyMessage;
//# sourceMappingURL=message.js.map