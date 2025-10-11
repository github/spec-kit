"use strict";
/**
 *  There are many simple utilities required to interact with
 *  Ethereum and to simplify the library, without increasing
 *  the library dependencies for simple functions.
 *
 *  @_section api/utils:Utilities  [about-utils]
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.toUtf8String = exports.toUtf8CodePoints = exports.toUtf8Bytes = exports.parseUnits = exports.formatUnits = exports.parseEther = exports.formatEther = exports.encodeRlp = exports.decodeRlp = exports.defineProperties = exports.resolveProperties = exports.toQuantity = exports.toBeArray = exports.toBeHex = exports.toNumber = exports.toBigInt = exports.getUint = exports.getNumber = exports.getBigInt = exports.mask = exports.toTwos = exports.fromTwos = exports.FixedNumber = exports.FetchCancelSignal = exports.FetchResponse = exports.FetchRequest = exports.EventPayload = exports.makeError = exports.assertNormalize = exports.assertPrivate = exports.assertArgumentCount = exports.assertArgument = exports.assert = exports.isError = exports.isCallException = exports.zeroPadBytes = exports.zeroPadValue = exports.stripZerosLeft = exports.dataSlice = exports.dataLength = exports.concat = exports.hexlify = exports.isBytesLike = exports.isHexString = exports.getBytesCopy = exports.getBytes = exports.encodeBase64 = exports.decodeBase64 = exports.encodeBase58 = exports.decodeBase58 = void 0;
exports.uuidV4 = exports.Utf8ErrorFuncs = void 0;
var base58_js_1 = require("./base58.js");
Object.defineProperty(exports, "decodeBase58", { enumerable: true, get: function () { return base58_js_1.decodeBase58; } });
Object.defineProperty(exports, "encodeBase58", { enumerable: true, get: function () { return base58_js_1.encodeBase58; } });
var base64_js_1 = require("./base64.js");
Object.defineProperty(exports, "decodeBase64", { enumerable: true, get: function () { return base64_js_1.decodeBase64; } });
Object.defineProperty(exports, "encodeBase64", { enumerable: true, get: function () { return base64_js_1.encodeBase64; } });
var data_js_1 = require("./data.js");
Object.defineProperty(exports, "getBytes", { enumerable: true, get: function () { return data_js_1.getBytes; } });
Object.defineProperty(exports, "getBytesCopy", { enumerable: true, get: function () { return data_js_1.getBytesCopy; } });
Object.defineProperty(exports, "isHexString", { enumerable: true, get: function () { return data_js_1.isHexString; } });
Object.defineProperty(exports, "isBytesLike", { enumerable: true, get: function () { return data_js_1.isBytesLike; } });
Object.defineProperty(exports, "hexlify", { enumerable: true, get: function () { return data_js_1.hexlify; } });
Object.defineProperty(exports, "concat", { enumerable: true, get: function () { return data_js_1.concat; } });
Object.defineProperty(exports, "dataLength", { enumerable: true, get: function () { return data_js_1.dataLength; } });
Object.defineProperty(exports, "dataSlice", { enumerable: true, get: function () { return data_js_1.dataSlice; } });
Object.defineProperty(exports, "stripZerosLeft", { enumerable: true, get: function () { return data_js_1.stripZerosLeft; } });
Object.defineProperty(exports, "zeroPadValue", { enumerable: true, get: function () { return data_js_1.zeroPadValue; } });
Object.defineProperty(exports, "zeroPadBytes", { enumerable: true, get: function () { return data_js_1.zeroPadBytes; } });
var errors_js_1 = require("./errors.js");
Object.defineProperty(exports, "isCallException", { enumerable: true, get: function () { return errors_js_1.isCallException; } });
Object.defineProperty(exports, "isError", { enumerable: true, get: function () { return errors_js_1.isError; } });
Object.defineProperty(exports, "assert", { enumerable: true, get: function () { return errors_js_1.assert; } });
Object.defineProperty(exports, "assertArgument", { enumerable: true, get: function () { return errors_js_1.assertArgument; } });
Object.defineProperty(exports, "assertArgumentCount", { enumerable: true, get: function () { return errors_js_1.assertArgumentCount; } });
Object.defineProperty(exports, "assertPrivate", { enumerable: true, get: function () { return errors_js_1.assertPrivate; } });
Object.defineProperty(exports, "assertNormalize", { enumerable: true, get: function () { return errors_js_1.assertNormalize; } });
Object.defineProperty(exports, "makeError", { enumerable: true, get: function () { return errors_js_1.makeError; } });
var events_js_1 = require("./events.js");
Object.defineProperty(exports, "EventPayload", { enumerable: true, get: function () { return events_js_1.EventPayload; } });
var fetch_js_1 = require("./fetch.js");
Object.defineProperty(exports, "FetchRequest", { enumerable: true, get: function () { return fetch_js_1.FetchRequest; } });
Object.defineProperty(exports, "FetchResponse", { enumerable: true, get: function () { return fetch_js_1.FetchResponse; } });
Object.defineProperty(exports, "FetchCancelSignal", { enumerable: true, get: function () { return fetch_js_1.FetchCancelSignal; } });
var fixednumber_js_1 = require("./fixednumber.js");
Object.defineProperty(exports, "FixedNumber", { enumerable: true, get: function () { return fixednumber_js_1.FixedNumber; } });
var maths_js_1 = require("./maths.js");
Object.defineProperty(exports, "fromTwos", { enumerable: true, get: function () { return maths_js_1.fromTwos; } });
Object.defineProperty(exports, "toTwos", { enumerable: true, get: function () { return maths_js_1.toTwos; } });
Object.defineProperty(exports, "mask", { enumerable: true, get: function () { return maths_js_1.mask; } });
Object.defineProperty(exports, "getBigInt", { enumerable: true, get: function () { return maths_js_1.getBigInt; } });
Object.defineProperty(exports, "getNumber", { enumerable: true, get: function () { return maths_js_1.getNumber; } });
Object.defineProperty(exports, "getUint", { enumerable: true, get: function () { return maths_js_1.getUint; } });
Object.defineProperty(exports, "toBigInt", { enumerable: true, get: function () { return maths_js_1.toBigInt; } });
Object.defineProperty(exports, "toNumber", { enumerable: true, get: function () { return maths_js_1.toNumber; } });
Object.defineProperty(exports, "toBeHex", { enumerable: true, get: function () { return maths_js_1.toBeHex; } });
Object.defineProperty(exports, "toBeArray", { enumerable: true, get: function () { return maths_js_1.toBeArray; } });
Object.defineProperty(exports, "toQuantity", { enumerable: true, get: function () { return maths_js_1.toQuantity; } });
var properties_js_1 = require("./properties.js");
Object.defineProperty(exports, "resolveProperties", { enumerable: true, get: function () { return properties_js_1.resolveProperties; } });
Object.defineProperty(exports, "defineProperties", { enumerable: true, get: function () { return properties_js_1.defineProperties; } });
var rlp_decode_js_1 = require("./rlp-decode.js");
Object.defineProperty(exports, "decodeRlp", { enumerable: true, get: function () { return rlp_decode_js_1.decodeRlp; } });
var rlp_encode_js_1 = require("./rlp-encode.js");
Object.defineProperty(exports, "encodeRlp", { enumerable: true, get: function () { return rlp_encode_js_1.encodeRlp; } });
var units_js_1 = require("./units.js");
Object.defineProperty(exports, "formatEther", { enumerable: true, get: function () { return units_js_1.formatEther; } });
Object.defineProperty(exports, "parseEther", { enumerable: true, get: function () { return units_js_1.parseEther; } });
Object.defineProperty(exports, "formatUnits", { enumerable: true, get: function () { return units_js_1.formatUnits; } });
Object.defineProperty(exports, "parseUnits", { enumerable: true, get: function () { return units_js_1.parseUnits; } });
var utf8_js_1 = require("./utf8.js");
Object.defineProperty(exports, "toUtf8Bytes", { enumerable: true, get: function () { return utf8_js_1.toUtf8Bytes; } });
Object.defineProperty(exports, "toUtf8CodePoints", { enumerable: true, get: function () { return utf8_js_1.toUtf8CodePoints; } });
Object.defineProperty(exports, "toUtf8String", { enumerable: true, get: function () { return utf8_js_1.toUtf8String; } });
Object.defineProperty(exports, "Utf8ErrorFuncs", { enumerable: true, get: function () { return utf8_js_1.Utf8ErrorFuncs; } });
var uuid_js_1 = require("./uuid.js");
Object.defineProperty(exports, "uuidV4", { enumerable: true, get: function () { return uuid_js_1.uuidV4; } });
//# sourceMappingURL=index.js.map