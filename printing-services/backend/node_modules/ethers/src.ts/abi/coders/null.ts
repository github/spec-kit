import { Coder } from "./abstract-coder.js";
import type { Reader, Writer } from "./abstract-coder.js";

const Empty = new Uint8Array([ ]);

/**
 *  @_ignore
 */
export class NullCoder extends Coder {

    constructor(localName: string) {
        super("null", "", localName, false);
    }

    defaultValue(): null {
        return null;
    }

    encode(writer: Writer, value: any): number {
        if (value != null) { this._throwError("not null", value); }
        return writer.writeBytes(Empty);
    }

    decode(reader: Reader): any {
        reader.readBytes(0);
        return null;
    }
}
