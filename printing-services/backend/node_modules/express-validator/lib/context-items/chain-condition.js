"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChainCondition = void 0;
const base_1 = require("../base");
class ChainCondition {
    constructor(chain) {
        this.chain = chain;
    }
    async run(_context, _value, meta) {
        const result = await this.chain.run(meta.req, { dryRun: true });
        if (!result.isEmpty()) {
            throw new base_1.ValidationHalt();
        }
    }
}
exports.ChainCondition = ChainCondition;
