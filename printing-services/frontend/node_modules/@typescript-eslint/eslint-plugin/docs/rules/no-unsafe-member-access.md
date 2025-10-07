---
description: 'Disallow member access on a value with type `any`.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-unsafe-member-access** for documentation.

The `any` type in TypeScript is a dangerous "escape hatch" from the type system.
Using `any` disables many type checking rules and is generally best used only as a last resort or when prototyping code.

Despite your best intentions, the `any` type can sometimes leak into your codebase.
Accessing a member of an `any`-typed value creates a potential type safety hole and source of bugs in your codebase.

This rule disallows member access on any variable that is typed as `any`.

## Examples

<!--tabs-->

### ❌ Incorrect

```ts
declare const anyVar: any;
declare const nestedAny: { prop: any };

anyVar.a;
anyVar.a.b;
anyVar['a'];
anyVar['a']['b'];

nestedAny.prop.a;
nestedAny.prop['a'];

const key = 'a';
nestedAny.prop[key];

// Using an any to access a member is unsafe
const arr = [1, 2, 3];
arr[anyVar];
nestedAny[anyVar];
```

### ✅ Correct

```ts
declare const properlyTyped: { prop: { a: string } };

properlyTyped.prop.a;
properlyTyped.prop['a'];

const key = 'a';
properlyTyped.prop[key];

const arr = [1, 2, 3];
arr[1];
let idx = 1;
arr[idx];
arr[idx++];
```

## When Not To Use It

If your codebase has many existing `any`s or areas of unsafe code, it may be difficult to enable this rule.
It may be easier to skip the `no-unsafe-*` rules pending increasing type safety in unsafe areas of your project.
You might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.

## Related To

- [`no-explicit-any`](./no-explicit-any.md)
- [`no-unsafe-argument`](./no-unsafe-argument.md)
- [`no-unsafe-assignment`](./no-unsafe-assignment.md)
- [`no-unsafe-call`](./no-unsafe-call.md)
- [`no-unsafe-return`](./no-unsafe-return.md)
