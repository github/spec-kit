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
const child_process_1 = __importDefault(require("child_process"));
const os_1 = __importDefault(require("os"));
const yauzl_1 = __importDefault(require("yauzl"));
const debug_1 = __importDefault(require("debug"));
const extract_zip_1 = __importDefault(require("extract-zip"));
const readline_1 = __importDefault(require("readline"));
const fs_extra_1 = __importDefault(require("fs-extra"));
const errors_1 = require("../errors");
const util_1 = __importDefault(require("../util"));
const assert_1 = __importDefault(require("assert"));
const debug = (0, debug_1.default)('cypress:cli:unzip');
const unzipTools = {
    extract: extract_zip_1.default,
};
// expose this function for simple testing
const unzip = (_a) => __awaiter(void 0, [_a], void 0, function* ({ zipFilePath, installDir, progress }) {
    debug('unzipping from %s', zipFilePath);
    debug('into', installDir);
    if (!zipFilePath) {
        throw new Error('Missing zip filename');
    }
    const startTime = Date.now();
    let yauzlDoneTime = 0;
    yield fs_extra_1.default.ensureDir(installDir);
    yield new Promise((resolve, reject) => {
        return yauzl_1.default.open(zipFilePath, (err, zipFile) => {
            yauzlDoneTime = Date.now();
            if (err) {
                debug('error using yauzl %s', err.message);
                return reject(err);
            }
            const total = zipFile.entryCount;
            debug('zipFile entries count', total);
            const started = new Date();
            let percent = 0;
            let count = 0;
            const notify = (percent) => {
                const elapsed = +new Date() - +started;
                const eta = util_1.default.calculateEta(percent, elapsed);
                progress.onProgress(percent, util_1.default.secsRemaining(eta));
            };
            const tick = () => {
                count += 1;
                percent = ((count / total) * 100);
                const displayPercent = percent.toFixed(0);
                return notify(Number(displayPercent));
            };
            const unzipWithNode = () => __awaiter(void 0, void 0, void 0, function* () {
                debug('unzipping with node.js (slow)');
                const opts = {
                    dir: installDir,
                    onEntry: tick,
                };
                debug('calling Node extract tool %s %o', zipFilePath, opts);
                try {
                    yield unzipTools.extract(zipFilePath, opts);
                    debug('node unzip finished');
                    return resolve();
                }
                catch (err) {
                    const error = err || new Error('Unknown error with Node extract tool');
                    debug('error %s', error.message);
                    return reject(error);
                }
            });
            const unzipFallback = lodash_1.default.once(unzipWithNode);
            const unzipWithUnzipTool = () => {
                debug('unzipping via `unzip`');
                const inflatingRe = /inflating:/;
                const sp = child_process_1.default.spawn('unzip', ['-o', zipFilePath, '-d', installDir]);
                sp.on('error', (err) => {
                    debug('unzip tool error: %s', err.message);
                    unzipFallback();
                });
                sp.on('close', (code) => {
                    debug('unzip tool close with code %d', code);
                    if (code === 0) {
                        percent = 100;
                        notify(percent);
                        return resolve();
                    }
                    debug('`unzip` failed %o', { code });
                    return unzipFallback();
                });
                sp.stdout.on('data', (data) => {
                    if (inflatingRe.test(data)) {
                        return tick();
                    }
                });
                sp.stderr.on('data', (data) => {
                    debug('`unzip` stderr %s', data);
                });
            };
            // we attempt to first unzip with the native osx
            // ditto because its less likely to have problems
            // with corruption, symlinks, or icons causing failures
            // and can handle resource forks
            // http://automatica.com.au/2011/02/unzip-mac-os-x-zip-in-terminal/
            const unzipWithOsx = () => {
                debug('unzipping via `ditto`');
                const copyingFileRe = /^copying file/;
                const sp = child_process_1.default.spawn('ditto', ['-xkV', zipFilePath, installDir]);
                // f-it just unzip with node
                sp.on('error', (err) => {
                    debug(err.message);
                    unzipFallback();
                });
                sp.on('close', (code) => {
                    if (code === 0) {
                        // make sure we get to 100% on the progress bar
                        // because reading in lines is not really accurate
                        percent = 100;
                        notify(percent);
                        return resolve();
                    }
                    debug('`ditto` failed %o', { code });
                    return unzipFallback();
                });
                return readline_1.default.createInterface({
                    input: sp.stderr,
                })
                    .on('line', (line) => {
                    if (copyingFileRe.test(line)) {
                        return tick();
                    }
                });
            };
            switch (os_1.default.platform()) {
                case 'darwin':
                    return unzipWithOsx();
                case 'linux':
                    return unzipWithUnzipTool();
                case 'win32':
                    return unzipWithNode();
                default:
                    return;
            }
        });
    });
    debug('unzip completed %o', {
        yauzlMs: yauzlDoneTime - startTime,
        unzipMs: Date.now() - yauzlDoneTime,
    });
});
function isMaybeWindowsMaxPathLengthError(err) {
    return os_1.default.platform() === 'win32' && err.code === 'ENOENT' && err.syscall === 'realpath';
}
const start = (_a) => __awaiter(void 0, [_a], void 0, function* ({ zipFilePath, installDir, progress }) {
    assert_1.default.ok(lodash_1.default.isString(installDir) && !lodash_1.default.isEmpty(installDir), 'missing installDir');
    if (!progress) {
        progress = { onProgress: () => {
                return {};
            } };
    }
    try {
        const installDirExists = yield fs_extra_1.default.pathExists(installDir);
        if (installDirExists) {
            debug('removing existing unzipped binary', installDir);
            yield fs_extra_1.default.remove(installDir);
        }
        yield unzip({ zipFilePath, installDir, progress });
    }
    catch (err) {
        const errorTemplate = isMaybeWindowsMaxPathLengthError(err) ?
            errors_1.errors.failedUnzipWindowsMaxPathLength
            : errors_1.errors.failedUnzip;
        yield (0, errors_1.throwFormErrorText)(errorTemplate)(err);
    }
});
const unzipModule = {
    start,
    utils: {
        unzip,
        unzipTools,
    },
};
exports.default = unzipModule;
