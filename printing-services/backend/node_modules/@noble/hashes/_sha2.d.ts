import { Hash, Input } from './utils.js';
export declare abstract class SHA2<T extends SHA2<T>> extends Hash<T> {
    readonly blockLen: number;
    outputLen: number;
    readonly padOffset: number;
    readonly isLE: boolean;
    protected abstract process(buf: DataView, offset: number): void;
    protected abstract get(): number[];
    protected abstract set(...args: number[]): void;
    abstract destroy(): void;
    protected abstract roundClean(): void;
    protected buffer: Uint8Array;
    protected view: DataView;
    protected finished: boolean;
    protected length: number;
    protected pos: number;
    protected destroyed: boolean;
    constructor(blockLen: number, outputLen: number, padOffset: number, isLE: boolean);
    update(data: Input): this;
    digestInto(out: Uint8Array): void;
    digest(): Uint8Array;
    _cloneInto(to?: T): T;
}
