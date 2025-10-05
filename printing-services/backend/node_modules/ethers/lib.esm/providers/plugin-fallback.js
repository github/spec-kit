import { defineProperties } from "../utils/index.js";
export const PluginIdFallbackProvider = "org.ethers.plugins.provider.QualifiedPlugin";
export class CheckQualifiedPlugin {
    constructor() {
        defineProperties(this, { name: PluginIdFallbackProvider });
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
export class PossiblyPrunedTransactionPlugin extends CheckQualifiedPlugin {
    isQualified(action, result) {
        if (action.method === "getTransaction" || action.method === "getTransactionReceipt") {
            if (result == null) {
                return false;
            }
        }
        return super.isQualified(action, result);
    }
}
//# sourceMappingURL=plugin-fallback.js.map