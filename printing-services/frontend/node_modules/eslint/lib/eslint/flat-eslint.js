/**
 * @fileoverview Main class using flat config
 * @author Nicholas C. Zakas
 */

"use strict";

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

// Note: Node.js 12 does not support fs/promises.
const fs = require("fs").promises;
const { existsSync } = require("fs");
const path = require("path");
const findUp = require("find-up");
const { version } = require("../../package.json");
const { Linter } = require("../linter");
const { getRuleFromConfig } = require("../config/flat-config-helpers");
const {
    Legacy: {
        ConfigOps: {
            getRuleSeverity
        },
        ModuleResolver,
        naming
    }
} = require("@eslint/eslintrc");

const {
    findFiles,
    getCacheFile,

    isNonEmptyString,
    isArrayOfNonEmptyString,

    createIgnoreResult,
    isErrorMessage,

    processOptions
} = require("./eslint-helpers");
const { pathToFileURL } = require("url");
const { FlatConfigArray } = require("../config/flat-config-array");
const LintResultCache = require("../cli-engine/lint-result-cache");

/*
 * This is necessary to allow overwriting writeFile for testing purposes.
 * We can just use fs/promises once we drop Node.js 12 support.
 */

//------------------------------------------------------------------------------
// Typedefs
//------------------------------------------------------------------------------

// For VSCode IntelliSense
/** @typedef {import("../shared/types").ConfigData} ConfigData */
/** @typedef {import("../shared/types").DeprecatedRuleInfo} DeprecatedRuleInfo */
/** @typedef {import("../shared/types").LintMessage} LintMessage */
/** @typedef {import("../shared/types").LintResult} LintResult */
/** @typedef {import("../shared/types").ParserOptions} ParserOptions */
/** @typedef {import("../shared/types").Plugin} Plugin */
/** @typedef {import("../shared/types").ResultsMeta} ResultsMeta */
/** @typedef {import("../shared/types").RuleConf} RuleConf */
/** @typedef {import("../shared/types").Rule} Rule */
/** @typedef {ReturnType<ConfigArray.extractConfig>} ExtractedConfig */

/**
 * The options with which to configure the ESLint instance.
 * @typedef {Object} FlatESLintOptions
 * @property {boolean} [allowInlineConfig] Enable or disable inline configuration comments.
 * @property {ConfigData} [baseConfig] Base config object, extended by all configs used with this instance
 * @property {boolean} [cache] Enable result caching.
 * @property {string} [cacheLocation] The cache file to use instead of .eslintcache.
 * @property {"metadata" | "content"} [cacheStrategy] The strategy used to detect changed files.
 * @property {string} [cwd] The value to use for the current working directory.
 * @property {boolean} [errorOnUnmatchedPattern] If `false` then `ESLint#lintFiles()` doesn't throw even if no target files found. Defaults to `true`.
 * @property {boolean|Function} [fix] Execute in autofix mode. If a function, should return a boolean.
 * @property {string[]} [fixTypes] Array of rule types to apply fixes for.
 * @property {boolean} [globInputPaths] Set to false to skip glob resolution of input file paths to lint (default: true). If false, each input file paths is assumed to be a non-glob path to an existing file.
 * @property {boolean} [ignore] False disables all ignore patterns except for the default ones.
 * @property {string[]} [ignorePatterns] Ignore file patterns to use in addition to config ignores. These patterns are relative to `cwd`.
 * @property {ConfigData} [overrideConfig] Override config object, overrides all configs used with this instance
 * @property {boolean|string} [overrideConfigFile] Searches for default config file when falsy;
 *      doesn't do any config file lookup when `true`; considered to be a config filename
 *      when a string.
 * @property {Record<string,Plugin>} [plugins] An array of plugin implementations.
 * @property {boolean} warnIgnored Show warnings when the file list includes ignored files
 */

//------------------------------------------------------------------------------
// Helpers
//------------------------------------------------------------------------------

const FLAT_CONFIG_FILENAMES = [
    "eslint.config.js",
    "eslint.config.mjs",
    "eslint.config.cjs"
];
const debug = require("debug")("eslint:flat-eslint");
const removedFormatters = new Set(["table", "codeframe"]);
const privateMembers = new WeakMap();
const importedConfigFileModificationTime = new Map();

