/**
 * @fileoverview Mocha/Jest test wrapper
 * @author Ilya Volodin
 */
"use strict";

/* globals describe, it -- Mocha globals */

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

const
    assert = require("assert"),
    util = require("util"),
    path = require("path"),
    equal = require("fast-deep-equal"),
    Traverser = require("../shared/traverser"),
    { getRuleOptionsSchema } = require("../config/flat-config-helpers"),
    { Linter, SourceCodeFixer, interpolate } = require("../linter"),
    CodePath = require("../linter/code-path-analysis/code-path");

const { FlatConfigArray } = require("../config/flat-config-array");
const { defaultConfig } = require("../config/default-config");

const ajv = require("../shared/ajv")({ strictDefaults: true });

const parserSymbol = Symbol.for("eslint.RuleTester.parser");
const { SourceCode } = require("../source-code");
const { ConfigArraySymbol } = require("@humanwhocodes/config-array");

//------------------------------------------------------------------------------
// Typedefs
//------------------------------------------------------------------------------

/** @typedef {import("../shared/types").Parser} Parser */
/** @typedef {import("../shared/types").LanguageOptions} LanguageOptions */
/** @typedef {import("../shared/types").Rule} Rule */


/**
 * A test case that is expected to pass lint.
 * @typedef {Object} ValidTestCase
 * @property {string} [name] Name for the test case.
 * @property {string} code Code for the test case.
 * @property {any[]} [options] Options for the test case.
 * @property {LanguageOptions} [languageOptions] The language options to use in the test case.
 * @property {{ [name: string]: any }} [settings] Settings for the test case.
 * @property {string} [filename] The fake filename for the test case. Useful for rules that make assertion about filenames.
 * @property {boolean} [only] Run only this test case or the subset of test cases with this property.
 */

/**
 * A test case that is expected to fail lint.
 * @typedef {Object} InvalidTestCase
 * @property {string} [name] Name for the test case.
 * @property {string} code Code for the test case.
 * @property {number | Array<TestCaseError | string | RegExp>} errors Expected errors.
 * @property {string | null} [output] The expected code after autofixes are applied. If set to `null`, the test runner will assert that no autofix is suggested.
 * @property {any[]} [options] Options for the test case.
 * @property {{ [name: string]: any }} [settings] Settings for the test case.
 * @property {string} [filename] The fake filename for the test case. Useful for rules that make assertion about filenames.
 * @property {LanguageOptions} [languageOptions] The language options to use in the test case.
 * @property {boolean} [only] Run only this test case or the subset of test cases with this property.
 */

/**
 * A description of a reported error used in a rule tester test.
 * @typedef {Object} TestCaseError
 * @property {string | RegExp} [message] Message.
 * @property {string} [messageId] Message ID.
 * @property {string} [type] The type of the reported AST node.
 * @property {{ [name: string]: string }} [data] The data used to fill the message template.
 * @property {number} [line] The 1-based line number of the reported start location.
 * @property {number} [column] The 1-based column number of the reported start location.
 * @property {number} [endLine] The 1-based line number of the reported end location.
 * @property {number} [endColumn] The 1-based column number of the reported end location.
 */

//------------------------------------------------------------------------------
// Private Members
//------------------------------------------------------------------------------

/*
 * testerDefaultConfig must not be modified as it allows to reset the tester to
 * the initial default configuration
 */
const testerDefaultConfig = { rules: {} };

/*
 * RuleTester uses this config as its default. This can be overwritten via
 * setDefaultConfig().
 */
let sharedDefaultConfig = { rules: {} };

/*
 * List every parameters possible on a test case that are not related to eslint
 * configuration
 */
const RuleTesterParameters = [
    "name",
    "code",
    "filename",
    "options",
    "errors",
    "output",
    "only"
];

/*
 * All allowed property names in error objects.
 */
const errorObjectParameters = new Set([
    "message",
    "messageId",
    "data",
    "type",
    "line",
    "column",
    "endLine",
    "endColumn",
    "suggestions"
]);
const friendlyErrorObjectParameterList = `[${[...errorObjectParameters].map(key => `'${key}'`).join(", ")}]`;

/*
 * All allowed property names in suggestion objects.
 */
const suggestionObjectParameters = new Set([
    "desc",
    "messageId",
    "data",
    "output"
]);
const friendlySuggestionObjectParameterList = `[${[...suggestionObjectParameters].map(key => `'${key}'`).join(", ")}]`;

const forbiddenMethods = [
    "applyInlineConfig",
    "applyLanguageOptions",
    "finalize"
];

