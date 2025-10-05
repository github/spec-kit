import { Typed } from "../typed.js";
import { Coder, Result, Writer } from "./abstract-coder.js";
import type { Reader } from "./abstract-coder.js";
/**
 *  @_ignore
 */
export declare function pack(writer: Writer, coders: ReadonlyArray<Coder>, values: Array<any> | {
    [name: string]: any;
}): number;
/**
 *  @_ignore
 */
export declare function unpack(reader: Reader, coders: ReadonlyArray<Coder>): Result;
/**
 *  @_ignore
 */
export declare class ArrayCoder extends Coder {
    readonly coder: Coder;
    readonly length: number;
    constructor(coder: Coder, length: number, localName: string);
    defaultValue(): Array<any>;
    encode(writer: Writer, _value: Array<any> | Typed): number;
    decode(reader: Reader): any;
}
//# sourceMappingURL=array.d.ts.map