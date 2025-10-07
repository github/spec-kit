/**
 * @fileoverview Flat config schema
 * @author Nicholas C. Zakas
 */

"use strict";

//-----------------------------------------------------------------------------
// Requirements
//-----------------------------------------------------------------------------

/*
 * Note: This can be removed in ESLint v9 because structuredClone is available globally
 * starting in Node.js v17.
 */
const structuredClone = require("@ungap/structured-clone").default;
const { normalizeSeverityToNumber } = require("../shared/severity");

//-----------------------------------------------------------------------------
// Type Definitions
//-----------------------------------------------------------------------------

/**
 * @typedef ObjectPropertySchema
 * @property {Function|string} merge The function or name of the function to call
 *      to merge multiple objects with this property.
 * @property {Function|string} validate The function or name of the function to call
 *      to validate the value of this property.
 */

//-----------------------------------------------------------------------------
// Helpers
//-----------------------------------------------------------------------------

const ruleSeverities = new Map([
    [0, 0], ["off", 0],
    [1, 1], ["warn", 1],
    [2, 2], ["error", 2]
]);

const globalVariablesValues = new Set([
    true, "true", "writable", "writeable",
    false, "false", "readonly", "readable", null,
    "off"
]);

/**
 * Check if a value is a non-null object.
 * @param {any} value The value to check.
 * @returns {boolean} `true` if the value is a non-null object.
 */
function isNonNullObject(value) {
    return typeof value === "object" && value !== null;
}

/**
 * Check if a value is a non-null non-array object.
 * @param {any} value The value to check.
 * @returns {boolean} `true` if the value is a non-null non-array object.
 */
function isNonArrayObject(value) {
    return isNonNullObject(value) && !Array.isArray(value);
}

/**
 * Check if a value is undefined.
 * @param {any} value The value to check.
 * @returns {boolean} `true` if the value is undefined.
 */
function isUndefined(value) {
    return typeof value === "undefined";
}

/**
 * Deeply merges two non-array objects.
 * @param {Object} first The base object.
 * @param {Object} second The overrides object.
 * @param {Map<string, Map<string, Object>>} [mergeMap] Maps the combination of first and second arguments to a merged result.
 * @returns {Object} An object with properties from both first and second.
 */
function deepMerge(first, second, mergeMap = new Map()) {

    let secondMergeMap = mergeMap.get(first);

    if (secondMergeMap) {
        const result = secondMergeMap.get(second);

        if (result) {

            // If this combination of first and second arguments has been already visited, return the previously created result.
            return result;
        }
    } else {
        secondMergeMap = new Map();
        mergeMap.set(first, secondMergeMap);
    }

    /*
     * First create a result object where properties from the second object
     * overwrite properties from the first. This sets up a baseline to use
     * later rather than needing to inspect and change every property
     * individually.
     */
    const result = {
        ...first,
        ...second
    };

    delete result.__proto__; // eslint-disable-line no-proto -- don't merge own property "__proto__"

    // Store the pending result for this combination of first and second arguments.
    secondMergeMap.set(second, result);

    for (const key of Object.keys(second)) {

        // avoid hairy edge case
        if (key === "__proto__" || !Object.prototype.propertyIsEnumerable.call(first, key)) {
            continue;
        }

        const firstValue = first[key];
        const secondValue = second[key];

        if (isNonArrayObject(firstValue) && isNonArrayObject(secondValue)) {
            result[key] = deepMerge(firstValue, secondValue, mergeMap);
        } else if (isUndefined(secondValue)) {
            result[key] = firstValue;
        }
    }

    return result;

}

/**
 * Normalizes the rule options config for a given rule by ensuring that
 * it is an array and that the first item is 0, 1, or 2.
 * @param {Array|string|number} ruleOptions The rule options config.
 * @returns {Array} An array of rule options.
 */
function normalizeRuleOptions(ruleOptions) {

    const finalOptions = Array.isArray(ruleOptions)
        ? ruleOptions.slice(0)
        : [ruleOptions];

    finalOptions[0] = ruleSeverities.get(finalOptions[0]);
    return structuredClone(finalOptions);
}

