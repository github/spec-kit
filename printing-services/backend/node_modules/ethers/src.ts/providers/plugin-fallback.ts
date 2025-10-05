
import { AbstractProviderPlugin } from "./abstract-provider.js";
import { defineProperties } from "../utils/index.js";

import type { AbstractProvider, PerformActionRequest } from "./abstract-provider.js";


export const PluginIdFallbackProvider = "org.ethers.plugins.provider.QualifiedPlugin";

export class CheckQualifiedPlugin implements AbstractProviderPlugin {
    declare name: string;

    constructor() {
        defineProperties<CheckQualifiedPlugin>(this, { name: PluginIdFallbackProvider });
    }

    connect(provider: AbstractProvider): CheckQualifiedPlugin {
        return this;
    }

    // Retruns true if this value should be considered qualified for
    // inclusion in the quorum.
    isQualified(action: PerformActionRequest, result: any): boolean {
        return true;
    }
}

export class PossiblyPrunedTransactionPlugin extends CheckQualifiedPlugin {
    isQualified(action: PerformActionRequest, result: any): boolean {
        if (action.method === "getTransaction" || action.method === "getTransactionReceipt") {
            if (result == null) { return false; }
        }
        return super.isQualified(action, result);
    }
}
