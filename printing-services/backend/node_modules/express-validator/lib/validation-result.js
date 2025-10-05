"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Result = exports.validationResult = void 0;
const _ = require("lodash");
const base_1 = require("./base");
const utils_1 = require("./utils");
/**
 * Extracts the validation errors of an express request
 */
exports.validationResult = Object.assign(withDefaults(), { withDefaults });
/**
 * The current state of the validation errors in a request.
 */
class Result {
    constructor(formatter, errors) {
        this.formatter = formatter;
        this.errors = errors;
    }
    /**
     * Gets the validation errors as an array.
     *
     * @param options.onlyFirstError whether only the first error of each
     */
    array(options) {
        return options && options.onlyFirstError
            ? Object.values(this.mapped())
            : this.errors.map(this.formatter);
    }
    /**
     * Gets the validation errors as an object.
     * If a field has more than one error, only the first one is set in the resulting object.
     *
     * @returns an object from field name to error
     */
    mapped() {
        return this.errors.reduce((mapping, error) => {
            const key = error.type === 'field' ? error.path : `_${error.type}`;
            if (!mapping[key]) {
                mapping[key] = this.formatter(error);
            }
            return mapping;
        }, {});
    }
    /**
     * Specifies a function to format errors with.
     * @param formatter the function to use for formatting errors
     * @returns A new {@link Result} instance with the given formatter
     */
    formatWith(formatter) {
        return new Result(formatter, this.errors);
    }
    /**
     * @returns `true` if there are no errors, `false` otherwise
     */
    isEmpty() {
        return this.errors.length === 0;
    }
    /**
     * Throws an error if there are validation errors.
     */
    throw() {
        if (!this.isEmpty()) {
            throw Object.assign(new Error(), (0, utils_1.bindAll)(this));
        }
    }
}
exports.Result = Result;
/**
 * Creates a `validationResult`-like function with default options passed to every {@link Result} it
 * returns.
 */
function withDefaults(options = {}) {
    const defaults = {
        formatter: error => error,
    };
    const actualOptions = _.defaults(options, defaults);
    return (req) => {
        const contexts = req[base_1.contextsKey] || [];
        const errors = _.flatMap(contexts, 'errors');
        return new Result(actualOptions.formatter, errors);
    };
}