//-----------------------------------------------------------------------------
// Assertions
//-----------------------------------------------------------------------------

/**
 * The error type when a rule's options are configured with an invalid type.
 */
class InvalidRuleOptionsError extends Error {

    /**
     * @param {string} ruleId Rule name being configured.
     * @param {any} value The invalid value.
     */
    constructor(ruleId, value) {
        super(`Key "${ruleId}": Expected severity of "off", 0, "warn", 1, "error", or 2.`);
        this.messageTemplate = "invalid-rule-options";
        this.messageData = { ruleId, value };
    }
}

/**
 * Validates that a value is a valid rule options entry.
 * @param {string} ruleId Rule name being configured.
 * @param {any} value The value to check.
 * @returns {void}
 * @throws {InvalidRuleOptionsError} If the value isn't a valid rule options.
 */
function assertIsRuleOptions(ruleId, value) {
    if (typeof value !== "string" && typeof value !== "number" && !Array.isArray(value)) {
        throw new InvalidRuleOptionsError(ruleId, value);
    }
}

/**
 * The error type when a rule's severity is invalid.
 */
class InvalidRuleSeverityError extends Error {

    /**
     * @param {string} ruleId Rule name being configured.
     * @param {any} value The invalid value.
     */
    constructor(ruleId, value) {
        super(`Key "${ruleId}": Expected severity of "off", 0, "warn", 1, "error", or 2.`);
        this.messageTemplate = "invalid-rule-severity";
        this.messageData = { ruleId, value };
    }
}

/**
 * Validates that a value is valid rule severity.
 * @param {string} ruleId Rule name being configured.
 * @param {any} value The value to check.
 * @returns {void}
 * @throws {InvalidRuleSeverityError} If the value isn't a valid rule severity.
 */
function assertIsRuleSeverity(ruleId, value) {
    const severity = ruleSeverities.get(value);

    if (typeof severity === "undefined") {
        throw new InvalidRuleSeverityError(ruleId, value);
    }
}

/**
 * Validates that a given string is the form pluginName/objectName.
 * @param {string} value The string to check.
 * @returns {void}
 * @throws {TypeError} If the string isn't in the correct format.
 */
function assertIsPluginMemberName(value) {
    if (!/[@a-z0-9-_$]+(?:\/(?:[a-z0-9-_$]+))+$/iu.test(value)) {
        throw new TypeError(`Expected string in the form "pluginName/objectName" but found "${value}".`);
    }
}

/**
 * Validates that a value is an object.
 * @param {any} value The value to check.
 * @returns {void}
 * @throws {TypeError} If the value isn't an object.
 */
function assertIsObject(value) {
    if (!isNonNullObject(value)) {
        throw new TypeError("Expected an object.");
    }
}

/**
 * The error type when there's an eslintrc-style options in a flat config.
 */
class IncompatibleKeyError extends Error {

    /**
     * @param {string} key The invalid key.
     */
    constructor(key) {
        super("This appears to be in eslintrc format rather than flat config format.");
        this.messageTemplate = "eslintrc-incompat";
        this.messageData = { key };
    }
}

/**
 * The error type when there's an eslintrc-style plugins array found.
 */
class IncompatiblePluginsError extends Error {

    /**
     * Creates a new instance.
     * @param {Array<string>} plugins The plugins array.
     */
    constructor(plugins) {
        super("This appears to be in eslintrc format (array of strings) rather than flat config format (object).");
        this.messageTemplate = "eslintrc-plugins";
        this.messageData = { plugins };
    }
}


//-----------------------------------------------------------------------------
// Low-Level Schemas
//-----------------------------------------------------------------------------

/** @type {ObjectPropertySchema} */
const booleanSchema = {
    merge: "replace",
    validate: "boolean"
};

const ALLOWED_SEVERITIES = new Set(["error", "warn", "off", 2, 1, 0]);

