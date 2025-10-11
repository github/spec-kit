---
description: 'Require unary negation to take a number.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-unsafe-unary-minus** for documentation.

TypeScript does not prevent you from putting a minus sign before things other than numbers:

```ts
const s = 'hello';
const x = -s; // x is NaN
```

This rule restricts the unary `-` operator to `number | bigint`.

## Examples

### ❌ Incorrect

```ts
declare const a: string;
-a;

declare const b: {};
-b;
```

### ✅ Correct

```ts
-42;
-42n;

declare const a: number;
-a;

declare const b: number;
-b;

declare const c: number | bigint;
-c;

declare const d: any;
-d;

declare const e: 1 | 2;
-e;
```

<!-- Intentionally Omitted: When Not To Use It -->
