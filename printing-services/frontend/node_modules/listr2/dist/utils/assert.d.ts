/**
 * This function asserts the given value as a function or itself.
 * If the value itself is a function it will evaluate it with the passed in arguments,
 * elsewise it will directly return itself.
 */
export declare function assertFunctionOrSelf<T>(functionOrSelf: T, ...args: T extends (...args: any[]) => any ? Parameters<T> : never): T extends (...args: any[]) => any ? ReturnType<T> : T;
