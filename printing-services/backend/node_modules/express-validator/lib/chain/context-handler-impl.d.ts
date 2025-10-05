import { ContextBuilder } from '../context-builder';
import { CustomValidator } from '../base';
import { BailOptions, ContextHandler, OptionalOptions } from './context-handler';
import { ContextRunner } from './context-runner';
export declare class ContextHandlerImpl<Chain> implements ContextHandler<Chain> {
    private readonly builder;
    private readonly chain;
    constructor(builder: ContextBuilder, chain: Chain);
    bail(opts?: BailOptions): Chain;
    if(condition: CustomValidator | ContextRunner): Chain;
    optional(options?: OptionalOptions | boolean): Chain;
    hide(hiddenValue?: string): Chain;
}
