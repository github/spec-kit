"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.checkExact = checkExact;
const base_1 = require("../base");
const chain_1 = require("../chain");
const context_1 = require("../context");
const field_selection_1 = require("../field-selection");
const utils_1 = require("../utils");
/**
 * Checks whether the request contains exactly only those fields that have been validated.
 *
 * Unknown fields, if found, will generate an error of type `unknown_fields`.
 *
 * @param chains either a single chain, an array of chains, or a mixed array of chains and array of chains.
 *               This means that all of the below are valid:
 * ```
 * checkExact(check('foo'))
 * checkExact([check('foo'), check('bar')])
 * checkExact([check('foo'), check('bar')])
 * checkExact(checkSchema({ ... }))
 * checkExact([checkSchema({ ... }), check('foo')])
 * ```
 * @param opts
 */
function checkExact(chains, opts) {
    // Don't include all locations by default. Browsers will add cookies and headers that the user
    // might not want to validate, which would be a footgun.
    const locations = opts?.locations || ['body', 'params', 'query'];
    const chainsArr = Array.isArray(chains) ? chains.flat() : chains ? [chains] : [];
    const run = async (req) => {
        const internalReq = req;
        const fieldsByLocation = new Map();
        await (0, utils_1.runAllChains)(req, chainsArr);
        // The chains above will have added contexts to the request
        (internalReq[base_1.contextsKey] || []).forEach(context => {
            context.locations.forEach(location => {
                if (!locations.includes(location)) {
                    return;
                }
                const locationFields = fieldsByLocation.get(location) || [];
                locationFields.push(...context.fields);
                fieldsByLocation.set(location, locationFields);
            });
        });
        // when none of the chains matched anything, then everything is unknown.
        if (!fieldsByLocation.size) {
            locations.forEach(location => fieldsByLocation.set(location, []));
        }
        let unknownFields = [];
        for (const [location, fields] of fieldsByLocation.entries()) {
            unknownFields = unknownFields.concat((0, field_selection_1.selectUnknownFields)(req, fields, [location]));
        }
        const context = new context_1.Context([], [], [], false, false);
        if (unknownFields.length) {
            context.addError({
                type: 'unknown_fields',
                req,
                message: opts?.message || 'Unknown field(s)',
                fields: unknownFields,
            });
        }
        internalReq[base_1.contextsKey] = internalReq[base_1.contextsKey] || [];
        internalReq[base_1.contextsKey].push(context);
        return new chain_1.ResultWithContextImpl(context);
    };
    const middleware = (req, _res, next) => run(req).then(() => next(), next);
    return Object.assign(middleware, { run });
}
