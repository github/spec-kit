import { Coder } from "./abstract-coder.js";
const Empty = new Uint8Array([]);
/**
 *  @_ignore
 */
export class NullCoder extends Coder {
    constructor(localName) {
        super("null", "", localName, false);
    }
    defaultValue() {
        return null;
    }
    encode(writer, value) {
        if (value != null) {
            this._throwError("not null", value);
        }
        return writer.writeBytes(Empty);
    }
    decode(reader) {
        reader.readBytes(0);
        return null;
    }
}
//# sourceMappingURL=null.js.map