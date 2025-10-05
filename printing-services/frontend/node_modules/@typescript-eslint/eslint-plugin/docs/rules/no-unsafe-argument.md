---
description: 'Disallow calling a function with a value with type `any`.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-unsafe-argument** for documentation.

The `any` type in TypeScript is a dangerous "escape hatch" from the type system.
Using `any` disables many type checking rules and is generally best used only as a last resort or when prototyping code.

Despite your best intentions, the `any` type can sometimes leak into your codebase.
Calling a function with an `any` typed argument creates a potential safety hole and source of bugs.

This rule disallows calling a function with `any` in its arguments.
That includes spreading arrays or tuples with `any` typed elements as function arguments.

This rule also compares generic type argument types to ensure you don't pass an unsafe `any` in a generic position to a receiver that's expecting a specific type.
For example, it will error if you pass `Set<any>` as an argument to a parameter declared as `Set<string>`.

## Examples

<!--tabs-->

### ❌ Incorrect

```ts
declare function foo(arg1: string, arg2: number, arg3: string): void;

const anyTyped = 1 as any;

foo(...anyTyped);
foo(anyTyped, 1, 'a');

const anyArray: any[] = [];
foo(...anyArray);

const tuple1 = ['a', anyTyped, 'b'] as const;
foo(...tuple1);

const tuple2 = [1] as const;
foo('a', ...tuple, anyTyped);

declare function bar(arg1: string, arg2: number, ...rest: string[]): void;
const x = [1, 2] as [number, ...number[]];
foo('a', ...x, anyTyped);

declare function baz(arg1: Set<string>, arg2: Map<string, string>): void;
foo(new Set<any>(), new Map<any, string>());
```

### ✅ Correct

```ts
declare function foo(arg1: string, arg2: number, arg3: string): void;

foo('a', 1, 'b');

const tuple1 = ['a', 1, 'b'] as const;
foo(...tuple1);

declare function bar(arg1: string, arg2: number, ...rest: string[]): void;
const array: string[] = ['a'];
bar('a', 1, ...array);

declare function baz(arg1: Set<string>, arg2: Map<string, string>): void;
foo(new Set<string>(), new Map<string, string>());
```

<!--/tabs-->

There are cases where the rule allows passing an argument of `any` to `unknown`.

Example of `any` to `unknown` assignment that are allowed:

```ts showPlaygroundButton
declare function foo(arg1: unknown, arg2: Set<unknown>, arg3: unknown[]): void;
foo(1 as any, new Set<any>(), [] as any[]);
```

## When Not To Use It

If your codebase has many existing `any`s or areas of unsafe code, it may be difficult to enable this rule.
It may be easier to skip the `no-unsafe-*` rules pending increasing type safety in unsafe areas of your project.
You might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.

## Related To

- [`no-explicit-any`](./no-explicit-any.md)
- [`no-unsafe-assignment`](./no-unsafe-assignment.md)
- [`no-unsafe-call`](./no-unsafe-call.md)
- [`no-unsafe-member-access`](./no-unsafe-member-access.md)
- [`no-unsafe-return`](./no-unsafe-return.md)
