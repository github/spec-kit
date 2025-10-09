import { PromptOptions, PromptSettings } from './prompt.interface';
import { TaskWrapper } from '../lib/task-wrapper';
/**
 * Create a new prompt with Enquirer externally.
 * This extends enquirer so you dont have to give a name to single prompts and such so it is also
 * useful to use externally.
 * @param this
 * @param options
 * @param settings
 */
export declare function createPrompt(this: any, options: PromptOptions | PromptOptions<true>[], settings?: PromptSettings): Promise<any>;
export declare function destroyPrompt(this: TaskWrapper<any, any>, throwError?: boolean): void;
