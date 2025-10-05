import { AlternativeMessageFactory, ErrorMessage, GroupedAlternativeMessageFactory, Middleware } from '../base';
import { ContextRunner, ValidationChain } from '../chain';
export type OneOfErrorType = 'grouped' | 'least_errored' | 'flat';
export type OneOfOptions = {
    /**
     * The error message to use in case none of the chains are valid.
     */
    message?: AlternativeMessageFactory | ErrorMessage;
    errorType?: Exclude<OneOfErrorType, 'grouped'>;
} | {
    /**
     * The error message to use in case none of the chain groups are valid.
     */
    message?: GroupedAlternativeMessageFactory | ErrorMessage;
    errorType?: 'grouped';
};
/**
 * Creates a middleware that will ensure that at least one of the given validation chains
 * or validation chain groups are valid.
 *
 * If none are, a single `AlternativeValidationError` or `GroupedAlternativeValidationError`
 * is added to the request, with the errors of each chain made available under the `nestedErrors` property.
 *
 * @param chains an array of validation chains to check if are valid.
 *               If any of the items of `chains` is an array of validation chains, then all of them
 *               must be valid together for the request to be considered valid.
 */
export declare function oneOf(chains: (ValidationChain | ValidationChain[])[], options?: OneOfOptions): Middleware & ContextRunner;
