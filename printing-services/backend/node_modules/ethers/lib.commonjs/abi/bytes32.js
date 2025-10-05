"use strict";
/**
 *  About bytes32 strings...
 *
 *  @_docloc: api/utils:Bytes32 Strings
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.decodeBytes32String = exports.encodeBytes32String = void 0;
const index_js_1 = require("../utils/index.js");
/**
 *  Encodes %%text%% as a Bytes32 string.
 */
function encodeBytes32String(text) {
    // Get the bytes
    const bytes = (0, index_js_1.toUtf8Bytes)(text);
    // Check we have room for null-termination
    if (bytes.length > 31) {
        throw new Error("bytes32 string must be less than 32 bytes");
    }
    // Zero-pad (implicitly null-terminates)
    return (0, index_js_1.zeroPadBytes)(bytes, 32);
}
exports.encodeBytes32String = encodeBytes32String;
/**
 *  Encodes the Bytes32-encoded %%bytes%% into a string.
 */
function decodeBytes32String(_bytes) {
    const data = (0, index_js_1.getBytes)(_bytes, "bytes");
    // Must be 32 bytes with a null-termination
    if (data.length !== 32) {
        throw new Error("invalid bytes32 - not 32 bytes long");
    }
    if (data[31] !== 0) {
        throw new Error("invalid bytes32 string - no null terminator");
    }
    // Find the null termination
    let length = 31;
    while (data[length - 1] === 0) {
        length--;
    }
    // Determine the string value
    return (0, index_js_1.toUtf8String)(data.slice(0, length));
}
exports.decodeBytes32String = decodeBytes32String;
//# sourceMappingURL=bytes32.js.map