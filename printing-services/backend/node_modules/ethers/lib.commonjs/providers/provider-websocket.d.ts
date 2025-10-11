import { SocketProvider } from "./provider-socket.js";
import type { JsonRpcApiProviderOptions } from "./provider-jsonrpc.js";
import type { Networkish } from "./network.js";
/**
 *  A generic interface to a Websocket-like object.
 */
export interface WebSocketLike {
    onopen: null | ((...args: Array<any>) => any);
    onmessage: null | ((...args: Array<any>) => any);
    onerror: null | ((...args: Array<any>) => any);
    readyState: number;
    send(payload: any): void;
    close(code?: number, reason?: string): void;
}
/**
 *  A function which can be used to re-create a WebSocket connection
 *  on disconnect.
 */
export type WebSocketCreator = () => WebSocketLike;
/**
 *  A JSON-RPC provider which is backed by a WebSocket.
 *
 *  WebSockets are often preferred because they retain a live connection
 *  to a server, which permits more instant access to events.
 *
 *  However, this incurs higher server infrasturture costs, so additional
 *  resources may be required to host your own WebSocket nodes and many
 *  third-party services charge additional fees for WebSocket endpoints.
 */
export declare class WebSocketProvider extends SocketProvider {
    #private;
    get websocket(): WebSocketLike;
    constructor(url: string | WebSocketLike | WebSocketCreator, network?: Networkish, options?: JsonRpcApiProviderOptions);
    _write(message: string): Promise<void>;
    destroy(): Promise<void>;
}
//# sourceMappingURL=provider-websocket.d.ts.map