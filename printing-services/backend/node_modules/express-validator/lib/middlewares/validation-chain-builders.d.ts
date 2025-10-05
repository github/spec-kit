import { ErrorMessage, FieldMessageFactory, Location } from '../base';
/**
 * Creates a variant of `check()` that checks the given request locations.
 *
 * @example
 *  const checkBodyAndQuery = buildCheckFunction(['body', 'query']);
 */
export declare function buildCheckFunction(locations: Location[]): (fields?: string | string[], message?: FieldMessageFactory | ErrorMessage) => import("..").ValidationChain;
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
export declare const check: (fields?: string | string[], message?: FieldMessageFactory | ErrorMessage) => import("..").ValidationChain;
/**
 * Same as {@link check()}, but only validates `req.body`.
 */
export declare const body: (fields?: string | string[], message?: FieldMessageFactory | ErrorMessage) => import("..").ValidationChain;
/**
 * Same as {@link check()}, but only validates `req.cookies`.
 */
export declare const cookie: (fields?: string | string[], message?: FieldMessageFactory | ErrorMessage) => import("..").ValidationChain;
/**
 * Same as {@link check()}, but only validates `req.headers`.
 */
export declare const header: (fields?: string | string[], message?: FieldMessageFactory | ErrorMessage) => import("..").ValidationChain;
/**
 * Same as {@link check()}, but only validates `req.params`.
 */
export declare const param: (fields?: string | string[], message?: FieldMessageFactory | ErrorMessage) => import("..").ValidationChain;
/**
 * Same as {@link check()}, but only validates `req.query`.
 */
export declare const query: (fields?: string | string[], message?: FieldMessageFactory | ErrorMessage) => import("..").ValidationChain;