/** @type {Map<string,WeakSet>} */
const forbiddenMethodCalls = new Map(forbiddenMethods.map(methodName => ([methodName, new WeakSet()])));

const hasOwnProperty = Function.call.bind(Object.hasOwnProperty);

/**
 * Clones a given value deeply.
 * Note: This ignores `parent` property.
 * @param {any} x A value to clone.
 * @returns {any} A cloned value.
 */
function cloneDeeplyExcludesParent(x) {
    if (typeof x === "object" && x !== null) {
        if (Array.isArray(x)) {
            return x.map(cloneDeeplyExcludesParent);
        }

        const retv = {};

        for (const key in x) {
            if (key !== "parent" && hasOwnProperty(x, key)) {
                retv[key] = cloneDeeplyExcludesParent(x[key]);
            }
        }

        return retv;
    }

    return x;
}

/**
 * Freezes a given value deeply.
 * @param {any} x A value to freeze.
 * @returns {void}
 */
function freezeDeeply(x) {
    if (typeof x === "object" && x !== null) {
        if (Array.isArray(x)) {
            x.forEach(freezeDeeply);
        } else {
            for (const key in x) {
                if (key !== "parent" && hasOwnProperty(x, key)) {
                    freezeDeeply(x[key]);
                }
            }
        }
        Object.freeze(x);
    }
}

/**
 * Replace control characters by `\u00xx` form.
 * @param {string} text The text to sanitize.
 * @returns {string} The sanitized text.
 */
function sanitize(text) {
    if (typeof text !== "string") {
        return "";
    }
    return text.replace(
        /[\u0000-\u0009\u000b-\u001a]/gu, // eslint-disable-line no-control-regex -- Escaping controls
        c => `\\u${c.codePointAt(0).toString(16).padStart(4, "0")}`
    );
}

/**
 * Define `start`/`end` properties as throwing error.
 * @param {string} objName Object name used for error messages.
 * @param {ASTNode} node The node to define.
 * @returns {void}
 */
function defineStartEndAsError(objName, node) {
    Object.defineProperties(node, {
        start: {
            get() {
                throw new Error(`Use ${objName}.range[0] instead of ${objName}.start`);
            },
            configurable: true,
            enumerable: false
        },
        end: {
            get() {
                throw new Error(`Use ${objName}.range[1] instead of ${objName}.end`);
            },
            configurable: true,
            enumerable: false
        }
    });
}


/**
 * Define `start`/`end` properties of all nodes of the given AST as throwing error.
 * @param {ASTNode} ast The root node to errorize `start`/`end` properties.
 * @param {Object} [visitorKeys] Visitor keys to be used for traversing the given ast.
 * @returns {void}
 */
function defineStartEndAsErrorInTree(ast, visitorKeys) {
    Traverser.traverse(ast, { visitorKeys, enter: defineStartEndAsError.bind(null, "node") });
    ast.tokens.forEach(defineStartEndAsError.bind(null, "token"));
    ast.comments.forEach(defineStartEndAsError.bind(null, "token"));
}

/**
 * Wraps the given parser in order to intercept and modify return values from the `parse` and `parseForESLint` methods, for test purposes.
 * In particular, to modify ast nodes, tokens and comments to throw on access to their `start` and `end` properties.
 * @param {Parser} parser Parser object.
 * @returns {Parser} Wrapped parser object.
 */
function wrapParser(parser) {

    if (typeof parser.parseForESLint === "function") {
        return {
            [parserSymbol]: parser,
            parseForESLint(...args) {
                const ret = parser.parseForESLint(...args);

                defineStartEndAsErrorInTree(ret.ast, ret.visitorKeys);
                return ret;
            }
        };
    }

    return {
        [parserSymbol]: parser,
        parse(...args) {
            const ast = parser.parse(...args);

            defineStartEndAsErrorInTree(ast);
            return ast;
        }
    };
}

/**
 * Function to replace `SourceCode.prototype.getComments`.
 * @returns {void}
 * @throws {Error} Deprecation message.
 */
function getCommentsDeprecation() {
    throw new Error(
        "`SourceCode#getComments()` is deprecated and will be removed in a future major version. Use `getCommentsBefore()`, `getCommentsAfter()`, and `getCommentsInside()` instead."
    );
}

/**
 * Emit a deprecation warning if rule uses CodePath#currentSegments.
 * @param {string} ruleName Name of the rule.
 * @returns {void}
 */
