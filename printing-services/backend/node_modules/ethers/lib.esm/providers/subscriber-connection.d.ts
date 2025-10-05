import type { Subscriber } from "./abstract-provider.js";
import type { Provider } from "./provider.js";
/**
 *  @TODO
 *
 *  @_docloc: api/providers/abstract-provider
 */
export interface ConnectionRpcProvider extends Provider {
    _subscribe(param: Array<any>, processFunc: (result: any) => void): number;
    _unsubscribe(filterId: number): void;
}
/**
 *  @TODO
 *
 *  @_docloc: api/providers/abstract-provider
 */
export declare class BlockConnectionSubscriber implements Subscriber {
    #private;
    constructor(provider: ConnectionRpcProvider);
    start(): void;
    stop(): void;
    pause(dropWhilePaused?: boolean): void;
    resume(): void;
}
//# sourceMappingURL=subscriber-connection.d.ts.map