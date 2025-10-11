import { Input } from './utils.js';
export type ArgonOpts = {
    t: number;
    m: number;
    p: number;
    version?: number;
    key?: Input;
    personalization?: Input;
    dkLen?: number;
    asyncTick?: number;
    maxmem?: number;
    onProgress?: (progress: number) => void;
};
export declare const argon2d: (password: Input, salt: Input, opts: ArgonOpts) => Uint8Array;
export declare const argon2i: (password: Input, salt: Input, opts: ArgonOpts) => Uint8Array;
export declare const argon2id: (password: Input, salt: Input, opts: ArgonOpts) => Uint8Array;
