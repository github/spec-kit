import { Request } from './base';
import { ContextRunningOptions, ResultWithContext, ValidationChainLike } from './chain';
export declare const bindAll: <T>(object: T) => { [K in keyof T]: T[K]; };
export declare function toString(value: any): string;
/**
 * Runs all validation chains, and returns their results.
 *
 * If one of them has a request-level bail set, the previous chains will be awaited on so that
 * results are not skewed, which can be slow.
 * If this same chain also contains errors, no further chains are run.
 */
export declare function runAllChains(req: Request, chains: readonly ValidationChainLike[], runOpts?: ContextRunningOptions): Promise<ResultWithContext[]>;
