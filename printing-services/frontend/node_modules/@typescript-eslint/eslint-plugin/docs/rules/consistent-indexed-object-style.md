---
description: 'Require or disallow the `Record` type.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/consistent-indexed-object-style** for documentation.

TypeScript supports defining arbitrary object keys using an index signature. TypeScript also has a builtin type named `Record` to create an empty object defining only an index signature. For example, the following types are equal:

```ts
interface Foo {
  [key: string]: unknown;
}

type Foo = {
  [key: string]: unknown;
};

type Foo = Record<string, unknown>;
```

Keeping to one declaration form consistently improve code readability.

## Options

- `"record"` _(default)_: only allow the `Record` type.
- `"index-signature"`: only allow index signatures.

### `record`

<!--tabs-->

#### ❌ Incorrect

```ts option='"record"'
interface Foo {
  [key: string]: unknown;
}

type Foo = {
  [key: string]: unknown;
};
```

#### ✅ Correct

```ts option='"record"'
type Foo = Record<string, unknown>;
```

### `index-signature`

<!--tabs-->

#### ❌ Incorrect

```ts option='"index-signature"'
type Foo = Record<string, unknown>;
```

#### ✅ Correct

```ts option='"index-signature"'
interface Foo {
  [key: string]: unknown;
}

type Foo = {
  [key: string]: unknown;
};
```

## When Not To Use It

This rule is purely a stylistic rule for maintaining consistency in your project.
You can turn it off if you don't want to keep a consistent style for indexed object types.

However, keep in mind that inconsistent style can harm readability in a project.
We recommend picking a single option for this rule that works best for your project.
