"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ContextRunnerImpl = exports.ResultWithContextImpl = void 0;
const _ = require("lodash");
const base_1 = require("../base");
const context_1 = require("../context");
const field_selection_1 = require("../field-selection");
const validation_result_1 = require("../validation-result");
class ResultWithContextImpl extends validation_result_1.Result {
    constructor(context) {
        super(error => error, context.errors);
        this.context = context;
    }
}
exports.ResultWithContextImpl = ResultWithContextImpl;
class ContextRunnerImpl {
    constructor(builderOrContext, selectFields = field_selection_1.selectFields) {
        this.builderOrContext = builderOrContext;
        this.selectFields = selectFields;
    }
    async run(req, options = {}) {
        const context = this.builderOrContext instanceof context_1.Context
            ? this.builderOrContext
            : this.builderOrContext.build();
        const internalReq = req;
        const bail = internalReq[base_1.contextsKey]?.some(context => context.bail && context.errors.length > 0);
        if (bail) {
            return new ResultWithContextImpl(context);
        }
        const instances = this.selectFields(req, context.fields, context.locations);
        context.addFieldInstances(instances);
        const haltedInstances = new Set();
        for (const contextItem of context.stack) {
            const promises = context.getData({ requiredOnly: true }).map(async (instance) => {
                const { location, path } = instance;
                const instanceKey = `${location}:${path}`;
                if (haltedInstances.has(instanceKey)) {
                    return;
                }
                try {
                    await contextItem.run(context, instance.value, {
                        req,
                        location,
                        path,
                        pathValues: instance.pathValues,
                    });
                    // An instance is mutable, so if an item changed its value, there's no need to call getData again
                    const newValue = instance.value;
                    // Checks whether the value changed.
                    // Avoids e.g. undefined values being set on the request if it didn't have the key initially.
                    const reqValue = path !== '' ? _.get(req[location], path) : req[location];
                    if (!options.dryRun && reqValue !== instance.value) {
                        path !== '' ? _.set(req[location], path, newValue) : _.set(req, location, newValue);
                    }
                }
                catch (e) {
                    if (e instanceof base_1.ValidationHalt) {
                        haltedInstances.add(instanceKey);
                        return;
                    }
                    throw e;
                }
            });
            await Promise.all(promises);
        }
        if (!options.dryRun) {
            internalReq[base_1.contextsKey] = (internalReq[base_1.contextsKey] || []).concat(context);
        }
        return new ResultWithContextImpl(context);
    }
}
exports.ContextRunnerImpl = ContextRunnerImpl;
