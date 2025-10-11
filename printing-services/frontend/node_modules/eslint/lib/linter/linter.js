/**
 * @fileoverview Main Linter Class
 * @author Gyandeep Singh
 * @author aladdin-add
 */

"use strict";

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

const
    path = require("path"),
    eslintScope = require("eslint-scope"),
    evk = require("eslint-visitor-keys"),
    espree = require("espree"),
    merge = require("lodash.merge"),
    pkg = require("../../package.json"),
    astUtils = require("../shared/ast-utils"),
    {
        directivesPattern
    } = require("../shared/directives"),
    {
        Legacy: {
            ConfigOps,
            ConfigValidator,
            environments: BuiltInEnvironments
        }
    } = require("@eslint/eslintrc/universal"),
    Traverser = require("../shared/traverser"),
    { SourceCode } = require("../source-code"),
    CodePathAnalyzer = require("./code-path-analysis/code-path-analyzer"),
    applyDisableDirectives = require("./apply-disable-directives"),
    ConfigCommentParser = require("./config-comment-parser"),
    NodeEventGenerator = require("./node-event-generator"),
    createReportTranslator = require("./report-translator"),
    Rules = require("./rules"),
    createEmitter = require("./safe-emitter"),
    SourceCodeFixer = require("./source-code-fixer"),
    timing = require("./timing"),
    ruleReplacements = require("../../conf/replacements.json");
const { getRuleFromConfig } = require("../config/flat-config-helpers");
const { FlatConfigArray } = require("../config/flat-config-array");
const { RuleValidator } = require("../config/rule-validator");
const { assertIsRuleOptions, assertIsRuleSeverity } = require("../config/flat-config-schema");
const { normalizeSeverityToString } = require("../shared/severity");
const debug = require("debug")("eslint:linter");
const MAX_AUTOFIX_PASSES = 10;
const DEFAULT_PARSER_NAME = "espree";
const DEFAULT_ECMA_VERSION = 5;
const commentParser = new ConfigCommentParser();
const DEFAULT_ERROR_LOC = { start: { line: 1, column: 0 }, end: { line: 1, column: 1 } };
const parserSymbol = Symbol.for("eslint.RuleTester.parser");

//------------------------------------------------------------------------------
// Typedefs
//------------------------------------------------------------------------------

/** @typedef {InstanceType<import("../cli-engine/config-array").ConfigArray>} ConfigArray */
/** @typedef {InstanceType<import("../cli-engine/config-array").ExtractedConfig>} ExtractedConfig */
/** @typedef {import("../shared/types").ConfigData} ConfigData */
/** @typedef {import("../shared/types").Environment} Environment */
/** @typedef {import("../shared/types").GlobalConf} GlobalConf */
/** @typedef {import("../shared/types").LintMessage} LintMessage */
/** @typedef {import("../shared/types").SuppressedLintMessage} SuppressedLintMessage */
/** @typedef {import("../shared/types").ParserOptions} ParserOptions */
/** @typedef {import("../shared/types").LanguageOptions} LanguageOptions */
/** @typedef {import("../shared/types").Processor} Processor */
/** @typedef {import("../shared/types").Rule} Rule */

/* eslint-disable jsdoc/valid-types -- https://github.com/jsdoc-type-pratt-parser/jsdoc-type-pratt-parser/issues/4#issuecomment-778805577 */
/**
 * @template T
 * @typedef {{ [P in keyof T]-?: T[P] }} Required
 */
/* eslint-enable jsdoc/valid-types -- https://github.com/jsdoc-type-pratt-parser/jsdoc-type-pratt-parser/issues/4#issuecomment-778805577 */

/**
 * @typedef {Object} DisableDirective
 * @property {("disable"|"enable"|"disable-line"|"disable-next-line")} type Type of directive
 * @property {number} line The line number
 * @property {number} column The column number
 * @property {(string|null)} ruleId The rule ID
 * @property {string} justification The justification of directive
 */

/**
 * The private data for `Linter` instance.
 * @typedef {Object} LinterInternalSlots
 * @property {ConfigArray|null} lastConfigArray The `ConfigArray` instance that the last `verify()` call used.
 * @property {SourceCode|null} lastSourceCode The `SourceCode` instance that the last `verify()` call used.
 * @property {SuppressedLintMessage[]} lastSuppressedMessages The `SuppressedLintMessage[]` instance that the last `verify()` call produced.
 * @property {Map<string, Parser>} parserMap The loaded parsers.
 * @property {Rules} ruleMap The loaded rules.
 */

/**
 * @typedef {Object} VerifyOptions
 * @property {boolean} [allowInlineConfig] Allow/disallow inline comments' ability
 *      to change config once it is set. Defaults to true if not supplied.
 *      Useful if you want to validate JS without comments overriding rules.
 * @property {boolean} [disableFixes] if `true` then the linter doesn't make `fix`
 *      properties into the lint result.
 * @property {string} [filename] the filename of the source code.
 * @property {boolean | "off" | "warn" | "error"} [reportUnusedDisableDirectives] Adds reported errors for
 *      unused `eslint-disable` directives.
 */

/**
 * @typedef {Object} ProcessorOptions
 * @property {(filename:string, text:string) => boolean} [filterCodeBlock] the
 *      predicate function that selects adopt code blocks.
 * @property {Processor.postprocess} [postprocess] postprocessor for report
 *      messages. If provided, this should accept an array of the message lists
 *      for each code block returned from the preprocessor, apply a mapping to
 *      the messages as appropriate, and return a one-dimensional array of
 *      messages.
 * @property {Processor.preprocess} [preprocess] preprocessor for source text.
 *      If provided, this should accept a string of source text, and return an
 *      array of code blocks to lint.
 */

/**
 * @typedef {Object} FixOptions
 * @property {boolean | ((message: LintMessage) => boolean)} [fix] Determines
 *      whether fixes should be applied.
 */

/**
 * @typedef {Object} InternalOptions
 * @property {string | null} warnInlineConfig The config name what `noInlineConfig` setting came from. If `noInlineConfig` setting didn't exist, this is null. If this is a config name, then the linter warns directive comments.
 * @property {"off" | "warn" | "error"} reportUnusedDisableDirectives (boolean values were normalized)
 */

//------------------------------------------------------------------------------
// Helpers
//------------------------------------------------------------------------------

/**
 * Determines if a given object is Espree.
 * @param {Object} parser The parser to check.
 * @returns {boolean} True if the parser is Espree or false if not.
 */
function isEspree(parser) {
    return !!(parser === espree || parser[parserSymbol] === espree);
}

/**
 * Ensures that variables representing built-in properties of the Global Object,
 * and any globals declared by special block comments, are present in the global
 * scope.
 * @param {Scope} globalScope The global scope.
 * @param {Object} configGlobals The globals declared in configuration
 * @param {{exportedVariables: Object, enabledGlobals: Object}} commentDirectives Directives from comment configuration
 * @returns {void}
 */
function addDeclaredGlobals(globalScope, configGlobals, { exportedVariables, enabledGlobals }) {

    // Define configured global variables.
    for (const id of new Set([...Object.keys(configGlobals), ...Object.keys(enabledGlobals)])) {

        /*
         * `ConfigOps.normalizeConfigGlobal` will throw an error if a configured global value is invalid. However, these errors would
         * typically be caught when validating a config anyway (validity for inline global comments is checked separately).
         */
        const configValue = configGlobals[id] === void 0 ? void 0 : ConfigOps.normalizeConfigGlobal(configGlobals[id]);
        const commentValue = enabledGlobals[id] && enabledGlobals[id].value;
        const value = commentValue || configValue;
        const sourceComments = enabledGlobals[id] && enabledGlobals[id].comments;

        if (value === "off") {
            continue;
        }

        let variable = globalScope.set.get(id);

        if (!variable) {
            variable = new eslintScope.Variable(id, globalScope);

            globalScope.variables.push(variable);
            globalScope.set.set(id, variable);
        }

        variable.eslintImplicitGlobalSetting = configValue;
        variable.eslintExplicitGlobal = sourceComments !== void 0;
        variable.eslintExplicitGlobalComments = sourceComments;
        variable.writeable = (value === "writable");
    }

    // mark all exported variables as such
    Object.keys(exportedVariables).forEach(name => {
        const variable = globalScope.set.get(name);

        if (variable) {
            variable.eslintUsed = true;
            variable.eslintExported = true;
        }
    });

    /*
     * "through" contains all references which definitions cannot be found.
     * Since we augment the global scope using configuration, we need to update
     * references and remove the ones that were added by configuration.
     */
    globalScope.through = globalScope.through.filter(reference => {
        const name = reference.identifier.name;
        const variable = globalScope.set.get(name);

        if (variable) {

            /*
             * Links the variable and the reference.
             * And this reference is removed from `Scope#through`.
             */
            reference.resolved = variable;
            variable.references.push(reference);

            return false;
        }

        return true;
    });
}

