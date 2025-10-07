/**
 * @fileoverview Helper functions for ESLint class
 * @author Nicholas C. Zakas
 */

"use strict";

//-----------------------------------------------------------------------------
// Requirements
//-----------------------------------------------------------------------------

const path = require("path");
const fs = require("fs");
const fsp = fs.promises;
const isGlob = require("is-glob");
const hash = require("../cli-engine/hash");
const minimatch = require("minimatch");
const fswalk = require("@nodelib/fs.walk");
const globParent = require("glob-parent");
const isPathInside = require("is-path-inside");

//-----------------------------------------------------------------------------
// Fixup references
//-----------------------------------------------------------------------------

const Minimatch = minimatch.Minimatch;
const MINIMATCH_OPTIONS = { dot: true };

//-----------------------------------------------------------------------------
// Types
//-----------------------------------------------------------------------------

/**
 * @typedef {Object} GlobSearch
 * @property {Array<string>} patterns The normalized patterns to use for a search.
 * @property {Array<string>} rawPatterns The patterns as entered by the user
 *      before doing any normalization.
 */

//-----------------------------------------------------------------------------
// Errors
//-----------------------------------------------------------------------------

/**
 * The error type when no files match a glob.
 */
class NoFilesFoundError extends Error {

    /**
     * @param {string} pattern The glob pattern which was not found.
     * @param {boolean} globEnabled If `false` then the pattern was a glob pattern, but glob was disabled.
     */
    constructor(pattern, globEnabled) {
        super(`No files matching '${pattern}' were found${!globEnabled ? " (glob was disabled)" : ""}.`);
        this.messageTemplate = "file-not-found";
        this.messageData = { pattern, globDisabled: !globEnabled };
    }
}

/**
 * The error type when a search fails to match multiple patterns.
 */
class UnmatchedSearchPatternsError extends Error {

    /**
     * @param {Object} options The options for the error.
     * @param {string} options.basePath The directory that was searched.
     * @param {Array<string>} options.unmatchedPatterns The glob patterns
     *      which were not found.
     * @param {Array<string>} options.patterns The glob patterns that were
     *      searched.
     * @param {Array<string>} options.rawPatterns The raw glob patterns that
     *      were searched.
     */
    constructor({ basePath, unmatchedPatterns, patterns, rawPatterns }) {
        super(`No files matching '${rawPatterns}' in '${basePath}' were found.`);
        this.basePath = basePath;
        this.unmatchedPatterns = unmatchedPatterns;
        this.patterns = patterns;
        this.rawPatterns = rawPatterns;
    }
}

/**
 * The error type when there are files matched by a glob, but all of them have been ignored.
 */
class AllFilesIgnoredError extends Error {

    /**
     * @param {string} pattern The glob pattern which was not found.
     */
    constructor(pattern) {
        super(`All files matched by '${pattern}' are ignored.`);
        this.messageTemplate = "all-files-ignored";
        this.messageData = { pattern };
    }
}


//-----------------------------------------------------------------------------
// General Helpers
//-----------------------------------------------------------------------------

/**
 * Check if a given value is a non-empty string or not.
 * @param {any} x The value to check.
 * @returns {boolean} `true` if `x` is a non-empty string.
 */
function isNonEmptyString(x) {
    return typeof x === "string" && x.trim() !== "";
}

/**
 * Check if a given value is an array of non-empty strings or not.
 * @param {any} x The value to check.
 * @returns {boolean} `true` if `x` is an array of non-empty strings.
 */
function isArrayOfNonEmptyString(x) {
    return Array.isArray(x) && x.every(isNonEmptyString);
}

//-----------------------------------------------------------------------------
// File-related Helpers
//-----------------------------------------------------------------------------

/**
 * Normalizes slashes in a file pattern to posix-style.
 * @param {string} pattern The pattern to replace slashes in.
 * @returns {string} The pattern with slashes normalized.
 */
function normalizeToPosix(pattern) {
    return pattern.replace(/\\/gu, "/");
}

/**
 * Check if a string is a glob pattern or not.
 * @param {string} pattern A glob pattern.
 * @returns {boolean} `true` if the string is a glob pattern.
 */
function isGlobPattern(pattern) {
    return isGlob(path.sep === "\\" ? normalizeToPosix(pattern) : pattern);
}


