"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.checkSchema = void 0;
exports.createCheckSchema = createCheckSchema;
const _ = require("lodash");
const chain_1 = require("../chain");
const utils_1 = require("../utils");
const check_1 = require("./check");
const validLocations = ['body', 'cookies', 'headers', 'params', 'query'];
const protectedNames = ['errorMessage', 'in', 'optional'];
/**
 * Factory for a {@link checkSchema()} function which can have extension validators and sanitizers.
 *
 * @see {@link checkSchema()}
 */
function createCheckSchema(createChain, extraValidators = [], extraSanitizers = []) {
    /** Type guard for an object entry for a standard validator. */
    function isStandardValidator(entry) {
        return (
        // #664 - explicitly exclude properties which should be set per validator
        !['not', 'withMessage'].includes(entry[0]) &&
            (entry[0] in chain_1.ValidatorsImpl.prototype || extraValidators.includes(entry[0])) &&
            entry[1]);
    }
    /** Type guard for an object entry for a standard sanitizer. */
    function isStandardSanitizer(entry) {
        return ((entry[0] in chain_1.SanitizersImpl.prototype || extraSanitizers.includes(entry[0])) &&
            entry[1]);
    }
    /** Type guard for an object entry for a custom validator. */
    function isCustomValidator(entry) {
        return (!isStandardValidator(entry) &&
            !isStandardSanitizer(entry) &&
            typeof entry[1] === 'object' &&
            entry[1] &&
            typeof entry[1].custom === 'function');
    }
    /** Type guard for an object entry for a custom sanitizer. */
    function isCustomSanitizer(entry) {
        return (!isStandardValidator(entry) &&
            !isStandardSanitizer(entry) &&
            typeof entry[1] === 'object' &&
            entry[1] &&
            typeof entry[1].customSanitizer === 'function');
    }
    return (schema, defaultLocations = validLocations) => {
        const chains = Object.keys(schema).map(field => {
            const config = schema[field];
            const chain = createChain(field, ensureLocations(config, defaultLocations), config.errorMessage);
            // optional doesn't matter where it happens in the chain
            if (config.optional) {
                chain.optional(config.optional === true ? true : config.optional.options);
            }
            for (const entry of Object.entries(config)) {
                if (protectedNames.includes(entry[0]) || !entry[1]) {
                    continue;
                }
                if (!isStandardValidator(entry) &&
                    !isStandardSanitizer(entry) &&
                    !isCustomValidator(entry) &&
                    !isCustomSanitizer(entry)) {
                    console.warn(`express-validator: schema of "${field}" has unknown validator/sanitizer "${entry[0]}"`);
                    continue;
                }
                // For validators, stuff that must come _before_ the validator itself in the chain.
                if ((isStandardValidator(entry) || isCustomValidator(entry)) && entry[1] !== true) {
                    const [, validatorConfig] = entry;
                    validatorConfig.if && chain.if(validatorConfig.if);
                    validatorConfig.negated && chain.not();
                }
                if (isStandardValidator(entry) || isStandardSanitizer(entry)) {
                    const options = entry[1] ? (entry[1] === true ? [] : _.castArray(entry[1].options)) : [];
                    chain[entry[0]](...options);
                }
                if (isCustomValidator(entry)) {
                    chain.custom(entry[1].custom);
                }
                if (isCustomSanitizer(entry)) {
                    chain.customSanitizer(entry[1].customSanitizer);
                }
                // For validators, stuff that must come _after_ the validator itself in the chain.
                if ((isStandardValidator(entry) || isCustomValidator(entry)) && entry[1] !== true) {
                    const [, validatorConfig] = entry;
                    validatorConfig.bail &&
                        chain.bail(validatorConfig.bail === true ? {} : validatorConfig.bail);
                    validatorConfig.errorMessage && chain.withMessage(validatorConfig.errorMessage);
                }
            }
            return chain;
        });
        const run = async (req) => (0, utils_1.runAllChains)(req, chains);
        return Object.assign(chains, { run });
    };
}
/**
 * Creates an express middleware with validations for multiple fields at once in the form of
 * a schema object.
 *
 * @param schema the schema to validate.
 * @param defaultLocations
 * @returns
 */
exports.checkSchema = createCheckSchema(check_1.check);
function ensureLocations(config, defaults) {
    // .filter(Boolean) is done because in can be undefined -- which is not going away from the type
    // See https://github.com/Microsoft/TypeScript/pull/29955 for details
    const locations = Array.isArray(config.in)
        ? config.in
        : [config.in].filter(Boolean);
    const actualLocations = locations.length ? locations : defaults;
    return actualLocations.filter(location => validLocations.includes(location));
}
