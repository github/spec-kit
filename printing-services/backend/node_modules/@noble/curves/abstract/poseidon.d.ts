/*! noble-curves - MIT License (c) 2022 Paul Miller (paulmillr.com) */
import { IField } from './modular.js';
export type PoseidonOpts = {
    Fp: IField<bigint>;
    t: number;
    roundsFull: number;
    roundsPartial: number;
    sboxPower?: number;
    reversePartialPowIdx?: boolean;
    mds: bigint[][];
    roundConstants: bigint[][];
};
export declare function validateOpts(opts: PoseidonOpts): Readonly<{
    rounds: number;
    sboxFn: (n: bigint) => bigint;
    roundConstants: bigint[][];
    mds: bigint[][];
    Fp: IField<bigint>;
    t: number;
    roundsFull: number;
    roundsPartial: number;
    sboxPower?: number | undefined;
    reversePartialPowIdx?: boolean | undefined;
}>;
export declare function splitConstants(rc: bigint[], t: number): bigint[][];
export declare function poseidon(opts: PoseidonOpts): {
    (values: bigint[]): bigint[];
    roundConstants: bigint[][];
};
//# sourceMappingURL=poseidon.d.ts.map