"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ModeOfOperation = void 0;
const aes_js_1 = require("./aes.js");
class ModeOfOperation {
    constructor(name, key, cls) {
        if (cls && !(this instanceof cls)) {
            throw new Error(`${name} must be instantiated with "new"`);
        }
        Object.defineProperties(this, {
            aes: { enumerable: true, value: new aes_js_1.AES(key) },
            name: { enumerable: true, value: name }
        });
    }
}
exports.ModeOfOperation = ModeOfOperation;
//# sourceMappingURL=mode.js.map