---
description: 'Require using Error objects as Promise rejection reasons.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/prefer-promise-reject-errors** for documentation.

This rule extends the base [`eslint/prefer-promise-reject-errors`](https://eslint.org/docs/rules/prefer-promise-reject-errors) rule.
It uses type information to enforce that `Promise`s are only rejected with `Error` objects.

## Examples

<!--tabs-->

### ❌ Incorrect

```ts
Promise.reject('error');

const err = new Error();
Promise.reject('an ' + err);

new Promise((resolve, reject) => reject('error'));

new Promise((resolve, reject) => {
  const err = new Error();
  reject('an ' + err);
});
```

### ✅ Correct

```ts
Promise.reject(new Error());

class CustomError extends Error {
  // ...
}
Promise.reject(new CustomError());

new Promise((resolve, reject) => reject(new Error()));

new Promise((resolve, reject) => {
  class CustomError extends Error {
    // ...
  }
  return reject(new CustomError());
});
```
