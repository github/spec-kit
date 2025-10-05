import { Meta } from '../base';
import { Context } from '../context';
export interface ContextItem {
    run(context: Context, value: any, meta: Meta): Promise<void>;
}
