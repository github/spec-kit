import { getBytesCopy, hexlify } from "../../utils/index.js";

import { Coder } from "./abstract-coder.js";

import type { Reader, Writer } from "./abstract-coder.js";


/**
 *  @_ignore
 */
export class DynamicBytesCoder extends Coder {
    constructor(type: string, localName: string) {
       super(type, type, localName, true);
    }

    defaultValue(): string {
        return "0x";
    }

    encode(writer: Writer, value: any): number {
        value = getBytesCopy(value);
        let length = writer.writeValue(value.length);
        length += writer.writeBytes(value);
        return length;
    }

    decode(reader: Reader): any {
        return reader.readBytes(reader.readIndex(), true);
    }
}

/**
 *  @_ignore
 */
export class BytesCoder extends DynamicBytesCoder {
    constructor(localName: string) {
        super("bytes", localName);
    }

    decode(reader: Reader): any {
        return hexlify(super.decode(reader));
    }
}
