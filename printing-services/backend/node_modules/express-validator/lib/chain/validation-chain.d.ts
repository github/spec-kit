import { Request } from '../base';
import { ContextBuilder } from '../context-builder';
import { Sanitizers } from './sanitizers';
import { Validators } from './validators';
import { ContextHandler } from './context-handler';
import { ContextRunner } from './context-runner';
export interface ValidationChain extends Validators<ValidationChain>, Sanitizers<ValidationChain>, ContextHandler<ValidationChain>, ContextRunner {
    (req: Request, res: any, next: (error?: any) => void): void;
    builder: ContextBuilder;
}
/**
 * A copy of `ValidationChain` where methods that would return the chain itself can return any other
 * value.
 * Useful for typing functions which accept either standard or custom validation chains.
 */
export type ValidationChainLike = {
    [K in keyof ValidationChain]: ValidationChain[K] extends (...args: infer A) => ValidationChain ? (...args: A) => any : ValidationChain[K];
};