function emitCodePathCurrentSegmentsWarning(ruleName) {
    if (!emitCodePathCurrentSegmentsWarning[`warned-${ruleName}`]) {
        emitCodePathCurrentSegmentsWarning[`warned-${ruleName}`] = true;
        process.emitWarning(
            `"${ruleName}" rule uses CodePath#currentSegments and will stop working in ESLint v9. Please read the documentation for how to update your code: https://eslint.org/docs/latest/extend/code-path-analysis#usage-examples`,
            "DeprecationWarning"
        );
    }
}

/**
 * Function to replace forbidden `SourceCode` methods. Allows just one call per method.
 * @param {string} methodName The name of the method to forbid.
 * @param {Function} prototype The prototype with the original method to call.
 * @returns {Function} The function that throws the error.
 */
function throwForbiddenMethodError(methodName, prototype) {

    const original = prototype[methodName];

    return function(...args) {

        const called = forbiddenMethodCalls.get(methodName);

        /* eslint-disable no-invalid-this -- needed to operate as a method. */
        if (!called.has(this)) {
            called.add(this);

            return original.apply(this, args);
        }
        /* eslint-enable no-invalid-this -- not needed past this point */

        throw new Error(
            `\`SourceCode#${methodName}()\` cannot be called inside a rule.`
        );
    };
}

//------------------------------------------------------------------------------
// Public Interface
//------------------------------------------------------------------------------

// default separators for testing
const DESCRIBE = Symbol("describe");
const IT = Symbol("it");
const IT_ONLY = Symbol("itOnly");

/**
 * This is `it` default handler if `it` don't exist.
 * @this {Mocha}
 * @param {string} text The description of the test case.
 * @param {Function} method The logic of the test case.
 * @throws {Error} Any error upon execution of `method`.
 * @returns {any} Returned value of `method`.
 */
function itDefaultHandler(text, method) {
    try {
        return method.call(this);
    } catch (err) {
        if (err instanceof assert.AssertionError) {
            err.message += ` (${util.inspect(err.actual)} ${err.operator} ${util.inspect(err.expected)})`;
        }
        throw err;
    }
}

/**
 * This is `describe` default handler if `describe` don't exist.
 * @this {Mocha}
 * @param {string} text The description of the test case.
 * @param {Function} method The logic of the test case.
 * @returns {any} Returned value of `method`.
 */
function describeDefaultHandler(text, method) {
    return method.call(this);
}

/**
 * Mocha test wrapper.
 */
class FlatRuleTester {

    /**
     * Creates a new instance of RuleTester.
     * @param {Object} [testerConfig] Optional, extra configuration for the tester
     */
    constructor(testerConfig = {}) {

        /**
         * The configuration to use for this tester. Combination of the tester
         * configuration and the default configuration.
         * @type {Object}
         */
        this.testerConfig = [
            sharedDefaultConfig,
            testerConfig,
            { rules: { "rule-tester/validate-ast": "error" } }
        ];

        this.linter = new Linter({ configType: "flat" });
    }

    /**
     * Set the configuration to use for all future tests
     * @param {Object} config the configuration to use.
     * @throws {TypeError} If non-object config.
     * @returns {void}
     */
    static setDefaultConfig(config) {
        if (typeof config !== "object" || config === null) {
            throw new TypeError("FlatRuleTester.setDefaultConfig: config must be an object");
        }
        sharedDefaultConfig = config;

        // Make sure the rules object exists since it is assumed to exist later
        sharedDefaultConfig.rules = sharedDefaultConfig.rules || {};
    }

    /**
     * Get the current configuration used for all tests
     * @returns {Object} the current configuration
     */
    static getDefaultConfig() {
        return sharedDefaultConfig;
    }

    /**
     * Reset the configuration to the initial configuration of the tester removing
     * any changes made until now.
     * @returns {void}
     */
    static resetDefaultConfig() {
        sharedDefaultConfig = {
            rules: {
                ...testerDefaultConfig.rules
            }
        };
    }


    /*
     * If people use `mocha test.js --watch` command, `describe` and `it` function
     * instances are different for each execution. So `describe` and `it` should get fresh instance
     * always.
     */
    static get describe() {
        return (
            this[DESCRIBE] ||
            (typeof describe === "function" ? describe : describeDefaultHandler)
        );
    }

    static set describe(value) {
        this[DESCRIBE] = value;
    }

    static get it() {
        return (
            this[IT] ||
            (typeof it === "function" ? it : itDefaultHandler)
        );
    }

    static set it(value) {
        this[IT] = value;
    }

