"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.checkConfigFile = exports.processTestingType = exports.throwInvalidOptionError = void 0;
const errors_1 = require("../errors");
/**
 * Throws an error with "details" property from
 * "errors" object.
 * @param {Object} details - Error details
 */
const throwInvalidOptionError = (details) => {
    if (!details) {
        details = errors_1.errors.unknownError;
    }
    // throw this error synchronously, it will be caught later on and
    // the details will be propagated to the promise chain
    const err = new Error();
    err.details = details;
    throw err;
};
exports.throwInvalidOptionError = throwInvalidOptionError;
/**
 * Selects exec args based on the configured `testingType`
 * @param {string} testingType The type of tests being executed
 * @returns {string[]} The array of new exec arguments
 */
const processTestingType = (options) => {
    if (options.e2e && options.component) {
        return (0, exports.throwInvalidOptionError)(errors_1.errors.incompatibleTestTypeFlags);
    }
    if (options.testingType && (options.component || options.e2e)) {
        return (0, exports.throwInvalidOptionError)(errors_1.errors.incompatibleTestTypeFlags);
    }
    if (options.testingType === 'component' || options.component || options.ct) {
        return ['--testing-type', 'component'];
    }
    if (options.testingType === 'e2e' || options.e2e) {
        return ['--testing-type', 'e2e'];
    }
    if (options.testingType) {
        return (0, exports.throwInvalidOptionError)(errors_1.errors.invalidTestingType);
    }
    return [];
};
exports.processTestingType = processTestingType;
/**
 * Throws an error if configFile is string 'false' or boolean false
 * @param {*} options
 */
const checkConfigFile = (options) => {
    // CLI will parse as string, module API can pass in boolean
    if (options.configFile === 'false' || options.configFile === false) {
        (0, exports.throwInvalidOptionError)(errors_1.errors.invalidConfigFile);
    }
};
exports.checkConfigFile = checkConfigFile;