/**
 * Determines if a given glob pattern will return any results.
 * Used primarily to help with useful error messages.
 * @param {Object} options The options for the function.
 * @param {string} options.basePath The directory to search.
 * @param {string} options.pattern A glob pattern to match.
 * @returns {Promise<boolean>} True if there is a glob match, false if not.
 */
function globMatch({ basePath, pattern }) {

    let found = false;
    const patternToUse = path.isAbsolute(pattern)
        ? normalizeToPosix(path.relative(basePath, pattern))
        : pattern;

    const matcher = new Minimatch(patternToUse, MINIMATCH_OPTIONS);

    const fsWalkSettings = {

        deepFilter(entry) {
            const relativePath = normalizeToPosix(path.relative(basePath, entry.path));

            return !found && matcher.match(relativePath, true);
        },

        entryFilter(entry) {
            if (found || entry.dirent.isDirectory()) {
                return false;
            }

            const relativePath = normalizeToPosix(path.relative(basePath, entry.path));

            if (matcher.match(relativePath)) {
                found = true;
                return true;
            }

            return false;
        }
    };

    return new Promise(resolve => {

        // using a stream so we can exit early because we just need one match
        const globStream = fswalk.walkStream(basePath, fsWalkSettings);

        globStream.on("data", () => {
            globStream.destroy();
            resolve(true);
        });

        // swallow errors as they're not important here
        globStream.on("error", () => { });

        globStream.on("end", () => {
            resolve(false);
        });
        globStream.read();
    });

}

/**
 * Searches a directory looking for matching glob patterns. This uses
 * the config array's logic to determine if a directory or file should
 * be ignored, so it is consistent with how ignoring works throughout
 * ESLint.
 * @param {Object} options The options for this function.
 * @param {string} options.basePath The directory to search.
 * @param {Array<string>} options.patterns An array of glob patterns
 *      to match.
 * @param {Array<string>} options.rawPatterns An array of glob patterns
 *      as the user inputted them. Used for errors.
 * @param {FlatConfigArray} options.configs The config array to use for
 *      determining what to ignore.
 * @param {boolean} options.errorOnUnmatchedPattern Determines if an error
 *      should be thrown when a pattern is unmatched.
 * @returns {Promise<Array<string>>} An array of matching file paths
 *      or an empty array if there are no matches.
 * @throws {UnmatchedSearchPatternsError} If there is a pattern that doesn't
 *      match any files.
 */
