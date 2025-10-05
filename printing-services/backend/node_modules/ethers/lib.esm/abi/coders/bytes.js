import { getBytesCopy, hexlify } from "../../utils/index.js";
import { Coder } from "./abstract-coder.js";
/**
 *  @_ignore
 */
export class DynamicBytesCoder extends Coder {
    constructor(type, localName) {
        super(type, type, localName, true);
    }
    defaultValue() {
        return "0x";
    }
    encode(writer, value) {
        value = getBytesCopy(value);
        let length = writer.writeValue(value.length);
        length += writer.writeBytes(value);
        return length;
    }
    decode(reader) {
        return reader.readBytes(reader.readIndex(), true);
    }
}
/**
 *  @_ignore
 */
export class BytesCoder extends DynamicBytesCoder {
    constructor(localName) {
        super("bytes", localName);
    }
    decode(reader) {
        return hexlify(super.decode(reader));
    }
}
//# sourceMappingURL=bytes.js.map