"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.IpcSocketProvider = void 0;
const net_1 = require("net");
const provider_socket_js_1 = require("./provider-socket.js");
// @TODO: Is this sufficient? Is this robust? Will newlines occur between
// all payloads and only between payloads?
function splitBuffer(data) {
    const messages = [];
    let lastStart = 0;
    while (true) {
        const nl = data.indexOf(10, lastStart);
        if (nl === -1) {
            break;
        }
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
class IpcSocketProvider extends provider_socket_js_1.SocketProvider {
    #socket;
    /**
     *  The connected socket.
     */
    get socket() { return this.#socket; }
    constructor(path, network, options) {
        super(network, options);
        this.#socket = (0, net_1.connect)(path);
        this.socket.on("ready", async () => {
            try {
                await this._start();
            }
            catch (error) {
                console.log("failed to start IpcSocketProvider", error);
                // @TODO: Now what? Restart?
            }
        });
        let response = Buffer.alloc(0);
        this.socket.on("data", (data) => {
            response = Buffer.concat([response, data]);
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
    destroy() {
        this.socket.destroy();
        this.socket.end();
        super.destroy();
    }
    async _write(message) {
        if (!message.endsWith("\n")) {
            message += "\n";
        }
        this.socket.write(message);
    }
}
exports.IpcSocketProvider = IpcSocketProvider;
//# sourceMappingURL=provider-ipcsocket.js.map