/**
 * It will calculate the error and warning count for collection of messages per file
 * @param {LintMessage[]} messages Collection of messages
 * @returns {Object} Contains the stats
 * @private
 */
function calculateStatsPerFile(messages) {
    const stat = {
        errorCount: 0,
        fatalErrorCount: 0,
        warningCount: 0,
        fixableErrorCount: 0,
        fixableWarningCount: 0
    };

    for (let i = 0; i < messages.length; i++) {
        const message = messages[i];

        if (message.fatal || message.severity === 2) {
            stat.errorCount++;
            if (message.fatal) {
                stat.fatalErrorCount++;
            }
            if (message.fix) {
                stat.fixableErrorCount++;
            }
        } else {
            stat.warningCount++;
            if (message.fix) {
                stat.fixableWarningCount++;
            }
        }
    }
    return stat;
}

/**
 * Create rulesMeta object.
 * @param {Map<string,Rule>} rules a map of rules from which to generate the object.
 * @returns {Object} metadata for all enabled rules.
 */
function createRulesMeta(rules) {
    return Array.from(rules).reduce((retVal, [id, rule]) => {
        retVal[id] = rule.meta;
        return retVal;
    }, {});
}

/**
 * Return the absolute path of a file named `"__placeholder__.js"` in a given directory.
 * This is used as a replacement for a missing file path.
 * @param {string} cwd An absolute directory path.
 * @returns {string} The absolute path of a file named `"__placeholder__.js"` in the given directory.
 */
function getPlaceholderPath(cwd) {
    return path.join(cwd, "__placeholder__.js");
}

/** @type {WeakMap<ExtractedConfig, DeprecatedRuleInfo[]>} */
const usedDeprecatedRulesCache = new WeakMap();

/**
 * Create used deprecated rule list.
 * @param {CLIEngine} eslint The CLIEngine instance.
 * @param {string} maybeFilePath The absolute path to a lint target file or `"<text>"`.
 * @returns {DeprecatedRuleInfo[]} The used deprecated rule list.
 */
function getOrFindUsedDeprecatedRules(eslint, maybeFilePath) {
    const {
        configs,
        options: { cwd }
    } = privateMembers.get(eslint);
    const filePath = path.isAbsolute(maybeFilePath)
        ? maybeFilePath
        : getPlaceholderPath(cwd);
    const config = configs.getConfig(filePath);

    // Most files use the same config, so cache it.
    if (config && !usedDeprecatedRulesCache.has(config)) {
        const retv = [];

        if (config.rules) {
            for (const [ruleId, ruleConf] of Object.entries(config.rules)) {
                if (getRuleSeverity(ruleConf) === 0) {
                    continue;
                }
                const rule = getRuleFromConfig(ruleId, config);
                const meta = rule && rule.meta;

                if (meta && meta.deprecated) {
                    retv.push({ ruleId, replacedBy: meta.replacedBy || [] });
                }
            }
        }


        usedDeprecatedRulesCache.set(config, Object.freeze(retv));
    }

    return config ? usedDeprecatedRulesCache.get(config) : Object.freeze([]);
}

/**
 * Processes the linting results generated by a CLIEngine linting report to
 * match the ESLint class's API.
 * @param {CLIEngine} eslint The CLIEngine instance.
 * @param {CLIEngineLintReport} report The CLIEngine linting report to process.
 * @returns {LintResult[]} The processed linting results.
 */
function processLintReport(eslint, { results }) {
    const descriptor = {
        configurable: true,
        enumerable: true,
        get() {
            return getOrFindUsedDeprecatedRules(eslint, this.filePath);
        }
    };

    for (const result of results) {
        Object.defineProperty(result, "usedDeprecatedRules", descriptor);
    }

    return results;
}

/**
 * An Array.prototype.sort() compatible compare function to order results by their file path.
 * @param {LintResult} a The first lint result.
 * @param {LintResult} b The second lint result.
 * @returns {number} An integer representing the order in which the two results should occur.
 */
function compareResultsByFilePath(a, b) {
    if (a.filePath < b.filePath) {
        return -1;
    }

    if (a.filePath > b.filePath) {
        return 1;
    }

    return 0;
}

/**
 * Searches from the current working directory up until finding the
 * given flat config filename.
 * @param {string} cwd The current working directory to search from.
 * @returns {Promise<string|undefined>} The filename if found or `undefined` if not.
 */