async function globSearch({
    basePath,
    patterns,
    rawPatterns,
    configs,
    errorOnUnmatchedPattern
}) {

    if (patterns.length === 0) {
        return [];
    }

    /*
     * In this section we are converting the patterns into Minimatch
     * instances for performance reasons. Because we are doing the same
     * matches repeatedly, it's best to compile those patterns once and
     * reuse them multiple times.
     *
     * To do that, we convert any patterns with an absolute path into a
     * relative path and normalize it to Posix-style slashes. We also keep
     * track of the relative patterns to map them back to the original
     * patterns, which we need in order to throw an error if there are any
     * unmatched patterns.
     */
    const relativeToPatterns = new Map();
    const matchers = patterns.map((pattern, i) => {
        const patternToUse = path.isAbsolute(pattern)
            ? normalizeToPosix(path.relative(basePath, pattern))
            : pattern;

        relativeToPatterns.set(patternToUse, patterns[i]);

        return new Minimatch(patternToUse, MINIMATCH_OPTIONS);
    });

    /*
     * We track unmatched patterns because we may want to throw an error when
     * they occur. To start, this set is initialized with all of the patterns.
     * Every time a match occurs, the pattern is removed from the set, making
     * it easy to tell if we have any unmatched patterns left at the end of
     * search.
     */
    const unmatchedPatterns = new Set([...relativeToPatterns.keys()]);

    const filePaths = (await new Promise((resolve, reject) => {

        let promiseRejected = false;

        /**
         * Wraps a boolean-returning filter function. The wrapped function will reject the promise if an error occurs.
         * @param {Function} filter A filter function to wrap.
         * @returns {Function} A function similar to the wrapped filter that rejects the promise if an error occurs.
         */
        function wrapFilter(filter) {
            return (...args) => {

                // No need to run the filter if an error has been thrown.
                if (!promiseRejected) {
                    try {
                        return filter(...args);
                    } catch (error) {
                        promiseRejected = true;
                        reject(error);
                    }
                }
                return false;
            };
        }

        fswalk.walk(
            basePath,
            {
                deepFilter: wrapFilter(entry => {
                    const relativePath = normalizeToPosix(path.relative(basePath, entry.path));
                    const matchesPattern = matchers.some(matcher => matcher.match(relativePath, true));

                    return matchesPattern && !configs.isDirectoryIgnored(entry.path);
                }),
                entryFilter: wrapFilter(entry => {
                    const relativePath = normalizeToPosix(path.relative(basePath, entry.path));

                    // entries may be directories or files so filter out directories
                    if (entry.dirent.isDirectory()) {
                        return false;
                    }

                    /*
                     * Optimization: We need to track when patterns are left unmatched
                     * and so we use `unmatchedPatterns` to do that. There is a bit of
                     * complexity here because the same file can be matched by more than
                     * one pattern. So, when we start, we actually need to test every
                     * pattern against every file. Once we know there are no remaining
                     * unmatched patterns, then we can switch to just looking for the
                     * first matching pattern for improved speed.
                     */
                    const matchesPattern = unmatchedPatterns.size > 0
                        ? matchers.reduce((previousValue, matcher) => {
                            const pathMatches = matcher.match(relativePath);

                            /*
                             * We updated the unmatched patterns set only if the path
                             * matches and the file isn't ignored. If the file is
                             * ignored, that means there wasn't a match for the
                             * pattern so it should not be removed.
                             *
                             * Performance note: isFileIgnored() aggressively caches
                             * results so there is no performance penalty for calling
                             * it twice with the same argument.
                             */
                            if (pathMatches && !configs.isFileIgnored(entry.path)) {
                                unmatchedPatterns.delete(matcher.pattern);
                            }

                            return pathMatches || previousValue;
                        }, false)
                        : matchers.some(matcher => matcher.match(relativePath));

                    return matchesPattern && !configs.isFileIgnored(entry.path);
                })
            },
            (error, entries) => {

                // If the promise is already rejected, calling `resolve` or `reject` will do nothing.
                if (error) {
                    reject(error);
                } else {
                    resolve(entries);
                }
            }
        );
    })).map(entry => entry.path);

    // now check to see if we have any unmatched patterns
    if (errorOnUnmatchedPattern && unmatchedPatterns.size > 0) {
        throw new UnmatchedSearchPatternsError({
            basePath,
            unmatchedPatterns: [...unmatchedPatterns].map(
                pattern => relativeToPatterns.get(pattern)
            ),
            patterns,
            rawPatterns
        });
    }

    return filePaths;
}

/**
 * Throws an error for unmatched patterns. The error will only contain information about the first one.
 * Checks to see if there are any ignored results for a given search.
 * @param {Object} options The options for this function.
 * @param {string} options.basePath The directory to search.
 * @param {Array<string>} options.patterns An array of glob patterns
 *      that were used in the original search.
 * @param {Array<string>} options.rawPatterns An array of glob patterns
 *      as the user inputted them. Used for errors.
 * @param {Array<string>} options.unmatchedPatterns A non-empty array of glob patterns
 *      that were unmatched in the original search.
 * @returns {void} Always throws an error.
 * @throws {NoFilesFoundError} If the first unmatched pattern
 *      doesn't match any files even when there are no ignores.
 * @throws {AllFilesIgnoredError} If the first unmatched pattern
 *      matches some files when there are no ignores.
 */
async function throwErrorForUnmatchedPatterns({
    basePath,
    patterns,
    rawPatterns,
    unmatchedPatterns
}) {

    const pattern = unmatchedPatterns[0];
    const rawPattern = rawPatterns[patterns.indexOf(pattern)];

    const patternHasMatch = await globMatch({
        basePath,
        pattern
    });

    if (patternHasMatch) {
        throw new AllFilesIgnoredError(rawPattern);
    }

    // if we get here there are truly no matches
    throw new NoFilesFoundError(rawPattern, true);
}

