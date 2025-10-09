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
const os_1 = __importDefault(require("os"));
const path_1 = __importDefault(require("path"));
const chalk_1 = __importDefault(require("chalk"));
const debug_1 = __importDefault(require("debug"));
const listr2_1 = require("listr2");
const log_symbols_1 = __importDefault(require("log-symbols"));
const common_tags_1 = require("common-tags");
const promises_1 = __importDefault(require("timers/promises"));
const fs_extra_1 = __importDefault(require("fs-extra"));
const download_1 = __importDefault(require("./download"));
const util_1 = __importDefault(require("../util"));
const state_1 = __importDefault(require("./state"));
const unzip_1 = __importDefault(require("./unzip"));
const logger_1 = __importDefault(require("../logger"));
const errors_1 = require("../errors");
const VerboseRenderer_1 = __importDefault(require("../VerboseRenderer"));
const debug = (0, debug_1.default)('cypress:cli');
// Import package.json dynamically to avoid TypeScript JSON import issues
const { buildInfo, version } = require('../../package.json');
function _getBinaryUrlFromBuildInfo(arch, { commitSha, commitBranch }) {
    const platform = os_1.default.platform();
    if ((platform === 'win32') && (arch === 'arm64')) {
        debug(`detected platform ${platform} architecture ${arch} combination`);
        arch = 'x64';
        debug(`overriding to download ${platform}-${arch} pre-release binary instead`);
    }
    return `https://cdn.cypress.io/beta/binary/${version}/${platform}-${arch}/${commitBranch}-${commitSha}/cypress.zip`;
}
const alreadyInstalledMsg = () => {
    if (!util_1.default.isPostInstall()) {
        logger_1.default.log((0, common_tags_1.stripIndent) `
      Skipping installation:

        Pass the ${chalk_1.default.yellow('--force')} option if you'd like to reinstall anyway.
    `);
    }
};
const displayCompletionMsg = () => {
    // check here to see if we are globally installed
    if (util_1.default.isInstalledGlobally()) {
        // if we are display a warning
        logger_1.default.log();
        logger_1.default.warn((0, common_tags_1.stripIndent) `
      ${log_symbols_1.default.warning} Warning: It looks like you\'ve installed Cypress globally.

        The recommended way to install Cypress is as a devDependency per project.

        You should probably run these commands:

        - ${chalk_1.default.cyan('npm uninstall -g cypress')}
        - ${chalk_1.default.cyan('npm install --save-dev cypress')}
    `);
        return;
    }
    logger_1.default.log();
    logger_1.default.log('You can now open Cypress by running one of the following, depending on your package manager:');
    logger_1.default.log();
    logger_1.default.log(chalk_1.default.cyan('- npx cypress open'));
    logger_1.default.log(chalk_1.default.cyan('- yarn cypress open'));
    logger_1.default.log(chalk_1.default.cyan('- pnpm cypress open'));
    logger_1.default.log();
    logger_1.default.log(chalk_1.default.grey('https://on.cypress.io/opening-the-app'));
    logger_1.default.log();
};
const downloadAndUnzip = ({ version, installDir, downloadDir }) => {
    const progress = {
        throttle: 100,
        onProgress: null,
    };
    const downloadDestination = path_1.default.join(downloadDir, `cypress-${process.pid}.zip`);
    const rendererOptions = getRendererOptions();
    // let the user know what version of cypress we're downloading!
    logger_1.default.log(`Installing Cypress ${chalk_1.default.gray(`(version: ${version})`)}`);
    logger_1.default.log();
    const tasks = new listr2_1.Listr([
        {
            options: { title: util_1.default.titleize('Downloading Cypress') },
            task: (ctx, task) => __awaiter(void 0, void 0, void 0, function* () {
                // as our download progresses indicate the status
                progress.onProgress = progessify(task, 'Downloading Cypress');
                const redirectVersion = yield download_1.default.start({ version, downloadDestination, progress });
                if (redirectVersion)
                    version = redirectVersion;
                debug(`finished downloading file: ${downloadDestination}`);
                // save the download destination for unzipping
                util_1.default.setTaskTitle(task, util_1.default.titleize(chalk_1.default.green('Downloaded Cypress')), rendererOptions.renderer);
            }),
        },
        unzipTask({
            progress,
            zipFilePath: downloadDestination,
            installDir,
            rendererOptions,
        }),
        {
            options: { title: util_1.default.titleize('Finishing Installation') },
            task: (ctx, task) => __awaiter(void 0, void 0, void 0, function* () {
                const cleanup = () => __awaiter(void 0, void 0, void 0, function* () {
                    debug('removing zip file %s', downloadDestination);
                    yield fs_extra_1.default.remove(downloadDestination);
                });
                yield cleanup();
                debug('finished installation in', installDir);
                util_1.default.setTaskTitle(task, util_1.default.titleize(chalk_1.default.green('Finished Installation'), chalk_1.default.gray(installDir)), rendererOptions.renderer);
            }),
        },
    ], { rendererOptions });
    // start the tasks!
    return tasks.run();
};
const validateOS = () => __awaiter(void 0, void 0, void 0, function* () {
    const platformInfo = yield util_1.default.getPlatformInfo();
    return platformInfo.match(/(win32-x64|win32-arm64|linux-x64|linux-arm64|darwin-x64|darwin-arm64)/);
});
/**
 * Returns the version to install - either a string like `1.2.3` to be fetched
 * from the download server or a file path or HTTP URL.
 */