/** @type {ObjectPropertySchema} */
const disableDirectiveSeveritySchema = {
    merge(first, second) {
        const value = second === void 0 ? first : second;

        if (typeof value === "boolean") {
            return value ? "warn" : "off";
        }

        return normalizeSeverityToNumber(value);
    },
    validate(value) {
        if (!(ALLOWED_SEVERITIES.has(value) || typeof value === "boolean")) {
            throw new TypeError("Expected one of: \"error\", \"warn\", \"off\", 0, 1, 2, or a boolean.");
        }
    }
};

/** @type {ObjectPropertySchema} */
const deepObjectAssignSchema = {
    merge(first = {}, second = {}) {
        return deepMerge(first, second);
    },
    validate: "object"
};

//-----------------------------------------------------------------------------
// High-Level Schemas
//-----------------------------------------------------------------------------

/** @type {ObjectPropertySchema} */
const globalsSchema = {
    merge: "assign",
    validate(value) {

        assertIsObject(value);

        for (const key of Object.keys(value)) {

            // avoid hairy edge case
            if (key === "__proto__") {
                continue;
            }

            if (key !== key.trim()) {
                throw new TypeError(`Global "${key}" has leading or trailing whitespace.`);
            }

            if (!globalVariablesValues.has(value[key])) {
                throw new TypeError(`Key "${key}": Expected "readonly", "writable", or "off".`);
            }
        }
    }
};

/** @type {ObjectPropertySchema} */
const parserSchema = {
    merge: "replace",
    validate(value) {

        if (!value || typeof value !== "object" ||
            (typeof value.parse !== "function" && typeof value.parseForESLint !== "function")
        ) {
            throw new TypeError("Expected object with parse() or parseForESLint() method.");
        }

    }
};

/** @type {ObjectPropertySchema} */
const pluginsSchema = {
    merge(first = {}, second = {}) {
        const keys = new Set([...Object.keys(first), ...Object.keys(second)]);
        const result = {};

        // manually validate that plugins are not redefined
        for (const key of keys) {

            // avoid hairy edge case
            if (key === "__proto__") {
                continue;
            }

            if (key in first && key in second && first[key] !== second[key]) {
                throw new TypeError(`Cannot redefine plugin "${key}".`);
            }

            result[key] = second[key] || first[key];
        }

        return result;
    },
    validate(value) {

        // first check the value to be sure it's an object
        if (value === null || typeof value !== "object") {
            throw new TypeError("Expected an object.");
        }

        // make sure it's not an array, which would mean eslintrc-style is used
        if (Array.isArray(value)) {
            throw new IncompatiblePluginsError(value);
        }

        // second check the keys to make sure they are objects
        for (const key of Object.keys(value)) {

            // avoid hairy edge case
            if (key === "__proto__") {
                continue;
            }

            if (value[key] === null || typeof value[key] !== "object") {
                throw new TypeError(`Key "${key}": Expected an object.`);
            }
        }
    }
};

/** @type {ObjectPropertySchema} */
const processorSchema = {
    merge: "replace",
    validate(value) {
        if (typeof value === "string") {
            assertIsPluginMemberName(value);
        } else if (value && typeof value === "object") {
            if (typeof value.preprocess !== "function" || typeof value.postprocess !== "function") {
                throw new TypeError("Object must have a preprocess() and a postprocess() method.");
            }
        } else {
            throw new TypeError("Expected an object or a string.");
        }
    }
};

