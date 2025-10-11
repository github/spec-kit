import { getNumber } from "../utils/index.js";
/**
 *  @TODO
 *
 *  @_docloc: api/providers/abstract-provider
 */
export class BlockConnectionSubscriber {
    #provider;
    #blockNumber;
    #running;
    #filterId;
    constructor(provider) {
        this.#provider = provider;
        this.#blockNumber = -2;
        this.#running = false;
        this.#filterId = null;
    }
    start() {
        if (this.#running) {
            return;
        }
        this.#running = true;
        this.#filterId = this.#provider._subscribe(["newHeads"], (result) => {
            const blockNumber = getNumber(result.number);
            const initial = (this.#blockNumber === -2) ? blockNumber : (this.#blockNumber + 1);
            for (let b = initial; b <= blockNumber; b++) {
                this.#provider.emit("block", b);
            }
            this.#blockNumber = blockNumber;
        });
    }
    stop() {
        if (!this.#running) {
            return;
        }
        this.#running = false;
        if (this.#filterId != null) {
            this.#provider._unsubscribe(this.#filterId);
            this.#filterId = null;
        }
    }
    pause(dropWhilePaused) {
        if (dropWhilePaused) {
            this.#blockNumber = -2;
        }
        this.stop();
    }
    resume() {
        this.start();
    }
}
//# sourceMappingURL=subscriber-connection.js.map