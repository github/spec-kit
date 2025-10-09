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
exports.needsSandbox = exports.start = exports.verifyTestRunnerTimeoutMs = void 0;
const lodash_1 = __importDefault(require("lodash"));
const chalk_1 = __importDefault(require("chalk"));
const listr2_1 = require("listr2");
const debug_1 = __importDefault(require("debug"));
const common_tags_1 = require("common-tags");
const bluebird_1 = __importDefault(require("bluebird"));
const log_symbols_1 = __importDefault(require("log-symbols"));
const path_1 = __importDefault(require("path"));
const os_1 = __importDefault(require("os"));
const VerboseRenderer_1 = __importDefault(require("../VerboseRenderer"));
const errors_1 = require("../errors");
const util_1 = __importDefault(require("../util"));
const logger_1 = __importDefault(require("../logger"));
const xvfb_1 = __importDefault(require("../exec/xvfb"));
const state_1 = __importDefault(require("./state"));
const debug = (0, debug_1.default)('cypress:cli');
const verifyTestRunnerTimeoutMs = () => {
    const verifyTimeout = +((util_1.default === null || util_1.default === void 0 ? void 0 : util_1.default.getEnv('CYPRESS_VERIFY_TIMEOUT')) || 'NaN');
    if (lodash_1.default.isNumber(verifyTimeout) && !lodash_1.default.isNaN(verifyTimeout)) {
        return verifyTimeout;
    }
    return 30000;
};
exports.verifyTestRunnerTimeoutMs = verifyTestRunnerTimeoutMs;
const checkExecutable = (binaryDir) => __awaiter(void 0, void 0, void 0, function* () {
    const executable = state_1.default.getPathToExecutable(binaryDir);
    debug('checking if executable exists', executable);
    try {
        const isExecutable = yield util_1.default.isExecutableAsync(executable);
        debug('Binary is executable? :', isExecutable);
        if (!isExecutable) {
            return (0, errors_1.throwFormErrorText)(errors_1.errors.binaryNotExecutable(executable))();
        }
    }
    catch (err) {
        if (err.code === 'ENOENT') {
            if (util_1.default.isCi()) {
                return (0, errors_1.throwFormErrorText)(errors_1.errors.notInstalledCI(executable))();
            }
            return (0, errors_1.throwFormErrorText)(errors_1.errors.missingApp(binaryDir))((0, common_tags_1.stripIndent) `
        Cypress executable not found at: ${chalk_1.default.cyan(executable)}
      `);
        }
        throw err;
    }
});
const runSmokeTest = (binaryDir, options) => {
    let executable = state_1.default.getPathToExecutable(binaryDir);
    const needsXvfb = xvfb_1.default.isNeeded();
    debug('needs Xvfb?', needsXvfb);
    /**
     * Spawn Cypress running smoke test to check if all operating system
     * dependencies are good.
     */
    const spawn = (linuxWithDisplayEnv) => __awaiter(void 0, void 0, void 0, function* () {
        const random = lodash_1.default.random(0, 1000);
        const args = ['--smoke-test', `--ping=${random}`];
        if ((0, exports.needsSandbox)()) {
            // electron requires --no-sandbox to run as root
            debug('disabling Electron sandbox');
            args.unshift('--no-sandbox');
        }
        if (options.dev) {
            executable = 'node';
            args.unshift(path_1.default.resolve(__dirname, '..', '..', '..', 'scripts', 'start.js'));
        }
        const smokeTestCommand = `${executable} ${args.join(' ')}`;
        debug('running smoke test');
        debug('using Cypress executable %s', executable);
        debug('smoke test command:', smokeTestCommand);
        debug('smoke test timeout %d ms', options.smokeTestTimeout);
        const stdioOptions = lodash_1.default.extend({}, {
            env: Object.assign(Object.assign({}, process.env), { FORCE_COLOR: '0' }),
            timeout: options.smokeTestTimeout,
        });
        try {
            const result = yield util_1.default.exec(executable, args, stdioOptions);
            // TODO: when execa > 1.1 is released
            // change this to `result.all` for both stderr and stdout
            // use lodash to be robust during tests against null result or missing stdout
            const smokeTestStdout = lodash_1.default.get(result, 'stdout', '');
            debug('smoke test stdout "%s"', smokeTestStdout);
            if (!util_1.default.stdoutLineMatches(String(random), smokeTestStdout)) {
                debug('Smoke test failed because could not find %d in:', random, result);
                const smokeTestStderr = lodash_1.default.get(result, 'stderr', '');
                const errorText = smokeTestStderr || smokeTestStdout;
                return (0, errors_1.throwFormErrorText)(errors_1.errors.smokeTestFailure(smokeTestCommand, false))(errorText);
            }
        }
        catch (err) {
            debug('Smoke test failed:', err);
            let errMessage = err.stderr || err.message;
            debug('error message:', errMessage);
            if (err.timedOut) {
                debug('error timedOut is true');
                return (0, errors_1.throwFormErrorText)(errors_1.errors.smokeTestFailure(smokeTestCommand, true))(errMessage);
            }
            if (linuxWithDisplayEnv && util_1.default.isBrokenGtkDisplay(errMessage)) {
                util_1.default.logBrokenGtkDisplayWarning();
                return (0, errors_1.throwFormErrorText)(errors_1.errors.invalidSmokeTestDisplayError)(errMessage);
            }
            return (0, errors_1.throwFormErrorText)(errors_1.errors.missingDependency)(errMessage);
        }
    });
    const spawnInXvfb = (linuxWithDisplayEnv) => __awaiter(void 0, void 0, void 0, function* () {
        yield xvfb_1.default.start();
        return spawn(linuxWithDisplayEnv || false).finally(() => __awaiter(void 0, void 0, void 0, function* () {
            yield xvfb_1.default.stop();
        }));
    });
    const userFriendlySpawn = (linuxWithDisplayEnv) => __awaiter(void 0, void 0, void 0, function* () {
        debug('spawning, should retry on display problem?', Boolean(linuxWithDisplayEnv));
        try {
            yield spawn(linuxWithDisplayEnv);
        }
        catch (err) {
            if (err.code === 'INVALID_SMOKE_TEST_DISPLAY_ERROR') {
                return spawnInXvfb(linuxWithDisplayEnv);
            }
            throw err;
        }
    });
    if (needsXvfb) {
        return spawnInXvfb();
    }
    // if we are on linux and there's already a DISPLAY
    // set, then we may need to rerun cypress after
    // spawning our own Xvfb server
    const linuxWithDisplayEnv = util_1.default.isPossibleLinuxWithIncorrectDisplay();
    return userFriendlySpawn(linuxWithDisplayEnv);
};
function testBinary(version, binaryDir, options) {
    debug('running binary verification check', version);
    // if running from 'cypress verify', don't print this message
    if (!options.force) {
        logger_1.default.log((0, common_tags_1.stripIndent) `
    It looks like this is your first time using Cypress: ${chalk_1.default.cyan(version)}
    `);
    }
    logger_1.default.log();
    // if we are running in CI then use
    // the verbose renderer else use
    // the default
    let renderer = util_1.default.isCi() ? VerboseRenderer_1.default : 'default';
    // NOTE: under test we set the listr renderer to 'silent' in order to get deterministic snapshots
    if (logger_1.default.logLevel() === 'silent' || options.listrRenderer)
        renderer = 'silent';
    const rendererOptions = {
        renderer,
    };
    const tasks = new listr2_1.Listr([
        {
            title: util_1.default.titleize('Verifying Cypress can run', chalk_1.default.gray(binaryDir)),
            task: (ctx, task) => __awaiter(this, void 0, void 0, function* () {
                debug('clearing out the verified version');
                yield state_1.default.clearBinaryStateAsync(binaryDir);
                yield Promise.all([
                    runSmokeTest(binaryDir, options),
                    bluebird_1.default.delay(1500), // good user experience
                ]);
                debug('write verified: true');
                yield state_1.default.writeBinaryVerifiedAsync(true, binaryDir);
                util_1.default.setTaskTitle(task, util_1.default.titleize(chalk_1.default.green('Verified Cypress!'), chalk_1.default.gray(binaryDir)), rendererOptions.renderer);
            }),
        },
    ], rendererOptions);
    return tasks.run();
}
const maybeVerify = (installedVersion, binaryDir, options) => __awaiter(void 0, void 0, void 0, function* () {
    const isVerified = yield state_1.default.getBinaryVerifiedAsync(binaryDir);
    debug('is Verified ?', isVerified);
    let shouldVerify = !isVerified;
    // force verify if options.force
    if (options.force) {
        debug('force verify');
        shouldVerify = true;
    }
    if (shouldVerify) {
        yield testBinary(installedVersion, binaryDir, options);
        if (options.welcomeMessage) {
            logger_1.default.log();
            logger_1.default.log('Opening Cypress...');
        }
    }
});
const start = (...args_1) => __awaiter(void 0, [...args_1], void 0, function* (options = {}) {
    debug('verifying Cypress app');
    const packageVersion = util_1.default.pkgVersion();
    let binaryDir = state_1.default.getBinaryDir(packageVersion);
    lodash_1.default.defaults(options, {
        dev: false,
        force: false,
        welcomeMessage: true,
        smokeTestTimeout: (0, exports.verifyTestRunnerTimeoutMs)(),
        skipVerify: util_1.default.getEnv('CYPRESS_SKIP_VERIFY') === 'true',
    });
    if (options.skipVerify) {
        debug('skipping verification of the Cypress app');
        return Promise.resolve();
    }
    if (options.dev) {
        return runSmokeTest('', options);
    }
    const parseBinaryEnvVar = () => __awaiter(void 0, void 0, void 0, function* () {
        const envBinaryPath = util_1.default.getEnv('CYPRESS_RUN_BINARY');
        debug('CYPRESS_RUN_BINARY exists, =', envBinaryPath);
        logger_1.default.log((0, common_tags_1.stripIndent) `
      ${chalk_1.default.yellow('Note:')} You have set the environment variable:

      ${chalk_1.default.white('CYPRESS_RUN_BINARY=')}${chalk_1.default.cyan(envBinaryPath)}

      This overrides the default Cypress binary path used.
    `);
        logger_1.default.log();
        try {
            const isExecutable = yield util_1.default.isExecutableAsync(envBinaryPath);
            debug('CYPRESS_RUN_BINARY is executable? :', isExecutable);
            if (!isExecutable) {
                return (0, errors_1.throwFormErrorText)(errors_1.errors.CYPRESS_RUN_BINARY.notValid(envBinaryPath))((0, common_tags_1.stripIndent) `
        The supplied binary path is not executable
        `);
            }
            const envBinaryDir = yield state_1.default.parseRealPlatformBinaryFolderAsync(envBinaryPath);
            if (!envBinaryDir) {
                return (0, errors_1.throwFormErrorText)(errors_1.errors.CYPRESS_RUN_BINARY.notValid(envBinaryPath))();
            }
            debug('CYPRESS_RUN_BINARY has binaryDir:', envBinaryDir);
            binaryDir = envBinaryDir;
        }
        catch (err) {
            if (err.code === 'ENOENT') {
                return (0, errors_1.throwFormErrorText)(errors_1.errors.CYPRESS_RUN_BINARY.notValid(envBinaryPath))(err.message);
            }
            throw err;
        }
    });
    try {
        debug('checking environment variables');
        if (util_1.default.getEnv('CYPRESS_RUN_BINARY')) {
            yield parseBinaryEnvVar();
        }
        yield checkExecutable(binaryDir);
        debug('binaryDir is ', binaryDir);
        const pkg = yield state_1.default.getBinaryPkgAsync(binaryDir);
        const binaryVersion = state_1.default.getBinaryPkgVersion(pkg);
        if (!binaryVersion) {
            debug('no Cypress binary found for cli version ', packageVersion);
            return (0, errors_1.throwFormErrorText)(errors_1.errors.missingApp(binaryDir))(`
      Cannot read binary version from: ${chalk_1.default.cyan(state_1.default.getBinaryPkgPath(binaryDir))}
    `);
        }
        debug(`Found binary version ${chalk_1.default.green(binaryVersion)} installed in: ${chalk_1.default.cyan(binaryDir)}`);
        if (binaryVersion !== packageVersion) {
            // warn if we installed with CYPRESS_INSTALL_BINARY or changed version
            // in the package.json
            logger_1.default.log(`Found binary version ${chalk_1.default.green(binaryVersion)} installed in: ${chalk_1.default.cyan(binaryDir)}`);
            logger_1.default.log();
            logger_1.default.warn((0, common_tags_1.stripIndent) `


      ${log_symbols_1.default.warning} Warning: Binary version ${chalk_1.default.green(binaryVersion)} does not match the expected package version ${chalk_1.default.green(packageVersion)}

        These versions may not work properly together.
      `);
            logger_1.default.log();
        }
        yield maybeVerify(binaryVersion, binaryDir, options);
    }
    catch (err) {
        if (err.known) {
            throw err;
        }
        return (0, errors_1.throwFormErrorText)(errors_1.errors.unexpected)(err.stack);
    }
});
exports.start = start;
const isLinuxLike = () => os_1.default.platform() !== 'win32';
/**
 * Returns true if running on a system where Electron needs "--no-sandbox" flag.
 * @see https://crbug.com/638180
 *
 * On Debian we had problems running in sandbox even for non-root users.
 * @see https://github.com/cypress-io/cypress/issues/5434
 * Seems there is a lot of discussion around this issue among Electron users
 * @see https://github.com/electron/electron/issues/17972
*/
const needsSandbox = () => isLinuxLike();
exports.needsSandbox = needsSandbox;
