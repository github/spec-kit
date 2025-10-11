import { Context } from '../context';
import { ContextItem } from './context-item';
export declare class Bail implements ContextItem {
    run(context: Context): Promise<void>;
}
