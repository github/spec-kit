"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.check = check;
const chain_1 = require("../chain");
const context_builder_1 = require("../context-builder");
const utils_1 = require("../utils");
function check(fields = '', locations = [], message) {
    const builder = new context_builder_1.ContextBuilder()
        .setFields(Array.isArray(fields) ? fields : [fields])
        .setLocations(locations)
        .setMessage(message);
    const runner = new chain_1.ContextRunnerImpl(builder);
    const middleware = async (req, _res, next) => {
        try {
            await runner.run(req);
            next();
        }
        catch (e) {
            next(e);
        }
    };
    return Object.assign(middleware, (0, utils_1.bindAll)(runner), (0, utils_1.bindAll)(new chain_1.SanitizersImpl(builder, middleware)), (0, utils_1.bindAll)(new chain_1.ValidatorsImpl(builder, middleware)), (0, utils_1.bindAll)(new chain_1.ContextHandlerImpl(builder, middleware)), { builder });
}