/**
 * creates a missing-rule message.
 * @param {string} ruleId the ruleId to create
 * @returns {string} created error message
 * @private
 */
function createMissingRuleMessage(ruleId) {
    return Object.prototype.hasOwnProperty.call(ruleReplacements.rules, ruleId)
        ? `Rule '${ruleId}' was removed and replaced by: ${ruleReplacements.rules[ruleId].join(", ")}`
        : `Definition for rule '${ruleId}' was not found.`;
}

/**
 * creates a linting problem
 * @param {Object} options to create linting error
 * @param {string} [options.ruleId] the ruleId to report
 * @param {Object} [options.loc] the loc to report
 * @param {string} [options.message] the error message to report
 * @param {string} [options.severity] the error message to report
 * @returns {LintMessage} created problem, returns a missing-rule problem if only provided ruleId.
 * @private
 */
function createLintingProblem(options) {
    const {
        ruleId = null,
        loc = DEFAULT_ERROR_LOC,
        message = createMissingRuleMessage(options.ruleId),
        severity = 2
    } = options;

    return {
        ruleId,
        message,
        line: loc.start.line,
        column: loc.start.column + 1,
        endLine: loc.end.line,
        endColumn: loc.end.column + 1,
        severity,
        nodeType: null
    };
}

/**
 * Creates a collection of disable directives from a comment
 * @param {Object} options to create disable directives
 * @param {("disable"|"enable"|"disable-line"|"disable-next-line")} options.type The type of directive comment
 * @param {token} options.commentToken The Comment token
 * @param {string} options.value The value after the directive in the comment
 * comment specified no specific rules, so it applies to all rules (e.g. `eslint-disable`)
 * @param {string} options.justification The justification of the directive
 * @param {function(string): {create: Function}} options.ruleMapper A map from rule IDs to defined rules
 * @returns {Object} Directives and problems from the comment
 */
function createDisableDirectives(options) {
    const { commentToken, type, value, justification, ruleMapper } = options;
    const ruleIds = Object.keys(commentParser.parseListConfig(value));
    const directiveRules = ruleIds.length ? ruleIds : [null];
    const result = {
        directives: [], // valid disable directives
        directiveProblems: [] // problems in directives
    };

    const parentComment = { commentToken, ruleIds };

    for (const ruleId of directiveRules) {

        // push to directives, if the rule is defined(including null, e.g. /*eslint enable*/)
        if (ruleId === null || !!ruleMapper(ruleId)) {
            if (type === "disable-next-line") {
                result.directives.push({
                    parentComment,
                    type,
                    line: commentToken.loc.end.line,
                    column: commentToken.loc.end.column + 1,
                    ruleId,
                    justification
                });
            } else {
                result.directives.push({
                    parentComment,
                    type,
                    line: commentToken.loc.start.line,
                    column: commentToken.loc.start.column + 1,
                    ruleId,
                    justification
                });
            }
        } else {
            result.directiveProblems.push(createLintingProblem({ ruleId, loc: commentToken.loc }));
        }
    }
    return result;
}

/**
 * Parses comments in file to extract file-specific config of rules, globals
 * and environments and merges them with global config; also code blocks
 * where reporting is disabled or enabled and merges them with reporting config.
 * @param {SourceCode} sourceCode The SourceCode object to get comments from.
 * @param {function(string): {create: Function}} ruleMapper A map from rule IDs to defined rules
 * @param {string|null} warnInlineConfig If a string then it should warn directive comments as disabled. The string value is the config name what the setting came from.
 * @returns {{configuredRules: Object, enabledGlobals: {value:string,comment:Token}[], exportedVariables: Object, problems: LintMessage[], disableDirectives: DisableDirective[]}}
 * A collection of the directive comments that were found, along with any problems that occurred when parsing
 */
function getDirectiveComments(sourceCode, ruleMapper, warnInlineConfig) {
    const configuredRules = {};
    const enabledGlobals = Object.create(null);
    const exportedVariables = {};
    const problems = [];
    const disableDirectives = [];
    const validator = new ConfigValidator({
        builtInRules: Rules
    });

    sourceCode.getInlineConfigNodes().filter(token => token.type !== "Shebang").forEach(comment => {
        const { directivePart, justificationPart } = commentParser.extractDirectiveComment(comment.value);

        const match = directivesPattern.exec(directivePart);

        if (!match) {
            return;
        }
        const directiveText = match[1];
        const lineCommentSupported = /^eslint-disable-(next-)?line$/u.test(directiveText);

        if (comment.type === "Line" && !lineCommentSupported) {
            return;
        }

        if (warnInlineConfig) {
            const kind = comment.type === "Block" ? `/*${directiveText}*/` : `//${directiveText}`;

            problems.push(createLintingProblem({
                ruleId: null,
                message: `'${kind}' has no effect because you have 'noInlineConfig' setting in ${warnInlineConfig}.`,
                loc: comment.loc,
                severity: 1
            }));
            return;
        }

        if (directiveText === "eslint-disable-line" && comment.loc.start.line !== comment.loc.end.line) {
            const message = `${directiveText} comment should not span multiple lines.`;

            problems.push(createLintingProblem({
                ruleId: null,
                message,
                loc: comment.loc
            }));
            return;
        }

        const directiveValue = directivePart.slice(match.index + directiveText.length);

        switch (directiveText) {
            case "eslint-disable":
            case "eslint-enable":
            case "eslint-disable-next-line":
            case "eslint-disable-line": {
                const directiveType = directiveText.slice("eslint-".length);
                const options = { commentToken: comment, type: directiveType, value: directiveValue, justification: justificationPart, ruleMapper };
                const { directives, directiveProblems } = createDisableDirectives(options);

                disableDirectives.push(...directives);
                problems.push(...directiveProblems);
                break;
            }

            case "exported":
                Object.assign(exportedVariables, commentParser.parseStringConfig(directiveValue, comment));
                break;

            case "globals":
            case "global":
                for (const [id, { value }] of Object.entries(commentParser.parseStringConfig(directiveValue, comment))) {
                    let normalizedValue;

                    try {
                        normalizedValue = ConfigOps.normalizeConfigGlobal(value);
                    } catch (err) {
                        problems.push(createLintingProblem({
                            ruleId: null,
                            loc: comment.loc,
                            message: err.message
                        }));
                        continue;
                    }

                    if (enabledGlobals[id]) {
                        enabledGlobals[id].comments.push(comment);
                        enabledGlobals[id].value = normalizedValue;
                    } else {
                        enabledGlobals[id] = {
                            comments: [comment],
                            value: normalizedValue
                        };
                    }
                }
                break;

            case "eslint": {
                const parseResult = commentParser.parseJsonConfig(directiveValue, comment.loc);

                if (parseResult.success) {
                    Object.keys(parseResult.config).forEach(name => {
                        const rule = ruleMapper(name);
                        const ruleValue = parseResult.config[name];

                        if (!rule) {
                            problems.push(createLintingProblem({ ruleId: name, loc: comment.loc }));
                            return;
                        }

                        try {
                            validator.validateRuleOptions(rule, name, ruleValue);
                        } catch (err) {
                            problems.push(createLintingProblem({
                                ruleId: name,
                                message: err.message,
                                loc: comment.loc
                            }));

                            // do not apply the config, if found invalid options.
                            return;
                        }

                        configuredRules[name] = ruleValue;
                    });
                } else {
                    problems.push(parseResult.error);
                }

                break;
            }

            // no default
        }
    });

    return {
        configuredRules,
        enabledGlobals,
        exportedVariables,
        problems,
        disableDirectives
    };
}

/**
 * Parses comments in file to extract disable directives.
 * @param {SourceCode} sourceCode The SourceCode object to get comments from.
 * @param {function(string): {create: Function}} ruleMapper A map from rule IDs to defined rules
 * @returns {{problems: LintMessage[], disableDirectives: DisableDirective[]}}
 * A collection of the directive comments that were found, along with any problems that occurred when parsing
 */
function getDirectiveCommentsForFlatConfig(sourceCode, ruleMapper) {
    const problems = [];
    const disableDirectives = [];

    sourceCode.getInlineConfigNodes().filter(token => token.type !== "Shebang").forEach(comment => {
        const { directivePart, justificationPart } = commentParser.extractDirectiveComment(comment.value);

        const match = directivesPattern.exec(directivePart);

        if (!match) {
            return;
        }
        const directiveText = match[1];
        const lineCommentSupported = /^eslint-disable-(next-)?line$/u.test(directiveText);

        if (comment.type === "Line" && !lineCommentSupported) {
            return;
        }

        if (directiveText === "eslint-disable-line" && comment.loc.start.line !== comment.loc.end.line) {
            const message = `${directiveText} comment should not span multiple lines.`;

            problems.push(createLintingProblem({
                ruleId: null,
                message,
                loc: comment.loc
            }));
            return;
        }

        const directiveValue = directivePart.slice(match.index + directiveText.length);

        switch (directiveText) {
            case "eslint-disable":
            case "eslint-enable":
            case "eslint-disable-next-line":
            case "eslint-disable-line": {
                const directiveType = directiveText.slice("eslint-".length);
                const options = { commentToken: comment, type: directiveType, value: directiveValue, justification: justificationPart, ruleMapper };
                const { directives, directiveProblems } = createDisableDirectives(options);

                disableDirectives.push(...directives);
                problems.push(...directiveProblems);
                break;
            }

            // no default
        }
    });

    return {
        problems,
        disableDirectives
    };
}

