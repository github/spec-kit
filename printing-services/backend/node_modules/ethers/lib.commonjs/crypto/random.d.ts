/**
 *  Return %%length%% bytes of cryptographically secure random data.
 *
 *  @example:
 *    randomBytes(8)
 *    //_result:
 */
export declare function randomBytes(length: number): Uint8Array;
export declare namespace randomBytes {
    var _: (length: number) => Uint8Array;
    var lock: () => void;
    var register: (func: (length: number) => Uint8Array) => void;
}
//# sourceMappingURL=random.d.ts.map