---
description: 'Require Promise-like statements to be handled appropriately.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-floating-promises** for documentation.

A "floating" Promise is one that is created without any code set up to handle any errors it might throw.
Floating Promises can cause several issues, such as improperly sequenced operations, ignored Promise rejections, and more.

This rule reports when a Promise is created and not properly handled.
Valid ways of handling a Promise-valued statement include:

- `await`ing it
- `return`ing it
- Calling its `.then()` with two arguments
- Calling its `.catch()` with one argument

This rule also reports when an Array containing Promises is created and not properly handled. The main way to resolve this is by using one of the Promise concurrency methods to create a single Promise, then handling that according to the procedure above. These methods include:

- `Promise.all()`,
- `Promise.allSettled()`,
- `Promise.any()`
- `Promise.race()`

:::tip
`no-floating-promises` only detects unhandled Promise _statements_.
See [`no-misused-promises`](./no-misused-promises.md) for detecting code that provides Promises to _logical_ locations such as if statements.
:::

## Examples

<!--tabs-->

### ❌ Incorrect

```ts
const promise = new Promise((resolve, reject) => resolve('value'));
promise;

async function returnsPromise() {
  return 'value';
}
returnsPromise().then(() => {});

Promise.reject('value').catch();

Promise.reject('value').finally();

[1, 2, 3].map(async x => x + 1);
```

### ✅ Correct

```ts
const promise = new Promise((resolve, reject) => resolve('value'));
await promise;

async function returnsPromise() {
  return 'value';
}
returnsPromise().then(
  () => {},
  () => {},
);

Promise.reject('value').catch(() => {});

await Promise.reject('value').finally(() => {});

await Promise.all([1, 2, 3].map(async x => x + 1));
```

## Options

### `ignoreVoid`

This allows you to stop the rule reporting promises consumed with void operator.
This can be a good way to explicitly mark a promise as intentionally not awaited.

Examples of **correct** code for this rule with `{ ignoreVoid: true }`:

```ts option='{ "ignoreVoid": true }' showPlaygroundButton
async function returnsPromise() {
  return 'value';
}
void returnsPromise();

void Promise.reject('value');
```

With this option set to `true`, and if you are using `no-void`, you should turn on the [`allowAsStatement`](https://eslint.org/docs/rules/no-void#allowasstatement) option.

### `ignoreIIFE`

This allows you to skip checking of async IIFEs (Immediately Invoked function Expressions).

Examples of **correct** code for this rule with `{ ignoreIIFE: true }`:

<!-- prettier-ignore -->
```ts option='{ "ignoreIIFE": true }' showPlaygroundButton
await (async function () {
  await res(1);
})();

(async function () {
  await res(1);
})();
```

## When Not To Use It

This rule can be difficult to enable on large existing projects that set up many floating Promises.
Alternately, if you're not worried about crashes from floating or misused Promises -such as if you have global unhandled Promise handlers registered- then in some cases it may be safe to not use this rule.
You might consider using `void`s and/or [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.

## Related To

- [`no-misused-promises`](./no-misused-promises.md)

## Further Reading

- ["Using Promises" MDN documentation](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises). Note especially the sections on [Promise rejection events](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises#promise_rejection_events) and [Composition](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises#composition).