/**
 * Normalize ECMAScript version from the initial config
 * @param {Parser} parser The parser which uses this options.
 * @param {number} ecmaVersion ECMAScript version from the initial config
 * @returns {number} normalized ECMAScript version
 */
function normalizeEcmaVersion(parser, ecmaVersion) {

    if (isEspree(parser)) {
        if (ecmaVersion === "latest") {
            return espree.latestEcmaVersion;
        }
    }

    /*
     * Calculate ECMAScript edition number from official year version starting with
     * ES2015, which corresponds with ES6 (or a difference of 2009).
     */
    return ecmaVersion >= 2015 ? ecmaVersion - 2009 : ecmaVersion;
}

/**
 * Normalize ECMAScript version from the initial config into languageOptions (year)
 * format.
 * @param {any} [ecmaVersion] ECMAScript version from the initial config
 * @returns {number} normalized ECMAScript version
 */
function normalizeEcmaVersionForLanguageOptions(ecmaVersion) {

    switch (ecmaVersion) {
        case 3:
            return 3;

        // void 0 = no ecmaVersion specified so use the default
        case 5:
        case void 0:
            return 5;

        default:
            if (typeof ecmaVersion === "number") {
                return ecmaVersion >= 2015 ? ecmaVersion : ecmaVersion + 2009;
            }
    }

    /*
     * We default to the latest supported ecmaVersion for everything else.
     * Remember, this is for languageOptions.ecmaVersion, which sets the version
     * that is used for a number of processes inside of ESLint. It's normally
     * safe to assume people want the latest unless otherwise specified.
     */
    return espree.latestEcmaVersion + 2009;
}

const eslintEnvPattern = /\/\*\s*eslint-env\s(.+?)(?:\*\/|$)/gsu;

/**
 * Checks whether or not there is a comment which has "eslint-env *" in a given text.
 * @param {string} text A source code text to check.
 * @returns {Object|null} A result of parseListConfig() with "eslint-env *" comment.
 */
function findEslintEnv(text) {
    let match, retv;

    eslintEnvPattern.lastIndex = 0;

    while ((match = eslintEnvPattern.exec(text)) !== null) {
        if (match[0].endsWith("*/")) {
            retv = Object.assign(
                retv || {},
                commentParser.parseListConfig(commentParser.extractDirectiveComment(match[1]).directivePart)
            );
        }
    }

    return retv;
}

/**
 * Convert "/path/to/<text>" to "<text>".
 * `CLIEngine#executeOnText()` method gives "/path/to/<text>" if the filename
 * was omitted because `configArray.extractConfig()` requires an absolute path.
 * But the linter should pass `<text>` to `RuleContext#filename` in that
 * case.
 * Also, code blocks can have their virtual filename. If the parent filename was
 * `<text>`, the virtual filename is `<text>/0_foo.js` or something like (i.e.,
 * it's not an absolute path).
 * @param {string} filename The filename to normalize.
 * @returns {string} The normalized filename.
 */
function normalizeFilename(filename) {
    const parts = filename.split(path.sep);
    const index = parts.lastIndexOf("<text>");

    return index === -1 ? filename : parts.slice(index).join(path.sep);
}

/**
 * Normalizes the possible options for `linter.verify` and `linter.verifyAndFix` to a
 * consistent shape.
 * @param {VerifyOptions} providedOptions Options
 * @param {ConfigData} config Config.
 * @returns {Required<VerifyOptions> & InternalOptions} Normalized options
 */
function normalizeVerifyOptions(providedOptions, config) {

    const linterOptions = config.linterOptions || config;

    // .noInlineConfig for eslintrc, .linterOptions.noInlineConfig for flat
    const disableInlineConfig = linterOptions.noInlineConfig === true;
    const ignoreInlineConfig = providedOptions.allowInlineConfig === false;
    const configNameOfNoInlineConfig = config.configNameOfNoInlineConfig
        ? ` (${config.configNameOfNoInlineConfig})`
        : "";

    let reportUnusedDisableDirectives = providedOptions.reportUnusedDisableDirectives;

    if (typeof reportUnusedDisableDirectives === "boolean") {
        reportUnusedDisableDirectives = reportUnusedDisableDirectives ? "error" : "off";
    }
    if (typeof reportUnusedDisableDirectives !== "string") {
        if (typeof linterOptions.reportUnusedDisableDirectives === "boolean") {
            reportUnusedDisableDirectives = linterOptions.reportUnusedDisableDirectives ? "warn" : "off";
        } else {
            reportUnusedDisableDirectives = linterOptions.reportUnusedDisableDirectives === void 0 ? "off" : normalizeSeverityToString(linterOptions.reportUnusedDisableDirectives);
        }
    }

    return {
        filename: normalizeFilename(providedOptions.filename || "<input>"),
        allowInlineConfig: !ignoreInlineConfig,
        warnInlineConfig: disableInlineConfig && !ignoreInlineConfig
            ? `your config${configNameOfNoInlineConfig}`
            : null,
        reportUnusedDisableDirectives,
        disableFixes: Boolean(providedOptions.disableFixes)
    };
}

/**
 * Combines the provided parserOptions with the options from environments
 * @param {Parser} parser The parser which uses this options.
 * @param {ParserOptions} providedOptions The provided 'parserOptions' key in a config
 * @param {Environment[]} enabledEnvironments The environments enabled in configuration and with inline comments
 * @returns {ParserOptions} Resulting parser options after merge
 */
function resolveParserOptions(parser, providedOptions, enabledEnvironments) {

    const parserOptionsFromEnv = enabledEnvironments
        .filter(env => env.parserOptions)
        .reduce((parserOptions, env) => merge(parserOptions, env.parserOptions), {});
    const mergedParserOptions = merge(parserOptionsFromEnv, providedOptions || {});
    const isModule = mergedParserOptions.sourceType === "module";

    if (isModule) {

        /*
         * can't have global return inside of modules
         * TODO: espree validate parserOptions.globalReturn when sourceType is setting to module.(@aladdin-add)
         */
        mergedParserOptions.ecmaFeatures = Object.assign({}, mergedParserOptions.ecmaFeatures, { globalReturn: false });
    }

    mergedParserOptions.ecmaVersion = normalizeEcmaVersion(parser, mergedParserOptions.ecmaVersion);

    return mergedParserOptions;
}

/**
 * Converts parserOptions to languageOptions for backwards compatibility with eslintrc.
 * @param {ConfigData} config Config object.
 * @param {Object} config.globals Global variable definitions.
 * @param {Parser} config.parser The parser to use.
 * @param {ParserOptions} config.parserOptions The parserOptions to use.
 * @returns {LanguageOptions} The languageOptions equivalent.
 */
function createLanguageOptions({ globals: configuredGlobals, parser, parserOptions }) {

    const {
        ecmaVersion,
        sourceType
    } = parserOptions;

    return {
        globals: configuredGlobals,
        ecmaVersion: normalizeEcmaVersionForLanguageOptions(ecmaVersion),
        sourceType,
        parser,
        parserOptions
    };
}

/**
 * Combines the provided globals object with the globals from environments
 * @param {Record<string, GlobalConf>} providedGlobals The 'globals' key in a config
 * @param {Environment[]} enabledEnvironments The environments enabled in configuration and with inline comments
 * @returns {Record<string, GlobalConf>} The resolved globals object
 */
function resolveGlobals(providedGlobals, enabledEnvironments) {
    return Object.assign(
        Object.create(null),
        ...enabledEnvironments.filter(env => env.globals).map(env => env.globals),
        providedGlobals
    );
}

/**
 * Strips Unicode BOM from a given text.
 * @param {string} text A text to strip.
 * @returns {string} The stripped text.
 */
function stripUnicodeBOM(text) {

    /*
     * Check Unicode BOM.
     * In JavaScript, string data is stored as UTF-16, so BOM is 0xFEFF.
     * http://www.ecma-international.org/ecma-262/6.0/#sec-unicode-format-control-characters
     */
    if (text.charCodeAt(0) === 0xFEFF) {
        return text.slice(1);
    }
    return text;
}

