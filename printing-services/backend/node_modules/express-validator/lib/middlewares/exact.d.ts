import { ErrorMessage, Location, Middleware, UnknownFieldMessageFactory } from '../base';
import { ContextRunner, ValidationChain } from '../chain';
type CheckExactOptions = {
    /**
     * The list of locations which `checkExact()` should check.
     * @default ['body', 'params', 'query']
     */
    locations?: readonly Location[];
    message?: UnknownFieldMessageFactory | ErrorMessage;
};
type CheckExactInput = ValidationChain | ValidationChain[] | (ValidationChain | ValidationChain[])[];
/**
 * Checks whether the request contains exactly only those fields that have been validated.
 *
 * Unknown fields, if found, will generate an error of type `unknown_fields`.
 *
 * @param chains either a single chain, an array of chains, or a mixed array of chains and array of chains.
 *               This means that all of the below are valid:
 * ```
 * checkExact(check('foo'))
 * checkExact([check('foo'), check('bar')])
 * checkExact([check('foo'), check('bar')])
 * checkExact(checkSchema({ ... }))
 * checkExact([checkSchema({ ... }), check('foo')])
 * ```
 * @param opts
 */
export declare function checkExact(chains?: CheckExactInput, opts?: CheckExactOptions): Middleware & ContextRunner;
export {};
