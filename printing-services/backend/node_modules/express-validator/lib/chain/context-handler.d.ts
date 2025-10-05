import { CustomValidator } from '../base';
import { Optional } from '../context';
import { ContextRunner } from './context-runner';
export interface BailOptions {
    /**
     * Defines the level at which to stop running further validations:
     * - When set to `chain`, further validations won't be run for this validation chain if there
     *   are any errors.
     * - When set to `request`, no further validations on the same request will be run either if
     *   there are any errors.
     *
     * @default 'chain'
     */
    level?: 'chain' | 'request';
}
export interface OptionalOptions {
    /**
     * Defines which kind of value makes a field optional.
     *
     * - `undefined`: only `undefined` values; equivalent to `value === undefined`
     * - `null`: only `undefined` and `null` values; equivalent to `value == null`
     * - `falsy`: all falsy values; equivalent to `!value`
     *
     * @default 'undefined'
     */
    values?: Exclude<Optional, false>;
    /**
     * Whether a field whose value is `null` or `undefined` is to be considered optional.
     * @default false
     * @deprecated  Use `values` instead.
     */
    nullable?: boolean;
    /**
     * Whether a field whose value is falsy (that is, `0`, `false`, `null`, `undefined` or an empty
     * string) is to be considered optional.
     * @default false
     * @deprecated  Use `values` instead.
     */
    checkFalsy?: boolean;
}
export interface ContextHandler<Chain> {
    /**
     * Stops running validations if any of the previous ones have failed.
     *
     * Useful to prevent a custom validator that touches a database or external API from running when
     * you know it will fail.
     *
     * May be used multiple times in the same validation chain if desired.
     *
     * @example
     *  check('username')
     *    .isEmail()
     *    // If not an email, stop here
     *    .bail()
     *    .custom(checkDenylistDomain)
     *    // If domain is not allowed, don't go check if it already exists
     *    .bail()
     *    .custom(checkEmailExists)
     *
     * @returns the current validation chain
     */
    bail(opts?: BailOptions): Chain;
    /**
     * Adds a condition on whether the validation should continue on a field or not.
     * @param condition may be either
     *  - a custom validator-like function, which must truthy or a promise that resolves to continue
     *    validation. If the return value is falsy, a promise that rejects, or if it throws, validation
     *    will stop.
     * - a validation chain which if it would produce errors, the validation chain stops.
     * @example
     *  check('newPassword')
     *    // Only validate if the old password has been provided
     *    .if((value, { req }) => req.body.oldPassword)
     *    // Or, use it with a a validation chain
     *    .if(body('oldPassword').notEmpty())
     * @returns the current validation chain
     */
    if(condition: CustomValidator | ContextRunner): Chain;
    /**
     * Marks the field(s) of the validation chain as optional.
     * By default, only fields with an `undefined` value are considered optional and will be ignored
     * when validating.
     *
     * @param options an object of options to customize the behavior of optional.
     * @returns the current validation chain
     */
    optional(options?: {
        values?: Optional;
        /**
         * @deprecated use `values` instead
         */
        checkFalsy?: boolean;
        /**
         * @deprecated use `values` instead
         */
        nullable?: boolean;
    } | boolean): Chain;
    /**
     * Hide the field's value in errors returned by `validationResult()`.
     *
     * If the value is confidential information (such as api key),
     * you might want to call this method to prevent exposing it.
     *
     * @param hiddenValue? String to replace the field's value with.
     *   If it's not set, the field value is removed from errors.
     *
     * @returns the current validation chain
     */
    hide(hiddenValue?: string): Chain;
}
