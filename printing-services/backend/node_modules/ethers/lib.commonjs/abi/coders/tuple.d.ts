import { Typed } from "../typed.js";
import { Coder } from "./abstract-coder.js";
import type { Reader, Writer } from "./abstract-coder.js";
/**
 *  @_ignore
 */
export declare class TupleCoder extends Coder {
    readonly coders: ReadonlyArray<Coder>;
    constructor(coders: Array<Coder>, localName: string);
    defaultValue(): any;
    encode(writer: Writer, _value: Array<any> | {
        [name: string]: any;
    } | Typed): number;
    decode(reader: Reader): any;
}
//# sourceMappingURL=tuple.d.ts.map