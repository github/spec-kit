"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Sanitization = void 0;
const utils_1 = require("../utils");
class Sanitization {
    constructor(sanitizer, custom, options = [], 
    // For testing only.
    // Deliberately not calling it `toString` in order to not override `Object.prototype.toString`.
    stringify = utils_1.toString) {
        this.sanitizer = sanitizer;
        this.custom = custom;
        this.options = options;
        this.stringify = stringify;
    }
    async run(context, value, meta) {
        const { path, location } = meta;
        const runCustomSanitizer = async () => {
            const sanitizerValue = this.sanitizer(value, meta);
            return Promise.resolve(sanitizerValue);
        };
        if (this.custom) {
            const newValue = await runCustomSanitizer();
            context.setData(path, newValue, location);
            return;
        }
        const values = Array.isArray(value) ? value : [value];
        const newValues = values.map(value => {
            return this.sanitizer(this.stringify(value), ...this.options);
        });
        // We get only the first value of the array if the orginal value was wrapped.
        context.setData(path, values !== value ? newValues[0] : newValues, location);
    }
}
exports.Sanitization = Sanitization;
