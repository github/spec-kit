import { Coder } from "./abstract-coder.js";
import type { Reader, Writer } from "./abstract-coder.js";
/**
 *  @_ignore
 */
export declare class NullCoder extends Coder {
    constructor(localName: string);
    defaultValue(): null;
    encode(writer: Writer, value: any): number;
    decode(reader: Reader): any;
}
//# sourceMappingURL=null.d.ts.map