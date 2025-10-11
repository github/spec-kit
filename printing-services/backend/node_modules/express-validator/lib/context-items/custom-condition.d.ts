import { CustomValidator, Meta } from '../base';
import { Context } from '../context';
import { ContextItem } from './context-item';
export declare class CustomCondition implements ContextItem {
    private readonly condition;
    constructor(condition: CustomValidator);
    run(_context: Context, value: any, meta: Meta): Promise<void>;
}