    /**
     * Adds the `only` property to a test to run it in isolation.
     * @param {string | ValidTestCase | InvalidTestCase} item A single test to run by itself.
     * @returns {ValidTestCase | InvalidTestCase} The test with `only` set.
     */
    static only(item) {
        if (typeof item === "string") {
            return { code: item, only: true };
        }

        return { ...item, only: true };
    }

    static get itOnly() {
        if (typeof this[IT_ONLY] === "function") {
            return this[IT_ONLY];
        }
        if (typeof this[IT] === "function" && typeof this[IT].only === "function") {
            return Function.bind.call(this[IT].only, this[IT]);
        }
        if (typeof it === "function" && typeof it.only === "function") {
            return Function.bind.call(it.only, it);
        }

        if (typeof this[DESCRIBE] === "function" || typeof this[IT] === "function") {
            throw new Error(
                "Set `RuleTester.itOnly` to use `only` with a custom test framework.\n" +
                "See https://eslint.org/docs/latest/integrate/nodejs-api#customizing-ruletester for more."
            );
        }
        if (typeof it === "function") {
            throw new Error("The current test framework does not support exclusive tests with `only`.");
        }
        throw new Error("To use `only`, use RuleTester with a test framework that provides `it.only()` like Mocha.");
    }

    static set itOnly(value) {
        this[IT_ONLY] = value;
    }