function findFlatConfigFile(cwd) {
    return findUp(
        FLAT_CONFIG_FILENAMES,
        { cwd }
    );
}

/**
 * Load the config array from the given filename.
 * @param {string} filePath The filename to load from.
 * @returns {Promise<any>} The config loaded from the config file.
 */
async function loadFlatConfigFile(filePath) {
    debug(`Loading config from ${filePath}`);

    const fileURL = pathToFileURL(filePath);

    debug(`Config file URL is ${fileURL}`);

    const mtime = (await fs.stat(filePath)).mtime.getTime();

    /*
     * Append a query with the config file's modification time (`mtime`) in order
     * to import the current version of the config file. Without the query, `import()` would
     * cache the config file module by the pathname only, and then always return
     * the same version (the one that was actual when the module was imported for the first time).
     *
     * This ensures that the config file module is loaded and executed again
     * if it has been changed since the last time it was imported.
     * If it hasn't been changed, `import()` will just return the cached version.
     *
     * Note that we should not overuse queries (e.g., by appending the current time
     * to always reload the config file module) as that could cause memory leaks
     * because entries are never removed from the import cache.
     */
    fileURL.searchParams.append("mtime", mtime);

    /*
     * With queries, we can bypass the import cache. However, when import-ing a CJS module,
     * Node.js uses the require infrastructure under the hood. That includes the require cache,
     * which caches the config file module by its file path (queries have no effect).
     * Therefore, we also need to clear the require cache before importing the config file module.
     * In order to get the same behavior with ESM and CJS config files, in particular - to reload
     * the config file only if it has been changed, we track file modification times and clear
     * the require cache only if the file has been changed.
     */
    if (importedConfigFileModificationTime.get(filePath) !== mtime) {
        delete require.cache[filePath];
    }

    const config = (await import(fileURL)).default;

    importedConfigFileModificationTime.set(filePath, mtime);

    return config;
}

/**
 * Determines which config file to use. This is determined by seeing if an
 * override config file was passed, and if so, using it; otherwise, as long
 * as override config file is not explicitly set to `false`, it will search
 * upwards from the cwd for a file named `eslint.config.js`.
 * @param {import("./eslint").ESLintOptions} options The ESLint instance options.
 * @returns {{configFilePath:string|undefined,basePath:string,error:Error|null}} Location information for
 *      the config file.
 */
async function locateConfigFileToUse({ configFile, cwd }) {

    // determine where to load config file from
    let configFilePath;
    let basePath = cwd;
    let error = null;

    if (typeof configFile === "string") {
        debug(`Override config file path is ${configFile}`);
        configFilePath = path.resolve(cwd, configFile);
    } else if (configFile !== false) {
        debug("Searching for eslint.config.js");
        configFilePath = await findFlatConfigFile(cwd);

        if (configFilePath) {
            basePath = path.resolve(path.dirname(configFilePath));
        } else {
            error = new Error("Could not find config file.");
        }

    }

    return {
        configFilePath,
        basePath,
        error
    };

}

/**
 * Calculates the config array for this run based on inputs.
 * @param {FlatESLint} eslint The instance to create the config array for.
 * @param {import("./eslint").ESLintOptions} options The ESLint instance options.
 * @returns {FlatConfigArray} The config array for `eslint``.
 */
