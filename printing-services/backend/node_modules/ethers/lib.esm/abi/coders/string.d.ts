import { Typed } from "../typed.js";
import { DynamicBytesCoder } from "./bytes.js";
import type { Reader, Writer } from "./abstract-coder.js";
/**
 *  @_ignore
 */
export declare class StringCoder extends DynamicBytesCoder {
    constructor(localName: string);
    defaultValue(): string;
    encode(writer: Writer, _value: string | Typed): number;
    decode(reader: Reader): any;
}
//# sourceMappingURL=string.d.ts.map