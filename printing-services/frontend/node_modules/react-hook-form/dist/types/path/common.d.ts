import type { IsAny, IsNever } from '../utils';
/**
 * Type alias to `string` which describes a lodash-like path through an object.
 * E.g. `'foo.bar.0.baz'`
 */
export type PathString = string;
/**
 * Type which can be traversed through with a {@link PathString}.
 * I.e. objects, arrays, and tuples
 */
export type Traversable = object;
/**
 * Type to query whether an array type T is a tuple type.
 * @typeParam T - type which may be an array or tuple
 * @example
 * ```
 * IsTuple<[number]> = true
 * IsTuple<number[]> = false
 * ```
 */
export type IsTuple<T extends ReadonlyArray<any>> = number extends T['length'] ? false : true;
/**
 * Type which can be used to index an array or tuple type.
 */
export type ArrayKey = number;
/**
 * Type which can be used to index an object.
 */
export type Key = string;
/**
 * Type to assert that a type is a {@link Key}.
 * @typeParam T - type which may be a {@link Key}
 */
export type AsKey<T> = Extract<T, Key>;
/**
 * Type to convert a type to a {@link Key}.
 * @typeParam T - type which may be converted to a {@link Key}
 */
export type ToKey<T> = T extends ArrayKey ? `${T}` : AsKey<T>;
/**
 * Type which describes a path through an object
 * as a list of individual {@link Key}s.
 */
export type PathTuple = Key[];
/**
 * Type to assert that a type is a {@link PathTuple}.
 * @typeParam T - type which may be a {@link PathTuple}
 */
export type AsPathTuple<T> = Extract<T, PathTuple>;
/**
 * Type to intersect a union type.
 * See https://fettblog.eu/typescript-union-to-intersection/
 * @typeParam U - union
 * @example
 * ```
 * UnionToIntersection<{ foo: string } | { bar: number }>
 *   = { foo: string; bar: number }
 * ```
 */
export type UnionToIntersection<U> = (U extends any ? (_: U) => any : never) extends (_: infer I) => any ? I : never;
/**
 * Type which appends a {@link Key} to the {@link PathTuple} only if it is not
 * blank, i.e. not the empty string.
 * @typeParam PT - path
 * @typeParam K  - key
 * @example
 * ```
 * AppendNonBlankKey<['foo'], 'bar'> = ['foo', 'bar']
 * AppendNonBlankKey<['foo'], ''> = ['foo']
 * ```
 */
type AppendNonBlankKey<PT extends PathTuple, K extends Key> = K extends '' ? PT : [...PT, K];
/**
 * Type to implement {@link SplitPathString} tail recursively.
 * @typeParam PS - remaining {@link PathString} which should be split into its
 *                 individual {@link Key}s
 * @typeParam PT - accumulator of the {@link Key}s which have been split from
 *                 the original {@link PathString} already
 */
type SplitPathStringImpl<PS extends PathString, PT extends PathTuple> = PS extends `${infer K}.${infer R}` ? SplitPathStringImpl<R, AppendNonBlankKey<PT, K>> : AppendNonBlankKey<PT, PS>;
/**
 * Type to split a {@link PathString} into a {@link PathTuple}.
 * The individual {@link Key}s may be empty strings.
 * @typeParam PS  - {@link PathString} which should be split into its
 *                  individual {@link Key}s
 * @example
 * ```
 * SplitPathString<'foo'> = ['foo']
 * SplitPathString<'foo.bar.0.baz'> = ['foo', 'bar', '0', 'baz']
 * SplitPathString<'.'> = []
 * ```
 */
export type SplitPathString<PS extends PathString> = SplitPathStringImpl<PS, [
]>;
/**
 * Type to implement {@link JoinPathTuple} tail-recursively.
 * @typeParam PT - remaining {@link Key}s which needs to be joined
 * @typeParam PS - accumulator of the already joined {@link Key}s
 */
type JoinPathTupleImpl<PT extends PathTuple, PS extends PathString> = PT extends [infer K, ...infer R] ? JoinPathTupleImpl<AsPathTuple<R>, `${PS}.${AsKey<K>}`> : PS;
/**
 * Type to join a {@link PathTuple} to a {@link PathString}.
 * @typeParam PT - {@link PathTuple} which should be joined.
 * @example
 * ```
 * JoinPathTuple<['foo']> = 'foo'
 * JoinPathTuple<['foo', 'bar', '0', 'baz']> = 'foo.bar.0.baz'
 * JoinPathTuple<[]> = never
 * ```
 */
