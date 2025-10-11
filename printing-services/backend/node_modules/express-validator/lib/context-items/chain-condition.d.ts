import { Meta } from '../base';
import { ContextRunner } from '../chain';
import { Context } from '../context';
import { ContextItem } from './context-item';
export declare class ChainCondition implements ContextItem {
    private readonly chain;
    constructor(chain: ContextRunner);
    run(_context: Context, _value: any, meta: Meta): Promise<void>;
}
