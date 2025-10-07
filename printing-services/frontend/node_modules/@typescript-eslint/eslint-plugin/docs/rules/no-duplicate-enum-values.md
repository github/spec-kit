---
description: 'Disallow duplicate enum member values.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-duplicate-enum-values** for documentation.

Although TypeScript supports duplicate enum member values, people usually expect members to have unique values within the same enum. Duplicate values can lead to bugs that are hard to track down.

## Examples

This rule disallows defining an enum with multiple members initialized to the same value.

> This rule only enforces on enum members initialized with string or number literals.
> Members without an initializer or initialized with an expression are not checked by this rule.

<!--tabs-->

### ❌ Incorrect

```ts
enum E {
  A = 0,
  B = 0,
}
```

```ts
enum E {
  A = 'A',
  B = 'A',
}
```

### ✅ Correct

```ts
enum E {
  A = 0,
  B = 1,
}
```

```ts
enum E {
  A = 'A',
  B = 'B',
}
```

## When Not To Use It

It can sometimes be useful to include duplicate enum members for very specific use cases.
For example, when renaming an enum member, it can sometimes be useful to keep the old name until a scheduled major breaking change.
You might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.

In general, if your project intentionally duplicates enum member values, you can avoid this rule.