export type JoinPathTuple<PT extends PathTuple> = PT extends [
    infer K,
    ...infer R
] ? JoinPathTupleImpl<AsPathTuple<R>, AsKey<K>> : never;
/**
 * Type which converts all keys of an object to {@link Key}s.
 * @typeParam T - object type
 * @example
 * ```
 * MapKeys<{0: string}> = {'0': string}
 * ```
 */
type MapKeys<T> = {
    [K in keyof T as ToKey<K>]: T[K];
};
/**
 * Type to access a type by a key.
 *  - Returns undefined if it can't be indexed by that key.
 *  - Returns null if the type is null.
 *  - Returns undefined if the type is not traversable.
 * @typeParam T - type which is indexed by the key
 * @typeParam K - key into the type
 * ```
 * TryAccess<{foo: string}, 'foo'> = string
 * TryAccess<{foo: string}, 'bar'> = undefined
 * TryAccess<null, 'foo'> = null
 * TryAccess<string, 'foo'> = undefined
 * ```
 */
type TryAccess<T, K> = K extends keyof T ? T[K] : T extends null ? null : undefined;
/**
 * Type to access an array type by a key.
 * Returns undefined if the key is non-numeric.
 * @typeParam T - type which is indexed by the key
 * @typeParam K - key into the type
 * ```
 * TryAccessArray<string[], '0'> = string
 * TryAccessArray<string[], 'foo'> = undefined
 * ```
 */
type TryAccessArray<T extends ReadonlyArray<any>, K extends Key> = K extends `${ArrayKey}` ? T[number] : TryAccess<T, K>;
/**
 * Type to evaluate the type which the given key points to.
 * @typeParam T - type which is indexed by the key
 * @typeParam K - key into the type
 * @example
 * ```
 * EvaluateKey<{foo: string}, 'foo'> = string
 * EvaluateKey<[number, string], '1'> = string
 * EvaluateKey<string[], '1'> = string
 * ```
 */
export type EvaluateKey<T, K extends Key> = T extends ReadonlyArray<any> ? IsTuple<T> extends true ? TryAccess<T, K> : TryAccessArray<T, K> : TryAccess<MapKeys<T>, K>;
/**
 * Type to evaluate the type which the given path points to.
 * @typeParam T  - deeply nested type which is indexed by the path
 * @typeParam PT - path into the deeply nested type
 * @example
 * ```
 * EvaluatePath<{foo: {bar: string}}, ['foo', 'bar']> = string
 * EvaluatePath<[number, string], ['1']> = string
 * EvaluatePath<number, []> = number
 * EvaluatePath<number, ['foo']> = undefined
 * ```
 */
export type EvaluatePath<T, PT extends PathTuple> = PT extends [
    infer K,
    ...infer R
] ? EvaluatePath<EvaluateKey<T, AsKey<K>>, AsPathTuple<R>> : T;
/**
 * Type which given a tuple type returns its own keys, i.e. only its indices.
 * @typeParam T - tuple type
 * @example
 * ```
 * TupleKeys<[number, string]> = '0' | '1'
 * ```
 */
export type TupleKeys<T extends ReadonlyArray<any>> = Exclude<keyof T, keyof any[]>;
/**
 * Type which extracts all numeric keys from an object.
 * @typeParam T - type
 * @example
 * ```
 * NumericObjectKeys<{0: string, '1': string, foo: string}> = '0' | '1'
 * ```
 */
type NumericObjectKeys<T extends Traversable> = ToKey<Extract<keyof T, ArrayKey | `${ArrayKey}`>>;
/**
 * Type which extracts all numeric keys from an object, tuple, or array.
 * If a union is passed, it evaluates to the overlapping numeric keys.
 * @typeParam T - type
 * @example
 * ```
 * NumericKeys<{0: string, '1': string, foo: string}> = '0' | '1'
 * NumericKeys<number[]> = `${number}`
 * NumericKeys<[string, number]> = '0' | '1'
 * NumericKeys<{0: string, '1': string} | [number] | number[]> = '0'
 * ```
 */
export type NumericKeys<T extends Traversable> = UnionToIntersection<T extends ReadonlyArray<any> ? IsTuple<T> extends true ? [TupleKeys<T>] : [ToKey<ArrayKey>] : [NumericObjectKeys<T>]>[never];
/**
 * Type which extracts all keys from an object.
 * If a union is passed, it evaluates to the overlapping keys.
 * @typeParam T - object type
 * @example
 * ```
 * ObjectKeys<{foo: string, bar: string}> = 'foo' | 'bar'
 * ObjectKeys<{foo: string, bar: number} | { foo: string }> = 'foo'
 * ```
 */
