import { Coder } from "./abstract-coder.js";
/**
 *  Clones the functionality of an existing Coder, but without a localName
 *
 *  @_ignore
 */
export class AnonymousCoder extends Coder {
    coder;
    constructor(coder) {
        super(coder.name, coder.type, "_", coder.dynamic);
        this.coder = coder;
    }
    defaultValue() {
        return this.coder.defaultValue();
    }
    encode(writer, value) {
        return this.coder.encode(writer, value);
    }
    decode(reader) {
        return this.coder.decode(reader);
    }
}
//# sourceMappingURL=anonymous.js.map