/**
 * Performs multiple glob searches in parallel.
 * @param {Object} options The options for this function.
 * @param {Map<string,GlobSearch>} options.searches
 *      An array of glob patterns to match.
 * @param {FlatConfigArray} options.configs The config array to use for
 *      determining what to ignore.
 * @param {boolean} options.errorOnUnmatchedPattern Determines if an
 *      unmatched glob pattern should throw an error.
 * @returns {Promise<Array<string>>} An array of matching file paths
 *      or an empty array if there are no matches.
 */
async function globMultiSearch({ searches, configs, errorOnUnmatchedPattern }) {

    /*
     * For convenience, we normalized the search map into an array of objects.
     * Next, we filter out all searches that have no patterns. This happens
     * primarily for the cwd, which is prepopulated in the searches map as an
     * optimization. However, if it has no patterns, it means all patterns
     * occur outside of the cwd and we can safely filter out that search.
     */
    const normalizedSearches = [...searches].map(
        ([basePath, { patterns, rawPatterns }]) => ({ basePath, patterns, rawPatterns })
    ).filter(({ patterns }) => patterns.length > 0);

    const results = await Promise.allSettled(
        normalizedSearches.map(
            ({ basePath, patterns, rawPatterns }) => globSearch({
                basePath,
                patterns,
                rawPatterns,
                configs,
                errorOnUnmatchedPattern
            })
        )
    );

    const filePaths = [];

    for (let i = 0; i < results.length; i++) {

        const result = results[i];
        const currentSearch = normalizedSearches[i];

        if (result.status === "fulfilled") {

            // if the search was successful just add the results
            if (result.value.length > 0) {
                filePaths.push(...result.value);
            }

            continue;
        }

        // if we make it here then there was an error
        const error = result.reason;

        // unexpected errors should be re-thrown
        if (!error.basePath) {
            throw error;
        }

        if (errorOnUnmatchedPattern) {

            await throwErrorForUnmatchedPatterns({
                ...currentSearch,
                unmatchedPatterns: error.unmatchedPatterns
            });

        }

    }

    return filePaths;

}

/**
 * Finds all files matching the options specified.
 * @param {Object} args The arguments objects.
 * @param {Array<string>} args.patterns An array of glob patterns.
 * @param {boolean} args.globInputPaths true to interpret glob patterns,
 *      false to not interpret glob patterns.
 * @param {string} args.cwd The current working directory to find from.
 * @param {FlatConfigArray} args.configs The configs for the current run.
 * @param {boolean} args.errorOnUnmatchedPattern Determines if an unmatched pattern
 *      should throw an error.
 * @returns {Promise<Array<string>>} The fully resolved file paths.
 * @throws {AllFilesIgnoredError} If there are no results due to an ignore pattern.
 * @throws {NoFilesFoundError} If no files matched the given patterns.
 */
async function findFiles({
    patterns,
    globInputPaths,
    cwd,
    configs,
    errorOnUnmatchedPattern
}) {

    const results = [];
    const missingPatterns = [];
    let globbyPatterns = [];
    let rawPatterns = [];
    const searches = new Map([[cwd, { patterns: globbyPatterns, rawPatterns: [] }]]);

    // check to see if we have explicit files and directories
    const filePaths = patterns.map(filePath => path.resolve(cwd, filePath));
    const stats = await Promise.all(
        filePaths.map(
            filePath => fsp.stat(filePath).catch(() => { })
        )
    );

    stats.forEach((stat, index) => {

        const filePath = filePaths[index];
        const pattern = normalizeToPosix(patterns[index]);

        if (stat) {

            // files are added directly to the list
            if (stat.isFile()) {
                results.push(filePath);
            }

            // directories need extensions attached
            if (stat.isDirectory()) {

                // group everything in cwd together and split out others
                if (isPathInside(filePath, cwd)) {
                    ({ patterns: globbyPatterns, rawPatterns } = searches.get(cwd));
                } else {
                    if (!searches.has(filePath)) {
                        searches.set(filePath, { patterns: [], rawPatterns: [] });
                    }
                    ({ patterns: globbyPatterns, rawPatterns } = searches.get(filePath));
                }

                globbyPatterns.push(`${normalizeToPosix(filePath)}/**`);
                rawPatterns.push(pattern);
            }

            return;
        }

        // save patterns for later use based on whether globs are enabled
        if (globInputPaths && isGlobPattern(pattern)) {

            const basePath = path.resolve(cwd, globParent(pattern));

            // group in cwd if possible and split out others
            if (isPathInside(basePath, cwd)) {
                ({ patterns: globbyPatterns, rawPatterns } = searches.get(cwd));
            } else {
                if (!searches.has(basePath)) {
                    searches.set(basePath, { patterns: [], rawPatterns: [] });
                }
                ({ patterns: globbyPatterns, rawPatterns } = searches.get(basePath));
            }

            globbyPatterns.push(filePath);
            rawPatterns.push(pattern);
        } else {
            missingPatterns.push(pattern);
        }
    });

    // there were patterns that didn't match anything, tell the user
    if (errorOnUnmatchedPattern && missingPatterns.length) {
        throw new NoFilesFoundError(missingPatterns[0], globInputPaths);
    }

    // now we are safe to do the search
    const globbyResults = await globMultiSearch({
        searches,
        configs,
        errorOnUnmatchedPattern
    });

    return [
        ...new Set([
            ...results,
            ...globbyResults.map(filePath => path.resolve(filePath))
        ])
    ];
}

