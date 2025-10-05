"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ContextBuilder = void 0;
const context_1 = require("./context");
class ContextBuilder {
    constructor() {
        this.stack = [];
        this.fields = [];
        this.locations = [];
        this.optional = false;
        this.requestBail = false;
        this.visibility = { type: 'visible' };
    }
    setFields(fields) {
        this.fields = fields;
        return this;
    }
    setLocations(locations) {
        this.locations = locations;
        return this;
    }
    setMessage(message) {
        this.message = message;
        return this;
    }
    addItem(...items) {
        this.stack.push(...items);
        return this;
    }
    setOptional(options) {
        this.optional = options;
        return this;
    }
    setRequestBail() {
        this.requestBail = true;
        return this;
    }
    setHidden(hidden, hiddenValue) {
        if (hidden) {
            this.visibility =
                hiddenValue !== undefined ? { type: 'redacted', value: hiddenValue } : { type: 'hidden' };
        }
        else {
            this.visibility = { type: 'visible' };
        }
        return this;
    }
    build() {
        return new context_1.Context(this.fields, this.locations, this.stack, this.optional, this.requestBail, this.visibility, this.message);
    }
}
exports.ContextBuilder = ContextBuilder;
