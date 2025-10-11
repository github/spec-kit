"use strict";
/**
 *  The [[link-rlp]] (RLP) encoding is used throughout Ethereum
 *  to serialize nested structures of Arrays and data.
 *
 *  @_subsection api/utils:Recursive-Length Prefix  [about-rlp]
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.encodeRlp = exports.decodeRlp = void 0;
var rlp_decode_js_1 = require("./rlp-decode.js");
Object.defineProperty(exports, "decodeRlp", { enumerable: true, get: function () { return rlp_decode_js_1.decodeRlp; } });
var rlp_encode_js_1 = require("./rlp-encode.js");
Object.defineProperty(exports, "encodeRlp", { enumerable: true, get: function () { return rlp_encode_js_1.encodeRlp; } });
//# sourceMappingURL=rlp.js.map