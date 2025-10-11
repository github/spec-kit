"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CustomCondition = void 0;
const base_1 = require("../base");
class CustomCondition {
    constructor(condition) {
        this.condition = condition;
    }
    async run(_context, value, meta) {
        try {
            const result = this.condition(value, meta);
            await result;
            // if the promise resolved or the result is truthy somehow, then there's no validation halt.
            if (!result) {
                // the error thrown here is symbolic, it will be re-thrown in the catch clause anyway.
                throw new Error();
            }
        }
        catch (e) {
            throw new base_1.ValidationHalt();
        }
    }
}
exports.CustomCondition = CustomCondition;
