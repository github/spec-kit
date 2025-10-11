import { Request, ValidationError } from '../base';
import { ReadonlyContext } from '../context';
import { Result } from '../validation-result';
export type ContextRunningOptions = {
    /**
     * Defines whether errors and sanitization should be persisted to `req`.
     * @default false
     */
    dryRun?: boolean;
};
export interface ResultWithContext extends Result<ValidationError> {
    readonly context: ReadonlyContext;
}
export interface ContextRunner {
    /**
     * Runs the current validation chain.
     * @param req the express request to validate
     * @param options an object of options to customize how the chain will be run
     * @returns a promise for a {@link Result} that resolves when the validation chain has finished
     */
    run(req: Request, options?: ContextRunningOptions): Promise<ResultWithContext>;
}
