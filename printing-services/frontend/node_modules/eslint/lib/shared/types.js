/**
 * @fileoverview Define common types for input completion.
 * @author Toru Nagashima <https://github.com/mysticatea>
 */
"use strict";

/** @type {any} */
module.exports = {};

/** @typedef {boolean | "off" | "readable" | "readonly" | "writable" | "writeable"} GlobalConf */
/** @typedef {0 | 1 | 2 | "off" | "warn" | "error"} SeverityConf */
/** @typedef {SeverityConf | [SeverityConf, ...any[]]} RuleConf */

/**
 * @typedef {Object} EcmaFeatures
 * @property {boolean} [globalReturn] Enabling `return` statements at the top-level.
 * @property {boolean} [jsx] Enabling JSX syntax.
 * @property {boolean} [impliedStrict] Enabling strict mode always.
 */

/**
 * @typedef {Object} ParserOptions
 * @property {EcmaFeatures} [ecmaFeatures] The optional features.
 * @property {3|5|6|7|8|9|10|11|12|13|14|15|2015|2016|2017|2018|2019|2020|2021|2022|2023|2024} [ecmaVersion] The ECMAScript version (or revision number).
 * @property {"script"|"module"} [sourceType] The source code type.
 * @property {boolean} [allowReserved] Allowing the use of reserved words as identifiers in ES3.
 */

/**
 * @typedef {Object} LanguageOptions
 * @property {number|"latest"} [ecmaVersion] The ECMAScript version (or revision number).
 * @property {Record<string, GlobalConf>} [globals] The global variable settings.
 * @property {"script"|"module"|"commonjs"} [sourceType] The source code type.
 * @property {string|Object} [parser] The parser to use.
 * @property {Object} [parserOptions] The parser options to use.
 */

/**
 * @typedef {Object} ConfigData
 * @property {Record<string, boolean>} [env] The environment settings.
 * @property {string | string[]} [extends] The path to other config files or the package name of shareable configs.
 * @property {Record<string, GlobalConf>} [globals] The global variable settings.
 * @property {string | string[]} [ignorePatterns] The glob patterns that ignore to lint.
 * @property {boolean} [noInlineConfig] The flag that disables directive comments.
 * @property {OverrideConfigData[]} [overrides] The override settings per kind of files.
 * @property {string} [parser] The path to a parser or the package name of a parser.
 * @property {ParserOptions} [parserOptions] The parser options.
 * @property {string[]} [plugins] The plugin specifiers.
 * @property {string} [processor] The processor specifier.
 * @property {boolean} [reportUnusedDisableDirectives] The flag to report unused `eslint-disable` comments.
 * @property {boolean} [root] The root flag.
 * @property {Record<string, RuleConf>} [rules] The rule settings.
 * @property {Object} [settings] The shared settings.
 */

/**
 * @typedef {Object} OverrideConfigData
 * @property {Record<string, boolean>} [env] The environment settings.
 * @property {string | string[]} [excludedFiles] The glob patterns for excluded files.
 * @property {string | string[]} [extends] The path to other config files or the package name of shareable configs.
 * @property {string | string[]} files The glob patterns for target files.
 * @property {Record<string, GlobalConf>} [globals] The global variable settings.
 * @property {boolean} [noInlineConfig] The flag that disables directive comments.
 * @property {OverrideConfigData[]} [overrides] The override settings per kind of files.
 * @property {string} [parser] The path to a parser or the package name of a parser.
 * @property {ParserOptions} [parserOptions] The parser options.
 * @property {string[]} [plugins] The plugin specifiers.
 * @property {string} [processor] The processor specifier.
 * @property {boolean} [reportUnusedDisableDirectives] The flag to report unused `eslint-disable` comments.
 * @property {Record<string, RuleConf>} [rules] The rule settings.
 * @property {Object} [settings] The shared settings.
 */

/**
 * @typedef {Object} ParseResult
 * @property {Object} ast The AST.
 * @property {ScopeManager} [scopeManager] The scope manager of the AST.
 * @property {Record<string, any>} [services] The services that the parser provides.
 * @property {Record<string, string[]>} [visitorKeys] The visitor keys of the AST.
 */

/**
 * @typedef {Object} Parser
 * @property {(text:string, options:ParserOptions) => Object} parse The definition of global variables.
 * @property {(text:string, options:ParserOptions) => ParseResult} [parseForESLint] The parser options that will be enabled under this environment.
 */

/**
 * @typedef {Object} Environment
 * @property {Record<string, GlobalConf>} [globals] The definition of global variables.
 * @property {ParserOptions} [parserOptions] The parser options that will be enabled under this environment.
 */

/**
 * @typedef {Object} LintMessage
 * @property {number|undefined} column The 1-based column number.
 * @property {number} [endColumn] The 1-based column number of the end location.
 * @property {number} [endLine] The 1-based line number of the end location.
 * @property {boolean} [fatal] If `true` then this is a fatal error.
 * @property {{range:[number,number], text:string}} [fix] Information for autofix.
 * @property {number|undefined} line The 1-based line number.
 * @property {string} message The error message.
 * @property {string} [messageId] The ID of the message in the rule's meta.
 * @property {(string|null)} nodeType Type of node
 * @property {string|null} ruleId The ID of the rule which makes this message.
 * @property {0|1|2} severity The severity of this message.
 * @property {Array<{desc?: string, messageId?: string, fix: {range: [number, number], text: string}}>} [suggestions] Information for suggestions.
 */

