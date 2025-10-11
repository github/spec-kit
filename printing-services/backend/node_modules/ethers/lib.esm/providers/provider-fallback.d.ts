import { AbstractProvider } from "./abstract-provider.js";
import { Network } from "./network.js";
import type { PerformActionRequest } from "./abstract-provider.js";
import type { Networkish } from "./network.js";
/**
 *  A configuration entry for how to use a [[Provider]].
 */
export interface FallbackProviderConfig {
    /**
     *  The provider.
     */
    provider: AbstractProvider;
    /**
     *  The amount of time to wait before kicking off the next provider.
     *
     *  Any providers that have not responded can still respond and be
     *  counted, but this ensures new providers start.
     */
    stallTimeout?: number;
    /**
     *  The priority. Lower priority providers are dispatched first.
     */
    priority?: number;
    /**
     *  The amount of weight a provider is given against the quorum.
     */
    weight?: number;
}
/**
 *  The statistics and state maintained for a [[Provider]].
 */
export interface FallbackProviderState extends Required<FallbackProviderConfig> {
    /**
     *  The most recent blockNumber this provider has reported (-2 if none).
     */
    blockNumber: number;
    /**
     *  The number of total requests ever sent to this provider.
     */
    requests: number;
    /**
     *  The number of responses that errored.
     */
    errorResponses: number;
    /**
     *  The number of responses that occured after the result resolved.
     */
    lateResponses: number;
    /**
     *  How many times syncing was required to catch up the expected block.
     */
    outOfSync: number;
    /**
     *  The number of requests which reported unsupported operation.
     */
    unsupportedEvents: number;
    /**
     *  A rolling average (5% current duration) for response time.
     */
    rollingDuration: number;
    /**
     *  The ratio of quorum-agreed results to total.
     */
    score: number;
}
/**
 *  Additional options to configure a [[FallbackProvider]].
 */
export type FallbackProviderOptions = {
    quorum?: number;
    eventQuorum?: number;
    eventWorkers?: number;
    cacheTimeout?: number;
    pollingInterval?: number;
};
/**
 *  A **FallbackProvider** manages several [[Providers]] providing
 *  resilience by switching between slow or misbehaving nodes, security
 *  by requiring multiple backends to aggree and performance by allowing
 *  faster backends to respond earlier.
 *
 */
export declare class FallbackProvider extends AbstractProvider {
    #private;
    /**
     *  The number of backends that must agree on a value before it is
     *  accpeted.
     */
    readonly quorum: number;
    /**
     *  @_ignore:
     */
    readonly eventQuorum: number;
    /**
     *  @_ignore:
     */
    readonly eventWorkers: number;
    /**
     *  Creates a new **FallbackProvider** with %%providers%% connected to
     *  %%network%%.
     *
     *  If a [[Provider]] is included in %%providers%%, defaults are used
     *  for the configuration.
     */
    constructor(providers: Array<AbstractProvider | FallbackProviderConfig>, network?: Networkish, options?: FallbackProviderOptions);
    get providerConfigs(): Array<FallbackProviderState>;
    _detectNetwork(): Promise<Network>;
    /**
     *  Transforms a %%req%% into the correct method call on %%provider%%.
     */
    _translatePerform(provider: AbstractProvider, req: PerformActionRequest): Promise<any>;
    _perform<T = any>(req: PerformActionRequest): Promise<T>;
    destroy(): Promise<void>;
}
//# sourceMappingURL=provider-fallback.d.ts.map