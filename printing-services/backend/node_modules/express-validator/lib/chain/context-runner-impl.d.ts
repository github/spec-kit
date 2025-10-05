import { Request } from '../base';
import { Context, ReadonlyContext } from '../context';
import { ContextBuilder } from '../context-builder';
import { SelectFields } from '../field-selection';
import { Result } from '../validation-result';
import { ContextRunner, ResultWithContext } from './context-runner';
export declare class ResultWithContextImpl extends Result implements ResultWithContext {
    readonly context: ReadonlyContext;
    constructor(context: ReadonlyContext);
}
export declare class ContextRunnerImpl implements ContextRunner {
    private readonly builderOrContext;
    private readonly selectFields;
    constructor(builderOrContext: ContextBuilder | Context, selectFields?: SelectFields);
    run(req: Request, options?: {
        dryRun?: boolean;
    }): Promise<ResultWithContextImpl>;
}