/**
 * @typedef {Object} SuppressedLintMessage
 * @property {number|undefined} column The 1-based column number.
 * @property {number} [endColumn] The 1-based column number of the end location.
 * @property {number} [endLine] The 1-based line number of the end location.
 * @property {boolean} [fatal] If `true` then this is a fatal error.
 * @property {{range:[number,number], text:string}} [fix] Information for autofix.
 * @property {number|undefined} line The 1-based line number.
 * @property {string} message The error message.
 * @property {string} [messageId] The ID of the message in the rule's meta.
 * @property {(string|null)} nodeType Type of node
 * @property {string|null} ruleId The ID of the rule which makes this message.
 * @property {0|1|2} severity The severity of this message.
 * @property {Array<{kind: string, justification: string}>} suppressions The suppression info.
 * @property {Array<{desc?: string, messageId?: string, fix: {range: [number, number], text: string}}>} [suggestions] Information for suggestions.
 */

/**
 * @typedef {Object} SuggestionResult
 * @property {string} desc A short description.
 * @property {string} [messageId] Id referencing a message for the description.
 * @property {{ text: string, range: number[] }} fix fix result info
 */

/**
 * @typedef {Object} Processor
 * @property {(text:string, filename:string) => Array<string | { text:string, filename:string }>} [preprocess] The function to extract code blocks.
 * @property {(messagesList:LintMessage[][], filename:string) => LintMessage[]} [postprocess] The function to merge messages.
 * @property {boolean} [supportsAutofix] If `true` then it means the processor supports autofix.
 */

/**
 * @typedef {Object} RuleMetaDocs
 * @property {string} description The description of the rule.
 * @property {boolean} recommended If `true` then the rule is included in `eslint:recommended` preset.
 * @property {string} url The URL of the rule documentation.
 */

/**
 * @typedef {Object} RuleMeta
 * @property {boolean} [deprecated] If `true` then the rule has been deprecated.
 * @property {RuleMetaDocs} docs The document information of the rule.
 * @property {"code"|"whitespace"} [fixable] The autofix type.
 * @property {boolean} [hasSuggestions] If `true` then the rule provides suggestions.
 * @property {Record<string,string>} [messages] The messages the rule reports.
 * @property {string[]} [replacedBy] The IDs of the alternative rules.
 * @property {Array|Object} schema The option schema of the rule.
 * @property {"problem"|"suggestion"|"layout"} type The rule type.
 */

/**
 * @typedef {Object} Rule
 * @property {Function} create The factory of the rule.
 * @property {RuleMeta} meta The meta data of the rule.
 */

/**
 * @typedef {Object} Plugin
 * @property {Record<string, ConfigData>} [configs] The definition of plugin configs.
 * @property {Record<string, Environment>} [environments] The definition of plugin environments.
 * @property {Record<string, Processor>} [processors] The definition of plugin processors.
 * @property {Record<string, Function | Rule>} [rules] The definition of plugin rules.
 */

/**
 * Information of deprecated rules.
 * @typedef {Object} DeprecatedRuleInfo
 * @property {string} ruleId The rule ID.
 * @property {string[]} replacedBy The rule IDs that replace this deprecated rule.
 */

/**
 * A linting result.
 * @typedef {Object} LintResult
 * @property {string} filePath The path to the file that was linted.
 * @property {LintMessage[]} messages All of the messages for the result.
 * @property {SuppressedLintMessage[]} suppressedMessages All of the suppressed messages for the result.
 * @property {number} errorCount Number of errors for the result.
 * @property {number} fatalErrorCount Number of fatal errors for the result.
 * @property {number} warningCount Number of warnings for the result.
 * @property {number} fixableErrorCount Number of fixable errors for the result.
 * @property {number} fixableWarningCount Number of fixable warnings for the result.
 * @property {string} [source] The source code of the file that was linted.
 * @property {string} [output] The source code of the file that was linted, with as many fixes applied as possible.
 * @property {DeprecatedRuleInfo[]} usedDeprecatedRules The list of used deprecated rules.
 */

/**
 * Information provided when the maximum warning threshold is exceeded.
 * @typedef {Object} MaxWarningsExceeded
 * @property {number} maxWarnings Number of warnings to trigger nonzero exit code.
 * @property {number} foundWarnings Number of warnings found while linting.
 */

/**
 * Metadata about results for formatters.
 * @typedef {Object} ResultsMeta
 * @property {MaxWarningsExceeded} [maxWarningsExceeded] Present if the maxWarnings threshold was exceeded.
 */

/**
 * A formatter function.
 * @callback FormatterFunction
 * @param {LintResult[]} results The list of linting results.
 * @param {{cwd: string, maxWarningsExceeded?: MaxWarningsExceeded, rulesMeta: Record<string, RuleMeta>}} [context] A context object.
 * @returns {string | Promise<string>} Formatted text.
 */
