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
const untildify_1 = __importDefault(require("untildify"));
const debug_1 = __importDefault(require("debug"));
const process_1 = require("process");
const fs_extra_1 = __importDefault(require("fs-extra"));
const util_1 = __importDefault(require("../util"));
const debug = (0, debug_1.default)('cypress:cli');
const getPlatformExecutable = () => {
    const platform = os_1.default.platform();
    switch (platform) {
        case 'darwin': return 'Contents/MacOS/Cypress';
        case 'linux': return 'Cypress';
        case 'win32': return 'Cypress.exe';
        // TODO handle this error using our standard
        default: throw new Error(`Platform: "${platform}" is not supported.`);
    }
};
const getPlatFormBinaryFolder = () => {
    const platform = os_1.default.platform();
    switch (platform) {
        case 'darwin': return 'Cypress.app';
        case 'linux': return 'Cypress';
        case 'win32': return 'Cypress';
        // TODO handle this error using our standard
        default: throw new Error(`Platform: "${platform}" is not supported.`);
    }
};
const getBinaryPkgPath = (binaryDir) => {
    const platform = os_1.default.platform();
    switch (platform) {
        case 'darwin': return path_1.default.join(binaryDir, 'Contents', 'Resources', 'app', 'package.json');
        case 'linux': return path_1.default.join(binaryDir, 'resources', 'app', 'package.json');
        case 'win32': return path_1.default.join(binaryDir, 'resources', 'app', 'package.json');
        // TODO handle this error using our standard
        default: throw new Error(`Platform: "${platform}" is not supported.`);
    }
};
/**
 * Get path to binary directory
*/
const getBinaryDir = (version = util_1.default.pkgVersion()) => {
    return path_1.default.join(getVersionDir(version), getPlatFormBinaryFolder());
};
const getVersionDir = (version = util_1.default.pkgVersion(), buildInfo = util_1.default.pkgBuildInfo()) => {
    if (buildInfo && !buildInfo.stable) {
        version = ['beta', version, buildInfo.commitBranch, buildInfo.commitSha.slice(0, 8)].join('-');
    }
    return path_1.default.join(getCacheDir(), version);
};
/**
 * When executing "npm postinstall" hook, the working directory is set to
 * "<current folder>/node_modules/cypress", which can be surprising when using relative paths.
 */
const isInstallingFromPostinstallHook = () => {
    // individual folders
    const cwdFolders = (0, process_1.cwd)().split(path_1.default.sep);
    const length = cwdFolders.length;
    return cwdFolders[length - 2] === 'node_modules' && cwdFolders[length - 1] === 'cypress';
};
const getCacheDir = () => {
    let cache_directory = util_1.default.getCacheDir();
    if (util_1.default.getEnv('CYPRESS_CACHE_FOLDER')) {
        const envVarCacheDir = (0, untildify_1.default)(util_1.default.getEnv('CYPRESS_CACHE_FOLDER'));
        debug('using environment variable CYPRESS_CACHE_FOLDER %s', envVarCacheDir);
        if (!path_1.default.isAbsolute(envVarCacheDir) && isInstallingFromPostinstallHook()) {
            const packageRootFolder = path_1.default.join('..', '..', envVarCacheDir);
            cache_directory = path_1.default.resolve(packageRootFolder);
            debug('installing from postinstall hook, original root folder is %s', packageRootFolder);
            debug('and resolved cache directory is %s', cache_directory);
        }
        else {
            cache_directory = path_1.default.resolve(envVarCacheDir);
        }
    }
    return cache_directory;
};
const parseRealPlatformBinaryFolderAsync = (binaryPath) => __awaiter(void 0, void 0, void 0, function* () {
    const realPath = yield fs_extra_1.default.realpath(binaryPath);
    debug('CYPRESS_RUN_BINARY has realpath:', realPath);
    if (!realPath.toString().endsWith(getPlatformExecutable())) {
        return false;
    }
    if (os_1.default.platform() === 'darwin') {
        return path_1.default.resolve(realPath, '..', '..', '..');
    }
    return path_1.default.resolve(realPath, '..');
});
const getDistDir = () => {
    return path_1.default.join(__dirname, '..', '..', 'dist');
};
/**
 * Returns full filename to the file that keeps the Test Runner verification state as JSON text.
 * Note: the binary state file will be stored one level up from the given binary folder.
 * @param {string} binaryDir - full path to the folder holding the binary.
 */
const getBinaryStatePath = (binaryDir) => {
    return path_1.default.join(binaryDir, '..', 'binary_state.json');
};
const getBinaryStateContentsAsync = (binaryDir) => __awaiter(void 0, void 0, void 0, function* () {
    const fullPath = getBinaryStatePath(binaryDir);
    try {
        const contents = yield fs_extra_1.default.readJson(fullPath);
        debug('binary_state.json contents:', contents);
        return contents;
    }
    catch (error) {
        if (error.code === 'ENOENT' || error instanceof SyntaxError) {
            debug('could not read binary_state.json file at "%s"', fullPath);
            return {};
        }
        throw error;
    }
});
const getBinaryVerifiedAsync = (binaryDir) => __awaiter(void 0, void 0, void 0, function* () {
    const contents = yield getBinaryStateContentsAsync(binaryDir);
    return contents.verified;
});
const clearBinaryStateAsync = (binaryDir) => __awaiter(void 0, void 0, void 0, function* () {
    yield fs_extra_1.default.remove(getBinaryStatePath(binaryDir));
});
/**
 * Writes the new binary status.
 * @param {boolean} verified The new test runner state after smoke test
 * @param {string} binaryDir Folder holding the binary
 * @returns {Promise<void>} returns a promise
 */
const writeBinaryVerifiedAsync = (verified, binaryDir) => __awaiter(void 0, void 0, void 0, function* () {
    const contents = yield getBinaryStateContentsAsync(binaryDir);
    yield fs_extra_1.default.outputJson(getBinaryStatePath(binaryDir), lodash_1.default.extend(contents, { verified }), { spaces: 2 });
});
const getPathToExecutable = (binaryDir) => {
    return path_1.default.join(binaryDir, getPlatformExecutable());
};
/**
 * Resolves with an object read from the binary app package.json file.
 * If the file does not exist resolves with null
 */
const getBinaryPkgAsync = (binaryDir) => __awaiter(void 0, void 0, void 0, function* () {
    const pathToPackageJson = getBinaryPkgPath(binaryDir);
    debug('Reading binary package.json from:', pathToPackageJson);
    const exists = yield fs_extra_1.default.pathExists(pathToPackageJson);
    if (!exists) {
        return null;
    }
    return fs_extra_1.default.readJson(pathToPackageJson);
});
const getBinaryPkgVersion = (o) => lodash_1.default.get(o, 'version', null);
const getBinaryElectronVersion = (o) => lodash_1.default.get(o, 'electronVersion', null);
const getBinaryElectronNodeVersion = (o) => lodash_1.default.get(o, 'electronNodeVersion', null);
const stateModule = {
    getPathToExecutable,
    getPlatformExecutable,
    // those names start to sound like Java
    getBinaryElectronNodeVersion,
    getBinaryElectronVersion,
    getBinaryPkgVersion,
    getBinaryVerifiedAsync,
    getBinaryPkgAsync,
    getBinaryPkgPath,
    getBinaryDir,
    getCacheDir,
    clearBinaryStateAsync,
    writeBinaryVerifiedAsync,
    parseRealPlatformBinaryFolderAsync,
    getDistDir,
    getVersionDir,
};
exports.default = stateModule;
