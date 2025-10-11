"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.parseOptions = void 0;
const util_1 = require("../../util");
const enums_1 = require("./enums");
const shared_1 = require("./shared");
const validator_1 = require("./validator");
function normalizeOption(option) {
    let weight = 0;
    option.modifiers?.forEach(mod => {
        weight |= enums_1.Modifiers[mod];
    });
    option.types?.forEach(mod => {
        weight |= enums_1.TypeModifiers[mod];
    });
    // give selectors with a filter the _highest_ priority
    if (option.filter) {
        weight |= 1 << 30;
    }
    const normalizedOption = {
        // format options
        format: option.format ? option.format.map(f => enums_1.PredefinedFormats[f]) : null,
        custom: option.custom
            ? {
                regex: new RegExp(option.custom.regex, 'u'),
                match: option.custom.match,
            }
            : null,
        leadingUnderscore: option.leadingUnderscore !== undefined
            ? enums_1.UnderscoreOptions[option.leadingUnderscore]
            : null,
        trailingUnderscore: option.trailingUnderscore !== undefined
            ? enums_1.UnderscoreOptions[option.trailingUnderscore]
            : null,
        prefix: option.prefix && option.prefix.length > 0 ? option.prefix : null,
        suffix: option.suffix && option.suffix.length > 0 ? option.suffix : null,
        modifiers: option.modifiers?.map(m => enums_1.Modifiers[m]) ?? null,
        types: option.types?.map(m => enums_1.TypeModifiers[m]) ?? null,
        filter: option.filter !== undefined
            ? typeof option.filter === 'string'
                ? {
                    regex: new RegExp(option.filter, 'u'),
                    match: true,
                }
                : {
                    regex: new RegExp(option.filter.regex, 'u'),
                    match: option.filter.match,
                }
            : null,
        // calculated ordering weight based on modifiers
        modifierWeight: weight,
    };
    const selectors = Array.isArray(option.selector)
        ? option.selector
        : [option.selector];
    return selectors.map(selector => ({
        selector: (0, shared_1.isMetaSelector)(selector)
            ? enums_1.MetaSelectors[selector]
            : enums_1.Selectors[selector],
        ...normalizedOption,
    }));
}
function parseOptions(context) {
    const normalizedOptions = context.options
        .map(opt => normalizeOption(opt))
        .reduce((acc, val) => acc.concat(val), []);
    const result = (0, util_1.getEnumNames)(enums_1.Selectors).reduce((acc, k) => {
        acc[k] = (0, validator_1.createValidator)(k, context, normalizedOptions);
        return acc;
        // eslint-disable-next-line @typescript-eslint/prefer-reduce-type-parameter
    }, {});
    return result;
}
exports.parseOptions = parseOptions;
//# sourceMappingURL=parse-options.js.map