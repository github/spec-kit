import { Request, ValidationError } from './base';
/**
 * Given a validation error, returns a new value that represents it.
 */
export type ErrorFormatter<T = any> = (error: ValidationError) => T;
type ToArrayOptions = {
    /**
     * Whether only the first error of each field should be returned.
     * @default false
     */
    onlyFirstError?: boolean;
};
export type ResultFactory<T> = (req: Request) => Result<T>;
interface ResultFactoryBuilderOptions<T = any> {
    /**
     * The default error formatter of every {@link Result} instance returned by
     * the custom `validationResult()` function.
     */
    formatter: ErrorFormatter<T>;
}
/**
 * Extracts the validation errors of an express request
 */
export declare const validationResult: ResultFactory<ValidationError> & {
    withDefaults: typeof withDefaults;
};
/**
 * The current state of the validation errors in a request.
 */
export declare class Result<T = any> {
    private formatter;
    private readonly errors;
    constructor(formatter: ErrorFormatter<T>, errors: readonly ValidationError[]);
    /**
     * Gets the validation errors as an array.
     *
     * @param options.onlyFirstError whether only the first error of each
     */
    array(options?: ToArrayOptions): T[];
    /**
     * Gets the validation errors as an object.
     * If a field has more than one error, only the first one is set in the resulting object.
     *
     * @returns an object from field name to error
     */
    mapped(): Record<string, T>;
    /**
     * Specifies a function to format errors with.
     * @param formatter the function to use for formatting errors
     * @returns A new {@link Result} instance with the given formatter
     */
    formatWith<T2>(formatter: ErrorFormatter<T2>): Result<T2>;
    /**
     * @returns `true` if there are no errors, `false` otherwise
     */
    isEmpty(): boolean;
    /**
     * Throws an error if there are validation errors.
     */
    throw(): void;
}
/**
 * Creates a `validationResult`-like function with default options passed to every {@link Result} it
 * returns.
 */
declare function withDefaults<T = any>(options?: Partial<ResultFactoryBuilderOptions<T>>): ResultFactory<T>;
export {};
