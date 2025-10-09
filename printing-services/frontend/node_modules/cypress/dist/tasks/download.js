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
const os_1 = __importDefault(require("os"));
const assert_1 = __importDefault(require("assert"));
const lodash_1 = __importDefault(require("lodash"));
const url_1 = __importDefault(require("url"));
const path_1 = __importDefault(require("path"));
const debug_1 = __importDefault(require("debug"));
const request_1 = __importDefault(require("@cypress/request"));
const bluebird_1 = __importDefault(require("bluebird"));
const request_progress_1 = __importDefault(require("request-progress"));
const common_tags_1 = require("common-tags");
const proxy_from_env_1 = require("proxy-from-env");
const errors_1 = require("../errors");
const fs_extra_1 = __importDefault(require("fs-extra"));
const util_1 = __importDefault(require("../util"));
const debug = (0, debug_1.default)('cypress:cli');
const defaultBaseUrl = 'https://download.cypress.io/';
const defaultMaxRedirects = 10;
const getProxyForUrlWithNpmConfig = (url) => {
    return (0, proxy_from_env_1.getProxyForUrl)(url) ||
        process.env.npm_config_https_proxy ||
        process.env.npm_config_proxy ||
        null;
};
const getBaseUrl = () => {
    if (util_1.default.getEnv('CYPRESS_DOWNLOAD_MIRROR')) {
        let baseUrl = util_1.default.getEnv('CYPRESS_DOWNLOAD_MIRROR');
        if (!(baseUrl === null || baseUrl === void 0 ? void 0 : baseUrl.endsWith('/'))) {
            baseUrl += '/';
        }
        return baseUrl || defaultBaseUrl;
    }
    return defaultBaseUrl;
};
const getCA = () => __awaiter(void 0, void 0, void 0, function* () {
    if (process.env.npm_config_cafile) {
        try {
            const caFileContent = yield fs_extra_1.default.readFile(process.env.npm_config_cafile, 'utf8');
            return caFileContent;
        }
        catch (error) {
            debug('error reading ca file', error);
            return;
        }
    }
    if (process.env.npm_config_ca) {
        return process.env.npm_config_ca;
    }
    return;
});
const prepend = (arch, urlPath, version) => {
    const endpoint = url_1.default.resolve(getBaseUrl(), urlPath);
    const platform = os_1.default.platform();
    const pathTemplate = util_1.default.getEnv('CYPRESS_DOWNLOAD_PATH_TEMPLATE', true);
    if ((platform === 'win32') && (arch === 'arm64')) {
        debug(`detected platform ${platform} architecture ${arch} combination`);
        arch = 'x64';
        debug(`overriding to download ${platform}-${arch} instead`);
    }
    return pathTemplate
        ? (pathTemplate
            .replace(/\\?\$\{endpoint\}/g, endpoint)
            .replace(/\\?\$\{platform\}/g, platform)
            .replace(/\\?\$\{arch\}/g, arch)
            .replace(/\\?\$\{version\}/g, version))
        : `${endpoint}?platform=${platform}&arch=${arch}`;
};
const getUrl = (arch, version) => {
    if (lodash_1.default.isString(version) && version.match(/^https?:\/\/.*$/)) {
        debug('version is already an url', version);
        return version;
    }
    const urlPath = version ? `desktop/${version}` : 'desktop';
    return prepend(arch, urlPath, version || '');
};
const statusMessage = (err) => {
    return (err.statusCode
        ? [err.statusCode, err.statusMessage].join(' - ')
        : err.toString());
};
const prettyDownloadErr = (err, url) => {
    const msg = (0, common_tags_1.stripIndent) `
    URL: ${url}
    ${statusMessage(err)}
  `;
    debug(msg);
    return (0, errors_1.throwFormErrorText)(errors_1.errors.failedDownload)(msg);
};
/**
 * Checks checksum and file size for the given file. Allows both
 * values or just one of them to be checked.
 */
