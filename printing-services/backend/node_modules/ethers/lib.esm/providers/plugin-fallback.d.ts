import { AbstractProviderPlugin } from "./abstract-provider.js";
import type { AbstractProvider, PerformActionRequest } from "./abstract-provider.js";
export declare const PluginIdFallbackProvider = "org.ethers.plugins.provider.QualifiedPlugin";
export declare class CheckQualifiedPlugin implements AbstractProviderPlugin {
    name: string;
    constructor();
    connect(provider: AbstractProvider): CheckQualifiedPlugin;
    isQualified(action: PerformActionRequest, result: any): boolean;
}
export declare class PossiblyPrunedTransactionPlugin extends CheckQualifiedPlugin {
    isQualified(action: PerformActionRequest, result: any): boolean;
}
//# sourceMappingURL=plugin-fallback.d.ts.map