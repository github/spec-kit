import { Context } from '../context';
import { CustomSanitizer, Meta, StandardSanitizer } from '../base';
import { toString as toStringImpl } from '../utils';
import { ContextItem } from './context-item';
export declare class Sanitization implements ContextItem {
    private readonly sanitizer;
    private readonly custom;
    private readonly options;
    private readonly stringify;
    constructor(sanitizer: StandardSanitizer | CustomSanitizer, custom: boolean, options?: any[], stringify?: typeof toStringImpl);
    run(context: Context, value: any, meta: Meta): Promise<void>;
}