const verifyDownloadedFile = (filename, expectedSize, expectedChecksum) => __awaiter(void 0, void 0, void 0, function* () {
    if (expectedSize && expectedChecksum) {
        debug('verifying checksum and file size');
        return bluebird_1.default.join(util_1.default.getFileChecksum(filename), util_1.default.getFileSize(filename), (checksum, filesize) => {
            if (checksum === expectedChecksum && filesize === expectedSize) {
                debug('downloaded file has the expected checksum and size ✅');
                return;
            }
            debug('raising error: checksum or file size mismatch');
            const text = (0, common_tags_1.stripIndent) `
          Corrupted download

          Expected downloaded file to have checksum: ${expectedChecksum}
          Computed checksum: ${checksum}

          Expected downloaded file to have size: ${expectedSize}
          Computed size: ${filesize}
        `;
            debug(text);
            throw new Error(text);
        });
    }
    if (expectedChecksum) {
        debug('only checking expected file checksum %d', expectedChecksum);
        const checksum = yield util_1.default.getFileChecksum(filename);
        if (checksum === expectedChecksum) {
            debug('downloaded file has the expected checksum ✅');
            return;
        }
        debug('raising error: file checksum mismatch');
        const text = (0, common_tags_1.stripIndent) `
      Corrupted download

      Expected downloaded file to have checksum: ${expectedChecksum}
      Computed checksum: ${checksum}
    `;
        throw new Error(text);
    }
    if (expectedSize) {
        // maybe we don't have a checksum, but at least CDN returns content length
        // which we can check against the file size
        debug('only checking expected file size %d', expectedSize);
        const filesize = yield util_1.default.getFileSize(filename);
        if (filesize === expectedSize) {
            debug('downloaded file has the expected size ✅');
            return;
        }
        debug('raising error: file size mismatch');
        const text = (0, common_tags_1.stripIndent) `
        Corrupted download

        Expected downloaded file to have size: ${expectedSize}
        Computed size: ${filesize}
      `;
        throw new Error(text);
    }
    debug('downloaded file lacks checksum or size to verify');
    return;
});
// downloads from given url
// return an object with
// {filename: ..., downloaded: true}
const downloadFromUrl = ({ url, downloadDestination, progress, ca, version, redirectTTL = defaultMaxRedirects }) => {
    if (redirectTTL <= 0) {
        return bluebird_1.default.reject(new Error((0, common_tags_1.stripIndent) `
          Failed downloading the Cypress binary.
          There were too many redirects. The default allowance is ${defaultMaxRedirects}.
          Maybe you got stuck in a redirect loop?
        `));
    }
    return new bluebird_1.default((resolve, reject) => {
        const proxy = getProxyForUrlWithNpmConfig(url);
        debug('Downloading package', {
            url,
            proxy,
            downloadDestination,
        });
        if (ca) {
            debug('using custom CA details from npm config');
        }
        const reqOptions = Object.assign(Object.assign(Object.assign({ uri: url }, (proxy ? { proxy } : {})), (ca ? { agentOptions: { ca } } : {})), { method: 'GET', followRedirect: false });
        const req = (0, request_1.default)(reqOptions);
        // closure
        let started = null;
        let expectedSize;
        let expectedChecksum;
        (0, request_progress_1.default)(req, {
            throttle: progress.throttle,
        })
            .on('response', (response) => {
            // we have computed checksum and filesize during test runner binary build
            // and have set it on the S3 object as user meta data, available via
            // these custom headers "x-amz-meta-..."
            // see https://github.com/cypress-io/cypress/pull/4092
            expectedSize = response.headers['x-amz-meta-size'] ||
                response.headers['content-length'];
            expectedChecksum = response.headers['x-amz-meta-checksum'];
            if (expectedChecksum) {
                debug('expected checksum %s', expectedChecksum);
            }
            if (expectedSize) {
                // convert from string (all Amazon custom headers are strings)
                expectedSize = Number(expectedSize);
                debug('expected file size %d', expectedSize);
            }
            // start counting now once we've gotten
            // response headers
            started = new Date();
            if (/^3/.test(response.statusCode)) {
                const redirectVersion = response.headers['x-version'];
                const redirectUrl = response.headers.location;
                debug('redirect version:', redirectVersion);
                debug('redirect url:', redirectUrl);
                downloadFromUrl({ url: redirectUrl, progress, ca, downloadDestination, version: redirectVersion, redirectTTL: redirectTTL - 1 })
                    .then(resolve).catch(reject);
                // if our status code does not start with 200
            }
            else if (!/^2/.test(response.statusCode)) {
                debug('response code %d', response.statusCode);
                const err = new Error((0, common_tags_1.stripIndent) `
          Failed downloading the Cypress binary.
          Response code: ${response.statusCode}
          Response message: ${response.statusMessage}
        `);
                reject(err);
                // status codes here are all 2xx
            }
            else {
                // We only enable this pipe connection when we know we've got a successful return
                // and handle the completion with verify and resolve
                // there was a possible race condition between end of request and close of writeStream
                // that is made ordered with this Promise.all
                bluebird_1.default.all([new bluebird_1.default((r) => {
                        return response.pipe(fs_extra_1.default.createWriteStream(downloadDestination).on('close', r));
                    }), new bluebird_1.default((r) => response.on('end', r))])
                    .then(() => {
                    debug('downloading finished');
                    verifyDownloadedFile(downloadDestination, expectedSize, expectedChecksum)
                        .then(() => debug('verified'))
                        .then(() => resolve(version))
                        .catch(reject);
                });
            }
        })
            .on('error', (e) => {
            if (e.code === 'ECONNRESET')
                return; // sometimes proxies give ECONNRESET but we don't care
            reject(e);
        })
            .on('progress', (state) => {
            // total time we've elapsed
            // starting on our first progress notification
            const elapsed = +new Date() - +started;
            // request-progress sends a value between 0 and 1
            const percentage = util_1.default.convertPercentToPercentage(state.percent);
            const eta = util_1.default.calculateEta(percentage, elapsed);
            // send up our percent and seconds remaining
            progress.onProgress(percentage, util_1.default.secsRemaining(eta));
        });
    });
};
/**
 * Download Cypress.zip from external versionUrl to local file.
 * @param [string] version Could be "3.3.0" or full URL
 * @param [string] downloadDestination Local filename to save as
 */
const start = (opts) => __awaiter(void 0, void 0, void 0, function* () {
    let { version, downloadDestination, progress, redirectTTL } = opts;
    if (!downloadDestination) {
        assert_1.default.ok(lodash_1.default.isString(downloadDestination) && !lodash_1.default.isEmpty(downloadDestination), 'missing download dir');
    }
    if (!progress) {
        progress = { onProgress: () => {
                return {};
            } };
    }
    const arch = yield util_1.default.getRealArch();
    const versionUrl = getUrl(arch, version);
    progress.throttle = 100;
    debug('needed Cypress version: %s', version);
    debug('source url %s', versionUrl);
    debug(`downloading cypress.zip to "${downloadDestination}"`);
    try {
        // ensure download dir exists
        yield fs_extra_1.default.ensureDir(path_1.default.dirname(downloadDestination));
        const ca = yield getCA();
        return downloadFromUrl(Object.assign({ url: versionUrl, downloadDestination, progress, ca, version }, (redirectTTL ? { redirectTTL } : {})));
    }
    catch (err) {
        return prettyDownloadErr(err, versionUrl);
    }
});
const downloadModule = {
    start,
    getUrl,
    getProxyForUrlWithNpmConfig,
    getCA,
};
exports.default = downloadModule;
