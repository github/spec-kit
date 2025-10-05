import { getAddress } from "../../address/index.js";
import { toBeHex } from "../../utils/maths.js";

import { Typed } from "../typed.js";
import { Coder } from "./abstract-coder.js";

import type { Reader, Writer } from "./abstract-coder.js";


/**
 *  @_ignore
 */
export class AddressCoder extends Coder {

    constructor(localName: string) {
        super("address", "address", localName, false);
    }

    defaultValue(): string {
        return "0x0000000000000000000000000000000000000000";
    }

    encode(writer: Writer, _value: string | Typed): number {
        let value = Typed.dereference(_value, "string");
        try {
            value = getAddress(value);
        } catch (error: any) {
            return this._throwError(error.message, _value);
        }
        return writer.writeValue(value);
    }

    decode(reader: Reader): any {
        return getAddress(toBeHex(reader.readValue(), 20));
    }
}