//-----------------------------------------------------------------------------
// Results-related Helpers
//-----------------------------------------------------------------------------

/**
 * Checks if the given message is an error message.
 * @param {LintMessage} message The message to check.
 * @returns {boolean} Whether or not the message is an error message.
 * @private
 */
function isErrorMessage(message) {
    return message.severity === 2;
}

/**
 * Returns result with warning by ignore settings
 * @param {string} filePath File path of checked code
 * @param {string} baseDir Absolute path of base directory
 * @returns {LintResult} Result with single warning
 * @private
 */
function createIgnoreResult(filePath, baseDir) {
    let message;
    const isInNodeModules = baseDir && path.dirname(path.relative(baseDir, filePath)).split(path.sep).includes("node_modules");

    if (isInNodeModules) {
        message = "File ignored by default because it is located under the node_modules directory. Use ignore pattern \"!**/node_modules/\" to disable file ignore settings or use \"--no-warn-ignored\" to suppress this warning.";
    } else {
        message = "File ignored because of a matching ignore pattern. Use \"--no-ignore\" to disable file ignore settings or use \"--no-warn-ignored\" to suppress this warning.";
    }

    return {
        filePath: path.resolve(filePath),
        messages: [
            {
                ruleId: null,
                fatal: false,
                severity: 1,
                message,
                nodeType: null
            }
        ],
        suppressedMessages: [],
        errorCount: 0,
        warningCount: 1,
        fatalErrorCount: 0,
        fixableErrorCount: 0,
        fixableWarningCount: 0
    };
}

//-----------------------------------------------------------------------------
// Options-related Helpers
//-----------------------------------------------------------------------------


/**
 * Check if a given value is a valid fix type or not.
 * @param {any} x The value to check.
 * @returns {boolean} `true` if `x` is valid fix type.
 */
function isFixType(x) {
    return x === "directive" || x === "problem" || x === "suggestion" || x === "layout";
}

/**
 * Check if a given value is an array of fix types or not.
 * @param {any} x The value to check.
 * @returns {boolean} `true` if `x` is an array of fix types.
 */
function isFixTypeArray(x) {
    return Array.isArray(x) && x.every(isFixType);
}

/**
 * The error for invalid options.
 */
class ESLintInvalidOptionsError extends Error {
    constructor(messages) {
        super(`Invalid Options:\n- ${messages.join("\n- ")}`);
        this.code = "ESLINT_INVALID_OPTIONS";
        Error.captureStackTrace(this, ESLintInvalidOptionsError);
    }
}

/**
 * Validates and normalizes options for the wrapped CLIEngine instance.
 * @param {FlatESLintOptions} options The options to process.
 * @throws {ESLintInvalidOptionsError} If of any of a variety of type errors.
 * @returns {FlatESLintOptions} The normalized options.
 */
