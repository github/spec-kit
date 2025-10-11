import { CustomSanitizer, CustomValidator, ErrorMessage, FieldMessageFactory, Location, Request } from '../base';
import { BailOptions, OptionalOptions, ValidationChain, ValidationChainLike } from '../chain';
import { ResultWithContext } from '../chain/context-runner';
import { Sanitizers } from '../chain/sanitizers';
import { Validators } from '../chain/validators';
type BaseValidatorSchemaOptions = {
    /**
     * The error message if there's a validation error,
     * or a function for creating an error message dynamically.
     */
    errorMessage?: FieldMessageFactory | ErrorMessage;
    /**
     * Whether the validation should be reversed.
     */
    negated?: boolean;
    /**
     * Whether the validation should bail after running this validator
     */
    bail?: boolean | BailOptions;
    /**
     * Specify a condition upon which this validator should run.
     * Can either be a validation chain, or a custom validator function.
     */
    if?: CustomValidator | ValidationChain;
};
type ValidatorSchemaOptions<K extends keyof Validators<any>> = boolean | (BaseValidatorSchemaOptions & {
    /**
     * Options to pass to the validator.
     */
    options?: Parameters<Validators<any>[K]> | Parameters<Validators<any>[K]>[0];
});
type CustomValidatorSchemaOptions = BaseValidatorSchemaOptions & {
    /**
     * The implementation of a custom validator.
     */
    custom: CustomValidator;
};
export type ExtensionValidatorSchemaOptions = boolean | BaseValidatorSchemaOptions;
export type ValidatorsSchema = {
    [K in Exclude<keyof Validators<any>, 'not' | 'withMessage'>]?: ValidatorSchemaOptions<K>;
};
type SanitizerSchemaOptions<K extends keyof Sanitizers<any>> = boolean | {
    /**
     * Options to pass to the sanitizer.
     */
    options?: Parameters<Sanitizers<any>[K]> | Parameters<Sanitizers<any>[K]>[0];
};
type CustomSanitizerSchemaOptions = {
    /**
     * The implementation of a custom sanitizer.
     */
    customSanitizer: CustomSanitizer;
};
export type ExtensionSanitizerSchemaOptions = true;
export type SanitizersSchema = {
    [K in keyof Sanitizers<any>]?: SanitizerSchemaOptions<K>;
};
type BaseParamSchema = {
    /**
     * Which request location(s) the field to validate is.
     * If unset, the field will be checked in every request location.
     */
    in?: Location | Location[];
    /**
     * The general error message in case a validator doesn't specify one,
     * or a function for creating the error message dynamically.
     */
    errorMessage?: FieldMessageFactory | any;
    /**
     * Whether this field should be considered optional
     */
    optional?: boolean | {
        options?: OptionalOptions;
    };
};
export type DefaultSchemaKeys = keyof BaseParamSchema | keyof ValidatorsSchema | keyof SanitizersSchema;
/**
 * Defines a schema of validations/sanitizations for a field
 */
export type ParamSchema<T extends string = DefaultSchemaKeys> = BaseParamSchema & ValidatorsSchema & SanitizersSchema & {
    [K in T]?: K extends keyof BaseParamSchema ? BaseParamSchema[K] : K extends keyof ValidatorsSchema ? ValidatorsSchema[K] : K extends keyof SanitizersSchema ? SanitizersSchema[K] : CustomValidatorSchemaOptions | CustomSanitizerSchemaOptions;
};
/**
 * Defines a mapping from field name to a validations/sanitizations schema.
 */
export type Schema<T extends string = DefaultSchemaKeys> = Record<string, ParamSchema<T>>;
/**
 * Shortcut type for the return of a {@link checkSchema()}-like function.
 */
export type RunnableValidationChains<C extends ValidationChainLike> = C[] & {
    run(req: Request): Promise<ResultWithContext[]>;
};
/**
 * Factory for a {@link checkSchema()} function which can have extension validators and sanitizers.
 *
 * @see {@link checkSchema()}
 */
export declare function createCheckSchema<C extends ValidationChainLike>(createChain: (fields?: string | string[], locations?: Location[], errorMessage?: any) => C, extraValidators?: (keyof C)[], extraSanitizers?: (keyof C)[]): <T extends string = DefaultSchemaKeys>(schema: Schema<T>, defaultLocations?: Location[]) => RunnableValidationChains<C>;
/**
 * Creates an express middleware with validations for multiple fields at once in the form of
 * a schema object.
 *
 * @param schema the schema to validate.
 * @param defaultLocations
 * @returns
 */
export declare const checkSchema: <T extends string = DefaultSchemaKeys>(schema: Schema<T>, defaultLocations?: Location[]) => RunnableValidationChains<ValidationChain>;
export {};
