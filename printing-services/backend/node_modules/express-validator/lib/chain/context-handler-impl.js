"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ContextHandlerImpl = void 0;
const context_items_1 = require("../context-items");
const bail_1 = require("../context-items/bail");
class ContextHandlerImpl {
    constructor(builder, chain) {
        this.builder = builder;
        this.chain = chain;
    }
    bail(opts) {
        if (opts?.level === 'request') {
            this.builder.setRequestBail();
        }
        this.builder.addItem(new bail_1.Bail());
        return this.chain;
    }
    if(condition) {
        if ('run' in condition) {
            this.builder.addItem(new context_items_1.ChainCondition(condition));
        }
        else if (typeof condition === 'function') {
            this.builder.addItem(new context_items_1.CustomCondition(condition));
        }
        else {
            throw new Error('express-validator: condition is not a validation chain nor a function');
        }
        return this.chain;
    }
    optional(options = true) {
        let value;
        if (typeof options === 'boolean') {
            value = options ? 'undefined' : false;
        }
        else {
            value = options.values
                ? options.values
                : options.checkFalsy
                    ? 'falsy'
                    : options.nullable
                        ? 'null'
                        : 'undefined';
        }
        this.builder.setOptional(value);
        return this.chain;
    }
    hide(hiddenValue) {
        this.builder.setHidden(true, hiddenValue);
        return this.chain;
    }
}
exports.ContextHandlerImpl = ContextHandlerImpl;
