---
description: 'Enforce consistent returning of awaited values.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/return-await** for documentation.

Returning an awaited promise can make sense for better stack trace information as well as for consistent error handling (returned promises will not be caught in an async function try/catch).

This rule builds on top of the [`eslint/no-return-await`](https://eslint.org/docs/rules/no-return-await) rule.
It expands upon the base rule to add support for optionally requiring `return await` in certain cases.

The extended rule is named `return-await` instead of `no-return-await` because the extended rule can enforce the positive or the negative. Additionally, while the core rule is now deprecated, the extended rule is still useful in many contexts.

## Options

```ts
type Options = 'in-try-catch' | 'always' | 'never';

const defaultOptions: Options = 'in-try-catch';
```

### `in-try-catch`

Requires that a returned promise must be `await`ed in `try-catch-finally` blocks, and disallows it elsewhere.
Specifically:

- if you `return` a promise within a `try`, then it must be `await`ed.
- if you `return` a promise within a `catch`, and there **_is no_** `finally`, then it **_must not_** be `await`ed.
- if you `return` a promise within a `catch`, and there **_is a_** `finally`, then it **_must_** be `await`ed.
- if you `return` a promise within a `finally`, then it **_must not_** be `await`ed.

Examples of code with `in-try-catch`:

<!--tabs-->

#### ❌ Incorrect

```ts option='"in-try-catch"'
async function invalidInTryCatch1() {
  try {
    return Promise.resolve('try');
  } catch (e) {}
}

async function invalidInTryCatch2() {
  try {
    throw new Error('error');
  } catch (e) {
    return await Promise.resolve('catch');
  }
}

async function invalidInTryCatch3() {
  try {
    throw new Error('error');
  } catch (e) {
    return Promise.resolve('catch');
  } finally {
    console.log('cleanup');
  }
}

async function invalidInTryCatch4() {
  try {
    throw new Error('error');
  } catch (e) {
    throw new Error('error2');
  } finally {
    return await Promise.resolve('finally');
  }
}

async function invalidInTryCatch5() {
  return await Promise.resolve('try');
}

async function invalidInTryCatch6() {
  return await 'value';
}
```

#### ✅ Correct

```ts option='"in-try-catch"'
async function validInTryCatch1() {
  try {
    return await Promise.resolve('try');
  } catch (e) {}
}

async function validInTryCatch2() {
  try {
    throw new Error('error');
  } catch (e) {
    return Promise.resolve('catch');
  }
}

async function validInTryCatch3() {
  try {
    throw new Error('error');
  } catch (e) {
    return await Promise.resolve('catch');
  } finally {
    console.log('cleanup');
  }
}

async function validInTryCatch4() {
  try {
    throw new Error('error');
  } catch (e) {
    throw new Error('error2');
  } finally {
    return Promise.resolve('finally');
  }
}

async function validInTryCatch5() {
  return Promise.resolve('try');
}

async function validInTryCatch6() {
  return 'value';
}
```

### `always`

Requires that all returned promises are `await`ed.

Examples of code with `always`:

<!--tabs-->

#### ❌ Incorrect

```ts option='"always"'
async function invalidAlways1() {
  try {
    return Promise.resolve('try');
  } catch (e) {}
}

async function invalidAlways2() {
  return Promise.resolve('try');
}

async function invalidAlways3() {
  return await 'value';
}
```

#### ✅ Correct

```ts option='"always"'
async function validAlways1() {
  try {
    return await Promise.resolve('try');
  } catch (e) {}
}

async function validAlways2() {
  return await Promise.resolve('try');
}

async function validAlways3() {
  return 'value';
}
```

### `never`

Disallows all `await`ing any returned promises.

Examples of code with `never`:

<!--tabs-->

#### ❌ Incorrect

```ts option='"never"'
async function invalidNever1() {
  try {
    return await Promise.resolve('try');
  } catch (e) {}
}

async function invalidNever2() {
  return await Promise.resolve('try');
}

async function invalidNever3() {
  return await 'value';
}
```

#### ✅ Correct

```ts option='"never"'
async function validNever1() {
  try {
    return Promise.resolve('try');
  } catch (e) {}
}

async function validNever2() {
  return Promise.resolve('try');
}

async function validNever3() {
  return 'value';
}
```
