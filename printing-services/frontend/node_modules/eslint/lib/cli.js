/**
 * @fileoverview Main CLI object.
 * @author Nicholas C. Zakas
 */

"use strict";

/*
 * NOTE: The CLI object should *not* call process.exit() directly. It should only return
 * exit codes. This allows other programs to use the CLI object and still control
 * when the program exits.
 */

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

const fs = require("fs"),
    path = require("path"),
    { promisify } = require("util"),
    { ESLint } = require("./eslint"),
    { FlatESLint, shouldUseFlatConfig } = require("./eslint/flat-eslint"),
    createCLIOptions = require("./options"),
    log = require("./shared/logging"),
    RuntimeInfo = require("./shared/runtime-info"),
    { normalizeSeverityToString } = require("./shared/severity");
const { Legacy: { naming } } = require("@eslint/eslintrc");
const { ModuleImporter } = require("@humanwhocodes/module-importer");

const debug = require("debug")("eslint:cli");

//------------------------------------------------------------------------------
// Types
//------------------------------------------------------------------------------

/** @typedef {import("./eslint/eslint").ESLintOptions} ESLintOptions */
/** @typedef {import("./eslint/eslint").LintMessage} LintMessage */
/** @typedef {import("./eslint/eslint").LintResult} LintResult */
/** @typedef {import("./options").ParsedCLIOptions} ParsedCLIOptions */
/** @typedef {import("./shared/types").ResultsMeta} ResultsMeta */

//------------------------------------------------------------------------------
// Helpers
//------------------------------------------------------------------------------

const mkdir = promisify(fs.mkdir);
const stat = promisify(fs.stat);
const writeFile = promisify(fs.writeFile);

/**
 * Predicate function for whether or not to apply fixes in quiet mode.
 * If a message is a warning, do not apply a fix.
 * @param {LintMessage} message The lint result.
 * @returns {boolean} True if the lint message is an error (and thus should be
 * autofixed), false otherwise.
 */
function quietFixPredicate(message) {
    return message.severity === 2;
}

/**
 * Translates the CLI options into the options expected by the ESLint constructor.
 * @param {ParsedCLIOptions} cliOptions The CLI options to translate.
 * @param {"flat"|"eslintrc"} [configType="eslintrc"] The format of the
 *      config to generate.
 * @returns {Promise<ESLintOptions>} The options object for the ESLint constructor.
 * @private
 */
async function translateOptions({
    cache,
    cacheFile,
    cacheLocation,
    cacheStrategy,
    config,
    configLookup,
    env,
    errorOnUnmatchedPattern,
    eslintrc,
    ext,
    fix,
    fixDryRun,
    fixType,
    global,
    ignore,
    ignorePath,
    ignorePattern,
    inlineConfig,
    parser,
    parserOptions,
    plugin,
    quiet,
    reportUnusedDisableDirectives,
    reportUnusedDisableDirectivesSeverity,
    resolvePluginsRelativeTo,
    rule,
    rulesdir,
    warnIgnored
}, configType) {

    let overrideConfig, overrideConfigFile;
    const importer = new ModuleImporter();

    if (configType === "flat") {
        overrideConfigFile = (typeof config === "string") ? config : !configLookup;
        if (overrideConfigFile === false) {
            overrideConfigFile = void 0;
        }

        let globals = {};

        if (global) {
            globals = global.reduce((obj, name) => {
                if (name.endsWith(":true")) {
                    obj[name.slice(0, -5)] = "writable";
                } else {
                    obj[name] = "readonly";
                }
                return obj;
            }, globals);
        }

        overrideConfig = [{
            languageOptions: {
                globals,
                parserOptions: parserOptions || {}
            },
            rules: rule ? rule : {}
        }];

        if (reportUnusedDisableDirectives || reportUnusedDisableDirectivesSeverity !== void 0) {
            overrideConfig[0].linterOptions = {
                reportUnusedDisableDirectives: reportUnusedDisableDirectives
                    ? "error"
                    : normalizeSeverityToString(reportUnusedDisableDirectivesSeverity)
            };
        }

        if (parser) {
            overrideConfig[0].languageOptions.parser = await importer.import(parser);
        }

        if (plugin) {
            const plugins = {};

            for (const pluginName of plugin) {

                const shortName = naming.getShorthandName(pluginName, "eslint-plugin");
                const longName = naming.normalizePackageName(pluginName, "eslint-plugin");

                plugins[shortName] = await importer.import(longName);
            }

            overrideConfig[0].plugins = plugins;
        }

    } else {
        overrideConfigFile = config;

        overrideConfig = {
            env: env && env.reduce((obj, name) => {
                obj[name] = true;
                return obj;
            }, {}),
            globals: global && global.reduce((obj, name) => {
                if (name.endsWith(":true")) {
                    obj[name.slice(0, -5)] = "writable";
                } else {
                    obj[name] = "readonly";
                }
                return obj;
            }, {}),
            ignorePatterns: ignorePattern,
            parser,
            parserOptions,
            plugins: plugin,
            rules: rule
        };
    }

    const options = {
        allowInlineConfig: inlineConfig,
        cache,
        cacheLocation: cacheLocation || cacheFile,
        cacheStrategy,
        errorOnUnmatchedPattern,
        fix: (fix || fixDryRun) && (quiet ? quietFixPredicate : true),
        fixTypes: fixType,
        ignore,
        overrideConfig,
        overrideConfigFile
    };

    if (configType === "flat") {
        options.ignorePatterns = ignorePattern;
        options.warnIgnored = warnIgnored;
    } else {
        options.resolvePluginsRelativeTo = resolvePluginsRelativeTo;
        options.rulePaths = rulesdir;
        options.useEslintrc = eslintrc;
        options.extensions = ext;
        options.ignorePath = ignorePath;
        if (reportUnusedDisableDirectives || reportUnusedDisableDirectivesSeverity !== void 0) {
            options.reportUnusedDisableDirectives = reportUnusedDisableDirectives
                ? "error"
                : normalizeSeverityToString(reportUnusedDisableDirectivesSeverity);
        }
    }

    return options;
}

