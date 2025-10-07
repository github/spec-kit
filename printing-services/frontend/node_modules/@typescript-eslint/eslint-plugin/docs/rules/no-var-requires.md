---
description: 'Disallow `require` statements except in import statements.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-var-requires** for documentation.

In other words, the use of forms such as `var foo = require("foo")` are banned. Instead use ES6 style imports or `import foo = require("foo")` imports.

## Examples

<!--tabs-->

### ❌ Incorrect

```ts
var foo = require('foo');
const foo = require('foo');
let foo = require('foo');
```

### ✅ Correct

```ts
import foo = require('foo');
require('foo');
import foo from 'foo';
```

## Options

### `allow`

A array of strings. These strings will be compiled into regular expressions with the `u` flag and be used to test against the imported path. A common use case is to allow importing `package.json`. This is because `package.json` commonly lives outside of the TS root directory, so statically importing it would lead to root directory conflicts, especially with `resolveJsonModule` enabled. You can also use it to allow importing any JSON if your environment doesn't support JSON modules, or use it for other cases where `import` statements cannot work.

With `{allow: ['/package\\.json$']}`:

<!--tabs-->

### ❌ Incorrect

```ts
const foo = require('../data.json');
```

### ✅ Correct

```ts
const foo = require('../package.json');
```

## When Not To Use It

If your project frequently uses older CommonJS `require`s, then this rule might not be applicable to you.
If only a subset of your project uses `require`s then you might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.

## Related To

- [`no-require-imports`](./no-require-imports.md)