function getVersionOverride({ arch, envVarVersion, buildInfo }) {
    // let this environment variable reset the binary version we need
    if (envVarVersion) {
        return envVarVersion;
    }
    if (buildInfo && !buildInfo.stable) {
        logger_1.default.log(chalk_1.default.yellow((0, common_tags_1.stripIndent) `
        ${log_symbols_1.default.warning} Warning: You are installing a pre-release build of Cypress.

        Bugs may be present which do not exist in production builds.

        This build was created from:
          * Commit SHA: ${buildInfo.commitSha}
          * Commit Branch: ${buildInfo.commitBranch}
          * Commit Timestamp: ${buildInfo.commitDate}
      `));
        logger_1.default.log();
        return _getBinaryUrlFromBuildInfo(arch, buildInfo);
    }
}
function getEnvVarVersion() {
    if (!util_1.default.getEnv('CYPRESS_INSTALL_BINARY'))
        return;
    // because passed file paths are often double quoted
    // and might have extra whitespace around, be robust and trim the string
    const trimAndRemoveDoubleQuotes = true;
    const envVarVersion = util_1.default.getEnv('CYPRESS_INSTALL_BINARY', trimAndRemoveDoubleQuotes);
    debug('using environment variable CYPRESS_INSTALL_BINARY "%s"', envVarVersion);
    return envVarVersion;
}
const start = (...args_1) => __awaiter(void 0, [...args_1], void 0, function* (options = {}) {
    debug('installing with options %j', options);
    const envVarVersion = getEnvVarVersion();
    if (envVarVersion === '0') {
        debug('environment variable CYPRESS_INSTALL_BINARY = 0, skipping install');
        logger_1.default.log((0, common_tags_1.stripIndent) `
        ${chalk_1.default.yellow('Note:')} Skipping binary installation: Environment variable CYPRESS_INSTALL_BINARY = 0.`);
        logger_1.default.log();
        return;
    }
    lodash_1.default.defaults(options, {
        force: false,
        buildInfo,
    });
    if (util_1.default.getEnv('CYPRESS_CACHE_FOLDER')) {
        const envCache = util_1.default.getEnv('CYPRESS_CACHE_FOLDER');
        logger_1.default.log((0, common_tags_1.stripIndent) `
        ${chalk_1.default.yellow('Note:')} Overriding Cypress cache directory to: ${chalk_1.default.cyan(envCache)}

              Previous installs of Cypress may not be found.
      `);
        logger_1.default.log();
    }
    const pkgVersion = util_1.default.pkgVersion();
    const arch = yield util_1.default.getRealArch();
    const versionOverride = getVersionOverride({ arch, envVarVersion, buildInfo: options.buildInfo });
    const versionToInstall = versionOverride || pkgVersion;
    debug('version in package.json is %s, version to install is %s', pkgVersion, versionToInstall);
    const installDir = state_1.default.getVersionDir(pkgVersion, options.buildInfo);
    const cacheDir = state_1.default.getCacheDir();
    const binaryDir = state_1.default.getBinaryDir(pkgVersion);
    if (!(yield validateOS())) {
        return (0, errors_1.throwFormErrorText)(errors_1.errors.invalidOS)();
    }
    try {
        yield fs_extra_1.default.ensureDir(cacheDir);
    }
    catch (err) {
        if (err.code === 'EACCES') {
            return (0, errors_1.throwFormErrorText)(errors_1.errors.invalidCacheDirectory)((0, common_tags_1.stripIndent) `
        Failed to access ${chalk_1.default.cyan(cacheDir)}:

        ${err.message}
      `);
        }
        throw err;
    }
    const binaryPkg = yield state_1.default.getBinaryPkgAsync(binaryDir);
    const binaryVersion = yield state_1.default.getBinaryPkgVersion(binaryPkg);
    const shouldInstall = () => {
        if (!binaryVersion) {
            debug('no binary installed under cli version');
            return true;
        }
        logger_1.default.log();
        logger_1.default.log((0, common_tags_1.stripIndent) `
      Cypress ${chalk_1.default.green(binaryVersion)} is installed in ${chalk_1.default.cyan(installDir)}
      `);
        logger_1.default.log();
        if (options.force) {
            debug('performing force install over existing binary');
            return true;
        }
        if ((binaryVersion === versionToInstall) || !util_1.default.isSemver(versionToInstall)) {
            // our version matches, tell the user this is a noop
            alreadyInstalledMsg();
            return false;
        }
        return true;
    };
    // noop if we've been told not to download
    if (!shouldInstall()) {
        return debug('Not downloading or installing binary');
    }
    if (envVarVersion) {
        logger_1.default.log(chalk_1.default.yellow((0, common_tags_1.stripIndent) `
        ${log_symbols_1.default.warning} Warning: Forcing a binary version different than the default.

          The CLI expected to install version: ${chalk_1.default.green(pkgVersion)}

          Instead we will install version: ${chalk_1.default.green(versionToInstall)}

          These versions may not work properly together.
      `));
        logger_1.default.log();
    }
    const getLocalFilePath = () => __awaiter(void 0, void 0, void 0, function* () {
        // see if version supplied is a path to a binary
        if (yield fs_extra_1.default.pathExists(versionToInstall)) {
            return path_1.default.extname(versionToInstall) === '.zip' ? versionToInstall : false;
        }
        const possibleFile = util_1.default.formAbsolutePath(versionToInstall);
        debug('checking local file', possibleFile, 'cwd', process.cwd());
        // if this exists return the path to it
        // else false
        if ((yield fs_extra_1.default.pathExists(possibleFile)) && path_1.default.extname(possibleFile) === '.zip') {
            return possibleFile;
        }
        return false;
    });
    const pathToLocalFile = yield getLocalFilePath();
    if (pathToLocalFile) {
        const absolutePath = path_1.default.resolve(versionToInstall);
        debug('found local file at', absolutePath);
        debug('skipping download');
        const rendererOptions = getRendererOptions();
        return new listr2_1.Listr([unzipTask({
                progress: {
                    throttle: 100,
                    onProgress: null,
                },
                zipFilePath: absolutePath,
                installDir,
                rendererOptions,
            })], { rendererOptions }).run();
    }
    if (options.force) {
        debug('Cypress already installed at', installDir);
        debug('but the installation was forced');
    }
    debug('preparing to download and unzip version ', versionToInstall, 'to path', installDir);
    const downloadDir = os_1.default.tmpdir();
    yield downloadAndUnzip({ version: versionToInstall, installDir, downloadDir });
    // delay 1 sec for UX, unless we are testing
    yield promises_1.default.setTimeout(1000);
    displayCompletionMsg();
});
const unzipTask = ({ zipFilePath, installDir, progress, rendererOptions }) => {
    return {
        options: { title: util_1.default.titleize('Unzipping Cypress') },
        task: (ctx, task) => __awaiter(void 0, void 0, void 0, function* () {
            // as our unzip progresses indicate the status
            progress.onProgress = progessify(task, 'Unzipping Cypress');
            yield unzip_1.default.start({ zipFilePath, installDir, progress });
            util_1.default.setTaskTitle(task, util_1.default.titleize(chalk_1.default.green('Unzipped Cypress')), rendererOptions.renderer);
        }),
    };
};
const progessify = (task, title) => {
    // return higher order function
    return (percentComplete, remaining) => {
        const percentCompleteStr = chalk_1.default.white(` ${percentComplete}%`);
        // pluralize seconds remaining
        const remainingStr = chalk_1.default.gray(`${remaining}s`);
        util_1.default.setTaskTitle(task, util_1.default.titleize(title, percentCompleteStr, remainingStr), getRendererOptions().renderer);
    };
};
// if we are running in CI then use
// the verbose renderer else use
// the default
const getRendererOptions = () => {
    let renderer = util_1.default.isCi() ? VerboseRenderer_1.default : 'default';
    if (logger_1.default.logLevel() === 'silent') {
        renderer = 'silent';
    }
    return {
        renderer,
    };
};
exports.default = {
    start,
    _getBinaryUrlFromBuildInfo,
};
