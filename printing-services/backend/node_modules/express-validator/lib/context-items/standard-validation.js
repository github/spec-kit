"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.StandardValidation = void 0;
const utils_1 = require("../utils");
class StandardValidation {
    constructor(validator, negated, options = [], 
    // For testing only.
    // Deliberately not calling it `toString` in order to not override `Object.prototype.toString`.
    stringify = utils_1.toString) {
        this.validator = validator;
        this.negated = negated;
        this.options = options;
        this.stringify = stringify;
    }
    async run(context, value, meta) {
        const values = Array.isArray(value) ? value : [value];
        values.forEach(value => {
            const result = this.validator(this.stringify(value), ...this.options);
            if (this.negated ? result : !result) {
                context.addError({ type: 'field', message: this.message, value, meta });
            }
        });
    }
}
exports.StandardValidation = StandardValidation;
