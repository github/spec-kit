import { defineProperties, getBytesCopy, hexlify } from "../../utils/index.js";
import { Typed } from "../typed.js";
import { Coder } from "./abstract-coder.js";
/**
 *  @_ignore
 */
export class FixedBytesCoder extends Coder {
    size;
    constructor(size, localName) {
        let name = "bytes" + String(size);
        super(name, name, localName, false);
        defineProperties(this, { size }, { size: "number" });
    }
    defaultValue() {
        return ("0x0000000000000000000000000000000000000000000000000000000000000000").substring(0, 2 + this.size * 2);
    }
    encode(writer, _value) {
        let data = getBytesCopy(Typed.dereference(_value, this.type));
        if (data.length !== this.size) {
            this._throwError("incorrect data length", _value);
        }
        return writer.writeBytes(data);
    }
    decode(reader) {
        return hexlify(reader.readBytes(this.size));
    }
}
//# sourceMappingURL=fixed-bytes.js.map