---
description: 'Disallow duplicate constituents of union or intersection types.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-duplicate-type-constituents** for documentation.

TypeScript supports types ("constituents") within union and intersection types being duplicates of each other.
However, developers typically expect each constituent to be unique within its intersection or union.
Duplicate values make the code overly verbose and generally reduce readability.

This rule disallows duplicate union or intersection constituents.
We consider types to be duplicate if they evaluate to the same result in the type system.
For example, given `type A = string` and `type T = string | A`, this rule would flag that `A` is the same type as `string`.

<!--tabs-->

### ❌ Incorrect

```ts
type T1 = 'A' | 'A';

type T2 = A | A | B;

type T3 = { a: string } & { a: string };

type T4 = [1, 2, 3] | [1, 2, 3];

type StringA = string;
type StringB = string;
type T5 = StringA | StringB;
```

### ✅ Correct

```ts
type T1 = 'A' | 'B';

type T2 = A | B | C;

type T3 = { a: string } & { b: string };

type T4 = [1, 2, 3] | [1, 2, 3, 4];

type StringA = string;
type NumberB = number;
type T5 = StringA | NumberB;
```

## Options

### `ignoreIntersections`

When set to true, duplicate checks on intersection type constituents are ignored.

### `ignoreUnions`

When set to true, duplicate checks on union type constituents are ignored.

## When Not To Use It

It can sometimes be useful for the sake of documentation to include aliases for the same type.
You might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.

> In some of those cases, [branded types](https://basarat.gitbook.io/typescript/main-1/nominaltyping#using-interfaces) might be a type-safe way to represent the underlying data types.
