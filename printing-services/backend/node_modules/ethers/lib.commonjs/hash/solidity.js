"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.solidityPackedSha256 = exports.solidityPackedKeccak256 = exports.solidityPacked = void 0;
const index_js_1 = require("../address/index.js");
const index_js_2 = require("../crypto/index.js");
const index_js_3 = require("../utils/index.js");
const regexBytes = new RegExp("^bytes([0-9]+)$");
const regexNumber = new RegExp("^(u?int)([0-9]*)$");
const regexArray = new RegExp("^(.*)\\[([0-9]*)\\]$");
function _pack(type, value, isArray) {
    switch (type) {
        case "address":
            if (isArray) {
                return (0, index_js_3.getBytes)((0, index_js_3.zeroPadValue)(value, 32));
            }
            return (0, index_js_3.getBytes)((0, index_js_1.getAddress)(value));
        case "string":
            return (0, index_js_3.toUtf8Bytes)(value);
        case "bytes":
            return (0, index_js_3.getBytes)(value);
        case "bool":
            value = (!!value ? "0x01" : "0x00");
            if (isArray) {
                return (0, index_js_3.getBytes)((0, index_js_3.zeroPadValue)(value, 32));
            }
            return (0, index_js_3.getBytes)(value);
    }
    let match = type.match(regexNumber);
    if (match) {
        let signed = (match[1] === "int");
        let size = parseInt(match[2] || "256");
        (0, index_js_3.assertArgument)((!match[2] || match[2] === String(size)) && (size % 8 === 0) && size !== 0 && size <= 256, "invalid number type", "type", type);
        if (isArray) {
            size = 256;
        }
        if (signed) {
            value = (0, index_js_3.toTwos)(value, size);
        }
        return (0, index_js_3.getBytes)((0, index_js_3.zeroPadValue)((0, index_js_3.toBeArray)(value), size / 8));
    }
    match = type.match(regexBytes);
    if (match) {
        const size = parseInt(match[1]);
        (0, index_js_3.assertArgument)(String(size) === match[1] && size !== 0 && size <= 32, "invalid bytes type", "type", type);
        (0, index_js_3.assertArgument)((0, index_js_3.dataLength)(value) === size, `invalid value for ${type}`, "value", value);
        if (isArray) {
            return (0, index_js_3.getBytes)((0, index_js_3.zeroPadBytes)(value, 32));
        }
        return value;
    }
    match = type.match(regexArray);
    if (match && Array.isArray(value)) {
        const baseType = match[1];
        const count = parseInt(match[2] || String(value.length));
        (0, index_js_3.assertArgument)(count === value.length, `invalid array length for ${type}`, "value", value);
        const result = [];
        value.forEach(function (value) {
            result.push(_pack(baseType, value, true));
        });
        return (0, index_js_3.getBytes)((0, index_js_3.concat)(result));
    }
    (0, index_js_3.assertArgument)(false, "invalid type", "type", type);
}
// @TODO: Array Enum
/**
 *   Computes the [[link-solc-packed]] representation of %%values%%
 *   respectively to their %%types%%.
 *
 *   @example:
 *       addr = "0x8ba1f109551bd432803012645ac136ddd64dba72"
 *       solidityPacked([ "address", "uint" ], [ addr, 45 ]);
 *       //_result:
 */
function solidityPacked(types, values) {
    (0, index_js_3.assertArgument)(types.length === values.length, "wrong number of values; expected ${ types.length }", "values", values);
    const tight = [];
    types.forEach(function (type, index) {
        tight.push(_pack(type, values[index]));
    });
    return (0, index_js_3.hexlify)((0, index_js_3.concat)(tight));
}
exports.solidityPacked = solidityPacked;
/**
 *   Computes the [[link-solc-packed]] [[keccak256]] hash of %%values%%
 *   respectively to their %%types%%.
 *
 *   @example:
 *       addr = "0x8ba1f109551bd432803012645ac136ddd64dba72"
 *       solidityPackedKeccak256([ "address", "uint" ], [ addr, 45 ]);
 *       //_result:
 */
function solidityPackedKeccak256(types, values) {
    return (0, index_js_2.keccak256)(solidityPacked(types, values));
}
exports.solidityPackedKeccak256 = solidityPackedKeccak256;
/**
 *   Computes the [[link-solc-packed]] [[sha256]] hash of %%values%%
 *   respectively to their %%types%%.
 *
 *   @example:
 *       addr = "0x8ba1f109551bd432803012645ac136ddd64dba72"
 *       solidityPackedSha256([ "address", "uint" ], [ addr, 45 ]);
 *       //_result:
 */
function solidityPackedSha256(types, values) {
    return (0, index_js_2.sha256)(solidityPacked(types, values));
}
exports.solidityPackedSha256 = solidityPackedSha256;
//# sourceMappingURL=solidity.js.map