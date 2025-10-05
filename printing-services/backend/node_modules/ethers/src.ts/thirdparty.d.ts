

declare module "ws" {
    export class WebSocket {
        constructor(...args: Array<any>);

        onopen: null | ((...args: Array<any>) => any);
        onmessage: null | ((...args: Array<any>) => any);
        onerror: null | ((...args: Array<any>) => any);

        readyState: number;

        send(payload: any): void;
        close(code?: number, reason?: string): void;
    }
}
