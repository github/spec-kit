---
description: 'Require any function or method that returns a Promise to be marked async.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/promise-function-async** for documentation.

Ensures that each function is only capable of:

- returning a rejected promise, or
- throwing an Error object.

In contrast, non-`async`, `Promise`-returning functions are technically capable of either.
Code that handles the results of those functions will often need to handle both cases, which can get complex.
This rule's practice removes a requirement for creating code to handle both cases.

> When functions return unions of `Promise` and non-`Promise` types implicitly, it is usually a mistake—this rule flags those cases. If it is intentional, make the return type explicitly to allow the rule to pass.

## Examples

Examples of code for this rule

<!--tabs-->

### ❌ Incorrect

```ts
const arrowFunctionReturnsPromise = () => Promise.resolve('value');

function functionReturnsPromise() {
  return Promise.resolve('value');
}

function functionReturnsUnionWithPromiseImplicitly(p: boolean) {
  return p ? 'value' : Promise.resolve('value');
}
```

### ✅ Correct

```ts
const arrowFunctionReturnsPromise = async () => Promise.resolve('value');

async function functionReturnsPromise() {
  return Promise.resolve('value');
}

// An explicit return type that is not Promise means this function cannot be made async, so it is ignored by the rule
function functionReturnsUnionWithPromiseExplicitly(
  p: boolean,
): string | Promise<string> {
  return p ? 'value' : Promise.resolve('value');
}

async function functionReturnsUnionWithPromiseImplicitly(p: boolean) {
  return p ? 'value' : Promise.resolve('value');
}
```

## Options

### `allowAny`

Whether to ignore functions that return `any` and `unknown`.
If you want additional safety, consider turning this option off, as it makes the rule less able to catch incorrect Promise behaviors.

Examples of code with `{ "allowAny": false }`:

<!--tabs-->

#### ❌ Incorrect

```ts option='{ "allowAny": false }'
const returnsAny = () => ({}) as any;
```

#### ✅ Correct

```ts option='{ "allowAny": false }'
const returnsAny = async () => ({}) as any;
```

### `allowedPromiseNames`

For projects that use constructs other than the global built-in `Promise` for asynchronous code.
This option allows specifying string names of classes or interfaces that cause a function to be checked as well.

Examples of code with `{ "allowedPromiseNames": ["Bluebird"] }`:

<!--tabs-->

#### ❌ Incorrect

```ts option='{ "allowedPromiseNames": ["Bluebird"] }'
import { Bluebird } from 'bluebird';

const returnsBluebird = () => new Bluebird(() => {});
```

#### ✅ Correct

```ts option='{ "allowedPromiseNames": ["Bluebird"] }'
import { Bluebird } from 'bluebird';

const returnsBluebird = async () => new Bluebird(() => {});
```

### `checkArrowFunctions`

Whether to check arrow functions.
`true` by default, but can be set to `false` to ignore them.

### `checkFunctionDeclarations`

Whether to check standalone function declarations.
`true` by default, but can be set to `false` to ignore them.

### `checkFunctionExpressions`

Whether to check inline function expressions.
`true` by default, but can be set to `false` to ignore them.

### `checkMethodDeclarations`

Whether to check methods on classes and object literals
`true` by default, but can be set to `false` to ignore them.

## When Not To Use It

This rule can be difficult to enable on projects that use APIs which require functions to always be `async`.
You might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) along with filing issues on your dependencies for those specific situations instead of completely disabling this rule.
