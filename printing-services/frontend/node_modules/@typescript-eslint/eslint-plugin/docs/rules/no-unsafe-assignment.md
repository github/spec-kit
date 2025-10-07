---
description: 'Disallow assigning a value with type `any` to variables and properties.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-unsafe-assignment** for documentation.

The `any` type in TypeScript is a dangerous "escape hatch" from the type system.
Using `any` disables many type checking rules and is generally best used only as a last resort or when prototyping code.

Despite your best intentions, the `any` type can sometimes leak into your codebase.
Assigning an `any` typed value to a variable can be hard to pick up on, particularly if it leaks in from an external library.

This rule disallows assigning `any` to a variable, and assigning `any[]` to an array destructuring.

This rule also compares generic type argument types to ensure you don't pass an unsafe `any` in a generic position to a receiver that's expecting a specific type.
For example, it will error if you assign `Set<any>` to a variable declared as `Set<string>`.

## Examples

<!--tabs-->

### ❌ Incorrect

```ts
const x = 1 as any,
  y = 1 as any;
const [x] = 1 as any;
const [x] = [] as any[];
const [x] = [1 as any];
[x] = [1] as [any];

function foo(a = 1 as any) {}
class Foo {
  constructor(private a = 1 as any) {}
}
class Foo {
  private a = 1 as any;
}

// generic position examples
const x: Set<string> = new Set<any>();
const x: Map<string, string> = new Map<string, any>();
const x: Set<string[]> = new Set<any[]>();
const x: Set<Set<Set<string>>> = new Set<Set<Set<any>>>();
```

### ✅ Correct

```ts
const x = 1,
  y = 1;
const [x] = [1];
[x] = [1] as [number];

function foo(a = 1) {}
class Foo {
  constructor(private a = 1) {}
}
class Foo {
  private a = 1;
}

// generic position examples
const x: Set<string> = new Set<string>();
const x: Map<string, string> = new Map<string, string>();
const x: Set<string[]> = new Set<string[]>();
const x: Set<Set<Set<string>>> = new Set<Set<Set<string>>>();
```

<!--/tabs-->

There are cases where the rule allows assignment of `any` to `unknown`.

Example of `any` to `unknown` assignment that are allowed:

```ts showPlaygroundButton
const x: unknown = y as any;
const x: unknown[] = y as any[];
const x: Set<unknown> = y as Set<any>;
```

## When Not To Use It

If your codebase has many existing `any`s or areas of unsafe code, it may be difficult to enable this rule.
It may be easier to skip the `no-unsafe-*` rules pending increasing type safety in unsafe areas of your project.
You might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.

## Related To

- [`no-explicit-any`](./no-explicit-any.md)
- [`no-unsafe-argument`](./no-unsafe-argument.md)
- [`no-unsafe-call`](./no-unsafe-call.md)
- [`no-unsafe-member-access`](./no-unsafe-member-access.md)
- [`no-unsafe-return`](./no-unsafe-return.md)