function processOptions({
    allowInlineConfig = true, // ← we cannot use `overrideConfig.noInlineConfig` instead because `allowInlineConfig` has side-effect that suppress warnings that show inline configs are ignored.
    baseConfig = null,
    cache = false,
    cacheLocation = ".eslintcache",
    cacheStrategy = "metadata",
    cwd = process.cwd(),
    errorOnUnmatchedPattern = true,
    fix = false,
    fixTypes = null, // ← should be null by default because if it's an array then it suppresses rules that don't have the `meta.type` property.
    globInputPaths = true,
    ignore = true,
    ignorePatterns = null,
    overrideConfig = null,
    overrideConfigFile = null,
    plugins = {},
    warnIgnored = true,
    ...unknownOptions
}) {
    const errors = [];
    const unknownOptionKeys = Object.keys(unknownOptions);

    if (unknownOptionKeys.length >= 1) {
        errors.push(`Unknown options: ${unknownOptionKeys.join(", ")}`);
        if (unknownOptionKeys.includes("cacheFile")) {
            errors.push("'cacheFile' has been removed. Please use the 'cacheLocation' option instead.");
        }
        if (unknownOptionKeys.includes("configFile")) {
            errors.push("'configFile' has been removed. Please use the 'overrideConfigFile' option instead.");
        }
        if (unknownOptionKeys.includes("envs")) {
            errors.push("'envs' has been removed.");
        }
        if (unknownOptionKeys.includes("extensions")) {
            errors.push("'extensions' has been removed.");
        }
        if (unknownOptionKeys.includes("resolvePluginsRelativeTo")) {
            errors.push("'resolvePluginsRelativeTo' has been removed.");
        }
        if (unknownOptionKeys.includes("globals")) {
            errors.push("'globals' has been removed. Please use the 'overrideConfig.languageOptions.globals' option instead.");
        }
        if (unknownOptionKeys.includes("ignorePath")) {
            errors.push("'ignorePath' has been removed.");
        }
        if (unknownOptionKeys.includes("ignorePattern")) {
            errors.push("'ignorePattern' has been removed. Please use the 'overrideConfig.ignorePatterns' option instead.");
        }
        if (unknownOptionKeys.includes("parser")) {
            errors.push("'parser' has been removed. Please use the 'overrideConfig.languageOptions.parser' option instead.");
        }
        if (unknownOptionKeys.includes("parserOptions")) {
            errors.push("'parserOptions' has been removed. Please use the 'overrideConfig.languageOptions.parserOptions' option instead.");
        }
        if (unknownOptionKeys.includes("rules")) {
            errors.push("'rules' has been removed. Please use the 'overrideConfig.rules' option instead.");
        }
        if (unknownOptionKeys.includes("rulePaths")) {
            errors.push("'rulePaths' has been removed. Please define your rules using plugins.");
        }
        if (unknownOptionKeys.includes("reportUnusedDisableDirectives")) {
            errors.push("'reportUnusedDisableDirectives' has been removed. Please use the 'overrideConfig.linterOptions.reportUnusedDisableDirectives' option instead.");
        }
    }
    if (typeof allowInlineConfig !== "boolean") {
        errors.push("'allowInlineConfig' must be a boolean.");
    }
    if (typeof baseConfig !== "object") {
        errors.push("'baseConfig' must be an object or null.");
    }
    if (typeof cache !== "boolean") {
        errors.push("'cache' must be a boolean.");
    }
    if (!isNonEmptyString(cacheLocation)) {
        errors.push("'cacheLocation' must be a non-empty string.");
    }
    if (
        cacheStrategy !== "metadata" &&
        cacheStrategy !== "content"
    ) {
        errors.push("'cacheStrategy' must be any of \"metadata\", \"content\".");
    }
    if (!isNonEmptyString(cwd) || !path.isAbsolute(cwd)) {
        errors.push("'cwd' must be an absolute path.");
    }
    if (typeof errorOnUnmatchedPattern !== "boolean") {
        errors.push("'errorOnUnmatchedPattern' must be a boolean.");
    }
    if (typeof fix !== "boolean" && typeof fix !== "function") {
        errors.push("'fix' must be a boolean or a function.");
    }
    if (fixTypes !== null && !isFixTypeArray(fixTypes)) {
        errors.push("'fixTypes' must be an array of any of \"directive\", \"problem\", \"suggestion\", and \"layout\".");
    }
    if (typeof globInputPaths !== "boolean") {
        errors.push("'globInputPaths' must be a boolean.");
    }
    if (typeof ignore !== "boolean") {
        errors.push("'ignore' must be a boolean.");
    }
    if (!isArrayOfNonEmptyString(ignorePatterns) && ignorePatterns !== null) {
        errors.push("'ignorePatterns' must be an array of non-empty strings or null.");
    }
    if (typeof overrideConfig !== "object") {
        errors.push("'overrideConfig' must be an object or null.");
    }
    if (!isNonEmptyString(overrideConfigFile) && overrideConfigFile !== null && overrideConfigFile !== true) {
        errors.push("'overrideConfigFile' must be a non-empty string, null, or true.");
    }
    if (typeof plugins !== "object") {
        errors.push("'plugins' must be an object or null.");
    } else if (plugins !== null && Object.keys(plugins).includes("")) {
        errors.push("'plugins' must not include an empty string.");
    }
    if (Array.isArray(plugins)) {
        errors.push("'plugins' doesn't add plugins to configuration to load. Please use the 'overrideConfig.plugins' option instead.");
    }
    if (typeof warnIgnored !== "boolean") {
        errors.push("'warnIgnored' must be a boolean.");
    }
    if (errors.length > 0) {
        throw new ESLintInvalidOptionsError(errors);
    }

    return {
        allowInlineConfig,
        baseConfig,
        cache,
        cacheLocation,
        cacheStrategy,

        // when overrideConfigFile is true that means don't do config file lookup
        configFile: overrideConfigFile === true ? false : overrideConfigFile,
        overrideConfig,
        cwd: path.normalize(cwd),
        errorOnUnmatchedPattern,
        fix,
        fixTypes,
        globInputPaths,
        ignore,
        ignorePatterns,
        warnIgnored
    };
}