/** @type {ObjectPropertySchema} */
const rulesSchema = {
    merge(first = {}, second = {}) {

        const result = {
            ...first,
            ...second
        };


        for (const ruleId of Object.keys(result)) {

            try {

                // avoid hairy edge case
                if (ruleId === "__proto__") {

                    /* eslint-disable-next-line no-proto -- Though deprecated, may still be present */
                    delete result.__proto__;
                    continue;
                }

                result[ruleId] = normalizeRuleOptions(result[ruleId]);

                /*
                 * If either rule config is missing, then the correct
                 * config is already present and we just need to normalize
                 * the severity.
                 */
                if (!(ruleId in first) || !(ruleId in second)) {
                    continue;
                }

                const firstRuleOptions = normalizeRuleOptions(first[ruleId]);
                const secondRuleOptions = normalizeRuleOptions(second[ruleId]);

                /*
                 * If the second rule config only has a severity (length of 1),
                 * then use that severity and keep the rest of the options from
                 * the first rule config.
                 */
                if (secondRuleOptions.length === 1) {
                    result[ruleId] = [secondRuleOptions[0], ...firstRuleOptions.slice(1)];
                    continue;
                }

                /*
                 * In any other situation, then the second rule config takes
                 * precedence. That means the value at `result[ruleId]` is
                 * already correct and no further work is necessary.
                 */
            } catch (ex) {
                throw new Error(`Key "${ruleId}": ${ex.message}`, { cause: ex });
            }

        }

        return result;


    },

    validate(value) {
        assertIsObject(value);

        /*
         * We are not checking the rule schema here because there is no
         * guarantee that the rule definition is present at this point. Instead
         * we wait and check the rule schema during the finalization step
         * of calculating a config.
         */
        for (const ruleId of Object.keys(value)) {

            // avoid hairy edge case
            if (ruleId === "__proto__") {
                continue;
            }

            const ruleOptions = value[ruleId];

            assertIsRuleOptions(ruleId, ruleOptions);

            if (Array.isArray(ruleOptions)) {
                assertIsRuleSeverity(ruleId, ruleOptions[0]);
            } else {
                assertIsRuleSeverity(ruleId, ruleOptions);
            }
        }
    }
};

/** @type {ObjectPropertySchema} */
const ecmaVersionSchema = {
    merge: "replace",
    validate(value) {
        if (typeof value === "number" || value === "latest") {
            return;
        }

        throw new TypeError("Expected a number or \"latest\".");
    }
};

/** @type {ObjectPropertySchema} */
const sourceTypeSchema = {
    merge: "replace",
    validate(value) {
        if (typeof value !== "string" || !/^(?:script|module|commonjs)$/u.test(value)) {
            throw new TypeError("Expected \"script\", \"module\", or \"commonjs\".");
        }
    }
};

/**
 * Creates a schema that always throws an error. Useful for warning
 * about eslintrc-style keys.
 * @param {string} key The eslintrc key to create a schema for.
 * @returns {ObjectPropertySchema} The schema.
 */
function createEslintrcErrorSchema(key) {
    return {
        merge: "replace",
        validate() {
            throw new IncompatibleKeyError(key);
        }
    };
}

const eslintrcKeys = [
    "env",
    "extends",
    "globals",
    "ignorePatterns",
    "noInlineConfig",
    "overrides",
    "parser",
    "parserOptions",
    "reportUnusedDisableDirectives",
    "root"
];

//-----------------------------------------------------------------------------
// Full schema
//-----------------------------------------------------------------------------

const flatConfigSchema = {

    // eslintrc-style keys that should always error
    ...Object.fromEntries(eslintrcKeys.map(key => [key, createEslintrcErrorSchema(key)])),

    // flat config keys
    settings: deepObjectAssignSchema,
    linterOptions: {
        schema: {
            noInlineConfig: booleanSchema,
            reportUnusedDisableDirectives: disableDirectiveSeveritySchema
        }
    },
    languageOptions: {
        schema: {
            ecmaVersion: ecmaVersionSchema,
            sourceType: sourceTypeSchema,
            globals: globalsSchema,
            parser: parserSchema,
            parserOptions: deepObjectAssignSchema
        }
    },
    processor: processorSchema,
    plugins: pluginsSchema,
    rules: rulesSchema
};

//-----------------------------------------------------------------------------
// Exports
//-----------------------------------------------------------------------------

module.exports = {
    flatConfigSchema,
    assertIsRuleSeverity,
    assertIsRuleOptions
};