async function calculateConfigArray(eslint, {
    cwd,
    baseConfig,
    overrideConfig,
    configFile,
    ignore: shouldIgnore,
    ignorePatterns
}) {

    // check for cached instance
    const slots = privateMembers.get(eslint);

    if (slots.configs) {
        return slots.configs;
    }

    const { configFilePath, basePath, error } = await locateConfigFileToUse({ configFile, cwd });

    // config file is required to calculate config
    if (error) {
        throw error;
    }

    const configs = new FlatConfigArray(baseConfig || [], { basePath, shouldIgnore });

    // load config file
    if (configFilePath) {
        const fileConfig = await loadFlatConfigFile(configFilePath);

        if (Array.isArray(fileConfig)) {
            configs.push(...fileConfig);
        } else {
            configs.push(fileConfig);
        }
    }

    // add in any configured defaults
    configs.push(...slots.defaultConfigs);

    // append command line ignore patterns
    if (ignorePatterns && ignorePatterns.length > 0) {

        let relativeIgnorePatterns;

        /*
         * If the config file basePath is different than the cwd, then
         * the ignore patterns won't work correctly. Here, we adjust the
         * ignore pattern to include the correct relative path. Patterns
         * passed as `ignorePatterns` are relative to the cwd, whereas
         * the config file basePath can be an ancestor of the cwd.
         */
        if (basePath === cwd) {
            relativeIgnorePatterns = ignorePatterns;
        } else {

            const relativeIgnorePath = path.relative(basePath, cwd);

            relativeIgnorePatterns = ignorePatterns.map(pattern => {
                const negated = pattern.startsWith("!");
                const basePattern = negated ? pattern.slice(1) : pattern;

                return (negated ? "!" : "") +
                path.posix.join(relativeIgnorePath, basePattern);
            });
        }

        /*
         * Ignore patterns are added to the end of the config array
         * so they can override default ignores.
         */
        configs.push({
            ignores: relativeIgnorePatterns
        });
    }

    if (overrideConfig) {
        if (Array.isArray(overrideConfig)) {
            configs.push(...overrideConfig);
        } else {
            configs.push(overrideConfig);
        }
    }

    await configs.normalize();

    // cache the config array for this instance
    slots.configs = configs;

    return configs;
}

/**
 * Processes an source code using ESLint.
 * @param {Object} config The config object.
 * @param {string} config.text The source code to verify.
 * @param {string} config.cwd The path to the current working directory.
 * @param {string|undefined} config.filePath The path to the file of `text`. If this is undefined, it uses `<text>`.
 * @param {FlatConfigArray} config.configs The config.
 * @param {boolean} config.fix If `true` then it does fix.
 * @param {boolean} config.allowInlineConfig If `true` then it uses directive comments.
 * @param {Linter} config.linter The linter instance to verify.
 * @returns {LintResult} The result of linting.
 * @private
 */
function verifyText({
    text,
    cwd,
    filePath: providedFilePath,
    configs,
    fix,
    allowInlineConfig,
    linter
}) {
    const filePath = providedFilePath || "<text>";

    debug(`Lint ${filePath}`);

    /*
     * Verify.
     * `config.extractConfig(filePath)` requires an absolute path, but `linter`
     * doesn't know CWD, so it gives `linter` an absolute path always.
     */
    const filePathToVerify = filePath === "<text>" ? getPlaceholderPath(cwd) : filePath;
    const { fixed, messages, output } = linter.verifyAndFix(
        text,
        configs,
        {
            allowInlineConfig,
            filename: filePathToVerify,
            fix,

            /**
             * Check if the linter should adopt a given code block or not.
             * @param {string} blockFilename The virtual filename of a code block.
             * @returns {boolean} `true` if the linter should adopt the code block.
             */
            filterCodeBlock(blockFilename) {
                return configs.getConfig(blockFilename) !== void 0;
            }
        }
    );

    // Tweak and return.
    const result = {
        filePath: filePath === "<text>" ? filePath : path.resolve(filePath),
        messages,
        suppressedMessages: linter.getSuppressedMessages(),
        ...calculateStatsPerFile(messages)
    };

    if (fixed) {
        result.output = output;
    }

    if (
        result.errorCount + result.warningCount > 0 &&
        typeof result.output === "undefined"
    ) {
        result.source = text;
    }

    return result;
}

/**
 * Checks whether a message's rule type should be fixed.
 * @param {LintMessage} message The message to check.
 * @param {FlatConfig} config The config for the file that generated the message.
 * @param {string[]} fixTypes An array of fix types to check.
 * @returns {boolean} Whether the message should be fixed.
 */
function shouldMessageBeFixed(message, config, fixTypes) {
    if (!message.ruleId) {
        return fixTypes.has("directive");
    }

    const rule = message.ruleId && getRuleFromConfig(message.ruleId, config);

    return Boolean(rule && rule.meta && fixTypes.has(rule.meta.type));
}

/**
 * Creates an error to be thrown when an array of results passed to `getRulesMetaForResults` was not created by the current engine.
 * @returns {TypeError} An error object.
 */
function createExtraneousResultsError() {
    return new TypeError("Results object was not created from this ESLint instance.");
}

