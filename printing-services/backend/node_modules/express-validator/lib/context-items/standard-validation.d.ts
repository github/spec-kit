import { Meta, StandardValidator } from '../base';
import { toString as toStringImpl } from '../utils';
import { Context } from '../context';
import { ContextItem } from './context-item';
export declare class StandardValidation implements ContextItem {
    private readonly validator;
    private readonly negated;
    private readonly options;
    private readonly stringify;
    message: any;
    constructor(validator: StandardValidator, negated: boolean, options?: any[], stringify?: typeof toStringImpl);
    run(context: Context, value: any, meta: Meta): Promise<void>;
}