/**
 * Count error messages.
 * @param {LintResult[]} results The lint results.
 * @returns {{errorCount:number;fatalErrorCount:number,warningCount:number}} The number of error messages.
 */
function countErrors(results) {
    let errorCount = 0;
    let fatalErrorCount = 0;
    let warningCount = 0;

    for (const result of results) {
        errorCount += result.errorCount;
        fatalErrorCount += result.fatalErrorCount;
        warningCount += result.warningCount;
    }

    return { errorCount, fatalErrorCount, warningCount };
}

/**
 * Check if a given file path is a directory or not.
 * @param {string} filePath The path to a file to check.
 * @returns {Promise<boolean>} `true` if the given path is a directory.
 */
async function isDirectory(filePath) {
    try {
        return (await stat(filePath)).isDirectory();
    } catch (error) {
        if (error.code === "ENOENT" || error.code === "ENOTDIR") {
            return false;
        }
        throw error;
    }
}

/**
 * Outputs the results of the linting.
 * @param {ESLint} engine The ESLint instance to use.
 * @param {LintResult[]} results The results to print.
 * @param {string} format The name of the formatter to use or the path to the formatter.
 * @param {string} outputFile The path for the output file.
 * @param {ResultsMeta} resultsMeta Warning count and max threshold.
 * @returns {Promise<boolean>} True if the printing succeeds, false if not.
 * @private
 */
async function printResults(engine, results, format, outputFile, resultsMeta) {
    let formatter;

    try {
        formatter = await engine.loadFormatter(format);
    } catch (e) {
        log.error(e.message);
        return false;
    }

    const output = await formatter.format(results, resultsMeta);

    if (output) {
        if (outputFile) {
            const filePath = path.resolve(process.cwd(), outputFile);

            if (await isDirectory(filePath)) {
                log.error("Cannot write to output file path, it is a directory: %s", outputFile);
                return false;
            }

            try {
                await mkdir(path.dirname(filePath), { recursive: true });
                await writeFile(filePath, output);
            } catch (ex) {
                log.error("There was a problem writing the output file:\n%s", ex);
                return false;
            }
        } else {
            log.info(output);
        }
    }

    return true;
}

//------------------------------------------------------------------------------
// Public Interface
//------------------------------------------------------------------------------

/**
 * Encapsulates all CLI behavior for eslint. Makes it easier to test as well as
 * for other Node.js programs to effectively run the CLI.
 */
