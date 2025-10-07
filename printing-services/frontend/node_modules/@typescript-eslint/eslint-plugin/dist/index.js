"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
const all_1 = __importDefault(require("./configs/all"));
const base_1 = __importDefault(require("./configs/base"));
const disable_type_checked_1 = __importDefault(require("./configs/disable-type-checked"));
const eslint_recommended_1 = __importDefault(require("./configs/eslint-recommended"));
const recommended_1 = __importDefault(require("./configs/recommended"));
const recommended_type_checked_1 = __importDefault(require("./configs/recommended-type-checked"));
const strict_1 = __importDefault(require("./configs/strict"));
const strict_type_checked_1 = __importDefault(require("./configs/strict-type-checked"));
const stylistic_1 = __importDefault(require("./configs/stylistic"));
const stylistic_type_checked_1 = __importDefault(require("./configs/stylistic-type-checked"));
const rules_1 = __importDefault(require("./rules"));
// note - cannot migrate this to an import statement because it will make TSC copy the package.json to the dist folder
const { name, version } = require('../package.json');
module.exports = {
    configs: {
        all: all_1.default,
        base: base_1.default,
        'disable-type-checked': disable_type_checked_1.default,
        'eslint-recommended': eslint_recommended_1.default,
        recommended: recommended_1.default,
        /** @deprecated - please use "recommended-type-checked" instead. */
        'recommended-requiring-type-checking': recommended_type_checked_1.default,
        'recommended-type-checked': recommended_type_checked_1.default,
        strict: strict_1.default,
        'strict-type-checked': strict_type_checked_1.default,
        stylistic: stylistic_1.default,
        'stylistic-type-checked': stylistic_type_checked_1.default,
    },
    meta: {
        name,
        version,
    },
    rules: rules_1.default,
};
//# sourceMappingURL=index.js.map