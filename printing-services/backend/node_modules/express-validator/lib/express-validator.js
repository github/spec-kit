"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ExpressValidator = void 0;
const matched_data_1 = require("./matched-data");
const check_1 = require("./middlewares/check");
const exact_1 = require("./middlewares/exact");
const one_of_1 = require("./middlewares/one-of");
const schema_1 = require("./middlewares/schema");
const validation_result_1 = require("./validation-result");
/* eslint-enable no-use-before-define */
class ExpressValidator {
    constructor(validators, sanitizers, options) {
        this.validators = validators;
        this.sanitizers = sanitizers;
        this.options = options;
        /**
         * Creates a middleware/validation chain for one or more fields that may be located in
         * any of the following:
         *
         * - `req.body`
         * - `req.cookies`
         * - `req.headers`
         * - `req.params`
         * - `req.query`
         *
         * @param fields  a string or array of field names to validate/sanitize
         * @param message an error message to use when failed validations don't specify a custom message.
         *                Defaults to `Invalid Value`.
         */
        this.check = this.buildCheckFunction(['body', 'cookies', 'headers', 'params', 'query']);
        /**
         * Same as {@link ExpressValidator.check}, but only validates in `req.body`.
         */
        this.body = this.buildCheckFunction(['body']);
        /**
         * Same as {@link ExpressValidator.check}, but only validates in `req.cookies`.
         */
        this.cookie = this.buildCheckFunction(['cookies']);
        /**
         * Same as {@link ExpressValidator.check}, but only validates in `req.headers`.
         */
        this.header = this.buildCheckFunction(['headers']);
        /**
         * Same as {@link ExpressValidator.check}, but only validates in `req.params`.
         */
        this.param = this.buildCheckFunction(['params']);
        /**
         * Same as {@link ExpressValidator.check}, but only validates in `req.query`.
         */
        this.query = this.buildCheckFunction(['query']);
        /**
         * Checks whether the request contains exactly only those fields that have been validated.
         *
         * This method is here for convenience; it does exactly the same as `checkExact`.
         *
         * @see {@link checkExact}
         */
        this.checkExact = exact_1.checkExact;
        /**
         * Creates an express middleware with validations for multiple fields at once in the form of
         * a schema object.
         *
         * @param schema the schema to validate.
         * @param defaultLocations which locations to validate in each field. Defaults to every location.
         */
        // NOTE: This method references its own type, so the type cast is necessary.
        this.checkSchema = (0, schema_1.createCheckSchema)((...args) => this.createChain(...args), Object.keys(this.validators || {}), Object.keys(this.sanitizers || {}));
        /**
         * Extracts the validation errors of an express request using the default error formatter of this
         * instance.
         *
         * @see {@link validationResult()}
         * @param req the express request object
         * @returns a `Result` which will by default use the error formatter passed when
         *          instantiating `ExpressValidator`.
         */
        this.validationResult = (req) => {
            const formatter = this.options?.errorFormatter;
            const result = (0, validation_result_1.validationResult)(req);
            return formatter ? result.formatWith(formatter) : result;
        };
        this.validatorEntries = Object.entries(validators || {});
        this.sanitizerEntries = Object.entries(sanitizers || {});
        // Can't use arrow function in the declaration of `buildCheckFunction` due to the following
        // error which only happens when tests are run without Jest cache (so CI only):
        //
        //    'buildCheckFunction' implicitly has type 'any' because it does not have a type annotation
        //    and is referenced directly or indirectly in its own initializer
        this.buildCheckFunction = this.buildCheckFunction.bind(this);
    }
    createChain(fields = '', locations = [], message) {
        const middleware = (0, check_1.check)(fields, locations, message);
        const boundValidators = Object.fromEntries(this.validatorEntries.map(([name, fn]) => [name, () => middleware.custom(fn)]));
        const boundSanitizers = Object.fromEntries(this.sanitizerEntries.map(([name, fn]) => [name, () => middleware.customSanitizer(fn)]));
        return Object.assign(middleware, boundValidators, boundSanitizers);
    }
    buildCheckFunction(locations) {
        return (fields, message) => this.createChain(fields, locations, message);
    }
    /**
     * Creates a middleware that will ensure that at least one of the given validation chains
     * or validation chain groups are valid.
     *
     * If none are, a single error of type `alternative` is added to the request,
     * with the errors of each chain made available under the `nestedErrors` property.
     *
     * @param chains an array of validation chains to check if are valid.
     *               If any of the items of `chains` is an array of validation chains, then all of them
     *               must be valid together for the request to be considered valid.
     */
    oneOf(chains, options) {
        return (0, one_of_1.oneOf)(chains, options);
    }
    /**
     * Extracts data validated or sanitized from the request, and builds an object with them.
     *
     * This method is a shortcut for `matchedData`; it does nothing different than it.
     *
     * @see {@link matchedData}
     */
    matchedData(req, options) {
        return (0, matched_data_1.matchedData)(req, options);
    }
}
exports.ExpressValidator = ExpressValidator;
