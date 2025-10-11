import { Typed } from "../typed.js";
import { Coder } from "./abstract-coder.js";
import type { Reader, Writer } from "./abstract-coder.js";
/**
 *  @_ignore
 */
export declare class AddressCoder extends Coder {
    constructor(localName: string);
    defaultValue(): string;
    encode(writer: Writer, _value: string | Typed): number;
    decode(reader: Reader): any;
}
//# sourceMappingURL=address.d.ts.map