    /**
     * Adds a new rule test to execute.
     * @param {string} ruleName The name of the rule to run.
     * @param {Function | Rule} rule The rule to test.
     * @param {{
     *   valid: (ValidTestCase | string)[],
     *   invalid: InvalidTestCase[]
     * }} test The collection of tests to run.
     * @throws {TypeError|Error} If non-object `test`, or if a required
     * scenario of the given type is missing.
     * @returns {void}
     */
    run(ruleName, rule, test) {

        const testerConfig = this.testerConfig,
            requiredScenarios = ["valid", "invalid"],
            scenarioErrors = [],
            linter = this.linter,
            ruleId = `rule-to-test/${ruleName}`;

        if (!test || typeof test !== "object") {
            throw new TypeError(`Test Scenarios for rule ${ruleName} : Could not find test scenario object`);
        }

        requiredScenarios.forEach(scenarioType => {
            if (!test[scenarioType]) {
                scenarioErrors.push(`Could not find any ${scenarioType} test scenarios`);
            }
        });

        if (scenarioErrors.length > 0) {
            throw new Error([
                `Test Scenarios for rule ${ruleName} is invalid:`
            ].concat(scenarioErrors).join("\n"));
        }

        const baseConfig = [
            { files: ["**"] }, // Make sure the default config matches for all files
            {
                plugins: {

                    // copy root plugin over
                    "@": {

                        /*
                         * Parsers are wrapped to detect more errors, so this needs
                         * to be a new object for each call to run(), otherwise the
                         * parsers will be wrapped multiple times.
                         */
                        parsers: {
                            ...defaultConfig[0].plugins["@"].parsers
                        },

                        /*
                         * The rules key on the default plugin is a proxy to lazy-load
                         * just the rules that are needed. So, don't create a new object
                         * here, just use the default one to keep that performance
                         * enhancement.
                         */
                        rules: defaultConfig[0].plugins["@"].rules
                    },
                    "rule-to-test": {
                        rules: {
                            [ruleName]: Object.assign({}, rule, {

                                // Create a wrapper rule that freezes the `context` properties.
                                create(context) {
                                    freezeDeeply(context.options);
                                    freezeDeeply(context.settings);
                                    freezeDeeply(context.parserOptions);

                                    // freezeDeeply(context.languageOptions);

                                    return (typeof rule === "function" ? rule : rule.create)(context);
                                }
                            })
                        }
                    }
                },
                languageOptions: {
                    ...defaultConfig[0].languageOptions
                }
            },
            ...defaultConfig.slice(1)
        ];

        /**
         * Run the rule for the given item
         * @param {string|Object} item Item to run the rule against
         * @throws {Error} If an invalid schema.
         * @returns {Object} Eslint run result
         * @private
         */
        function runRuleForItem(item) {
            const flatConfigArrayOptions = {
                baseConfig
            };

            if (item.filename) {
                flatConfigArrayOptions.basePath = path.parse(item.filename).root;
            }

            const configs = new FlatConfigArray(testerConfig, flatConfigArrayOptions);

            /*
             * Modify the returned config so that the parser is wrapped to catch
             * access of the start/end properties. This method is called just
             * once per code snippet being tested, so each test case gets a clean
             * parser.
             */
            configs[ConfigArraySymbol.finalizeConfig] = function(...args) {

                // can't do super here :(
                const proto = Object.getPrototypeOf(this);
                const calculatedConfig = proto[ConfigArraySymbol.finalizeConfig].apply(this, args);

                // wrap the parser to catch start/end property access
                calculatedConfig.languageOptions.parser = wrapParser(calculatedConfig.languageOptions.parser);
                return calculatedConfig;
            };

            let code, filename, output, beforeAST, afterAST;

            if (typeof item === "string") {
                code = item;
            } else {
                code = item.code;

                /*
                 * Assumes everything on the item is a config except for the
                 * parameters used by this tester
                 */
                const itemConfig = { ...item };

                for (const parameter of RuleTesterParameters) {
                    delete itemConfig[parameter];
                }

                // wrap any parsers
                if (itemConfig.languageOptions && itemConfig.languageOptions.parser) {

                    const parser = itemConfig.languageOptions.parser;

                    if (parser && typeof parser !== "object") {
                        throw new Error("Parser must be an object with a parse() or parseForESLint() method.");
                    }

                }

                /*
                 * Create the config object from the tester config and this item
                 * specific configurations.
                 */
                configs.push(itemConfig);
            }

            if (item.filename) {
                filename = item.filename;
            }

            let ruleConfig = 1;

            if (hasOwnProperty(item, "options")) {
                assert(Array.isArray(item.options), "options must be an array");
                ruleConfig = [1, ...item.options];
            }

            configs.push({
                rules: {
                    [ruleId]: ruleConfig
                }
            });

            const schema = getRuleOptionsSchema(rule);

            /*
             * Setup AST getters.
             * The goal is to check whether or not AST was modified when
             * running the rule under test.
             */
            configs.push({
                plugins: {
                    "rule-tester": {
                        rules: {
                            "validate-ast": {
                                create() {
                                    return {
                                        Program(node) {
                                            beforeAST = cloneDeeplyExcludesParent(node);
                                        },
                                        "Program:exit"(node) {
                                            afterAST = node;
                                        }
                                    };
                                }
                            }
                        }
                    }
                }
            });

            if (schema) {
                ajv.validateSchema(schema);

                if (ajv.errors) {
                    const errors = ajv.errors.map(error => {
                        const field = error.dataPath[0] === "." ? error.dataPath.slice(1) : error.dataPath;

                        return `\t${field}: ${error.message}`;
                    }).join("\n");

                    throw new Error([`Schema for rule ${ruleName} is invalid:`, errors]);
                }

                /*
                 * `ajv.validateSchema` checks for errors in the structure of the schema (by comparing the schema against a "meta-schema"),
                 * and it reports those errors individually. However, there are other types of schema errors that only occur when compiling
                 * the schema (e.g. using invalid defaults in a schema), and only one of these errors can be reported at a time. As a result,
                 * the schema is compiled here separately from checking for `validateSchema` errors.
                 */
                try {
                    ajv.compile(schema);
                } catch (err) {
                    throw new Error(`Schema for rule ${ruleName} is invalid: ${err.message}`);
                }
            }

            // check for validation errors
            try {
                configs.normalizeSync();
                configs.getConfig("test.js");
            } catch (error) {
                error.message = `ESLint configuration in rule-tester is invalid: ${error.message}`;
                throw error;
            }

            // Verify the code.
            const { getComments, applyLanguageOptions, applyInlineConfig, finalize } = SourceCode.prototype;
            const originalCurrentSegments = Object.getOwnPropertyDescriptor(CodePath.prototype, "currentSegments");
            let messages;

            try {
                SourceCode.prototype.getComments = getCommentsDeprecation;
                Object.defineProperty(CodePath.prototype, "currentSegments", {
                    get() {
                        emitCodePathCurrentSegmentsWarning(ruleName);
                        return originalCurrentSegments.get.call(this);
                    }
                });

                forbiddenMethods.forEach(methodName => {
                    SourceCode.prototype[methodName] = throwForbiddenMethodError(methodName, SourceCode.prototype);
                });

                messages = linter.verify(code, configs, filename);
            } finally {
                SourceCode.prototype.getComments = getComments;
                Object.defineProperty(CodePath.prototype, "currentSegments", originalCurrentSegments);
                SourceCode.prototype.applyInlineConfig = applyInlineConfig;
                SourceCode.prototype.applyLanguageOptions = applyLanguageOptions;
                SourceCode.prototype.finalize = finalize;
            }


            const fatalErrorMessage = messages.find(m => m.fatal);

            assert(!fatalErrorMessage, `A fatal parsing error occurred: ${fatalErrorMessage && fatalErrorMessage.message}`);

            // Verify if autofix makes a syntax error or not.
            if (messages.some(m => m.fix)) {
                output = SourceCodeFixer.applyFixes(code, messages).output;
                const errorMessageInFix = linter.verify(output, configs, filename).find(m => m.fatal);

                assert(!errorMessageInFix, [
                    "A fatal parsing error occurred in autofix.",
                    `Error: ${errorMessageInFix && errorMessageInFix.message}`,
                    "Autofix output:",
                    output
                ].join("\n"));
            } else {
                output = code;
            }

            return {
                messages,
                output,
                beforeAST,
                afterAST: cloneDeeplyExcludesParent(afterAST)
            };
        }

        /**
         * Check if the AST was changed
         * @param {ASTNode} beforeAST AST node before running
         * @param {ASTNode} afterAST AST node after running
         * @returns {void}
         * @private
         */
        function assertASTDidntChange(beforeAST, afterAST) {
            if (!equal(beforeAST, afterAST)) {
                assert.fail("Rule should not modify AST.");
            }
        }

        /**
         * Check if the template is valid or not
         * all valid cases go through this
         * @param {string|Object} item Item to run the rule against
         * @returns {void}
         * @private
         */
        function testValidTemplate(item) {
            const code = typeof item === "object" ? item.code : item;

            assert.ok(typeof code === "string", "Test case must specify a string value for 'code'");
            if (item.name) {
                assert.ok(typeof item.name === "string", "Optional test case property 'name' must be a string");
            }

            const result = runRuleForItem(item);
            const messages = result.messages;

            assert.strictEqual(messages.length, 0, util.format("Should have no errors but had %d: %s",
                messages.length,
                util.inspect(messages)));

            assertASTDidntChange(result.beforeAST, result.afterAST);
        }

        /**
         * Asserts that the message matches its expected value. If the expected
         * value is a regular expression, it is checked against the actual
         * value.
         * @param {string} actual Actual value
         * @param {string|RegExp} expected Expected value
         * @returns {void}
         * @private
         */
        function assertMessageMatches(actual, expected) {
            if (expected instanceof RegExp) {

                // assert.js doesn't have a built-in RegExp match function
                assert.ok(
                    expected.test(actual),
                    `Expected '${actual}' to match ${expected}`
                );
            } else {
                assert.strictEqual(actual, expected);
            }
        }

        /**
         * Check if the template is invalid or not
         * all invalid cases go through this.
         * @param {string|Object} item Item to run the rule against
         * @returns {void}
         * @private
         */
        function testInvalidTemplate(item) {
            assert.ok(typeof item.code === "string", "Test case must specify a string value for 'code'");
            if (item.name) {
                assert.ok(typeof item.name === "string", "Optional test case property 'name' must be a string");
            }
            assert.ok(item.errors || item.errors === 0,
                `Did not specify errors for an invalid test of ${ruleName}`);

            if (Array.isArray(item.errors) && item.errors.length === 0) {
                assert.fail("Invalid cases must have at least one error");
            }

            const ruleHasMetaMessages = hasOwnProperty(rule, "meta") && hasOwnProperty(rule.meta, "messages");
            const friendlyIDList = ruleHasMetaMessages ? `[${Object.keys(rule.meta.messages).map(key => `'${key}'`).join(", ")}]` : null;

            const result = runRuleForItem(item);
            const messages = result.messages;

            if (typeof item.errors === "number") {

                if (item.errors === 0) {
                    assert.fail("Invalid cases must have 'error' value greater than 0");
                }

                assert.strictEqual(messages.length, item.errors, util.format("Should have %d error%s but had %d: %s",
                    item.errors,
                    item.errors === 1 ? "" : "s",
                    messages.length,
                    util.inspect(messages)));
            } else {
                assert.strictEqual(
                    messages.length, item.errors.length, util.format(
                        "Should have %d error%s but had %d: %s",
                        item.errors.length,
                        item.errors.length === 1 ? "" : "s",
                        messages.length,
                        util.inspect(messages)
                    )
                );

                const hasMessageOfThisRule = messages.some(m => m.ruleId === ruleId);

                for (let i = 0, l = item.errors.length; i < l; i++) {
                    const error = item.errors[i];
                    const message = messages[i];

                    assert(hasMessageOfThisRule, "Error rule name should be the same as the name of the rule being tested");

                    if (typeof error === "string" || error instanceof RegExp) {

                        // Just an error message.
                        assertMessageMatches(message.message, error);
                    } else if (typeof error === "object" && error !== null) {

                        /*
                         * Error object.
                         * This may have a message, messageId, data, node type, line, and/or
                         * column.
                         */

                        Object.keys(error).forEach(propertyName => {
                            assert.ok(
                                errorObjectParameters.has(propertyName),
                                `Invalid error property name '${propertyName}'. Expected one of ${friendlyErrorObjectParameterList}.`
                            );
                        });

                        if (hasOwnProperty(error, "message")) {
                            assert.ok(!hasOwnProperty(error, "messageId"), "Error should not specify both 'message' and a 'messageId'.");
                            assert.ok(!hasOwnProperty(error, "data"), "Error should not specify both 'data' and 'message'.");
                            assertMessageMatches(message.message, error.message);
                        } else if (hasOwnProperty(error, "messageId")) {
                            assert.ok(
                                ruleHasMetaMessages,
                                "Error can not use 'messageId' if rule under test doesn't define 'meta.messages'."
                            );
                            if (!hasOwnProperty(rule.meta.messages, error.messageId)) {
                                assert(false, `Invalid messageId '${error.messageId}'. Expected one of ${friendlyIDList}.`);
                            }
                            assert.strictEqual(
                                message.messageId,
                                error.messageId,
                                `messageId '${message.messageId}' does not match expected messageId '${error.messageId}'.`
                            );
                            if (hasOwnProperty(error, "data")) {

                                /*
                                 *  if data was provided, then directly compare the returned message to a synthetic
                                 *  interpolated message using the same message ID and data provided in the test.
                                 *  See https://github.com/eslint/eslint/issues/9890 for context.
                                 */
                                const unformattedOriginalMessage = rule.meta.messages[error.messageId];
                                const rehydratedMessage = interpolate(unformattedOriginalMessage, error.data);

                                assert.strictEqual(
                                    message.message,
                                    rehydratedMessage,
                                    `Hydrated message "${rehydratedMessage}" does not match "${message.message}"`
                                );
                            }
                        }

                        assert.ok(
                            hasOwnProperty(error, "data") ? hasOwnProperty(error, "messageId") : true,
                            "Error must specify 'messageId' if 'data' is used."
                        );

                        if (error.type) {
                            assert.strictEqual(message.nodeType, error.type, `Error type should be ${error.type}, found ${message.nodeType}`);
                        }

                        if (hasOwnProperty(error, "line")) {
                            assert.strictEqual(message.line, error.line, `Error line should be ${error.line}`);
                        }

                        if (hasOwnProperty(error, "column")) {
                            assert.strictEqual(message.column, error.column, `Error column should be ${error.column}`);
                        }

                        if (hasOwnProperty(error, "endLine")) {
                            assert.strictEqual(message.endLine, error.endLine, `Error endLine should be ${error.endLine}`);
                        }

                        if (hasOwnProperty(error, "endColumn")) {
                            assert.strictEqual(message.endColumn, error.endColumn, `Error endColumn should be ${error.endColumn}`);
                        }

                        if (hasOwnProperty(error, "suggestions")) {

                            // Support asserting there are no suggestions
                            if (!error.suggestions || (Array.isArray(error.suggestions) && error.suggestions.length === 0)) {
                                if (Array.isArray(message.suggestions) && message.suggestions.length > 0) {
                                    assert.fail(`Error should have no suggestions on error with message: "${message.message}"`);
                                }
                            } else {
                                assert.strictEqual(Array.isArray(message.suggestions), true, `Error should have an array of suggestions. Instead received "${message.suggestions}" on error with message: "${message.message}"`);
                                assert.strictEqual(message.suggestions.length, error.suggestions.length, `Error should have ${error.suggestions.length} suggestions. Instead found ${message.suggestions.length} suggestions`);

                                error.suggestions.forEach((expectedSuggestion, index) => {
                                    assert.ok(
                                        typeof expectedSuggestion === "object" && expectedSuggestion !== null,
                                        "Test suggestion in 'suggestions' array must be an object."
                                    );
                                    Object.keys(expectedSuggestion).forEach(propertyName => {
                                        assert.ok(
                                            suggestionObjectParameters.has(propertyName),
                                            `Invalid suggestion property name '${propertyName}'. Expected one of ${friendlySuggestionObjectParameterList}.`
                                        );
                                    });

                                    const actualSuggestion = message.suggestions[index];
                                    const suggestionPrefix = `Error Suggestion at index ${index} :`;

                                    if (hasOwnProperty(expectedSuggestion, "desc")) {
                                        assert.ok(
                                            !hasOwnProperty(expectedSuggestion, "data"),
                                            `${suggestionPrefix} Test should not specify both 'desc' and 'data'.`
                                        );
                                        assert.strictEqual(
                                            actualSuggestion.desc,
                                            expectedSuggestion.desc,
                                            `${suggestionPrefix} desc should be "${expectedSuggestion.desc}" but got "${actualSuggestion.desc}" instead.`
                                        );
                                    }

                                    if (hasOwnProperty(expectedSuggestion, "messageId")) {
                                        assert.ok(
                                            ruleHasMetaMessages,
                                            `${suggestionPrefix} Test can not use 'messageId' if rule under test doesn't define 'meta.messages'.`
                                        );
                                        assert.ok(
                                            hasOwnProperty(rule.meta.messages, expectedSuggestion.messageId),
                                            `${suggestionPrefix} Test has invalid messageId '${expectedSuggestion.messageId}', the rule under test allows only one of ${friendlyIDList}.`
                                        );
                                        assert.strictEqual(
                                            actualSuggestion.messageId,
                                            expectedSuggestion.messageId,
                                            `${suggestionPrefix} messageId should be '${expectedSuggestion.messageId}' but got '${actualSuggestion.messageId}' instead.`
                                        );
                                        if (hasOwnProperty(expectedSuggestion, "data")) {
                                            const unformattedMetaMessage = rule.meta.messages[expectedSuggestion.messageId];
                                            const rehydratedDesc = interpolate(unformattedMetaMessage, expectedSuggestion.data);

                                            assert.strictEqual(
                                                actualSuggestion.desc,
                                                rehydratedDesc,
                                                `${suggestionPrefix} Hydrated test desc "${rehydratedDesc}" does not match received desc "${actualSuggestion.desc}".`
                                            );
                                        }
                                    } else {
                                        assert.ok(
                                            !hasOwnProperty(expectedSuggestion, "data"),
                                            `${suggestionPrefix} Test must specify 'messageId' if 'data' is used.`
                                        );
                                    }

                                    if (hasOwnProperty(expectedSuggestion, "output")) {
                                        const codeWithAppliedSuggestion = SourceCodeFixer.applyFixes(item.code, [actualSuggestion]).output;

                                        assert.strictEqual(codeWithAppliedSuggestion, expectedSuggestion.output, `Expected the applied suggestion fix to match the test suggestion output for suggestion at index: ${index} on error with message: "${message.message}"`);
                                    }
                                });
                            }
                        }
                    } else {

                        // Message was an unexpected type
                        assert.fail(`Error should be a string, object, or RegExp, but found (${util.inspect(message)})`);
                    }
                }
            }

            if (hasOwnProperty(item, "output")) {
                if (item.output === null) {
                    assert.strictEqual(
                        result.output,
                        item.code,
                        "Expected no autofixes to be suggested"
                    );
                } else {
                    assert.strictEqual(result.output, item.output, "Output is incorrect.");
                }
            } else {
                assert.strictEqual(
                    result.output,
                    item.code,
                    "The rule fixed the code. Please add 'output' property."
                );
            }

            assertASTDidntChange(result.beforeAST, result.afterAST);
        }

        /*
         * This creates a mocha test suite and pipes all supplied info through
         * one of the templates above.
         * The test suites for valid/invalid are created conditionally as
         * test runners (eg. vitest) fail for empty test suites.
         */
        this.constructor.describe(ruleName, () => {
            if (test.valid.length > 0) {
                this.constructor.describe("valid", () => {
                    test.valid.forEach(valid => {
                        this.constructor[valid.only ? "itOnly" : "it"](
                            sanitize(typeof valid === "object" ? valid.name || valid.code : valid),
                            () => {
                                testValidTemplate(valid);
                            }
                        );
                    });
                });
            }

            if (test.invalid.length > 0) {
                this.constructor.describe("invalid", () => {
                    test.invalid.forEach(invalid => {
                        this.constructor[invalid.only ? "itOnly" : "it"](
                            sanitize(invalid.name || invalid.code),
                            () => {
                                testInvalidTemplate(invalid);
                            }
                        );
                    });
                });
            }
        });
    }
}

FlatRuleTester[DESCRIBE] = FlatRuleTester[IT] = FlatRuleTester[IT_ONLY] = null;

module.exports = FlatRuleTester;
