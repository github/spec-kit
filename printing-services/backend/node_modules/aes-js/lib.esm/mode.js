import { AES } from "./aes.js";
export class ModeOfOperation {
    constructor(name, key, cls) {
        if (cls && !(this instanceof cls)) {
            throw new Error(`${name} must be instantiated with "new"`);
        }
        Object.defineProperties(this, {
            aes: { enumerable: true, value: new AES(key) },
            name: { enumerable: true, value: name }
        });
    }
}
//# sourceMappingURL=mode.js.map