/**
 * Creates a fixer function based on the provided fix, fixTypesSet, and config.
 * @param {Function|boolean} fix The original fix option.
 * @param {Set<string>} fixTypesSet A set of fix types to filter messages for fixing.
 * @param {FlatConfig} config The config for the file that generated the message.
 * @returns {Function|boolean} The fixer function or the original fix value.
 */
function getFixerForFixTypes(fix, fixTypesSet, config) {
    if (!fix || !fixTypesSet) {
        return fix;
    }

    const originalFix = (typeof fix === "function") ? fix : () => true;

    return message => shouldMessageBeFixed(message, config, fixTypesSet) && originalFix(message);
}

//-----------------------------------------------------------------------------
// Main API
//-----------------------------------------------------------------------------

/**
 * Primary Node.js API for ESLint.
 */
class FlatESLint {

    /**
     * Creates a new instance of the main ESLint API.
     * @param {FlatESLintOptions} options The options for this instance.
     */
    constructor(options = {}) {

        const defaultConfigs = [];
        const processedOptions = processOptions(options);
        const linter = new Linter({
            cwd: processedOptions.cwd,
            configType: "flat"
        });

        const cacheFilePath = getCacheFile(
            processedOptions.cacheLocation,
            processedOptions.cwd
        );

        const lintResultCache = processedOptions.cache
            ? new LintResultCache(cacheFilePath, processedOptions.cacheStrategy)
            : null;

        privateMembers.set(this, {
            options: processedOptions,
            linter,
            cacheFilePath,
            lintResultCache,
            defaultConfigs,
            configs: null
        });

        /**
         * If additional plugins are passed in, add that to the default
         * configs for this instance.
         */
        if (options.plugins) {

            const plugins = {};

            for (const [pluginName, plugin] of Object.entries(options.plugins)) {
                plugins[naming.getShorthandName(pluginName, "eslint-plugin")] = plugin;
            }

            defaultConfigs.push({
                plugins
            });
        }

    }

    /**
     * The version text.
     * @type {string}
     */
    static get version() {
        return version;
    }

    /**
     * Outputs fixes from the given results to files.
     * @param {LintResult[]} results The lint results.
     * @returns {Promise<void>} Returns a promise that is used to track side effects.
     */
    static async outputFixes(results) {
        if (!Array.isArray(results)) {
            throw new Error("'results' must be an array");
        }

        await Promise.all(
            results
                .filter(result => {
                    if (typeof result !== "object" || result === null) {
                        throw new Error("'results' must include only objects");
                    }
                    return (
                        typeof result.output === "string" &&
                        path.isAbsolute(result.filePath)
                    );
                })
                .map(r => fs.writeFile(r.filePath, r.output))
        );
    }

    /**
     * Returns results that only contains errors.
     * @param {LintResult[]} results The results to filter.
     * @returns {LintResult[]} The filtered results.
     */
    static getErrorResults(results) {
        const filtered = [];

        results.forEach(result => {
            const filteredMessages = result.messages.filter(isErrorMessage);
            const filteredSuppressedMessages = result.suppressedMessages.filter(isErrorMessage);

            if (filteredMessages.length > 0) {
                filtered.push({
                    ...result,
                    messages: filteredMessages,
                    suppressedMessages: filteredSuppressedMessages,
                    errorCount: filteredMessages.length,
                    warningCount: 0,
                    fixableErrorCount: result.fixableErrorCount,
                    fixableWarningCount: 0
                });
            }
        });

        return filtered;
    }