/**
 * Get the options for a rule (not including severity), if any
 * @param {Array|number} ruleConfig rule configuration
 * @returns {Array} of rule options, empty Array if none
 */
function getRuleOptions(ruleConfig) {
    if (Array.isArray(ruleConfig)) {
        return ruleConfig.slice(1);
    }
    return [];

}

/**
 * Analyze scope of the given AST.
 * @param {ASTNode} ast The `Program` node to analyze.
 * @param {LanguageOptions} languageOptions The parser options.
 * @param {Record<string, string[]>} visitorKeys The visitor keys.
 * @returns {ScopeManager} The analysis result.
 */
function analyzeScope(ast, languageOptions, visitorKeys) {
    const parserOptions = languageOptions.parserOptions;
    const ecmaFeatures = parserOptions.ecmaFeatures || {};
    const ecmaVersion = languageOptions.ecmaVersion || DEFAULT_ECMA_VERSION;

    return eslintScope.analyze(ast, {
        ignoreEval: true,
        nodejsScope: ecmaFeatures.globalReturn,
        impliedStrict: ecmaFeatures.impliedStrict,
        ecmaVersion: typeof ecmaVersion === "number" ? ecmaVersion : 6,
        sourceType: languageOptions.sourceType || "script",
        childVisitorKeys: visitorKeys || evk.KEYS,
        fallback: Traverser.getKeys
    });
}

/**
 * Parses text into an AST. Moved out here because the try-catch prevents
 * optimization of functions, so it's best to keep the try-catch as isolated
 * as possible
 * @param {string} text The text to parse.
 * @param {LanguageOptions} languageOptions Options to pass to the parser
 * @param {string} filePath The path to the file being parsed.
 * @returns {{success: false, error: LintMessage}|{success: true, sourceCode: SourceCode}}
 * An object containing the AST and parser services if parsing was successful, or the error if parsing failed
 * @private
 */
function parse(text, languageOptions, filePath) {
    const textToParse = stripUnicodeBOM(text).replace(astUtils.shebangPattern, (match, captured) => `//${captured}`);
    const { ecmaVersion, sourceType, parser } = languageOptions;
    const parserOptions = Object.assign(
        { ecmaVersion, sourceType },
        languageOptions.parserOptions,
        {
            loc: true,
            range: true,
            raw: true,
            tokens: true,
            comment: true,
            eslintVisitorKeys: true,
            eslintScopeManager: true,
            filePath
        }
    );

    /*
     * Check for parsing errors first. If there's a parsing error, nothing
     * else can happen. However, a parsing error does not throw an error
     * from this method - it's just considered a fatal error message, a
     * problem that ESLint identified just like any other.
     */
    try {
        debug("Parsing:", filePath);
        const parseResult = (typeof parser.parseForESLint === "function")
            ? parser.parseForESLint(textToParse, parserOptions)
            : { ast: parser.parse(textToParse, parserOptions) };

        debug("Parsing successful:", filePath);
        const ast = parseResult.ast;
        const parserServices = parseResult.services || {};
        const visitorKeys = parseResult.visitorKeys || evk.KEYS;

        debug("Scope analysis:", filePath);
        const scopeManager = parseResult.scopeManager || analyzeScope(ast, languageOptions, visitorKeys);

        debug("Scope analysis successful:", filePath);

        return {
            success: true,

            /*
             * Save all values that `parseForESLint()` returned.
             * If a `SourceCode` object is given as the first parameter instead of source code text,
             * linter skips the parsing process and reuses the source code object.
             * In that case, linter needs all the values that `parseForESLint()` returned.
             */
            sourceCode: new SourceCode({
                text,
                ast,
                parserServices,
                scopeManager,
                visitorKeys
            })
        };
    } catch (ex) {

        // If the message includes a leading line number, strip it:
        const message = `Parsing error: ${ex.message.replace(/^line \d+:/iu, "").trim()}`;

        debug("%s\n%s", message, ex.stack);

        return {
            success: false,
            error: {
                ruleId: null,
                fatal: true,
                severity: 2,
                message,
                line: ex.lineNumber,
                column: ex.column,
                nodeType: null
            }
        };
    }
}

/**
 * Runs a rule, and gets its listeners
 * @param {Rule} rule A normalized rule with a `create` method
 * @param {Context} ruleContext The context that should be passed to the rule
 * @throws {any} Any error during the rule's `create`
 * @returns {Object} A map of selector listeners provided by the rule
 */
function createRuleListeners(rule, ruleContext) {
    try {
        return rule.create(ruleContext);
    } catch (ex) {
        ex.message = `Error while loading rule '${ruleContext.id}': ${ex.message}`;
        throw ex;
    }
}

// methods that exist on SourceCode object
const DEPRECATED_SOURCECODE_PASSTHROUGHS = {
    getSource: "getText",
    getSourceLines: "getLines",
    getAllComments: "getAllComments",
    getNodeByRangeIndex: "getNodeByRangeIndex",
    getComments: "getComments",
    getCommentsBefore: "getCommentsBefore",
    getCommentsAfter: "getCommentsAfter",
    getCommentsInside: "getCommentsInside",
    getJSDocComment: "getJSDocComment",
    getFirstToken: "getFirstToken",
    getFirstTokens: "getFirstTokens",
    getLastToken: "getLastToken",
    getLastTokens: "getLastTokens",
    getTokenAfter: "getTokenAfter",
    getTokenBefore: "getTokenBefore",
    getTokenByRangeStart: "getTokenByRangeStart",
    getTokens: "getTokens",
    getTokensAfter: "getTokensAfter",
    getTokensBefore: "getTokensBefore",
    getTokensBetween: "getTokensBetween"
};


const BASE_TRAVERSAL_CONTEXT = Object.freeze(
    Object.keys(DEPRECATED_SOURCECODE_PASSTHROUGHS).reduce(
        (contextInfo, methodName) =>
            Object.assign(contextInfo, {
                [methodName](...args) {
                    return this.sourceCode[DEPRECATED_SOURCECODE_PASSTHROUGHS[methodName]](...args);
                }
            }),
        {}
    )
);

/**
 * Runs the given rules on the given SourceCode object
 * @param {SourceCode} sourceCode A SourceCode object for the given text
 * @param {Object} configuredRules The rules configuration
 * @param {function(string): Rule} ruleMapper A mapper function from rule names to rules
 * @param {string | undefined} parserName The name of the parser in the config
 * @param {LanguageOptions} languageOptions The options for parsing the code.
 * @param {Object} settings The settings that were enabled in the config
 * @param {string} filename The reported filename of the code
 * @param {boolean} disableFixes If true, it doesn't make `fix` properties.
 * @param {string | undefined} cwd cwd of the cli
 * @param {string} physicalFilename The full path of the file on disk without any code block information
 * @returns {LintMessage[]} An array of reported problems
 */
