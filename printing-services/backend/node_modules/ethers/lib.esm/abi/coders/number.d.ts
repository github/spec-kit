import { Typed } from "../typed.js";
import { Coder } from "./abstract-coder.js";
import type { BigNumberish } from "../../utils/index.js";
import type { Reader, Writer } from "./abstract-coder.js";
/**
 *  @_ignore
 */
export declare class NumberCoder extends Coder {
    readonly size: number;
    readonly signed: boolean;
    constructor(size: number, signed: boolean, localName: string);
    defaultValue(): number;
    encode(writer: Writer, _value: BigNumberish | Typed): number;
    decode(reader: Reader): any;
}
//# sourceMappingURL=number.d.ts.map