export type ObjectKeys<T extends Traversable> = Exclude<ToKey<keyof T>, `${string}.${string}` | ''>;
/**
 * Type to check whether a type's property matches the constraint type
 * and return its key. Converts the key to a {@link Key}.
 * @typeParam T - type whose property should be checked
 * @typeParam K - key of the property
 * @typeParam U - constraint type
 * @example
 * ```
 * CheckKeyConstraint<{foo: string}, 'foo', string> = 'foo'
 * CheckKeyConstraint<{foo: string}, 'foo', number> = never
 * CheckKeyConstraint<string[], number, string> = `${number}`
 * ```
 */
export type CheckKeyConstraint<T, K extends Key, U> = K extends any ? EvaluateKey<T, K> extends U ? K : never : never;
/**
 * Type which evaluates to true when the type is an array or tuple or is a union
 * which contains an array or tuple.
 * @typeParam T - type
 * @example
 * ```
 * ContainsIndexable<{foo: string}> = false
 * ContainsIndexable<{foo: string} | number[]> = true
 * ```
 */
export type ContainsIndexable<T> = IsNever<Extract<T, ReadonlyArray<any>>> extends true ? false : true;
/**
 * Type to implement {@link Keys} for non-nullable values.
 * @typeParam T - non-nullable type whose property should be checked
 */
type KeysImpl<T> = [T] extends [Traversable] ? ContainsIndexable<T> extends true ? NumericKeys<T> : ObjectKeys<T> : never;
/**
 * Type to find all properties of a type that match the constraint type
 * and return their keys.
 * If a union is passed, it evaluates to the overlapping keys.
 * @typeParam T - type whose property should be checked
 * @typeParam U - constraint type
 * @example
 * ```
 * Keys<{foo: string, bar: string}, string> = 'foo' | 'bar'
 * Keys<{foo?: string, bar?: string}> = 'foo' | 'bar'
 * Keys<{foo: string, bar: number}, string> = 'foo'
 * Keys<[string, number], string> = '0'
 * Keys<string[], string> = `${number}`
 * Keys<{0: string, '1': string} | [number] | number[]> = '0'
 * ```
 */
export type Keys<T, U = unknown> = IsAny<T> extends true ? Key : IsNever<T> extends true ? Key : IsNever<NonNullable<T>> extends true ? never : CheckKeyConstraint<T, KeysImpl<NonNullable<T>>, U>;
/**
 * Type to check whether a {@link Key} is present in a type.
 * If a union of {@link Key}s is passed, all {@link Key}s have to be present
 * in the type.
 * @typeParam T - type which is introspected
 * @typeParam K - key
 * @example
 * ```
 * HasKey<{foo: string}, 'foo'> = true
 * HasKey<{foo: string}, 'bar'> = false
 * HasKey<{foo: string}, 'foo' | 'bar'> = false
 * ```
 */
export type HasKey<T, K extends Key> = IsNever<Exclude<K, Keys<T>>>;
/**
 * Type to implement {@link ValidPathPrefix} tail recursively.
 * @typeParam T   - type which the path should be checked against
 * @typeParam PT  - path which should exist within the given type
 * @typeParam VPT - accumulates the prefix of {@link Key}s which have been
 *                  confirmed to exist already
 */
type ValidPathPrefixImpl<T, PT extends PathTuple, VPT extends PathTuple> = PT extends [infer K, ...infer R] ? HasKey<T, AsKey<K>> extends true ? ValidPathPrefixImpl<EvaluateKey<T, AsKey<K>>, AsPathTuple<R>, AsPathTuple<[...VPT, K]>> : VPT : VPT;
/**
 * Type to find the longest path prefix which is still valid,
 * i.e. exists within the given type.
 * @typeParam T  - type which the path should be checked against
 * @typeParam PT - path which should exist within the given type
 * @example
 * ```
 * ValidPathPrefix<{foo: {bar: string}}, ['foo', 'bar']> = ['foo', 'bar']
 * ValidPathPrefix<{foo: {bar: string}}, ['foo', 'ba']> = ['foo']
 * ```
 */
export type ValidPathPrefix<T, PT extends PathTuple> = ValidPathPrefixImpl<T, PT, [
]>;
/**
 * Type to check whether a path through a type exists.
 * @typeParam T  - type which the path should be checked against
 * @typeParam PT - path which should exist within the given type
 * @example
 * ```
 * HasPath<{foo: {bar: string}}, ['foo', 'bar']> = true
 * HasPath<{foo: {bar: string}}, ['foo', 'ba']> = false
 * ```
 */
export type HasPath<T, PT extends PathTuple> = ValidPathPrefix<T, PT> extends PT ? true : false;
export {};
//# sourceMappingURL=common.d.ts.map