    /**
     * Returns meta objects for each rule represented in the lint results.
     * @param {LintResult[]} results The results to fetch rules meta for.
     * @returns {Object} A mapping of ruleIds to rule meta objects.
     * @throws {TypeError} When the results object wasn't created from this ESLint instance.
     * @throws {TypeError} When a plugin or rule is missing.
     */
    getRulesMetaForResults(results) {

        // short-circuit simple case
        if (results.length === 0) {
            return {};
        }

        const resultRules = new Map();
        const {
            configs,
            options: { cwd }
        } = privateMembers.get(this);

        /*
         * We can only accurately return rules meta information for linting results if the
         * results were created by this instance. Otherwise, the necessary rules data is
         * not available. So if the config array doesn't already exist, just throw an error
         * to let the user know we can't do anything here.
         */
        if (!configs) {
            throw createExtraneousResultsError();
        }

        for (const result of results) {

            /*
             * Normalize filename for <text>.
             */
            const filePath = result.filePath === "<text>"
                ? getPlaceholderPath(cwd) : result.filePath;
            const allMessages = result.messages.concat(result.suppressedMessages);

            for (const { ruleId } of allMessages) {
                if (!ruleId) {
                    continue;
                }

                /*
                 * All of the plugin and rule information is contained within the
                 * calculated config for the given file.
                 */
                const config = configs.getConfig(filePath);

                if (!config) {
                    throw createExtraneousResultsError();
                }
                const rule = getRuleFromConfig(ruleId, config);

                // ignore unknown rules
                if (rule) {
                    resultRules.set(ruleId, rule);
                }
            }
        }

        return createRulesMeta(resultRules);
    }

    /**
     * Executes the current configuration on an array of file and directory names.
     * @param {string|string[]} patterns An array of file and directory names.
     * @returns {Promise<LintResult[]>} The results of linting the file patterns given.
     */
    async lintFiles(patterns) {
        if (!isNonEmptyString(patterns) && !isArrayOfNonEmptyString(patterns)) {
            throw new Error("'patterns' must be a non-empty string or an array of non-empty strings");
        }

        const {
            cacheFilePath,
            lintResultCache,
            linter,
            options: eslintOptions
        } = privateMembers.get(this);
        const configs = await calculateConfigArray(this, eslintOptions);
        const {
            allowInlineConfig,
            cache,
            cwd,
            fix,
            fixTypes,
            globInputPaths,
            errorOnUnmatchedPattern,
            warnIgnored
        } = eslintOptions;
        const startTime = Date.now();
        const fixTypesSet = fixTypes ? new Set(fixTypes) : null;

        // Delete cache file; should this be done here?
        if (!cache && cacheFilePath) {
            debug(`Deleting cache file at ${cacheFilePath}`);

            try {
                await fs.unlink(cacheFilePath);
            } catch (error) {
                const errorCode = error && error.code;

                // Ignore errors when no such file exists or file system is read only (and cache file does not exist)
                if (errorCode !== "ENOENT" && !(errorCode === "EROFS" && !existsSync(cacheFilePath))) {
                    throw error;
                }
            }
        }

        const filePaths = await findFiles({
            patterns: typeof patterns === "string" ? [patterns] : patterns,
            cwd,
            globInputPaths,
            configs,
            errorOnUnmatchedPattern
        });

        debug(`${filePaths.length} files found in: ${Date.now() - startTime}ms`);

        /*
         * Because we need to process multiple files, including reading from disk,
         * it is most efficient to start by reading each file via promises so that
         * they can be done in parallel. Then, we can lint the returned text. This
         * ensures we are waiting the minimum amount of time in between lints.
         */
        const results = await Promise.all(

            filePaths.map(filePath => {

                const config = configs.getConfig(filePath);

                /*
                 * If a filename was entered that cannot be matched
                 * to a config, then notify the user.
                 */
                if (!config) {
                    if (warnIgnored) {
                        return createIgnoreResult(filePath, cwd);
                    }

                    return void 0;
                }

                // Skip if there is cached result.
                if (lintResultCache) {
                    const cachedResult =
                        lintResultCache.getCachedLintResults(filePath, config);

                    if (cachedResult) {
                        const hadMessages =
                            cachedResult.messages &&
                            cachedResult.messages.length > 0;

                        if (hadMessages && fix) {
                            debug(`Reprocessing cached file to allow autofix: ${filePath}`);
                        } else {
                            debug(`Skipping file since it hasn't changed: ${filePath}`);
                            return cachedResult;
                        }
                    }
                }


                // set up fixer for fixTypes if necessary
                const fixer = getFixerForFixTypes(fix, fixTypesSet, config);

                return fs.readFile(filePath, "utf8")
                    .then(text => {

                        // do the linting
                        const result = verifyText({
                            text,
                            filePath,
                            configs,
                            cwd,
                            fix: fixer,
                            allowInlineConfig,
                            linter
                        });

                        /*
                         * Store the lint result in the LintResultCache.
                         * NOTE: The LintResultCache will remove the file source and any
                         * other properties that are difficult to serialize, and will
                         * hydrate those properties back in on future lint runs.
                         */
                        if (lintResultCache) {
                            lintResultCache.setCachedLintResults(filePath, config, result);
                        }

                        return result;
                    });

            })
        );

        // Persist the cache to disk.
        if (lintResultCache) {
            lintResultCache.reconcile();
        }

        const finalResults = results.filter(result => !!result);

        return processLintReport(this, {
            results: finalResults
        });
    }

