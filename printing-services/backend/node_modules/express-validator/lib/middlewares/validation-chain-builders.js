"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.query = exports.param = exports.header = exports.cookie = exports.body = exports.check = void 0;
exports.buildCheckFunction = buildCheckFunction;
const check_1 = require("./check");
/**
 * Creates a variant of `check()` that checks the given request locations.
 *
 * @example
 *  const checkBodyAndQuery = buildCheckFunction(['body', 'query']);
 */
function buildCheckFunction(locations) {
    return (fields, message) => (0, check_1.check)(fields, locations, message);
}
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
exports.check = buildCheckFunction(['body', 'cookies', 'headers', 'params', 'query']);
/**
 * Same as {@link check()}, but only validates `req.body`.
 */
exports.body = buildCheckFunction(['body']);
/**
 * Same as {@link check()}, but only validates `req.cookies`.
 */
exports.cookie = buildCheckFunction(['cookies']);
/**
 * Same as {@link check()}, but only validates `req.headers`.
 */
exports.header = buildCheckFunction(['headers']);
/**
 * Same as {@link check()}, but only validates `req.params`.
 */
exports.param = buildCheckFunction(['params']);
/**
 * Same as {@link check()}, but only validates `req.query`.
 */
exports.query = buildCheckFunction(['query']);
