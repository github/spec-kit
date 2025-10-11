"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PossiblyPrunedTransactionPlugin = exports.CheckQualifiedPlugin = exports.PluginIdFallbackProvider = void 0;
const index_js_1 = require("../utils/index.js");
exports.PluginIdFallbackProvider = "org.ethers.plugins.provider.QualifiedPlugin";
class CheckQualifiedPlugin {
    constructor() {
        (0, index_js_1.defineProperties)(this, { name: exports.PluginIdFallbackProvider });
    }
    connect(provider) {
        return this;
    }
    // Retruns true if this value should be considered qualified for
    // inclusion in the quorum.
    isQualified(action, result) {
        return true;
    }
}
exports.CheckQualifiedPlugin = CheckQualifiedPlugin;
class PossiblyPrunedTransactionPlugin extends CheckQualifiedPlugin {
    isQualified(action, result) {
        if (action.method === "getTransaction" || action.method === "getTransactionReceipt") {
            if (result == null) {
                return false;
            }
        }
        return super.isQualified(action, result);
    }
}
exports.PossiblyPrunedTransactionPlugin = PossiblyPrunedTransactionPlugin;
//# sourceMappingURL=plugin-fallback.js.map