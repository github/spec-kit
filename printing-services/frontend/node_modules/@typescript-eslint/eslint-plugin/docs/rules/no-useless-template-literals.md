---
description: 'Disallow unnecessary template literals.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-useless-template-literals** for documentation.

This rule reports template literals that can be simplified to a normal string literal.

## Examples

<!--tabs-->

### ❌ Incorrect

```ts
const ab1 = `${'a'}${'b'}`;
const ab2 = `a${'b'}`;

const stringWithNumber = `${'1 + 1 = '}${2}`;

const stringWithBoolean = `${'true is '}${true}`;

const text = 'a';
const wrappedText = `${text}`;

declare const intersectionWithString: string & { _brand: 'test-brand' };
const wrappedIntersection = `${intersectionWithString}`;
```

### ✅ Correct

```ts
const ab1 = 'ab';
const ab2 = 'ab';

const stringWithNumber = `1 + 1 = 2`;

const stringWithBoolean = `true is true`;

const text = 'a';
const wrappedText = text;

declare const intersectionWithString: string & { _brand: 'test-brand' };
const wrappedIntersection = intersectionWithString;
```

<!--/tabs-->

## When Not To Use It

When you want to allow string expressions inside template literals.

## Related To

- [`restrict-template-expressions`](./restrict-template-expressions.md)
