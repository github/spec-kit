"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
// @ts-check
const lodash_1 = __importDefault(require("lodash"));
const commander_1 = __importDefault(require("commander"));
const common_tags_1 = require("common-tags");
const log_symbols_1 = __importDefault(require("log-symbols"));
const debug_1 = __importDefault(require("debug"));
const util_1 = __importDefault(require("./util"));
const logger_1 = __importDefault(require("./logger"));
const errors_1 = require("./errors");
const cache_1 = __importDefault(require("./tasks/cache"));
const open_1 = __importDefault(require("./exec/open"));
const run_1 = __importDefault(require("./exec/run"));
const verify_1 = require("./tasks/verify");
const install_1 = __importDefault(require("./tasks/install"));
const versions_1 = __importDefault(require("./exec/versions"));
const info_1 = __importDefault(require("./exec/info"));
const debug = (0, debug_1.default)('cypress:cli:cli');
// patch "commander" method called when a user passed an unknown option
// we want to print help for the current command and exit with an error
function unknownOption(flag, type = 'option') {
    if (this._allowUnknownOption)
        return;
    logger_1.default.error();
    logger_1.default.error(`  error: unknown ${type}:`, flag);
    logger_1.default.error();
    this.outputHelp();
    process.exit(1);
}
commander_1.default.Command.prototype.unknownOption = unknownOption;
const coerceFalse = (arg) => {
    return arg !== 'false';
};
const coerceAnyStringToInt = (arg) => {
    return typeof arg === 'string' ? parseInt(arg) : arg;
};
const spaceDelimitedArgsMsg = (flag, args) => {
    let msg = `
    ${log_symbols_1.default.warning} Warning: It looks like you're passing --${flag} a space-separated list of arguments:

    "${args.join(' ')}"

    This will work, but it's not recommended.

    If you are trying to pass multiple arguments, separate them with commas instead:
      cypress run --${flag} arg1,arg2,arg3
  `;
    if (flag === 'spec') {
        msg += `
    The most common cause of this warning is using an unescaped glob pattern. If you are
    trying to pass a glob pattern, escape it using quotes:
      cypress run --spec "**/*.spec.js"
    `;
    }
    logger_1.default.log();
    logger_1.default.warn((0, common_tags_1.stripIndent)(msg));
    logger_1.default.log();
};
const parseVariableOpts = (fnArgs, args) => {
    const [opts, unknownArgs] = fnArgs;
    if ((unknownArgs && unknownArgs.length) && (opts.spec || opts.tag)) {
        // this will capture space-delimited args after
        // flags that could have possible multiple args
        // but before the next option
        // --spec spec1 spec2 or --tag foo bar
        const multiArgFlags = lodash_1.default.compact([
            opts.spec ? 'spec' : opts.spec,
            opts.tag ? 'tag' : opts.tag,
        ]);
        lodash_1.default.forEach(multiArgFlags, (flag) => {
            const argIndex = lodash_1.default.indexOf(args, `--${flag}`) + 2;
            const nextOptOffset = lodash_1.default.findIndex(lodash_1.default.slice(args, argIndex), (arg) => {
                return lodash_1.default.startsWith(arg, '--');
            });
            const endIndex = nextOptOffset !== -1 ? argIndex + nextOptOffset : args.length;
            const maybeArgs = lodash_1.default.slice(args, argIndex, endIndex);
            const extraArgs = lodash_1.default.intersection(maybeArgs, unknownArgs);
            if (extraArgs.length) {
                opts[flag] = [opts[flag]].concat(extraArgs);
                spaceDelimitedArgsMsg(flag, opts[flag]);
                opts[flag] = opts[flag].join(',');
            }
        });
    }
    debug('variable-length opts parsed %o', { args, opts });
    return util_1.default.parseOpts(opts);
};
const descriptions = {
    autoCancelAfterFailures: 'overrides the project-level Cloud configuration to set the failed test threshold for auto cancellation or to disable auto cancellation when recording to the Cloud',
    browser: 'runs Cypress in the browser with the given name. if a filesystem path is supplied, Cypress will attempt to use the browser at that path.',
    cacheClear: 'delete all cached binaries',
    cachePrune: 'deletes all cached binaries except for the version currently in use',
    cacheList: 'list cached binary versions',
    cachePath: 'print the path to the binary cache',
    cacheSize: 'Used with the list command to show the sizes of the cached folders',
    ciBuildId: 'the unique identifier for a run on your CI provider. typically a "BUILD_ID" env var. this value is automatically detected for most CI providers',
    component: 'runs component tests',
    config: 'sets configuration values. separate multiple values with a comma. overrides any value in cypress.config.{js,ts,mjs,cjs}.',
    configFile: 'path to script file where configuration values are set. defaults to "cypress.config.{js,ts,mjs,cjs}".',
    detached: 'runs Cypress application in detached mode',
    dev: 'runs cypress in development and bypasses binary check',
    e2e: 'runs end to end tests',
    env: 'sets environment variables. separate multiple values with a comma. overrides any value in cypress.config.{js,ts,mjs,cjs} or cypress.env.json',
    exit: 'keep the browser open after tests finish',
    forceInstall: 'force install the Cypress binary',
    global: 'force Cypress into global mode as if it were globally installed',
    group: 'a named group for recorded runs in Cypress Cloud',
    headed: 'displays the browser instead of running headlessly',
    headless: 'hide the browser instead of running headed (default for cypress run)',
    key: 'your secret Record Key. you can omit this if you set a CYPRESS_RECORD_KEY environment variable.',
    parallel: 'enables concurrent runs and automatic load balancing of specs across multiple machines or processes',
    port: 'runs Cypress on a specific port. overrides any value in cypress.config.{js,ts,mjs,cjs}.',
    project: 'path to the project',
    posixExitCodes: 'use POSIX exit codes for error handling',
    quiet: 'run quietly, using only the configured reporter',
    record: 'records the run. sends test results, screenshots and videos to Cypress Cloud.',
    reporter: 'runs a specific mocha reporter. pass a path to use a custom reporter. defaults to "spec"',
    reporterOptions: 'options for the mocha reporter. defaults to "null"',
    runnerUi: 'displays the Cypress Runner UI',
    noRunnerUi: 'hides the Cypress Runner UI',
    spec: 'runs specific spec file(s). defaults to "all"',
    tag: 'named tag(s) for recorded runs in Cypress Cloud',
    version: 'prints Cypress version',
};
const knownCommands = [
    'cache',
    'help',
    '-h',
    '--help',
    'install',
    'open',
    'run',
    'verify',
    '-v',
    '--version',
    'version',
    'info',
];
const text = (description) => {
    if (!descriptions[description]) {
        throw new Error(`Could not find description for: ${description}`);
    }
    return descriptions[description];
};
function includesVersion(args) {
    return (lodash_1.default.includes(args, '--version') ||
        lodash_1.default.includes(args, '-v'));
}
function showVersions(opts) {
    return __awaiter(this, void 0, void 0, function* () {
        debug('printing Cypress version');
        debug('additional arguments %o', opts);
        debug('parsed version arguments %o', opts);
        const reportAllVersions = (versions) => {
            logger_1.default.always('Cypress package version:', versions.package);
            logger_1.default.always('Cypress binary version:', versions.binary);
            logger_1.default.always('Electron version:', versions.electronVersion);
            logger_1.default.always('Bundled Node version:', versions.electronNodeVersion);
        };
        const reportComponentVersion = (componentName, versions) => {
            const names = {
                package: 'package',
                binary: 'binary',
                electron: 'electronVersion',
                node: 'electronNodeVersion',
            };
            if (!names[componentName]) {
                throw new Error(`Unknown component name "${componentName}"`);
            }
            const name = names[componentName];
            if (!versions[name]) {
                throw new Error(`Cannot find version for component "${componentName}" under property "${name}"`);
            }
            const version = versions[name];
            logger_1.default.always(version);
        };
        const defaultVersions = {
            package: undefined,
            binary: undefined,
            electronVersion: undefined,
            electronNodeVersion: undefined,
        };
        try {
            const versions = (yield versions_1.default.getVersions()) || defaultVersions;
            if (opts === null || opts === void 0 ? void 0 : opts.component) {
                reportComponentVersion(opts.component, versions);
            }
            else {
                reportAllVersions(versions);
            }
            process.exit(0);
        }
        catch (e) {
            util_1.default.logErrorExit1(e);
        }
    });
}
const createProgram = () => {
    const program = new commander_1.default.Command();
    // bug in commander not printing name
    // in usage help docs
    program._name = 'cypress';
    program.usage('<command> [options]');
    return program;
};
const addCypressRunCommand = (program) => {
    return program
        .command('run')
        .usage('[options]')
        .description('Runs Cypress tests from the CLI without the GUI')
        .option('--auto-cancel-after-failures <test-failure-count || false>', text('autoCancelAfterFailures'))
        .option('-b, --browser <browser-name-or-path>', text('browser'))
        .option('--ci-build-id <id>', text('ciBuildId'))
        .option('--component', text('component'))
        .option('-c, --config <config>', text('config'))
        .option('-C, --config-file <config-file>', text('configFile'))
        .option('--e2e', text('e2e'))
        .option('-e, --env <env>', text('env'))
        .option('--group <name>', text('group'))
        .option('-k, --key <record-key>', text('key'))
        .option('--headed', text('headed'))
        .option('--headless', text('headless'))
        .option('--no-exit', text('exit'))
        .option('--parallel', text('parallel'))
        .option('-p, --port <port>', text('port'))
        .option('-P, --project <project-path>', text('project'))
        .option('--posix-exit-codes', text('posixExitCodes'))
        .option('-q, --quiet', text('quiet'))
        .option('--record [bool]', text('record'), coerceFalse)
        .option('-r, --reporter <reporter>', text('reporter'))
        .option('--runner-ui', text('runnerUi'))
        .option('--no-runner-ui', text('noRunnerUi'))
        .option('-o, --reporter-options <reporter-options>', text('reporterOptions'))
        .option('-s, --spec <spec>', text('spec'))
        .option('-t, --tag <tag>', text('tag'))
        .option('--dev', text('dev'), coerceFalse);
};
const addCypressOpenCommand = (program) => {
    return program
        .command('open')
        .usage('[options]')
        .description('Opens Cypress in the interactive GUI.')
        .option('-b, --browser <browser-path>', text('browser'))
        .option('--component', text('component'))
        .option('-c, --config <config>', text('config'))
        .option('-C, --config-file <config-file>', text('configFile'))
        .option('-d, --detached [bool]', text('detached'), coerceFalse)
        .option('--e2e', text('e2e'))
        .option('-e, --env <env>', text('env'))
        .option('--global', text('global'))
        .option('-p, --port <port>', text('port'))
        .option('-P, --project <project-path>', text('project'))
        .option('--dev', text('dev'), coerceFalse);
};
const maybeAddInspectFlags = (program) => {
    if (process.argv.includes('--dev')) {
        return program
            .option('--inspect', 'Node option')
            .option('--inspect-brk', 'Node option');
    }
    return program;
};
/**
 * Casts known command line options for "cypress run" to their intended type.
 * For example if the user passes "--port 5005" the ".port" property should be
 * a number 5005 and not a string "5005".
 *
 * Returns a clone of the original object.
 */
