import { CustomSanitizer, CustomValidator, ErrorMessage, FieldMessageFactory, Location, Middleware, Request, ValidationError } from './base';
import { ContextRunner, ValidationChain } from './chain';
import { MatchedDataOptions } from './matched-data';
import { checkExact } from './middlewares/exact';
import { OneOfOptions } from './middlewares/one-of';
import { DefaultSchemaKeys, ExtensionSanitizerSchemaOptions, ExtensionValidatorSchemaOptions, ParamSchema, RunnableValidationChains } from './middlewares/schema';
import { ErrorFormatter, Result } from './validation-result';
type CustomValidatorsMap = Record<string, CustomValidator>;
type CustomSanitizersMap = Record<string, CustomSanitizer>;
type CustomOptions<E = ValidationError> = {
    errorFormatter?: ErrorFormatter<E>;
};
/**
 * A validation chain that contains some extension validators/sanitizers.
 *
 * Built-in methods return the same chain type so that chaining using more of the extensions is
 * possible.
 *
 * @example
 * ```
 * function createChain(chain: ValidationChainWithExtensions<'isAllowedDomain' | 'removeEmailAttribute'>) {
 *  return chain
 *    .isEmail()
 *    .isAllowedDomain()
 *    .trim()
 *    .removeEmailAttribute();
 * }
 * ```
 */
export type ValidationChainWithExtensions<T extends string> = Middleware & {
    [K in keyof ValidationChain]: ValidationChain[K] extends (...args: infer A) => ValidationChain ? (...params: A) => ValidationChainWithExtensions<T> : ValidationChain[K];
} & {
    [K in T]: () => ValidationChainWithExtensions<T>;
};
/**
 * Schema of validations/sanitizations for a field, including extension validators/sanitizers
 */
export type ParamSchemaWithExtensions<V extends string, S extends string, T extends string = DefaultSchemaKeys> = {
    [K in keyof ParamSchema<T> | V | S]?: K extends V ? ExtensionValidatorSchemaOptions : K extends S ? ExtensionSanitizerSchemaOptions : K extends keyof ParamSchema<T> ? ParamSchema<T>[K] : never;
};
/**
 * Type of a validation chain created by a custom ExpressValidator instance.
 *
 * @example
 * ```
 * const myExpressValidator = new ExpressValidator({
 *  isAllowedDomain: value => value.endsWith('@gmail.com')
 * });
 *
 * type MyCustomValidationChain = CustomValidationChain<typeof myExpressValidator>
 * function createMyCustomChain(): MyCustomValidationChain {
 *  return myExpressValidator.body('email').isAllowedDomain();
 * }
 * ```
 */
export type CustomValidationChain<T extends ExpressValidator<any, any, any>> = T extends ExpressValidator<infer V, infer S, any> ? ValidationChainWithExtensions<Extract<keyof V | keyof S, string>> : never;
/**
 * Mapping from field name to a validations/sanitizations schema, including extensions from an
 * ExpressValidator instance.
 */
export type CustomSchema<T extends ExpressValidator<any, any, any>, K extends string = DefaultSchemaKeys> = T extends ExpressValidator<infer V, infer S, any> ? Record<string, ParamSchemaWithExtensions<Extract<keyof V, string>, Extract<keyof S, string>, K>> : never;
export declare class ExpressValidator<V extends CustomValidatorsMap = {}, S extends CustomSanitizersMap = {}, E = ValidationError> {
    private readonly validators?;
    private readonly sanitizers?;
    private readonly options?;
    private readonly validatorEntries;
    private readonly sanitizerEntries;
    constructor(validators?: V | undefined, sanitizers?: S | undefined, options?: CustomOptions<E> | undefined);
    private createChain;
    buildCheckFunction(locations: Location[]): (fields?: string | string[], message?: FieldMessageFactory | ErrorMessage) => CustomValidationChain<this>;
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
    readonly check: (fields?: string | string[], message?: FieldMessageFactory | ErrorMessage) => CustomValidationChain<this>;
    /**
     * Same as {@link ExpressValidator.check}, but only validates in `req.body`.
     */
    readonly body: (fields?: string | string[], message?: FieldMessageFactory | ErrorMessage) => CustomValidationChain<this>;
    /**
     * Same as {@link ExpressValidator.check}, but only validates in `req.cookies`.
     */
    readonly cookie: (fields?: string | string[], message?: FieldMessageFactory | ErrorMessage) => CustomValidationChain<this>;
    /**
     * Same as {@link ExpressValidator.check}, but only validates in `req.headers`.
     */
    readonly header: (fields?: string | string[], message?: FieldMessageFactory | ErrorMessage) => CustomValidationChain<this>;
    /**
     * Same as {@link ExpressValidator.check}, but only validates in `req.params`.
     */
    readonly param: (fields?: string | string[], message?: FieldMessageFactory | ErrorMessage) => CustomValidationChain<this>;
    /**
     * Same as {@link ExpressValidator.check}, but only validates in `req.query`.
     */
    readonly query: (fields?: string | string[], message?: FieldMessageFactory | ErrorMessage) => CustomValidationChain<this>;
    /**
     * Checks whether the request contains exactly only those fields that have been validated.
     *
     * This method is here for convenience; it does exactly the same as `checkExact`.
     *
     * @see {@link checkExact}
     */
    readonly checkExact: typeof checkExact;
    /**
     * Creates an express middleware with validations for multiple fields at once in the form of
     * a schema object.
     *
     * @param schema the schema to validate.
     * @param defaultLocations which locations to validate in each field. Defaults to every location.
     */
    readonly checkSchema: <T extends string = DefaultSchemaKeys>(schema: CustomSchema<this, T>, locations?: Location[]) => RunnableValidationChains<CustomValidationChain<this>>;
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
    oneOf(chains: (CustomValidationChain<this> | CustomValidationChain<this>[])[], options?: OneOfOptions): Middleware & ContextRunner;
    /**
     * Extracts the validation errors of an express request using the default error formatter of this
     * instance.
     *
     * @see {@link validationResult()}
     * @param req the express request object
     * @returns a `Result` which will by default use the error formatter passed when
     *          instantiating `ExpressValidator`.
     */
    readonly validationResult: (req: Request) => Result<E>;
    /**
     * Extracts data validated or sanitized from the request, and builds an object with them.
     *
     * This method is a shortcut for `matchedData`; it does nothing different than it.
     *
     * @see {@link matchedData}
     */
    matchedData(req: Request, options?: Partial<MatchedDataOptions>): Record<string, any>;
}
export {};