    /**
     * Executes the current configuration on text.
     * @param {string} code A string of JavaScript code to lint.
     * @param {Object} [options] The options.
     * @param {string} [options.filePath] The path to the file of the source code.
     * @param {boolean} [options.warnIgnored] When set to true, warn if given filePath is an ignored path.
     * @returns {Promise<LintResult[]>} The results of linting the string of code given.
     */
    async lintText(code, options = {}) {

        // Parameter validation

        if (typeof code !== "string") {
            throw new Error("'code' must be a string");
        }

        if (typeof options !== "object") {
            throw new Error("'options' must be an object, null, or undefined");
        }

        // Options validation

        const {
            filePath,
            warnIgnored,
            ...unknownOptions
        } = options || {};

        const unknownOptionKeys = Object.keys(unknownOptions);

        if (unknownOptionKeys.length > 0) {
            throw new Error(`'options' must not include the unknown option(s): ${unknownOptionKeys.join(", ")}`);
        }

        if (filePath !== void 0 && !isNonEmptyString(filePath)) {
            throw new Error("'options.filePath' must be a non-empty string or undefined");
        }

        if (typeof warnIgnored !== "boolean" && typeof warnIgnored !== "undefined") {
            throw new Error("'options.warnIgnored' must be a boolean or undefined");
        }

        // Now we can get down to linting

        const {
            linter,
            options: eslintOptions
        } = privateMembers.get(this);
        const configs = await calculateConfigArray(this, eslintOptions);
        const {
            allowInlineConfig,
            cwd,
            fix,
            fixTypes,
            warnIgnored: constructorWarnIgnored
        } = eslintOptions;
        const results = [];
        const startTime = Date.now();
        const fixTypesSet = fixTypes ? new Set(fixTypes) : null;
        const resolvedFilename = path.resolve(cwd, filePath || "__placeholder__.js");
        const config = configs.getConfig(resolvedFilename);

        const fixer = getFixerForFixTypes(fix, fixTypesSet, config);

        // Clear the last used config arrays.
        if (resolvedFilename && await this.isPathIgnored(resolvedFilename)) {
            const shouldWarnIgnored = typeof warnIgnored === "boolean" ? warnIgnored : constructorWarnIgnored;

            if (shouldWarnIgnored) {
                results.push(createIgnoreResult(resolvedFilename, cwd));
            }
        } else {

            // Do lint.
            results.push(verifyText({
                text: code,
                filePath: resolvedFilename.endsWith("__placeholder__.js") ? "<text>" : resolvedFilename,
                configs,
                cwd,
                fix: fixer,
                allowInlineConfig,
                linter
            }));
        }

        debug(`Linting complete in: ${Date.now() - startTime}ms`);

        return processLintReport(this, {
            results
        });

    }

