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
const bluebird_1 = __importDefault(require("bluebird"));
const xvfb_1 = __importDefault(require("@cypress/xvfb"));
const common_tags_1 = require("common-tags");
const debug_1 = __importDefault(require("debug"));
const errors_1 = require("../errors");
const util_1 = __importDefault(require("../util"));
const debug = (0, debug_1.default)('cypress:cli');
const debugXvfb = (0, debug_1.default)('cypress:xvfb');
debug.Debug = debugXvfb.Debug = debug_1.default;
const xvfbOptions = {
    displayNum: process.env.XVFB_DISPLAY_NUM,
    timeout: 30000, // milliseconds
    // need to explicitly define screen otherwise electron will crash
    // https://github.com/cypress-io/cypress/issues/6184
    xvfb_args: ['-screen', '0', '1280x1024x24'],
    onStderrData(data) {
        if (debugXvfb.enabled) {
            debugXvfb(data.toString());
        }
    },
};
const xvfb = bluebird_1.default.promisifyAll(new xvfb_1.default(xvfbOptions));
const xvfbModule = {
    _debugXvfb: debugXvfb, // expose for testing
    _xvfb: xvfb, // expose for testing
    _xvfbOptions: xvfbOptions, // expose for testing
    start() {
        return __awaiter(this, void 0, void 0, function* () {
            debug('Starting Xvfb');
            try {
                yield xvfb.startAsync();
                return null;
            }
            catch (e) {
                if (e.nonZeroExitCode === true) {
                    const raiseErrorFn = (0, errors_1.throwFormErrorText)(errors_1.errors.nonZeroExitCodeXvfb);
                    yield raiseErrorFn(e);
                }
                if (e.known) {
                    throw e;
                }
                const raiseErrorFn = (0, errors_1.throwFormErrorText)(errors_1.errors.missingXvfb);
                yield raiseErrorFn(e);
            }
        });
    },
    stop() {
        return __awaiter(this, void 0, void 0, function* () {
            debug('Stopping Xvfb');
            try {
                yield xvfb.stopAsync();
                return null;
            }
            catch (e) {
                return null;
            }
        });
    },
    isNeeded() {
        if (process.env.ELECTRON_RUN_AS_NODE) {
            debug('Environment variable ELECTRON_RUN_AS_NODE detected, xvfb is not needed');
            return false; // xvfb required for electron processes only.
        }
        if (os_1.default.platform() !== 'linux') {
            return false;
        }
        if (process.env.DISPLAY) {
            const issueUrl = util_1.default.getGitHubIssueUrl(4034);
            const message = (0, common_tags_1.stripIndent) `
        DISPLAY environment variable is set to ${process.env.DISPLAY} on Linux
        Assuming this DISPLAY points at working X11 server,
        Cypress will not spawn own Xvfb

        NOTE: if the X11 server is NOT working, Cypress will exit without explanation,
          see ${issueUrl}
        Solution: Unset the DISPLAY variable and try again:
          DISPLAY= npx cypress run ...
      `;
            debug(message);
            return false;
        }
        debug('undefined DISPLAY environment variable');
        debug('Cypress will spawn its own Xvfb');
        return true;
    },
    // async method, resolved with Boolean
    verify() {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                yield xvfb.startAsync();
                return true;
            }
            catch (err) {
                debug('Could not verify xvfb: %s', err.message);
                return false;
            }
            finally {
                yield xvfb.stopAsync();
            }
        });
    },
};
exports.default = xvfbModule;
