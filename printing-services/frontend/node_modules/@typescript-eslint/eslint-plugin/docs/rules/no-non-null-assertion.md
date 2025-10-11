---
description: 'Disallow non-null assertions using the `!` postfix operator.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-non-null-assertion** for documentation.

TypeScript's `!` non-null assertion operator asserts to the type system that an expression is non-nullable, as in not `null` or `undefined`.
Using assertions to tell the type system new information is often a sign that code is not fully type-safe.
It's generally better to structure program logic so that TypeScript understands when values may be nullable.

## Examples

<!--tabs-->

### ❌ Incorrect

```ts
interface Example {
  property?: string;
}

declare const example: Example;
const includesBaz = example.property!.includes('baz');
```

### ✅ Correct

```ts
interface Example {
  property?: string;
}

declare const example: Example;
const includesBaz = example.property?.includes('baz') ?? false;
```

## When Not To Use It

If your project's types don't yet fully describe whether certain values may be nullable, such as if you're transitioning to `strictNullChecks`, this rule might create many false reports.
You might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.
