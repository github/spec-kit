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
/* eslint-disable no-console */
const spawn_1 = require("./spawn");
const util_1 = __importDefault(require("../util"));
const state_1 = __importDefault(require("../tasks/state"));
const os_1 = __importDefault(require("os"));
const chalk_1 = __importDefault(require("chalk"));
const pretty_bytes_1 = __importDefault(require("pretty-bytes"));
const lodash_1 = __importDefault(require("lodash"));
// color for numbers and show values
const g = chalk_1.default.green;
// color for paths
const p = chalk_1.default.cyan;
const red = chalk_1.default.red;
// urls
const link = chalk_1.default.blue.underline;
// to be exported
const methods = {};
methods.findProxyEnvironmentVariables = () => {
    return lodash_1.default.pick(process.env, ['HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY']);
};
const maskSensitiveVariables = (obj) => {
    const masked = Object.assign({}, obj);
    if (masked.CYPRESS_RECORD_KEY) {
        masked.CYPRESS_RECORD_KEY = '<redacted>';
    }
    return masked;
};
methods.findCypressEnvironmentVariables = () => {
    const isCyVariable = (val, key) => key.startsWith('CYPRESS_');
    return lodash_1.default.pickBy(process.env, isCyVariable);
};
const formatCypressVariables = () => {
    const vars = methods.findCypressEnvironmentVariables();
    return maskSensitiveVariables(vars);
};
methods.start = (...args_1) => __awaiter(void 0, [...args_1], void 0, function* (options = {}) {
    const args = ['--mode=info'];
    yield (0, spawn_1.start)(args, {
        dev: options.dev,
    });
    console.log();
    const proxyVars = methods.findProxyEnvironmentVariables();
    if (lodash_1.default.isEmpty(proxyVars)) {
        console.log('Proxy Settings: none detected');
    }
    else {
        console.log('Proxy Settings:');
        lodash_1.default.forEach(proxyVars, (value, key) => {
            console.log('%s: %s', key, g(value));
        });
        console.log();
        console.log('Learn More: %s', link('https://on.cypress.io/proxy-configuration'));
        console.log();
    }
    const cyVars = formatCypressVariables();
    if (lodash_1.default.isEmpty(cyVars)) {
        console.log('Environment Variables: none detected');
    }
    else {
        console.log('Environment Variables:');
        lodash_1.default.forEach(cyVars, (value, key) => {
            console.log('%s: %s', key, g(value));
        });
    }
    console.log();
    console.log('Application Data:', p(util_1.default.getApplicationDataFolder()));
    console.log('Browser Profiles:', p(util_1.default.getApplicationDataFolder('browsers')));
    console.log('Binary Caches: %s', p(state_1.default.getCacheDir()));
    console.log();
    const osVersion = yield util_1.default.getOsVersionAsync();
    const buildInfo = util_1.default.pkgBuildInfo();
    const isStable = buildInfo && buildInfo.stable;
    console.log('Cypress Version: %s', g(util_1.default.pkgVersion()), isStable ? g('(stable)') : red('(pre-release)'));
    console.log('System Platform: %s (%s)', g(os_1.default.platform()), g(osVersion));
    console.log('System Memory: %s free %s', g((0, pretty_bytes_1.default)(os_1.default.totalmem())), g((0, pretty_bytes_1.default)(os_1.default.freemem())));
    if (!buildInfo) {
        console.log();
        console.log('This is the', red('development'), '(un-built) Cypress CLI.');
    }
    else if (!isStable) {
        console.log();
        console.log('This is a', red('pre-release'), 'build of Cypress.');
        console.log('Build info:');
        console.log('  Commit SHA:', g(buildInfo.commitSha));
        console.log('  Commit Branch:', g(buildInfo.commitBranch));
        console.log('  Commit Date:', g(buildInfo.commitDate));
    }
});
exports.default = methods;
