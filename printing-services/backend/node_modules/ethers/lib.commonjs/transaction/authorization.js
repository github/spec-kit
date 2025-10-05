"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.authorizationify = void 0;
const index_js_1 = require("../address/index.js");
const index_js_2 = require("../crypto/index.js");
const index_js_3 = require("../utils/index.js");
function authorizationify(auth) {
    return {
        address: (0, index_js_1.getAddress)(auth.address),
        nonce: (0, index_js_3.getBigInt)((auth.nonce != null) ? auth.nonce : 0),
        chainId: (0, index_js_3.getBigInt)((auth.chainId != null) ? auth.chainId : 0),
        signature: index_js_2.Signature.from(auth.signature)
    };
}
exports.authorizationify = authorizationify;
//# sourceMappingURL=authorization.js.map