//-----------------------------------------------------------------------------
// Cache-related helpers
//-----------------------------------------------------------------------------

/**
 * return the cacheFile to be used by eslint, based on whether the provided parameter is
 * a directory or looks like a directory (ends in `path.sep`), in which case the file
 * name will be the `cacheFile/.cache_hashOfCWD`
 *
 * if cacheFile points to a file or looks like a file then in will just use that file
 * @param {string} cacheFile The name of file to be used to store the cache
 * @param {string} cwd Current working directory
 * @returns {string} the resolved path to the cache file
 */
function getCacheFile(cacheFile, cwd) {

    /*
     * make sure the path separators are normalized for the environment/os
     * keeping the trailing path separator if present
     */
    const normalizedCacheFile = path.normalize(cacheFile);

    const resolvedCacheFile = path.resolve(cwd, normalizedCacheFile);
    const looksLikeADirectory = normalizedCacheFile.slice(-1) === path.sep;

    /**
     * return the name for the cache file in case the provided parameter is a directory
     * @returns {string} the resolved path to the cacheFile
     */
    function getCacheFileForDirectory() {
        return path.join(resolvedCacheFile, `.cache_${hash(cwd)}`);
    }

    let fileStats;

    try {
        fileStats = fs.lstatSync(resolvedCacheFile);
    } catch {
        fileStats = null;
    }


    /*
     * in case the file exists we need to verify if the provided path
     * is a directory or a file. If it is a directory we want to create a file
     * inside that directory
     */
    if (fileStats) {

        /*
         * is a directory or is a file, but the original file the user provided
         * looks like a directory but `path.resolve` removed the `last path.sep`
         * so we need to still treat this like a directory
         */
        if (fileStats.isDirectory() || looksLikeADirectory) {
            return getCacheFileForDirectory();
        }

        // is file so just use that file
        return resolvedCacheFile;
    }

    /*
     * here we known the file or directory doesn't exist,
     * so we will try to infer if its a directory if it looks like a directory
     * for the current operating system.
     */

    // if the last character passed is a path separator we assume is a directory
    if (looksLikeADirectory) {
        return getCacheFileForDirectory();
    }

    return resolvedCacheFile;
}


//-----------------------------------------------------------------------------
// Exports
//-----------------------------------------------------------------------------

module.exports = {
    isGlobPattern,
    findFiles,

    isNonEmptyString,
    isArrayOfNonEmptyString,

    createIgnoreResult,
    isErrorMessage,

    processOptions,

    getCacheFile
};