function runRules(sourceCode, configuredRules, ruleMapper, parserName, languageOptions, settings, filename, disableFixes, cwd, physicalFilename) {
    const emitter = createEmitter();
    const nodeQueue = [];
    let currentNode = sourceCode.ast;

    Traverser.traverse(sourceCode.ast, {
        enter(node, parent) {
            node.parent = parent;
            nodeQueue.push({ isEntering: true, node });
        },
        leave(node) {
            nodeQueue.push({ isEntering: false, node });
        },
        visitorKeys: sourceCode.visitorKeys
    });

    /*
     * Create a frozen object with the ruleContext properties and methods that are shared by all rules.
     * All rule contexts will inherit from this object. This avoids the performance penalty of copying all the
     * properties once for each rule.
     */
    const sharedTraversalContext = Object.freeze(
        Object.assign(
            Object.create(BASE_TRAVERSAL_CONTEXT),
            {
                getAncestors: () => sourceCode.getAncestors(currentNode),
                getDeclaredVariables: node => sourceCode.getDeclaredVariables(node),
                getCwd: () => cwd,
                cwd,
                getFilename: () => filename,
                filename,
                getPhysicalFilename: () => physicalFilename || filename,
                physicalFilename: physicalFilename || filename,
                getScope: () => sourceCode.getScope(currentNode),
                getSourceCode: () => sourceCode,
                sourceCode,
                markVariableAsUsed: name => sourceCode.markVariableAsUsed(name, currentNode),
                parserOptions: {
                    ...languageOptions.parserOptions
                },
                parserPath: parserName,
                languageOptions,
                parserServices: sourceCode.parserServices,
                settings
            }
        )
    );

    const lintingProblems = [];

    Object.keys(configuredRules).forEach(ruleId => {
        const severity = ConfigOps.getRuleSeverity(configuredRules[ruleId]);

        // not load disabled rules
        if (severity === 0) {
            return;
        }

        const rule = ruleMapper(ruleId);

        if (!rule) {
            lintingProblems.push(createLintingProblem({ ruleId }));
            return;
        }

        const messageIds = rule.meta && rule.meta.messages;
        let reportTranslator = null;
        const ruleContext = Object.freeze(
            Object.assign(
                Object.create(sharedTraversalContext),
                {
                    id: ruleId,
                    options: getRuleOptions(configuredRules[ruleId]),
                    report(...args) {

                        /*
                         * Create a report translator lazily.
                         * In a vast majority of cases, any given rule reports zero errors on a given
                         * piece of code. Creating a translator lazily avoids the performance cost of
                         * creating a new translator function for each rule that usually doesn't get
                         * called.
                         *
                         * Using lazy report translators improves end-to-end performance by about 3%
                         * with Node 8.4.0.
                         */
                        if (reportTranslator === null) {
                            reportTranslator = createReportTranslator({
                                ruleId,
                                severity,
                                sourceCode,
                                messageIds,
                                disableFixes
                            });
                        }
                        const problem = reportTranslator(...args);

                        if (problem.fix && !(rule.meta && rule.meta.fixable)) {
                            throw new Error("Fixable rules must set the `meta.fixable` property to \"code\" or \"whitespace\".");
                        }
                        if (problem.suggestions && !(rule.meta && rule.meta.hasSuggestions === true)) {
                            if (rule.meta && rule.meta.docs && typeof rule.meta.docs.suggestion !== "undefined") {

                                // Encourage migration from the former property name.
                                throw new Error("Rules with suggestions must set the `meta.hasSuggestions` property to `true`. `meta.docs.suggestion` is ignored by ESLint.");
                            }
                            throw new Error("Rules with suggestions must set the `meta.hasSuggestions` property to `true`.");
                        }
                        lintingProblems.push(problem);
                    }
                }
            )
        );

        const ruleListeners = timing.enabled ? timing.time(ruleId, createRuleListeners)(rule, ruleContext) : createRuleListeners(rule, ruleContext);

        /**
         * Include `ruleId` in error logs
         * @param {Function} ruleListener A rule method that listens for a node.
         * @returns {Function} ruleListener wrapped in error handler
         */
        function addRuleErrorHandler(ruleListener) {
            return function ruleErrorHandler(...listenerArgs) {
                try {
                    return ruleListener(...listenerArgs);
                } catch (e) {
                    e.ruleId = ruleId;
                    throw e;
                }
            };
        }

        if (typeof ruleListeners === "undefined" || ruleListeners === null) {
            throw new Error(`The create() function for rule '${ruleId}' did not return an object.`);
        }

        // add all the selectors from the rule as listeners
        Object.keys(ruleListeners).forEach(selector => {
            const ruleListener = timing.enabled
                ? timing.time(ruleId, ruleListeners[selector])
                : ruleListeners[selector];

            emitter.on(
                selector,
                addRuleErrorHandler(ruleListener)
            );
        });
    });

    // only run code path analyzer if the top level node is "Program", skip otherwise
    const eventGenerator = nodeQueue[0].node.type === "Program"
        ? new CodePathAnalyzer(new NodeEventGenerator(emitter, { visitorKeys: sourceCode.visitorKeys, fallback: Traverser.getKeys }))
        : new NodeEventGenerator(emitter, { visitorKeys: sourceCode.visitorKeys, fallback: Traverser.getKeys });

    nodeQueue.forEach(traversalInfo => {
        currentNode = traversalInfo.node;

        try {
            if (traversalInfo.isEntering) {
                eventGenerator.enterNode(currentNode);
            } else {
                eventGenerator.leaveNode(currentNode);
            }
        } catch (err) {
            err.currentNode = currentNode;
            throw err;
        }
    });

    return lintingProblems;
}

/**
 * Ensure the source code to be a string.
 * @param {string|SourceCode} textOrSourceCode The text or source code object.
 * @returns {string} The source code text.
 */
function ensureText(textOrSourceCode) {
    if (typeof textOrSourceCode === "object") {
        const { hasBOM, text } = textOrSourceCode;
        const bom = hasBOM ? "\uFEFF" : "";

        return bom + text;
    }

    return String(textOrSourceCode);
}

/**
 * Get an environment.
 * @param {LinterInternalSlots} slots The internal slots of Linter.
 * @param {string} envId The environment ID to get.
 * @returns {Environment|null} The environment.
 */
function getEnv(slots, envId) {
    return (
        (slots.lastConfigArray && slots.lastConfigArray.pluginEnvironments.get(envId)) ||
        BuiltInEnvironments.get(envId) ||
        null
    );
}

/**
 * Get a rule.
 * @param {LinterInternalSlots} slots The internal slots of Linter.
 * @param {string} ruleId The rule ID to get.
 * @returns {Rule|null} The rule.
 */
function getRule(slots, ruleId) {
    return (
        (slots.lastConfigArray && slots.lastConfigArray.pluginRules.get(ruleId)) ||
        slots.ruleMap.get(ruleId)
    );
}

/**
 * Normalize the value of the cwd
 * @param {string | undefined} cwd raw value of the cwd, path to a directory that should be considered as the current working directory, can be undefined.
 * @returns {string | undefined} normalized cwd
 */
function normalizeCwd(cwd) {
    if (cwd) {
        return cwd;
    }
    if (typeof process === "object") {
        return process.cwd();
    }

    // It's more explicit to assign the undefined
    // eslint-disable-next-line no-undefined -- Consistently returning a value
    return undefined;
}

/**
 * The map to store private data.
 * @type {WeakMap<Linter, LinterInternalSlots>}
 */
const internalSlotsMap = new WeakMap();

/**
 * Throws an error when the given linter is in flat config mode.
 * @param {Linter} linter The linter to check.
 * @returns {void}
 * @throws {Error} If the linter is in flat config mode.
 */
function assertEslintrcConfig(linter) {
    const { configType } = internalSlotsMap.get(linter);

    if (configType === "flat") {
        throw new Error("This method cannot be used with flat config. Add your entries directly into the config array.");
    }
}


//------------------------------------------------------------------------------
// Public Interface
//------------------------------------------------------------------------------

/**
 * Object that is responsible for verifying JavaScript text
 * @name Linter
 */
class Linter {

    /**
     * Initialize the Linter.
     * @param {Object} [config] the config object
     * @param {string} [config.cwd] path to a directory that should be considered as the current working directory, can be undefined.
     * @param {"flat"|"eslintrc"} [config.configType="eslintrc"] the type of config used.
     */
    constructor({ cwd, configType } = {}) {
        internalSlotsMap.set(this, {
            cwd: normalizeCwd(cwd),
            lastConfigArray: null,
            lastSourceCode: null,
            lastSuppressedMessages: [],
            configType, // TODO: Remove after flat config conversion
            parserMap: new Map([["espree", espree]]),
            ruleMap: new Rules()
        });

        this.version = pkg.version;
    }

    /**
     * Getter for package version.
     * @static
     * @returns {string} The version from package.json.
     */
    static get version() {
        return pkg.version;
    }

