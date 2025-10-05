function getGlobal() {
    if (typeof self !== 'undefined') {
        return self;
    }
    if (typeof window !== 'undefined') {
        return window;
    }
    if (typeof global !== 'undefined') {
        return global;
    }
    throw new Error('unable to locate global object');
}
;
const _WebSocket = getGlobal().WebSocket;
export { _WebSocket as WebSocket };
//# sourceMappingURL=ws-browser.js.map