const cli = {

    /**
     * Executes the CLI based on an array of arguments that is passed in.
     * @param {string|Array|Object} args The arguments to process.
     * @param {string} [text] The text to lint (used for TTY).
     * @param {boolean} [allowFlatConfig] Whether or not to allow flat config.
     * @returns {Promise<number>} The exit code for the operation.
     */
    async execute(args, text, allowFlatConfig) {
        if (Array.isArray(args)) {
            debug("CLI args: %o", args.slice(2));
        }

        /*
         * Before doing anything, we need to see if we are using a
         * flat config file. If so, then we need to change the way command
         * line args are parsed. This is temporary, and when we fully
         * switch to flat config we can remove this logic.
         */

        const usingFlatConfig = allowFlatConfig && await shouldUseFlatConfig();

        debug("Using flat config?", usingFlatConfig);

        const CLIOptions = createCLIOptions(usingFlatConfig);

        /** @type {ParsedCLIOptions} */
        let options;

        try {
            options = CLIOptions.parse(args);
        } catch (error) {
            debug("Error parsing CLI options:", error.message);

            let errorMessage = error.message;

            if (usingFlatConfig) {
                errorMessage += "\nYou're using eslint.config.js, some command line flags are no longer available. Please see https://eslint.org/docs/latest/use/command-line-interface for details.";
            }

            log.error(errorMessage);
            return 2;
        }

        const files = options._;
        const useStdin = typeof text === "string";

        if (options.help) {
            log.info(CLIOptions.generateHelp());
            return 0;
        }
        if (options.version) {
            log.info(RuntimeInfo.version());
            return 0;
        }
        if (options.envInfo) {
            try {
                log.info(RuntimeInfo.environment());
                return 0;
            } catch (err) {
                debug("Error retrieving environment info");
                log.error(err.message);
                return 2;
            }
        }

        if (options.printConfig) {
            if (files.length) {
                log.error("The --print-config option must be used with exactly one file name.");
                return 2;
            }
            if (useStdin) {
                log.error("The --print-config option is not available for piped-in code.");
                return 2;
            }

            const engine = usingFlatConfig
                ? new FlatESLint(await translateOptions(options, "flat"))
                : new ESLint(await translateOptions(options));
            const fileConfig =
                await engine.calculateConfigForFile(options.printConfig);

            log.info(JSON.stringify(fileConfig, null, "  "));
            return 0;
        }

        debug(`Running on ${useStdin ? "text" : "files"}`);

        if (options.fix && options.fixDryRun) {
            log.error("The --fix option and the --fix-dry-run option cannot be used together.");
            return 2;
        }
        if (useStdin && options.fix) {
            log.error("The --fix option is not available for piped-in code; use --fix-dry-run instead.");
            return 2;
        }
        if (options.fixType && !options.fix && !options.fixDryRun) {
            log.error("The --fix-type option requires either --fix or --fix-dry-run.");
            return 2;
        }

        if (options.reportUnusedDisableDirectives && options.reportUnusedDisableDirectivesSeverity !== void 0) {
            log.error("The --report-unused-disable-directives option and the --report-unused-disable-directives-severity option cannot be used together.");
            return 2;
        }

        const ActiveESLint = usingFlatConfig ? FlatESLint : ESLint;

        const engine = new ActiveESLint(await translateOptions(options, usingFlatConfig ? "flat" : "eslintrc"));
        let results;

        if (useStdin) {
            results = await engine.lintText(text, {
                filePath: options.stdinFilename,

                // flatConfig respects CLI flag and constructor warnIgnored, eslintrc forces true for backwards compatibility
                warnIgnored: usingFlatConfig ? void 0 : true
            });
        } else {
            results = await engine.lintFiles(files);
        }

        if (options.fix) {
            debug("Fix mode enabled - applying fixes");
            await ActiveESLint.outputFixes(results);
        }

        let resultsToPrint = results;

        if (options.quiet) {
            debug("Quiet mode enabled - filtering out warnings");
            resultsToPrint = ActiveESLint.getErrorResults(resultsToPrint);
        }

        const resultCounts = countErrors(results);
        const tooManyWarnings = options.maxWarnings >= 0 && resultCounts.warningCount > options.maxWarnings;
        const resultsMeta = tooManyWarnings
            ? {
                maxWarningsExceeded: {
                    maxWarnings: options.maxWarnings,
                    foundWarnings: resultCounts.warningCount
                }
            }
            : {};

        if (await printResults(engine, resultsToPrint, options.format, options.outputFile, resultsMeta)) {

            // Errors and warnings from the original unfiltered results should determine the exit code
            const shouldExitForFatalErrors =
                options.exitOnFatalError && resultCounts.fatalErrorCount > 0;

            if (!resultCounts.errorCount && tooManyWarnings) {
                log.error(
                    "ESLint found too many warnings (maximum: %s).",
                    options.maxWarnings
                );
            }

            if (shouldExitForFatalErrors) {
                return 2;
            }

            return (resultCounts.errorCount || tooManyWarnings) ? 1 : 0;
        }

        return 2;
    }
};

module.exports = cli;