    /**
     * Same as linter.verify, except without support for processors.
     * @param {string|SourceCode} textOrSourceCode The text to parse or a SourceCode object.
     * @param {ConfigData} providedConfig An ESLintConfig instance to configure everything.
     * @param {VerifyOptions} [providedOptions] The optional filename of the file being checked.
     * @throws {Error} If during rule execution.
     * @returns {(LintMessage|SuppressedLintMessage)[]} The results as an array of messages or an empty array if no messages.
     */
    _verifyWithoutProcessors(textOrSourceCode, providedConfig, providedOptions) {
        const slots = internalSlotsMap.get(this);
        const config = providedConfig || {};
        const options = normalizeVerifyOptions(providedOptions, config);
        let text;

        // evaluate arguments
        if (typeof textOrSourceCode === "string") {
            slots.lastSourceCode = null;
            text = textOrSourceCode;
        } else {
            slots.lastSourceCode = textOrSourceCode;
            text = textOrSourceCode.text;
        }

        // Resolve parser.
        let parserName = DEFAULT_PARSER_NAME;
        let parser = espree;

        if (typeof config.parser === "object" && config.parser !== null) {
            parserName = config.parser.filePath;
            parser = config.parser.definition;
        } else if (typeof config.parser === "string") {
            if (!slots.parserMap.has(config.parser)) {
                return [{
                    ruleId: null,
                    fatal: true,
                    severity: 2,
                    message: `Configured parser '${config.parser}' was not found.`,
                    line: 0,
                    column: 0,
                    nodeType: null
                }];
            }
            parserName = config.parser;
            parser = slots.parserMap.get(config.parser);
        }

        // search and apply "eslint-env *".
        const envInFile = options.allowInlineConfig && !options.warnInlineConfig
            ? findEslintEnv(text)
            : {};
        const resolvedEnvConfig = Object.assign({ builtin: true }, config.env, envInFile);
        const enabledEnvs = Object.keys(resolvedEnvConfig)
            .filter(envName => resolvedEnvConfig[envName])
            .map(envName => getEnv(slots, envName))
            .filter(env => env);

        const parserOptions = resolveParserOptions(parser, config.parserOptions || {}, enabledEnvs);
        const configuredGlobals = resolveGlobals(config.globals || {}, enabledEnvs);
        const settings = config.settings || {};
        const languageOptions = createLanguageOptions({
            globals: config.globals,
            parser,
            parserOptions
        });

        if (!slots.lastSourceCode) {
            const parseResult = parse(
                text,
                languageOptions,
                options.filename
            );

            if (!parseResult.success) {
                return [parseResult.error];
            }

            slots.lastSourceCode = parseResult.sourceCode;
        } else {

            /*
             * If the given source code object as the first argument does not have scopeManager, analyze the scope.
             * This is for backward compatibility (SourceCode is frozen so it cannot rebind).
             */
            if (!slots.lastSourceCode.scopeManager) {
                slots.lastSourceCode = new SourceCode({
                    text: slots.lastSourceCode.text,
                    ast: slots.lastSourceCode.ast,
                    parserServices: slots.lastSourceCode.parserServices,
                    visitorKeys: slots.lastSourceCode.visitorKeys,
                    scopeManager: analyzeScope(slots.lastSourceCode.ast, languageOptions)
                });
            }
        }

        const sourceCode = slots.lastSourceCode;
        const commentDirectives = options.allowInlineConfig
            ? getDirectiveComments(sourceCode, ruleId => getRule(slots, ruleId), options.warnInlineConfig)
            : { configuredRules: {}, enabledGlobals: {}, exportedVariables: {}, problems: [], disableDirectives: [] };

        // augment global scope with declared global variables
        addDeclaredGlobals(
            sourceCode.scopeManager.scopes[0],
            configuredGlobals,
            { exportedVariables: commentDirectives.exportedVariables, enabledGlobals: commentDirectives.enabledGlobals }
        );

        const configuredRules = Object.assign({}, config.rules, commentDirectives.configuredRules);
        let lintingProblems;

        try {
            lintingProblems = runRules(
                sourceCode,
                configuredRules,
                ruleId => getRule(slots, ruleId),
                parserName,
                languageOptions,
                settings,
                options.filename,
                options.disableFixes,
                slots.cwd,
                providedOptions.physicalFilename
            );
        } catch (err) {
            err.message += `\nOccurred while linting ${options.filename}`;
            debug("An error occurred while traversing");
            debug("Filename:", options.filename);
            if (err.currentNode) {
                const { line } = err.currentNode.loc.start;

                debug("Line:", line);
                err.message += `:${line}`;
            }
            debug("Parser Options:", parserOptions);
            debug("Parser Path:", parserName);
            debug("Settings:", settings);

            if (err.ruleId) {
                err.message += `\nRule: "${err.ruleId}"`;
            }

            throw err;
        }

        return applyDisableDirectives({
            directives: commentDirectives.disableDirectives,
            disableFixes: options.disableFixes,
            problems: lintingProblems
                .concat(commentDirectives.problems)
                .sort((problemA, problemB) => problemA.line - problemB.line || problemA.column - problemB.column),
            reportUnusedDisableDirectives: options.reportUnusedDisableDirectives
        });
    }

    /**
     * Verifies the text against the rules specified by the second argument.
     * @param {string|SourceCode} textOrSourceCode The text to parse or a SourceCode object.
     * @param {ConfigData|ConfigArray} config An ESLintConfig instance to configure everything.
     * @param {(string|(VerifyOptions&ProcessorOptions))} [filenameOrOptions] The optional filename of the file being checked.
     *      If this is not set, the filename will default to '<input>' in the rule context. If
     *      an object, then it has "filename", "allowInlineConfig", and some properties.
     * @returns {LintMessage[]} The results as an array of messages or an empty array if no messages.
     */
    verify(textOrSourceCode, config, filenameOrOptions) {
        debug("Verify");

        const { configType, cwd } = internalSlotsMap.get(this);

        const options = typeof filenameOrOptions === "string"
            ? { filename: filenameOrOptions }
            : filenameOrOptions || {};

        if (config) {
            if (configType === "flat") {

                /*
                 * Because of how Webpack packages up the files, we can't
                 * compare directly to `FlatConfigArray` using `instanceof`
                 * because it's not the same `FlatConfigArray` as in the tests.
                 * So, we work around it by assuming an array is, in fact, a
                 * `FlatConfigArray` if it has a `getConfig()` method.
                 */
                let configArray = config;

                if (!Array.isArray(config) || typeof config.getConfig !== "function") {
                    configArray = new FlatConfigArray(config, { basePath: cwd });
                    configArray.normalizeSync();
                }

                return this._distinguishSuppressedMessages(this._verifyWithFlatConfigArray(textOrSourceCode, configArray, options, true));
            }

            if (typeof config.extractConfig === "function") {
                return this._distinguishSuppressedMessages(this._verifyWithConfigArray(textOrSourceCode, config, options));
            }
        }

        /*
         * If we get to here, it means `config` is just an object rather
         * than a config array so we can go right into linting.
         */

        /*
         * `Linter` doesn't support `overrides` property in configuration.
         * So we cannot apply multiple processors.
         */
        if (options.preprocess || options.postprocess) {
            return this._distinguishSuppressedMessages(this._verifyWithProcessor(textOrSourceCode, config, options));
        }
        return this._distinguishSuppressedMessages(this._verifyWithoutProcessors(textOrSourceCode, config, options));
    }

    /**
     * Verify with a processor.
     * @param {string|SourceCode} textOrSourceCode The source code.
     * @param {FlatConfig} config The config array.
     * @param {VerifyOptions&ProcessorOptions} options The options.
     * @param {FlatConfigArray} [configForRecursive] The `ConfigArray` object to apply multiple processors recursively.
     * @returns {(LintMessage|SuppressedLintMessage)[]} The found problems.
     */
    _verifyWithFlatConfigArrayAndProcessor(textOrSourceCode, config, options, configForRecursive) {
        const filename = options.filename || "<input>";
        const filenameToExpose = normalizeFilename(filename);
        const physicalFilename = options.physicalFilename || filenameToExpose;
        const text = ensureText(textOrSourceCode);
        const preprocess = options.preprocess || (rawText => [rawText]);
        const postprocess = options.postprocess || (messagesList => messagesList.flat());
        const filterCodeBlock =
            options.filterCodeBlock ||
            (blockFilename => blockFilename.endsWith(".js"));
        const originalExtname = path.extname(filename);

        let blocks;

        try {
            blocks = preprocess(text, filenameToExpose);
        } catch (ex) {

            // If the message includes a leading line number, strip it:
            const message = `Preprocessing error: ${ex.message.replace(/^line \d+:/iu, "").trim()}`;

            debug("%s\n%s", message, ex.stack);

            return [
                {
                    ruleId: null,
                    fatal: true,
                    severity: 2,
                    message,
                    line: ex.lineNumber,
                    column: ex.column,
                    nodeType: null
                }
            ];
        }

        const messageLists = blocks.map((block, i) => {
            debug("A code block was found: %o", block.filename || "(unnamed)");

            // Keep the legacy behavior.
            if (typeof block === "string") {
                return this._verifyWithFlatConfigArrayAndWithoutProcessors(block, config, options);
            }

            const blockText = block.text;
            const blockName = path.join(filename, `${i}_${block.filename}`);

            // Skip this block if filtered.
            if (!filterCodeBlock(blockName, blockText)) {
                debug("This code block was skipped.");
                return [];
            }

            // Resolve configuration again if the file content or extension was changed.
            if (configForRecursive && (text !== blockText || path.extname(blockName) !== originalExtname)) {
                debug("Resolving configuration again because the file content or extension was changed.");
                return this._verifyWithFlatConfigArray(
                    blockText,
                    configForRecursive,
                    { ...options, filename: blockName, physicalFilename }
                );
            }

            // Does lint.
            return this._verifyWithFlatConfigArrayAndWithoutProcessors(
                blockText,
                config,
                { ...options, filename: blockName, physicalFilename }
            );
        });

        return postprocess(messageLists, filenameToExpose);
    }

