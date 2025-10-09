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
const lodash_1 = __importDefault(require("lodash"));
const debug_1 = __importDefault(require("debug"));
const util_1 = __importDefault(require("../util"));
const spawn_1 = require("./spawn");
const verify_1 = require("../tasks/verify");
const errors_1 = require("../errors");
const shared_1 = require("./shared");
const debug = (0, debug_1.default)('cypress:cli:run');
/**
 * Typically a user passes a string path to the project.
 * But "cypress open" allows using `false` to open in global mode,
 * and the user can accidentally execute `cypress run --project false`
 * which should be invalid.
 */
const isValidProject = (v) => {
    if (typeof v === 'boolean') {
        return false;
    }
    if (v === '' || v === 'false' || v === 'true') {
        return false;
    }
    return true;
};
/**
 * Maps options collected by the CLI
 * and forms list of CLI arguments to the server.
 *
 * Note: there is lightweight validation, with errors
 * thrown synchronously.
 *
 * @returns {string[]} list of CLI arguments
 */
const processRunOptions = (options = {}) => {
    debug('processing run options %o', options);
    if (!isValidProject(options.project)) {
        debug('invalid project option %o', { project: options.project });
        return (0, shared_1.throwInvalidOptionError)(errors_1.errors.invalidRunProjectPath);
    }
    const args = ['--run-project', options.project];
    if (options.autoCancelAfterFailures || options.autoCancelAfterFailures === 0 || options.autoCancelAfterFailures === false) {
        args.push('--auto-cancel-after-failures', options.autoCancelAfterFailures);
    }
    if (options.browser) {
        args.push('--browser', options.browser);
    }
    if (options.ciBuildId) {
        args.push('--ci-build-id', options.ciBuildId);
    }
    if (options.config) {
        args.push('--config', options.config);
    }
    if (options.configFile !== undefined) {
        (0, shared_1.checkConfigFile)(options);
        args.push('--config-file', options.configFile);
    }
    if (options.env) {
        args.push('--env', options.env);
    }
    if (options.exit === false) {
        args.push('--no-exit');
    }
    if (options.group) {
        args.push('--group', options.group);
    }
    if (options.headed) {
        args.push('--headed', options.headed);
    }
    if (options.headless) {
        if (options.headed) {
            return (0, shared_1.throwInvalidOptionError)(errors_1.errors.incompatibleHeadlessFlags);
        }
        args.push('--headed', String(!options.headless));
    }
    // if key is set use that - else attempt to find it by environment variable
    if (options.key == null) {
        debug('--key is not set, looking up environment variable CYPRESS_RECORD_KEY');
        options.key = util_1.default.getEnv('CYPRESS_RECORD_KEY');
    }
    // if we have a key assume we're in record mode
    if (options.key) {
        args.push('--key', options.key);
    }
    if (options.outputPath) {
        args.push('--output-path', options.outputPath);
    }
    if (options.parallel) {
        args.push('--parallel');
    }
    if (options.posixExitCodes) {
        args.push('--posix-exit-codes');
    }
    if (options.port) {
        args.push('--port', options.port);
    }
    if (options.quiet) {
        args.push('--quiet');
    }
    // if record is defined and we're not
    // already in ci mode, then send it up
    if (options.record != null) {
        args.push('--record', options.record);
    }
    // if we have a specific reporter push that into the args
    if (options.reporter) {
        args.push('--reporter', options.reporter);
    }
    // if we have a specific reporter push that into the args
    if (options.reporterOptions) {
        args.push('--reporter-options', options.reporterOptions);
    }
    if (options.runnerUi != null) {
        args.push('--runner-ui', options.runnerUi);
    }
    // if we have specific spec(s) push that into the args
    if (options.spec) {
        args.push('--spec', options.spec);
    }
    if (options.tag) {
        args.push('--tag', options.tag);
    }
    if (options.inspect) {
        args.push('--inspect');
    }
    if (options.inspectBrk) {
        args.push('--inspectBrk');
    }
    args.push(...(0, shared_1.processTestingType)(options));
    return args;
};
const runModule = {
    processRunOptions,
    isValidProject,
    // resolves with the number of failed tests
    start() {
        return __awaiter(this, arguments, void 0, function* (options = {}) {
            lodash_1.default.defaults(options, {
                key: null,
                spec: null,
                reporter: null,
                reporterOptions: null,
                project: process.cwd(),
            });
            function run() {
                try {
                    const args = processRunOptions(options);
                    debug('run to spawn.start args %j', args);
                    return (0, spawn_1.start)(args, {
                        dev: options.dev,
                    });
                }
                catch (err) {
                    if (err.details) {
                        return (0, errors_1.exitWithError)(err.details)();
                    }
                    throw err;
                }
            }
            if (options.dev) {
                return run();
            }
            yield (0, verify_1.start)();
            return run();
        });
    },
};
exports.default = runModule;