const castCypressOptions = (opts) => {
    // only properties that have type "string | false" in our TS definition
    // require special handling, because CLI parsing takes care of purely
    // boolean arguments
    const castOpts = Object.assign({}, opts);
    if (lodash_1.default.has(opts, 'port')) {
        castOpts.port = coerceAnyStringToInt(opts.port);
    }
    return castOpts;
};
const cliModule = {
    /**
     * Parses `cypress run` command line option array into an object
     * with options that you can feed into a `cypress.run()` module API call.
     * @example
     *  const options = parseRunCommand(['cypress', 'run', '--browser', 'chrome'])
     *  // options is {browser: 'chrome'}
     */
    parseRunCommand(args) {
        return new Promise((resolve, reject) => {
            if (!Array.isArray(args)) {
                return reject(new Error('Expected array of arguments'));
            }
            // make a copy of the input arguments array
            // and add placeholders where "node ..." would usually be
            // also remove "cypress" keyword at the start if present
            const cliArgs = args[0] === 'cypress' ? [...args.slice(1)] : [...args];
            cliArgs.unshift(null, null);
            debug('creating program parser');
            const program = createProgram();
            maybeAddInspectFlags(addCypressRunCommand(program))
                .action((...fnArgs) => {
                debug('parsed Cypress run %o', fnArgs);
                const options = parseVariableOpts(fnArgs, cliArgs);
                debug('parsed options %o', options);
                const casted = castCypressOptions(options);
                debug('casted options %o', casted);
                resolve(casted);
            });
            debug('parsing args: %o', cliArgs);
            program.parse(cliArgs);
        });
    },
    /**
     * Parses `cypress open` command line option array into an object
     * with options that you can feed into cy.openModeSystemTest test calls
     * @example
     *  const options = parseOpenCommand(['cypress', 'open', '--browser', 'chrome'])
     *  // options is {browser: 'chrome'}
     */
    parseOpenCommand(args) {
        return new Promise((resolve, reject) => {
            if (!Array.isArray(args)) {
                return reject(new Error('Expected array of arguments'));
            }
            // make a copy of the input arguments array
            // and add placeholders where "node ..." would usually be
            // also remove "cypress" keyword at the start if present
            const cliArgs = args[0] === 'cypress' ? [...args.slice(1)] : [...args];
            cliArgs.unshift(null, null);
            debug('creating program parser');
            const program = createProgram();
            maybeAddInspectFlags(addCypressOpenCommand(program))
                .action((...fnArgs) => {
                debug('parsed Cypress open %o', fnArgs);
                const options = parseVariableOpts(fnArgs, cliArgs);
                debug('parsed options %o', options);
                const casted = castCypressOptions(options);
                debug('casted options %o', casted);
                resolve(casted);
            });
            debug('parsing args: %o', cliArgs);
            program.parse(cliArgs);
        });
    },
    /**
     * Parses the command line and kicks off Cypress process.
     */
    init(args) {
        return __awaiter(this, void 0, void 0, function* () {
            if (!args) {
                args = process.argv;
            }
            const { CYPRESS_INTERNAL_ENV, CYPRESS_DOWNLOAD_USE_CA } = process.env;
            if (process.env.CYPRESS_DOWNLOAD_USE_CA) {
                let msg = `
        ${log_symbols_1.default.warning} Warning: It looks like you're setting CYPRESS_DOWNLOAD_USE_CA=${CYPRESS_DOWNLOAD_USE_CA}

        The environment variable "CYPRESS_DOWNLOAD_USE_CA" is no longer required to be set.
        
        You can safely unset this environment variable.
      `;
                logger_1.default.log();
                logger_1.default.warn((0, common_tags_1.stripIndent)(msg));
                logger_1.default.log();
            }
            if (!util_1.default.isValidCypressInternalEnvValue(CYPRESS_INTERNAL_ENV)) {
                debug('invalid CYPRESS_INTERNAL_ENV value', CYPRESS_INTERNAL_ENV);
                return (0, errors_1.exitWithError)(errors_1.errors.invalidCypressEnv)(`CYPRESS_INTERNAL_ENV=${CYPRESS_INTERNAL_ENV}`);
            }
            if (util_1.default.isNonProductionCypressInternalEnvValue(CYPRESS_INTERNAL_ENV)) {
                debug('non-production CYPRESS_INTERNAL_ENV value', CYPRESS_INTERNAL_ENV);
                let msg = `
        ${log_symbols_1.default.warning} Warning: It looks like you're passing CYPRESS_INTERNAL_ENV=${CYPRESS_INTERNAL_ENV}

        The environment variable "CYPRESS_INTERNAL_ENV" is reserved and should only be used internally.

        Unset the "CYPRESS_INTERNAL_ENV" environment variable and run Cypress again.
      `;
                logger_1.default.log();
                logger_1.default.warn((0, common_tags_1.stripIndent)(msg));
                logger_1.default.log();
            }
            const program = createProgram();
            program
                .command('help')
                .description('Shows CLI help and exits')
                .action(() => {
                program.help();
            });
            const handleVersion = (cmd) => {
                return cmd
                    .option('--component <package|binary|electron|node>', 'component to report version for')
                    .action((opts, ...other) => {
                    showVersions(util_1.default.parseOpts(opts));
                });
            };
            handleVersion(program
                .storeOptionsAsProperties()
                .option('-v, --version', text('version'))
                .command('version')
                .description(text('version')));
            maybeAddInspectFlags(addCypressOpenCommand(program))
                .action((opts) => __awaiter(this, void 0, void 0, function* () {
                debug('opening Cypress');
                try {
                    const code = yield open_1.default.start(util_1.default.parseOpts(opts));
                    process.exit(code);
                }
                catch (e) {
                    util_1.default.logErrorExit1(e);
                }
            }));
            maybeAddInspectFlags(addCypressRunCommand(program))
                .action((...fnArgs) => __awaiter(this, void 0, void 0, function* () {
                debug('running Cypress with args %o', fnArgs);
                try {
                    const code = yield run_1.default.start(parseVariableOpts(fnArgs, args));
                    process.exit(code);
                }
                catch (e) {
                    util_1.default.logErrorExit1(e);
                }
            }));
            program
                .command('install')
                .usage('[options]')
                .description('Installs the Cypress executable matching this package\'s version')
                .option('-f, --force', text('forceInstall'))
                .action((opts) => __awaiter(this, void 0, void 0, function* () {
                try {
                    yield install_1.default.start(util_1.default.parseOpts(opts));
                }
                catch (e) {
                    util_1.default.logErrorExit1(e);
                }
            }));
            program
                .command('verify')
                .usage('[options]')
                .description('Verifies that Cypress is installed correctly and executable')
                .option('--dev', text('dev'), coerceFalse)
                .action((opts) => __awaiter(this, void 0, void 0, function* () {
                const defaultOpts = { force: true, welcomeMessage: false };
                const parsedOpts = util_1.default.parseOpts(opts);
                const options = lodash_1.default.extend(parsedOpts, defaultOpts);
                try {
                    yield (0, verify_1.start)(options);
                }
                catch (e) {
                    util_1.default.logErrorExit1(e);
                }
            }));
            program
                .command('cache')
                .usage('[command]')
                .description('Manages the Cypress binary cache')
                .option('list', text('cacheList'))
                .option('path', text('cachePath'))
                .option('clear', text('cacheClear'))
                .option('prune', text('cachePrune'))
                .option('--size', text('cacheSize'))
                .action(function (opts, args) {
                return __awaiter(this, void 0, void 0, function* () {
                    if (!args || !args.length) {
                        this.outputHelp();
                        process.exit(1);
                    }
                    const [command] = args;
                    if (!lodash_1.default.includes(['list', 'path', 'clear', 'prune'], command)) {
                        unknownOption.call(this, `cache ${command}`, 'command');
                    }
                    if (command === 'list') {
                        debug('cache command %o', {
                            command,
                            size: opts.size,
                        });
                        try {
                            const result = yield cache_1.default.list(opts.size);
                            return result;
                        }
                        catch (e) {
                            if (e.code === 'ENOENT') {
                                logger_1.default.always('No cached binary versions were found.');
                                process.exit(0);
                            }
                            util_1.default.logErrorExit1(e);
                        }
                    }
                    cache_1.default[command]();
                });
            });
            program
                .command('info')
                .usage('[command]')
                .description('Prints Cypress and system information')
                .option('--dev', text('dev'), coerceFalse)
                .action((opts) => __awaiter(this, void 0, void 0, function* () {
                try {
                    const code = yield info_1.default.start(opts);
                    process.exit(code);
                }
                catch (e) {
                    util_1.default.logErrorExit1(e);
                }
            }));
            debug('cli starts with arguments %j', args);
            util_1.default.printNodeOptions();
            // if there are no arguments
            if (args.length <= 2) {
                debug('printing help');
                program.help();
                // exits
            }
            const firstCommand = args[2];
            if (!lodash_1.default.includes(knownCommands, firstCommand)) {
                debug('unknown command %s', firstCommand);
                logger_1.default.error('Unknown command', `"${firstCommand}"`);
                program.outputHelp();
                return process.exit(1);
            }
            if (includesVersion(args)) {
                // commander 2.11.0 changes behavior
                // and now does not understand top level options
                // .option('-v, --version').command('version')
                // so we have to manually catch '-v, --version'
                handleVersion(program);
            }
            debug('program parsing arguments');
            return program.parse(args);
        });
    },
};
exports.default = cliModule;