    /**
     * Same as linter.verify, except without support for processors.
     * @param {string|SourceCode} textOrSourceCode The text to parse or a SourceCode object.
     * @param {FlatConfig} providedConfig An ESLintConfig instance to configure everything.
     * @param {VerifyOptions} [providedOptions] The optional filename of the file being checked.
     * @throws {Error} If during rule execution.
     * @returns {(LintMessage|SuppressedLintMessage)[]} The results as an array of messages or an empty array if no messages.
     */
    _verifyWithFlatConfigArrayAndWithoutProcessors(textOrSourceCode, providedConfig, providedOptions) {
        const slots = internalSlotsMap.get(this);
        const config = providedConfig || {};
        const options = normalizeVerifyOptions(providedOptions, config);
        let text;

        // evaluate arguments
        if (typeof textOrSourceCode === "string") {
            slots.lastSourceCode = null;
            text = textOrSourceCode;
        } else {
            slots.lastSourceCode = textOrSourceCode;
            text = textOrSourceCode.text;
        }

        const languageOptions = config.languageOptions;

        languageOptions.ecmaVersion = normalizeEcmaVersionForLanguageOptions(
            languageOptions.ecmaVersion
        );

        // double check that there is a parser to avoid mysterious error messages
        if (!languageOptions.parser) {
            throw new TypeError(`No parser specified for ${options.filename}`);
        }

        // Espree expects this information to be passed in
        if (isEspree(languageOptions.parser)) {
            const parserOptions = languageOptions.parserOptions;

            if (languageOptions.sourceType) {

                parserOptions.sourceType = languageOptions.sourceType;

                if (
                    parserOptions.sourceType === "module" &&
                    parserOptions.ecmaFeatures &&
                    parserOptions.ecmaFeatures.globalReturn
                ) {
                    parserOptions.ecmaFeatures.globalReturn = false;
                }
            }
        }

        const settings = config.settings || {};

        if (!slots.lastSourceCode) {
            const parseResult = parse(
                text,
                languageOptions,
                options.filename
            );

            if (!parseResult.success) {
                return [parseResult.error];
            }

            slots.lastSourceCode = parseResult.sourceCode;
        } else {

            /*
             * If the given source code object as the first argument does not have scopeManager, analyze the scope.
             * This is for backward compatibility (SourceCode is frozen so it cannot rebind).
             */
            if (!slots.lastSourceCode.scopeManager) {
                slots.lastSourceCode = new SourceCode({
                    text: slots.lastSourceCode.text,
                    ast: slots.lastSourceCode.ast,
                    parserServices: slots.lastSourceCode.parserServices,
                    visitorKeys: slots.lastSourceCode.visitorKeys,
                    scopeManager: analyzeScope(slots.lastSourceCode.ast, languageOptions)
                });
            }
        }

        const sourceCode = slots.lastSourceCode;

        /*
         * Make adjustments based on the language options. For JavaScript,
         * this is primarily about adding variables into the global scope
         * to account for ecmaVersion and configured globals.
         */
        sourceCode.applyLanguageOptions(languageOptions);

        const mergedInlineConfig = {
            rules: {}
        };
        const inlineConfigProblems = [];

        /*
         * Inline config can be either enabled or disabled. If disabled, it's possible
         * to detect the inline config and emit a warning (though this is not required).
         * So we first check to see if inline config is allowed at all, and if so, we
         * need to check if it's a warning or not.
         */
        if (options.allowInlineConfig) {

            // if inline config should warn then add the warnings
            if (options.warnInlineConfig) {
                sourceCode.getInlineConfigNodes().forEach(node => {
                    inlineConfigProblems.push(createLintingProblem({
                        ruleId: null,
                        message: `'${sourceCode.text.slice(node.range[0], node.range[1])}' has no effect because you have 'noInlineConfig' setting in ${options.warnInlineConfig}.`,
                        loc: node.loc,
                        severity: 1
                    }));

                });
            } else {
                const inlineConfigResult = sourceCode.applyInlineConfig();

                inlineConfigProblems.push(
                    ...inlineConfigResult.problems
                        .map(createLintingProblem)
                        .map(problem => {
                            problem.fatal = true;
                            return problem;
                        })
                );

                // next we need to verify information about the specified rules
                const ruleValidator = new RuleValidator();

                for (const { config: inlineConfig, node } of inlineConfigResult.configs) {

                    Object.keys(inlineConfig.rules).forEach(ruleId => {
                        const rule = getRuleFromConfig(ruleId, config);
                        const ruleValue = inlineConfig.rules[ruleId];

                        if (!rule) {
                            inlineConfigProblems.push(createLintingProblem({ ruleId, loc: node.loc }));
                            return;
                        }

                        try {

                            const ruleOptions = Array.isArray(ruleValue) ? ruleValue : [ruleValue];

                            assertIsRuleOptions(ruleId, ruleValue);
                            assertIsRuleSeverity(ruleId, ruleOptions[0]);

                            ruleValidator.validate({
                                plugins: config.plugins,
                                rules: {
                                    [ruleId]: ruleOptions
                                }
                            });
                            mergedInlineConfig.rules[ruleId] = ruleValue;
                        } catch (err) {

                            let baseMessage = err.message.slice(
                                err.message.startsWith("Key \"rules\":")
                                    ? err.message.indexOf(":", 12) + 1
                                    : err.message.indexOf(":") + 1
                            ).trim();

                            if (err.messageTemplate) {
                                baseMessage += ` You passed "${ruleValue}".`;
                            }

                            inlineConfigProblems.push(createLintingProblem({
                                ruleId,
                                message: `Inline configuration for rule "${ruleId}" is invalid:\n\t${baseMessage}\n`,
                                loc: node.loc
                            }));
                        }
                    });
                }
            }
        }

        const commentDirectives = options.allowInlineConfig && !options.warnInlineConfig
            ? getDirectiveCommentsForFlatConfig(
                sourceCode,
                ruleId => getRuleFromConfig(ruleId, config)
            )
            : { problems: [], disableDirectives: [] };

        const configuredRules = Object.assign({}, config.rules, mergedInlineConfig.rules);
        let lintingProblems;

        sourceCode.finalize();

        try {
            lintingProblems = runRules(
                sourceCode,
                configuredRules,
                ruleId => getRuleFromConfig(ruleId, config),
                void 0,
                languageOptions,
                settings,
                options.filename,
                options.disableFixes,
                slots.cwd,
                providedOptions.physicalFilename
            );
        } catch (err) {
            err.message += `\nOccurred while linting ${options.filename}`;
            debug("An error occurred while traversing");
            debug("Filename:", options.filename);
            if (err.currentNode) {
                const { line } = err.currentNode.loc.start;

                debug("Line:", line);
                err.message += `:${line}`;
            }
            debug("Parser Options:", languageOptions.parserOptions);

            // debug("Parser Path:", parserName);
            debug("Settings:", settings);

            if (err.ruleId) {
                err.message += `\nRule: "${err.ruleId}"`;
            }

            throw err;
        }

        return applyDisableDirectives({
            directives: commentDirectives.disableDirectives,
            disableFixes: options.disableFixes,
            problems: lintingProblems
                .concat(commentDirectives.problems)
                .concat(inlineConfigProblems)
                .sort((problemA, problemB) => problemA.line - problemB.line || problemA.column - problemB.column),
            reportUnusedDisableDirectives: options.reportUnusedDisableDirectives
        });
    }

    /**
     * Verify a given code with `ConfigArray`.
     * @param {string|SourceCode} textOrSourceCode The source code.
     * @param {ConfigArray} configArray The config array.
     * @param {VerifyOptions&ProcessorOptions} options The options.
     * @returns {(LintMessage|SuppressedLintMessage)[]} The found problems.
     */
    _verifyWithConfigArray(textOrSourceCode, configArray, options) {
        debug("With ConfigArray: %s", options.filename);

        // Store the config array in order to get plugin envs and rules later.
        internalSlotsMap.get(this).lastConfigArray = configArray;

        // Extract the final config for this file.
        const config = configArray.extractConfig(options.filename);
        const processor =
            config.processor &&
            configArray.pluginProcessors.get(config.processor);

        // Verify.
        if (processor) {
            debug("Apply the processor: %o", config.processor);
            const { preprocess, postprocess, supportsAutofix } = processor;
            const disableFixes = options.disableFixes || !supportsAutofix;

            return this._verifyWithProcessor(
                textOrSourceCode,
                config,
                { ...options, disableFixes, postprocess, preprocess },
                configArray
            );
        }
        return this._verifyWithoutProcessors(textOrSourceCode, config, options);
    }

