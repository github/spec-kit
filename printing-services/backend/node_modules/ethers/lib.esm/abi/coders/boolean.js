import { Typed } from "../typed.js";
import { Coder } from "./abstract-coder.js";
/**
 *  @_ignore
 */
export class BooleanCoder extends Coder {
    constructor(localName) {
        super("bool", "bool", localName, false);
    }
    defaultValue() {
        return false;
    }
    encode(writer, _value) {
        const value = Typed.dereference(_value, "bool");
        return writer.writeValue(value ? 1 : 0);
    }
    decode(reader) {
        return !!reader.readValue();
    }
}
//# sourceMappingURL=boolean.js.map