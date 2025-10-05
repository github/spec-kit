import type { AbstractProvider, Subscriber } from "./abstract-provider.js";
import type { EventFilter, OrphanFilter, ProviderEvent } from "./provider.js";
/**
 *  Return the polling subscriber for common events.
 *
 *  @_docloc: api/providers/abstract-provider
 */
export declare function getPollingSubscriber(provider: AbstractProvider, event: ProviderEvent): Subscriber;
/**
 *  A **PollingBlockSubscriber** polls at a regular interval for a change
 *  in the block number.
 *
 *  @_docloc: api/providers/abstract-provider
 */
export declare class PollingBlockSubscriber implements Subscriber {
    #private;
    /**
     *  Create a new **PollingBlockSubscriber** attached to %%provider%%.
     */
    constructor(provider: AbstractProvider);
    /**
     *  The polling interval.
     */
    get pollingInterval(): number;
    set pollingInterval(value: number);
    start(): void;
    stop(): void;
    pause(dropWhilePaused?: boolean): void;
    resume(): void;
}
/**
 *  An **OnBlockSubscriber** can be sub-classed, with a [[_poll]]
 *  implmentation which will be called on every new block.
 *
 *  @_docloc: api/providers/abstract-provider
 */
export declare class OnBlockSubscriber implements Subscriber {
    #private;
    /**
     *  Create a new **OnBlockSubscriber** attached to %%provider%%.
     */
    constructor(provider: AbstractProvider);
    /**
     *  Called on every new block.
     */
    _poll(blockNumber: number, provider: AbstractProvider): Promise<void>;
    start(): void;
    stop(): void;
    pause(dropWhilePaused?: boolean): void;
    resume(): void;
}
export declare class PollingBlockTagSubscriber extends OnBlockSubscriber {
    #private;
    constructor(provider: AbstractProvider, tag: string);
    pause(dropWhilePaused?: boolean): void;
    _poll(blockNumber: number, provider: AbstractProvider): Promise<void>;
}
/**
 *  @_ignore:
 *
 *  @_docloc: api/providers/abstract-provider
 */
export declare class PollingOrphanSubscriber extends OnBlockSubscriber {
    #private;
    constructor(provider: AbstractProvider, filter: OrphanFilter);
    _poll(blockNumber: number, provider: AbstractProvider): Promise<void>;
}
/**
 *  A **PollingTransactionSubscriber** will poll for a given transaction
 *  hash for its receipt.
 *
 *  @_docloc: api/providers/abstract-provider
 */
export declare class PollingTransactionSubscriber extends OnBlockSubscriber {
    #private;
    /**
     *  Create a new **PollingTransactionSubscriber** attached to
     *  %%provider%%, listening for %%hash%%.
     */
    constructor(provider: AbstractProvider, hash: string);
    _poll(blockNumber: number, provider: AbstractProvider): Promise<void>;
}
/**
 *  A **PollingEventSubscriber** will poll for a given filter for its logs.
 *
 *  @_docloc: api/providers/abstract-provider
 */
export declare class PollingEventSubscriber implements Subscriber {
    #private;
    /**
     *  Create a new **PollingTransactionSubscriber** attached to
     *  %%provider%%, listening for %%filter%%.
     */
    constructor(provider: AbstractProvider, filter: EventFilter);
    start(): void;
    stop(): void;
    pause(dropWhilePaused?: boolean): void;
    resume(): void;
}
//# sourceMappingURL=subscriber-polling.d.ts.map