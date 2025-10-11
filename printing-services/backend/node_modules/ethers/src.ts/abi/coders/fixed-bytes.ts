
import { defineProperties, getBytesCopy, hexlify } from "../../utils/index.js";

import { Typed } from "../typed.js";
import { Coder } from "./abstract-coder.js";

import type { BytesLike } from "../../utils/index.js";

import type { Reader, Writer } from "./abstract-coder.js";


/**
 *  @_ignore
 */
export class FixedBytesCoder extends Coder {
    readonly size!: number;

    constructor(size: number, localName: string) {
        let name = "bytes" + String(size);
        super(name, name, localName, false);
        defineProperties<FixedBytesCoder>(this, { size }, { size: "number" });
    }

    defaultValue(): string {
        return ("0x0000000000000000000000000000000000000000000000000000000000000000").substring(0, 2 + this.size * 2);
    }

    encode(writer: Writer, _value: BytesLike | Typed): number {
        let data = getBytesCopy(Typed.dereference(_value, this.type));
        if (data.length !== this.size) { this._throwError("incorrect data length", _value); }
        return writer.writeBytes(data);
    }

    decode(reader: Reader): any {
        return hexlify(reader.readBytes(this.size));
    }
}
