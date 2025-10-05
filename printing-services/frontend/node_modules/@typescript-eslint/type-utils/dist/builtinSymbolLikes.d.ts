import * as ts from 'typescript';
/**
 * class Foo extends Promise<number> {}
 * Foo.reject
 *  ^ PromiseLike
 */
export declare function isPromiseLike(program: ts.Program, type: ts.Type): boolean;
/**
 * const foo = Promise
 * foo.reject
 *  ^ PromiseConstructorLike
 */
export declare function isPromiseConstructorLike(program: ts.Program, type: ts.Type): boolean;
/**
 * class Foo extends Error {}
 * new Foo()
 *      ^ ErrorLike
 */
export declare function isErrorLike(program: ts.Program, type: ts.Type): boolean;
/**
 * type T = Readonly<Error>
 *      ^ ReadonlyErrorLike
 */
export declare function isReadonlyErrorLike(program: ts.Program, type: ts.Type): boolean;
/**
 * type T = Readonly<{ foo: 'bar' }>
 *      ^ ReadonlyTypeLike
 */
export declare function isReadonlyTypeLike(program: ts.Program, type: ts.Type, predicate?: (subType: ts.Type & {
    aliasSymbol: ts.Symbol;
    aliasTypeArguments: readonly ts.Type[];
}) => boolean): boolean;
export declare function isBuiltinTypeAliasLike(program: ts.Program, type: ts.Type, predicate: (subType: ts.Type & {
    aliasSymbol: ts.Symbol;
    aliasTypeArguments: readonly ts.Type[];
}) => boolean): boolean;
export declare function isBuiltinSymbolLike(program: ts.Program, type: ts.Type, symbolName: string): boolean;
export declare function isBuiltinSymbolLikeRecurser(program: ts.Program, type: ts.Type, predicate: (subType: ts.Type) => boolean | null): boolean;
//# sourceMappingURL=builtinSymbolLikes.d.ts.map