
import { connect } from "net";
import { SocketProvider } from "./provider-socket.js";

import type { Socket } from "net";

import type { JsonRpcApiProviderOptions } from "./provider-jsonrpc.js";
import type { Networkish } from "./network.js";


// @TODO: Is this sufficient? Is this robust? Will newlines occur between
// all payloads and only between payloads?
function splitBuffer(data: Buffer): { messages: Array<string>, remaining: Buffer } {
    const messages: Array<string> = [ ];

    let lastStart = 0;
    while (true) {
        const nl = data.indexOf(10, lastStart);
        if (nl === -1) { break; }
        messages.push(data.subarray(lastStart, nl).toString().trim());
        lastStart = nl + 1;
    }

    return { messages, remaining: data.subarray(lastStart) };
}

/**
 *  An **IpcSocketProvider** connects over an IPC socket on the host
 *  which provides fast access to the node, but requires the node and
 *  the script run on the same machine.
 */
export class IpcSocketProvider extends SocketProvider {
    #socket: Socket;

    /**
     *  The connected socket.
     */
    get socket(): Socket { return this.#socket; }

    constructor(path: string, network?: Networkish, options?: JsonRpcApiProviderOptions) {
        super(network, options);
        this.#socket = connect(path);

        this.socket.on("ready", async () => {
            try {
                await this._start();
            } catch (error) {
                console.log("failed to start IpcSocketProvider", error);
                // @TODO: Now what? Restart?
            }
        });

        let response = Buffer.alloc(0);
        this.socket.on("data", (data) => {
            response = Buffer.concat([ response, data ]);
            const { messages, remaining } = splitBuffer(response);
            messages.forEach((message) => {
                this._processMessage(message);
            });
            response = remaining;
        });

        this.socket.on("end", () => {
            this.emit("close");
            this.socket.destroy();
            this.socket.end();
        });
    }

    destroy(): void {
        this.socket.destroy();
        this.socket.end();

        super.destroy();
    }

    async _write(message: string): Promise<void> {
        if (!message.endsWith("\n")) { message += "\n"; }
        this.socket.write(message);
    }
}
