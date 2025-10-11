import { Typed } from "../typed.js";
import { Coder } from "./abstract-coder.js";

import type { Reader, Writer } from "./abstract-coder.js";

/**
 *  @_ignore
 */
export class BooleanCoder extends Coder {

    constructor(localName: string) {
        super("bool", "bool", localName, false);
    }

    defaultValue(): boolean {
        return false;
    }

    encode(writer: Writer, _value: boolean | Typed): number {
        const value = Typed.dereference(_value, "bool");
        return writer.writeValue(value ? 1: 0);
    }

    decode(reader: Reader): any {
        return !!reader.readValue();
    }
}
