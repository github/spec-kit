"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.oneOf = oneOf;
const _ = require("lodash");
const chain_1 = require("../chain");
const context_builder_1 = require("../context-builder");
const utils_1 = require("../utils");
// A dummy context item that gets added to surrogate contexts just to make them run
const dummyItem = { async run() { } };
/**
 * Creates a middleware that will ensure that at least one of the given validation chains
 * or validation chain groups are valid.
 *
 * If none are, a single `AlternativeValidationError` or `GroupedAlternativeValidationError`
 * is added to the request, with the errors of each chain made available under the `nestedErrors` property.
 *
 * @param chains an array of validation chains to check if are valid.
 *               If any of the items of `chains` is an array of validation chains, then all of them
 *               must be valid together for the request to be considered valid.
 */
function oneOf(chains, options = {}) {
    const run = async (req, opts) => {
        const surrogateContext = new context_builder_1.ContextBuilder().addItem(dummyItem).build();
        // Run each group of chains in parallel
        const promises = chains.map(async (chain) => {
            const group = Array.isArray(chain) ? chain : [chain];
            const results = await (0, utils_1.runAllChains)(req, group, { dryRun: true });
            const { contexts, groupErrors } = results.reduce(({ contexts, groupErrors }, result) => {
                const { context } = result;
                contexts.push(context);
                const fieldErrors = context.errors.filter((error) => error.type === 'field');
                groupErrors.push(...fieldErrors);
                return { contexts, groupErrors };
            }, {
                contexts: [],
                groupErrors: [],
            });
            // #536: The data from a chain within oneOf() can only be made available to e.g. matchedData()
            // if its entire group is valid.
            if (!groupErrors.length) {
                contexts.forEach(context => {
                    surrogateContext.addFieldInstances(context.getData());
                });
            }
            return groupErrors;
        });
        const allErrors = await Promise.all(promises);
        const success = allErrors.some(groupErrors => groupErrors.length === 0);
        if (!success) {
            const message = options.message || 'Invalid value(s)';
            switch (options.errorType) {
                case 'flat':
                    surrogateContext.addError({
                        type: 'alternative',
                        req,
                        message,
                        nestedErrors: _.flatMap(allErrors),
                    });
                    break;
                case 'least_errored':
                    let leastErroredIndex = 0;
                    for (let i = 1; i < allErrors.length; i++) {
                        if (allErrors[i].length < allErrors[leastErroredIndex].length) {
                            leastErroredIndex = i;
                        }
                    }
                    surrogateContext.addError({
                        type: 'alternative',
                        req,
                        message,
                        nestedErrors: allErrors[leastErroredIndex],
                    });
                    break;
                case 'grouped':
                default:
                    // grouped
                    surrogateContext.addError({
                        type: 'alternative_grouped',
                        req,
                        message,
                        nestedErrors: allErrors,
                    });
                    break;
            }
        }
        // Final context running pass to ensure contexts are added and values are modified properly
        return await new chain_1.ContextRunnerImpl(surrogateContext).run(req, opts);
    };
    const middleware = (req, _res, next) => run(req).then(() => next(), next);
    return Object.assign(middleware, { run });
}
