"use strict";
/**
 *  Utilities for common tasks involving hashing. Also see
 *  [cryptographic hashing](about-crypto-hashing).
 *
 *  @_section: api/hashing:Hashing Utilities  [about-hashing]
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.verifyTypedData = exports.TypedDataEncoder = exports.solidityPackedSha256 = exports.solidityPackedKeccak256 = exports.solidityPacked = exports.verifyMessage = exports.hashMessage = exports.dnsEncode = exports.namehash = exports.isValidName = exports.ensNormalize = exports.id = exports.verifyAuthorization = exports.hashAuthorization = void 0;
var authorization_js_1 = require("./authorization.js");
Object.defineProperty(exports, "hashAuthorization", { enumerable: true, get: function () { return authorization_js_1.hashAuthorization; } });
Object.defineProperty(exports, "verifyAuthorization", { enumerable: true, get: function () { return authorization_js_1.verifyAuthorization; } });
var id_js_1 = require("./id.js");
Object.defineProperty(exports, "id", { enumerable: true, get: function () { return id_js_1.id; } });
var namehash_js_1 = require("./namehash.js");
Object.defineProperty(exports, "ensNormalize", { enumerable: true, get: function () { return namehash_js_1.ensNormalize; } });
Object.defineProperty(exports, "isValidName", { enumerable: true, get: function () { return namehash_js_1.isValidName; } });
Object.defineProperty(exports, "namehash", { enumerable: true, get: function () { return namehash_js_1.namehash; } });
Object.defineProperty(exports, "dnsEncode", { enumerable: true, get: function () { return namehash_js_1.dnsEncode; } });
var message_js_1 = require("./message.js");
Object.defineProperty(exports, "hashMessage", { enumerable: true, get: function () { return message_js_1.hashMessage; } });
Object.defineProperty(exports, "verifyMessage", { enumerable: true, get: function () { return message_js_1.verifyMessage; } });
var solidity_js_1 = require("./solidity.js");
Object.defineProperty(exports, "solidityPacked", { enumerable: true, get: function () { return solidity_js_1.solidityPacked; } });
Object.defineProperty(exports, "solidityPackedKeccak256", { enumerable: true, get: function () { return solidity_js_1.solidityPackedKeccak256; } });
Object.defineProperty(exports, "solidityPackedSha256", { enumerable: true, get: function () { return solidity_js_1.solidityPackedSha256; } });
var typed_data_js_1 = require("./typed-data.js");
Object.defineProperty(exports, "TypedDataEncoder", { enumerable: true, get: function () { return typed_data_js_1.TypedDataEncoder; } });
Object.defineProperty(exports, "verifyTypedData", { enumerable: true, get: function () { return typed_data_js_1.verifyTypedData; } });
//# sourceMappingURL=index.js.map