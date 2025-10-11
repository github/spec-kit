"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.encodeBase64 = exports.decodeBase64 = void 0;
/**
 *  [Base64 encoding](link-wiki-base64) using 6-bit words to encode
 *  arbitrary bytes into a string using 65 printable symbols, the
 *  upper-case and lower-case alphabet, the digits ``0`` through ``9``,
 *  ``"+"`` and ``"/"`` with the ``"="`` used for padding.
 *
 *  @_subsection: api/utils:Base64 Encoding  [about-base64]
 */
const data_js_1 = require("./data.js");
/**
 *  Decodes the base-64 encoded %%value%%.
 *
 *  @example:
 *    // The decoded value is always binary data...
 *    result = decodeBase64("SGVsbG8gV29ybGQhIQ==")
 *    //_result:
 *
 *    // ...use toUtf8String to convert it to a string.
 *    toUtf8String(result)
 *    //_result:
 *
 *    // Decoding binary data
 *    decodeBase64("EjQ=")
 *    //_result:
 */
function decodeBase64(value) {
    return (0, data_js_1.getBytesCopy)(Buffer.from(value, "base64"));
}
exports.decodeBase64 = decodeBase64;
;
/**
 *  Encodes %%data%% as a base-64 encoded string.
 *
 *  @example:
 *    // Encoding binary data as a hexstring
 *    encodeBase64("0x1234")
 *    //_result:
 *
 *    // Encoding binary data as a Uint8Array
 *    encodeBase64(new Uint8Array([ 0x12, 0x34 ]))
 *    //_result:
 *
 *    // The input MUST be data...
 *    encodeBase64("Hello World!!")
 *    //_error:
 *
 *    // ...use toUtf8Bytes for this.
 *    encodeBase64(toUtf8Bytes("Hello World!!"))
 *    //_result:
 */
function encodeBase64(data) {
    return Buffer.from((0, data_js_1.getBytes)(data)).toString("base64");
}
exports.encodeBase64 = encodeBase64;
//# sourceMappingURL=base64.js.map