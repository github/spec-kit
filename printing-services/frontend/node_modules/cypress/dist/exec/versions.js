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
const debug_1 = __importDefault(require("debug"));
const path_1 = __importDefault(require("path"));
const util_1 = __importDefault(require("../util"));
const state_1 = __importDefault(require("../tasks/state"));
const errors_1 = require("../errors");
const debug = (0, debug_1.default)('cypress:cli');
const getBinaryDirectory = () => __awaiter(void 0, void 0, void 0, function* () {
    if (util_1.default.getEnv('CYPRESS_RUN_BINARY')) {
        let envBinaryPath = path_1.default.resolve(util_1.default.getEnv('CYPRESS_RUN_BINARY'));
        try {
            const envBinaryDir = yield state_1.default.parseRealPlatformBinaryFolderAsync(envBinaryPath);
            if (!envBinaryDir) {
                const raiseErrorFn = (0, errors_1.throwFormErrorText)(errors_1.errors.CYPRESS_RUN_BINARY.notValid(envBinaryPath));
                yield raiseErrorFn();
            }
            debug('CYPRESS_RUN_BINARY has binaryDir:', envBinaryDir);
            return envBinaryDir;
        }
        catch (err) {
            const raiseErrorFn = (0, errors_1.throwFormErrorText)(errors_1.errors.CYPRESS_RUN_BINARY.notValid(envBinaryPath));
            yield raiseErrorFn(err.message);
        }
    }
    return state_1.default.getBinaryDir();
});
const getVersions = () => __awaiter(void 0, void 0, void 0, function* () {
    const binDir = yield getBinaryDirectory();
    const pkg = yield state_1.default.getBinaryPkgAsync(binDir);
    const versions = {
        binary: state_1.default.getBinaryPkgVersion(pkg),
        electronVersion: state_1.default.getBinaryElectronVersion(pkg),
        electronNodeVersion: state_1.default.getBinaryElectronNodeVersion(pkg),
    };
    debug('binary versions %o', versions);
    const buildInfo = util_1.default.pkgBuildInfo();
    let packageVersion = util_1.default.pkgVersion();
    if (!buildInfo)
        packageVersion += ' (development)';
    else if (!buildInfo.stable)
        packageVersion += ' (pre-release)';
    const versionsFinal = {
        package: packageVersion,
        binary: versions.binary || 'not installed',
        electronVersion: versions.electronVersion || 'not found',
        electronNodeVersion: versions.electronNodeVersion || 'not found',
    };
    debug('combined versions %o', versions);
    return versionsFinal;
});
const versionsModule = {
    getVersions,
};
exports.default = versionsModule;
