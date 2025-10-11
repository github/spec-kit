---
description: 'Disallow certain triple slash directives in favor of ES6-style import declarations.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/triple-slash-reference** for documentation.

TypeScript's `///` triple-slash references are a way to indicate that types from another module are available in a file.
Use of triple-slash reference type directives is generally discouraged in favor of ECMAScript Module `import`s.
This rule reports on the use of `/// <reference lib="..." />`, `/// <reference path="..." />`, or `/// <reference types="..." />` directives.

## Options

Any number of the three kinds of references can be specified as an option.
Specifying `'always'` disables this lint rule for that kind of reference.

### `lib`

When set to `'never'`, bans `/// <reference lib="..." />` and enforces using an `import` instead:

<!--tabs-->

#### ❌ Incorrect

```ts option='{ "lib": "never" }'
/// <reference lib="code" />

globalThis.value;
```

#### ✅ Correct

```ts option='{ "lib": "never" }'
import { value } from 'code';
```

### `path`

When set to `'never'`, bans `/// <reference path="..." />` and enforces using an `import` instead:

<!--tabs-->

#### ❌ Incorrect

```ts option='{ "path": "never" }'
/// <reference path="code" />

globalThis.value;
```

#### ✅ Correct

```ts option='{ "path": "never" }'
import { value } from 'code';
```

### `types`

When set to `'never'`, bans `/// <reference types="..." />` and enforces using an `import` instead:

<!--tabs-->

#### ❌ Incorrect

```ts option='{ "types": "never" }'
/// <reference types="code" />

globalThis.value;
```

#### ✅ Correct

```ts option='{ "types": "never" }'
import { value } from 'code';
```

<!-- /tabs -->

The `types` option may alternately be given a `"prefer-import"` value.
Doing so indicates the rule should only report if there is already an `import` from the same location:

<!--tabs-->

#### ❌ Incorrect

```ts option='{ "types": "prefer-import" }'
/// <reference types="code" />

import { valueA } from 'code';

globalThis.valueB;
```

#### ✅ Correct

```ts option='{ "types": "prefer-import" }'
import { valueA, valueB } from 'code';
```

## When Not To Use It

Most modern TypeScript projects generally use `import` statements to bring in types.
It's rare to need a `///` triple-slash reference outside of auto-generated code.
If your project is a rare one with one of those use cases, this rule might not be for you.
You might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.

## When Not To Use It

If you want to use all flavors of triple slash reference directives.
