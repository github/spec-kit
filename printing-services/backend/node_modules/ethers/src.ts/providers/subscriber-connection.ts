
import { getNumber } from "../utils/index.js";

import type { Subscriber } from "./abstract-provider.js";


//#TODO: Temp
import type { Provider } from "./provider.js";

/**
 *  @TODO
 *
 *  @_docloc: api/providers/abstract-provider
 */
export interface ConnectionRpcProvider extends Provider {
    //send(method: string, params: Array<any>): Promise<any>;
    _subscribe(param: Array<any>, processFunc: (result: any) => void): number;
    _unsubscribe(filterId: number): void;
}

/**
 *  @TODO
 *
 *  @_docloc: api/providers/abstract-provider
 */
export class BlockConnectionSubscriber implements Subscriber {
    #provider: ConnectionRpcProvider;
    #blockNumber: number;

    #running: boolean;

    #filterId: null | number;

    constructor(provider: ConnectionRpcProvider) {
        this.#provider = provider;
        this.#blockNumber = -2;
        this.#running = false;
        this.#filterId = null;
    }

    start(): void {
        if (this.#running) { return; }
        this.#running = true;

        this.#filterId = this.#provider._subscribe([ "newHeads" ], (result: any) => {
            const blockNumber = getNumber(result.number);
            const initial = (this.#blockNumber === -2) ? blockNumber: (this.#blockNumber + 1)
            for (let b = initial; b <= blockNumber; b++) {
                this.#provider.emit("block", b);
            }
            this.#blockNumber = blockNumber;
        });
    }

    stop(): void {
        if (!this.#running) { return; }
        this.#running = false;

        if (this.#filterId != null) {
            this.#provider._unsubscribe(this.#filterId);
            this.#filterId = null;
        }
    }

    pause(dropWhilePaused?: boolean): void {
        if (dropWhilePaused) { this.#blockNumber = -2; }
        this.stop();
    }

    resume(): void {
        this.start();
    }
}