    /**
     * Returns the formatter representing the given formatter name.
     * @param {string} [name] The name of the formatter to load.
     * The following values are allowed:
     * - `undefined` ... Load `stylish` builtin formatter.
     * - A builtin formatter name ... Load the builtin formatter.
     * - A third-party formatter name:
     *   - `foo` → `eslint-formatter-foo`
     *   - `@foo` → `@foo/eslint-formatter`
     *   - `@foo/bar` → `@foo/eslint-formatter-bar`
     * - A file path ... Load the file.
     * @returns {Promise<Formatter>} A promise resolving to the formatter object.
     * This promise will be rejected if the given formatter was not found or not
     * a function.
     */
    async loadFormatter(name = "stylish") {
        if (typeof name !== "string") {
            throw new Error("'name' must be a string");
        }

        // replace \ with / for Windows compatibility
        const normalizedFormatName = name.replace(/\\/gu, "/");
        const namespace = naming.getNamespaceFromTerm(normalizedFormatName);

        // grab our options
        const { cwd } = privateMembers.get(this).options;


        let formatterPath;

        // if there's a slash, then it's a file (TODO: this check seems dubious for scoped npm packages)
        if (!namespace && normalizedFormatName.includes("/")) {
            formatterPath = path.resolve(cwd, normalizedFormatName);
        } else {
            try {
                const npmFormat = naming.normalizePackageName(normalizedFormatName, "eslint-formatter");

                // TODO: This is pretty dirty...would be nice to clean up at some point.
                formatterPath = ModuleResolver.resolve(npmFormat, getPlaceholderPath(cwd));
            } catch {
                formatterPath = path.resolve(__dirname, "../", "cli-engine", "formatters", `${normalizedFormatName}.js`);
            }
        }

        let formatter;

        try {
            formatter = (await import(pathToFileURL(formatterPath))).default;
        } catch (ex) {

            // check for formatters that have been removed
            if (removedFormatters.has(name)) {
                ex.message = `The ${name} formatter is no longer part of core ESLint. Install it manually with \`npm install -D eslint-formatter-${name}\``;
            } else {
                ex.message = `There was a problem loading formatter: ${formatterPath}\nError: ${ex.message}`;
            }

            throw ex;
        }


        if (typeof formatter !== "function") {
            throw new TypeError(`Formatter must be a function, but got a ${typeof formatter}.`);
        }

        const eslint = this;

        return {

            /**
             * The main formatter method.
             * @param {LintResults[]} results The lint results to format.
             * @param {ResultsMeta} resultsMeta Warning count and max threshold.
             * @returns {string} The formatted lint results.
             */
            format(results, resultsMeta) {
                let rulesMeta = null;

                results.sort(compareResultsByFilePath);

                return formatter(results, {
                    ...resultsMeta,
                    cwd,
                    get rulesMeta() {
                        if (!rulesMeta) {
                            rulesMeta = eslint.getRulesMetaForResults(results);
                        }

                        return rulesMeta;
                    }
                });
            }
        };
    }

    /**
     * Returns a configuration object for the given file based on the CLI options.
     * This is the same logic used by the ESLint CLI executable to determine
     * configuration for each file it processes.
     * @param {string} filePath The path of the file to retrieve a config object for.
     * @returns {Promise<ConfigData|undefined>} A configuration object for the file
     *      or `undefined` if there is no configuration data for the object.
     */
    async calculateConfigForFile(filePath) {
        if (!isNonEmptyString(filePath)) {
            throw new Error("'filePath' must be a non-empty string");
        }
        const options = privateMembers.get(this).options;
        const absolutePath = path.resolve(options.cwd, filePath);
        const configs = await calculateConfigArray(this, options);

        return configs.getConfig(absolutePath);
    }

    /**
     * Finds the config file being used by this instance based on the options
     * passed to the constructor.
     * @returns {string|undefined} The path to the config file being used or
     *      `undefined` if no config file is being used.
     */
    async findConfigFile() {
        const options = privateMembers.get(this).options;
        const { configFilePath } = await locateConfigFileToUse(options);

        return configFilePath;
    }

    /**
     * Checks if a given path is ignored by ESLint.
     * @param {string} filePath The path of the file to check.
     * @returns {Promise<boolean>} Whether or not the given path is ignored.
     */
    async isPathIgnored(filePath) {
        const config = await this.calculateConfigForFile(filePath);

        return config === void 0;
    }
}

/**
 * The type of configuration used by this class.
 * @type {string}
 * @static
 */
FlatESLint.configType = "flat";

/**
 * Returns whether flat config should be used.
 * @param {Object} [options] The options for this function.
 * @param {string} [options.cwd] The current working directory.
 * @returns {Promise<boolean>} Whether flat config should be used.
 */
async function shouldUseFlatConfig({ cwd = process.cwd() } = {}) {
    switch (process.env.ESLINT_USE_FLAT_CONFIG) {
        case "true":
            return true;
        case "false":
            return false;
        default:

            /*
             * If neither explicitly enabled nor disabled, then use the presence
             * of a flat config file to determine enablement.
             */
            return !!(await findFlatConfigFile(cwd));
    }
}

//------------------------------------------------------------------------------
// Public Interface
//------------------------------------------------------------------------------

module.exports = {
    FlatESLint,
    shouldUseFlatConfig
};