    /**
     * Verify a given code with a flat config.
     * @param {string|SourceCode} textOrSourceCode The source code.
     * @param {FlatConfigArray} configArray The config array.
     * @param {VerifyOptions&ProcessorOptions} options The options.
     * @param {boolean} [firstCall=false] Indicates if this is being called directly
     *      from verify(). (TODO: Remove once eslintrc is removed.)
     * @returns {(LintMessage|SuppressedLintMessage)[]} The found problems.
     */
    _verifyWithFlatConfigArray(textOrSourceCode, configArray, options, firstCall = false) {
        debug("With flat config: %s", options.filename);

        // we need a filename to match configs against
        const filename = options.filename || "__placeholder__.js";

        // Store the config array in order to get plugin envs and rules later.
        internalSlotsMap.get(this).lastConfigArray = configArray;
        const config = configArray.getConfig(filename);

        if (!config) {
            return [
                {
                    ruleId: null,
                    severity: 1,
                    message: `No matching configuration found for ${filename}.`,
                    line: 0,
                    column: 0,
                    nodeType: null
                }
            ];
        }

        // Verify.
        if (config.processor) {
            debug("Apply the processor: %o", config.processor);
            const { preprocess, postprocess, supportsAutofix } = config.processor;
            const disableFixes = options.disableFixes || !supportsAutofix;

            return this._verifyWithFlatConfigArrayAndProcessor(
                textOrSourceCode,
                config,
                { ...options, filename, disableFixes, postprocess, preprocess },
                configArray
            );
        }

        // check for options-based processing
        if (firstCall && (options.preprocess || options.postprocess)) {
            return this._verifyWithFlatConfigArrayAndProcessor(textOrSourceCode, config, options);
        }

        return this._verifyWithFlatConfigArrayAndWithoutProcessors(textOrSourceCode, config, options);
    }

    /**
     * Verify with a processor.
     * @param {string|SourceCode} textOrSourceCode The source code.
     * @param {ConfigData|ExtractedConfig} config The config array.
     * @param {VerifyOptions&ProcessorOptions} options The options.
     * @param {ConfigArray} [configForRecursive] The `ConfigArray` object to apply multiple processors recursively.
     * @returns {(LintMessage|SuppressedLintMessage)[]} The found problems.
     */
    _verifyWithProcessor(textOrSourceCode, config, options, configForRecursive) {
        const filename = options.filename || "<input>";
        const filenameToExpose = normalizeFilename(filename);
        const physicalFilename = options.physicalFilename || filenameToExpose;
        const text = ensureText(textOrSourceCode);
        const preprocess = options.preprocess || (rawText => [rawText]);
        const postprocess = options.postprocess || (messagesList => messagesList.flat());
        const filterCodeBlock =
            options.filterCodeBlock ||
            (blockFilename => blockFilename.endsWith(".js"));
        const originalExtname = path.extname(filename);

        let blocks;

        try {
            blocks = preprocess(text, filenameToExpose);
        } catch (ex) {

            // If the message includes a leading line number, strip it:
            const message = `Preprocessing error: ${ex.message.replace(/^line \d+:/iu, "").trim()}`;

            debug("%s\n%s", message, ex.stack);

            return [
                {
                    ruleId: null,
                    fatal: true,
                    severity: 2,
                    message,
                    line: ex.lineNumber,
                    column: ex.column,
                    nodeType: null
                }
            ];
        }

        const messageLists = blocks.map((block, i) => {
            debug("A code block was found: %o", block.filename || "(unnamed)");

            // Keep the legacy behavior.
            if (typeof block === "string") {
                return this._verifyWithoutProcessors(block, config, options);
            }

            const blockText = block.text;
            const blockName = path.join(filename, `${i}_${block.filename}`);

            // Skip this block if filtered.
            if (!filterCodeBlock(blockName, blockText)) {
                debug("This code block was skipped.");
                return [];
            }

            // Resolve configuration again if the file content or extension was changed.
            if (configForRecursive && (text !== blockText || path.extname(blockName) !== originalExtname)) {
                debug("Resolving configuration again because the file content or extension was changed.");
                return this._verifyWithConfigArray(
                    blockText,
                    configForRecursive,
                    { ...options, filename: blockName, physicalFilename }
                );
            }

            // Does lint.
            return this._verifyWithoutProcessors(
                blockText,
                config,
                { ...options, filename: blockName, physicalFilename }
            );
        });

        return postprocess(messageLists, filenameToExpose);
    }

    /**
     * Given a list of reported problems, distinguish problems between normal messages and suppressed messages.
     * The normal messages will be returned and the suppressed messages will be stored as lastSuppressedMessages.
     * @param {Array<LintMessage|SuppressedLintMessage>} problems A list of reported problems.
     * @returns {LintMessage[]} A list of LintMessage.
     */
    _distinguishSuppressedMessages(problems) {
        const messages = [];
        const suppressedMessages = [];
        const slots = internalSlotsMap.get(this);

        for (const problem of problems) {
            if (problem.suppressions) {
                suppressedMessages.push(problem);
            } else {
                messages.push(problem);
            }
        }

        slots.lastSuppressedMessages = suppressedMessages;

        return messages;
    }

    /**
     * Gets the SourceCode object representing the parsed source.
     * @returns {SourceCode} The SourceCode object.
     */
    getSourceCode() {
        return internalSlotsMap.get(this).lastSourceCode;
    }

    /**
     * Gets the list of SuppressedLintMessage produced in the last running.
     * @returns {SuppressedLintMessage[]} The list of SuppressedLintMessage
     */
    getSuppressedMessages() {
        return internalSlotsMap.get(this).lastSuppressedMessages;
    }

    /**
     * Defines a new linting rule.
     * @param {string} ruleId A unique rule identifier
     * @param {Function | Rule} ruleModule Function from context to object mapping AST node types to event handlers
     * @returns {void}
     */
    defineRule(ruleId, ruleModule) {
        assertEslintrcConfig(this);
        internalSlotsMap.get(this).ruleMap.define(ruleId, ruleModule);
    }

    /**
     * Defines many new linting rules.
     * @param {Record<string, Function | Rule>} rulesToDefine map from unique rule identifier to rule
     * @returns {void}
     */
    defineRules(rulesToDefine) {
        assertEslintrcConfig(this);
        Object.getOwnPropertyNames(rulesToDefine).forEach(ruleId => {
            this.defineRule(ruleId, rulesToDefine[ruleId]);
        });
    }

    /**
     * Gets an object with all loaded rules.
     * @returns {Map<string, Rule>} All loaded rules
     */
    getRules() {
        assertEslintrcConfig(this);
        const { lastConfigArray, ruleMap } = internalSlotsMap.get(this);

        return new Map(function *() {
            yield* ruleMap;

            if (lastConfigArray) {
                yield* lastConfigArray.pluginRules;
            }
        }());
    }

    /**
     * Define a new parser module
     * @param {string} parserId Name of the parser
     * @param {Parser} parserModule The parser object
     * @returns {void}
     */
    defineParser(parserId, parserModule) {
        assertEslintrcConfig(this);
        internalSlotsMap.get(this).parserMap.set(parserId, parserModule);
    }

    /**
     * Performs multiple autofix passes over the text until as many fixes as possible
     * have been applied.
     * @param {string} text The source text to apply fixes to.
     * @param {ConfigData|ConfigArray|FlatConfigArray} config The ESLint config object to use.
     * @param {VerifyOptions&ProcessorOptions&FixOptions} options The ESLint options object to use.
     * @returns {{fixed:boolean,messages:LintMessage[],output:string}} The result of the fix operation as returned from the
     *      SourceCodeFixer.
     */
    verifyAndFix(text, config, options) {
        let messages = [],
            fixedResult,
            fixed = false,
            passNumber = 0,
            currentText = text;
        const debugTextDescription = options && options.filename || `${text.slice(0, 10)}...`;
        const shouldFix = options && typeof options.fix !== "undefined" ? options.fix : true;

        /**
         * This loop continues until one of the following is true:
         *
         * 1. No more fixes have been applied.
         * 2. Ten passes have been made.
         *
         * That means anytime a fix is successfully applied, there will be another pass.
         * Essentially, guaranteeing a minimum of two passes.
         */
        do {
            passNumber++;

            debug(`Linting code for ${debugTextDescription} (pass ${passNumber})`);
            messages = this.verify(currentText, config, options);

            debug(`Generating fixed text for ${debugTextDescription} (pass ${passNumber})`);
            fixedResult = SourceCodeFixer.applyFixes(currentText, messages, shouldFix);

            /*
             * stop if there are any syntax errors.
             * 'fixedResult.output' is a empty string.
             */
            if (messages.length === 1 && messages[0].fatal) {
                break;
            }

            // keep track if any fixes were ever applied - important for return value
            fixed = fixed || fixedResult.fixed;

            // update to use the fixed output instead of the original text
            currentText = fixedResult.output;

        } while (
            fixedResult.fixed &&
            passNumber < MAX_AUTOFIX_PASSES
        );

        /*
         * If the last result had fixes, we need to lint again to be sure we have
         * the most up-to-date information.
         */
        if (fixedResult.fixed) {
            fixedResult.messages = this.verify(currentText, config, options);
        }

        // ensure the last result properly reflects if fixes were done
        fixedResult.fixed = fixed;
        fixedResult.output = currentText;

        return fixedResult;
    }
}

module.exports = {
    Linter,

    /**
     * Get the internal slots of a given Linter instance for tests.
     * @param {Linter} instance The Linter instance to get.
     * @returns {LinterInternalSlots} The internal slots.
     */
    getLinterInternalSlots(instance) {
        return internalSlotsMap.get(instance);
    }
};
