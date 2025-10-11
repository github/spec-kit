import type { FieldValues } from '../fields';
import type { BrowserNativeObject, IsAny, IsEqual, Primitive } from '../utils';
import type { ArrayKey, IsTuple, TupleKeys } from './common';
/**
 * Helper function to break apart T1 and check if any are equal to T2
 *
 * See {@link IsEqual}
 */
type AnyIsEqual<T1, T2> = T1 extends T2 ? IsEqual<T1, T2> extends true ? true : never : never;
/**
 * Helper type for recursively constructing paths through a type.
 * This actually constructs the strings and recurses into nested
 * object types.
 *
 * See {@link Path}
 */
type PathImpl<K extends string | number, V, TraversedTypes> = V extends Primitive | BrowserNativeObject ? `${K}` : true extends AnyIsEqual<TraversedTypes, V> ? `${K}` : `${K}` | `${K}.${PathInternal<V, TraversedTypes | V>}`;
/**
 * Helper type for recursively constructing paths through a type.
 * This obscures the internal type param TraversedTypes from exported contract.
 *
 * See {@link Path}
 */
type PathInternal<T, TraversedTypes = T> = T extends ReadonlyArray<infer V> ? IsTuple<T> extends true ? {
    [K in TupleKeys<T>]-?: PathImpl<K & string, T[K], TraversedTypes>;
}[TupleKeys<T>] : PathImpl<ArrayKey, V, TraversedTypes> : {
    [K in keyof T]-?: PathImpl<K & string, T[K], TraversedTypes>;
}[keyof T];
/**
 * Type which eagerly collects all paths through a type
 * @typeParam T - type which should be introspected
 * @example
 * ```
 * Path<{foo: {bar: string}}> = 'foo' | 'foo.bar'
 * ```
 */
export type Path<T> = T extends any ? PathInternal<T> : never;
/**
 * See {@link Path}
 */
export type FieldPath<TFieldValues extends FieldValues> = Path<TFieldValues>;
/**
 * Helper type for recursively constructing paths through a type.
 * This actually constructs the strings and recurses into nested
 * object types.
 *
 * See {@link ArrayPath}
 */
type ArrayPathImpl<K extends string | number, V, TraversedTypes> = V extends Primitive | BrowserNativeObject ? IsAny<V> extends true ? string : never : V extends ReadonlyArray<infer U> ? U extends Primitive | BrowserNativeObject ? IsAny<V> extends true ? string : never : true extends AnyIsEqual<TraversedTypes, V> ? never : `${K}` | `${K}.${ArrayPathInternal<V, TraversedTypes | V>}` : true extends AnyIsEqual<TraversedTypes, V> ? never : `${K}.${ArrayPathInternal<V, TraversedTypes | V>}`;
/**
 * Helper type for recursively constructing paths through a type.
 * This obscures the internal type param TraversedTypes from exported contract.
 *
 * See {@link ArrayPath}
 */
type ArrayPathInternal<T, TraversedTypes = T> = T extends ReadonlyArray<infer V> ? IsTuple<T> extends true ? {
    [K in TupleKeys<T>]-?: ArrayPathImpl<K & string, T[K], TraversedTypes>;
}[TupleKeys<T>] : ArrayPathImpl<ArrayKey, V, TraversedTypes> : {
    [K in keyof T]-?: ArrayPathImpl<K & string, T[K], TraversedTypes>;
}[keyof T];
/**
 * Type which eagerly collects all paths through a type which point to an array
 * type.
 * @typeParam T - type which should be introspected.
 * @example
 * ```
 * Path<{foo: {bar: string[], baz: number[]}}> = 'foo.bar' | 'foo.baz'
 * ```
 */
export type ArrayPath<T> = T extends any ? ArrayPathInternal<T> : never;
/**
 * See {@link ArrayPath}
 */
export type FieldArrayPath<TFieldValues extends FieldValues> = ArrayPath<TFieldValues>;
/**
 * Type to evaluate the type which the given path points to.
 * @typeParam T - deeply nested type which is indexed by the path
 * @typeParam P - path into the deeply nested type
 * @example
 * ```
 * PathValue<{foo: {bar: string}}, 'foo.bar'> = string
 * PathValue<[number, string], '1'> = string
 * ```
 */
export type PathValue<T, P extends Path<T> | ArrayPath<T>> = PathValueImpl<T, P>;
type PathValueImpl<T, P extends string> = T extends any ? P extends `${infer K}.${infer R}` ? K extends keyof T ? PathValueImpl<T[K], R> : K extends `${ArrayKey}` ? T extends ReadonlyArray<infer V> ? PathValueImpl<V, R> : never : never : P extends keyof T ? T[P] : P extends `${ArrayKey}` ? T extends ReadonlyArray<infer V> ? V : never : never : never;
/**
 * See {@link PathValue}
 */
export type FieldPathValue<TFieldValues extends FieldValues, TFieldPath extends FieldPath<TFieldValues>> = PathValue<TFieldValues, TFieldPath>;
/**
 * See {@link PathValue}
 */
export type FieldArrayPathValue<TFieldValues extends FieldValues, TFieldArrayPath extends FieldArrayPath<TFieldValues>> = PathValue<TFieldValues, TFieldArrayPath>;
/**
 * Type to evaluate the type which the given paths point to.
 * @typeParam TFieldValues - field values which are indexed by the paths
 * @typeParam TPath        - paths into the deeply nested field values
 * @example
 * ```
 * FieldPathValues<{foo: {bar: string}}, ['foo', 'foo.bar']>
 *   = [{bar: string}, string]
 * ```
 */
export type FieldPathValues<TFieldValues extends FieldValues, TPath extends FieldPath<TFieldValues>[] | readonly FieldPath<TFieldValues>[]> = {} & {
    [K in keyof TPath]: FieldPathValue<TFieldValues, TPath[K] & FieldPath<TFieldValues>>;
};
/**
 * Type which eagerly collects all paths through a fieldType that matches a give type
 * @typeParam TFieldValues - field values which are indexed by the paths
 * @typeParam TValue       - the value you want to match into each type
 * @example
 * ```typescript
 * FieldPathByValue<{foo: {bar: number}, baz: number, bar: string}, number>
 *   = 'foo.bar' | 'baz'
 * ```
 */
export type FieldPathByValue<TFieldValues extends FieldValues, TValue> = {
    [Key in FieldPath<TFieldValues>]: FieldPathValue<TFieldValues, Key> extends TValue ? Key : never;
}[FieldPath<TFieldValues>];
/**
 * Type which eagerly collects all array paths through a fieldType that matches a give type
 * @typeParam TFieldValues - field values which are indexed by the paths
 * @typeParam TValue       - the value you want to match into each type
 * @example
 * ```typescript
 * FieldArrayPathByValue<{foo: {bar: number}[], baz: number, bar: string}, {bar: number}[]>
 *   = 'foo'
 * ```
 */
export type FieldArrayPathByValue<TFieldValues extends FieldValues, TValue> = {
    [Key in FieldArrayPath<TFieldValues>]: FieldArrayPathValue<TFieldValues, Key> extends TValue ? Key : never;
}[FieldArrayPath<TFieldValues>];
export {};
//# sourceMappingURL=eager.d.ts.map