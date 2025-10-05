export declare class BitWriter {
    #private;
    readonly width: number;
    constructor(width: number);
    write(value: number): void;
    get length(): number;
    get data(): string;
}
export interface AccentSet {
    accent: number;
    follows: string;
    positions: Array<number>;
    positionsLength: number;
    positionData: string;
    positionDataLength: number;
}
export declare function extractAccents(words: Array<string>): {
    accents: Array<AccentSet>;
    words: Array<string>;
};
export declare function encodeOwl(words: Array<string>): {
    subs: string;
    data: string;
};
//# sourceMappingURL=encode-latin.d.ts.map