import { Typed } from "../typed.js";
import { Coder } from "./abstract-coder.js";
import type { Reader, Writer } from "./abstract-coder.js";
/**
 *  @_ignore
 */
export declare class BooleanCoder extends Coder {
    constructor(localName: string);
    defaultValue(): boolean;
    encode(writer: Writer, _value: boolean | Typed): number;
    decode(reader: Reader): any;
}
//# sourceMappingURL=boolean.d.ts.map