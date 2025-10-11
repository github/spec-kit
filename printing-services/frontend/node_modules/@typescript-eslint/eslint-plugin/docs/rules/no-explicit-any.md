---
description: 'Disallow the `any` type.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-explicit-any** for documentation.

The `any` type in TypeScript is a dangerous "escape hatch" from the type system.
Using `any` disables many type checking rules and is generally best used only as a last resort or when prototyping code.
This rule reports on explicit uses of the `any` keyword as a type annotation.

Preferable alternatives to `any` include:

- If the type is known, describing it in an `interface` or `type`
- If the type is not known, using the safer `unknown` type

> TypeScript's `--noImplicitAny` compiler option prevents an implied `any`, but doesn't prevent `any` from being explicitly used the way this rule does.

## Examples

<!--tabs-->

### ❌ Incorrect

```ts
const age: any = 'seventeen';
```

```ts
const ages: any[] = ['seventeen'];
```

```ts
const ages: Array<any> = ['seventeen'];
```

```ts
function greet(): any {}
```

```ts
function greet(): any[] {}
```

```ts
function greet(): Array<any> {}
```

```ts
function greet(): Array<Array<any>> {}
```

```ts
function greet(param: Array<any>): string {}
```

```ts
function greet(param: Array<any>): Array<any> {}
```

### ✅ Correct

```ts
const age: number = 17;
```

```ts
const ages: number[] = [17];
```

```ts
const ages: Array<number> = [17];
```

```ts
function greet(): string {}
```

```ts
function greet(): string[] {}
```

```ts
function greet(): Array<string> {}
```

```ts
function greet(): Array<Array<string>> {}
```

```ts
function greet(param: Array<string>): string {}
```

```ts
function greet(param: Array<string>): Array<string> {}
```

## Options

### `fixToUnknown`

By default, this rule will not provide automatic ESLint _fixes_: only opt-in _suggestions_.
Switching types to `unknown` is safer but is likely to cause additional type errors.

Enabling `{ "fixToUnknown": true }` gives the rule an auto-fixer to replace `: any` with `: unknown`.

### `ignoreRestArgs`

A boolean to specify if arrays from the rest operator are considered okay. `false` by default.

The examples below are **incorrect** when `{ignoreRestArgs: false}`, but **correct** when `{ignoreRestArgs: true}`.

```ts option='{ "ignoreRestArgs": false }' showPlaygroundButton
function foo1(...args: any[]): void {}
function foo2(...args: readonly any[]): void {}
function foo3(...args: Array<any>): void {}
function foo4(...args: ReadonlyArray<any>): void {}

declare function bar(...args: any[]): void;

const baz = (...args: any[]) => {};
const qux = function (...args: any[]) {};

type Quux = (...args: any[]) => void;
type Quuz = new (...args: any[]) => void;

interface Grault {
  (...args: any[]): void;
}
interface Corge {
  new (...args: any[]): void;
}
interface Garply {
  f(...args: any[]): void;
}
```

## When Not To Use It

`any` is always a dangerous escape hatch.
Whenever possible, it is always safer to avoid it.
TypeScript's `unknown` is almost always preferable to `any`.

However, there are occasional situations where it can be necessary to use `any`.
Most commonly:

- If your project isn't fully onboarded to TypeScript yet, `any` can be temporarily used in places where types aren't yet known or representable
- If an external package doesn't yet have typings and you want to use `any` pending adding a `.d.ts` for it
- You're working with particularly complex or nuanced code that can't yet be represented in the TypeScript type system

You might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.

## Related To

- [`no-unsafe-argument`](./no-unsafe-argument.md)
- [`no-unsafe-assignment`](./no-unsafe-assignment.md)
- [`no-unsafe-call`](./no-unsafe-call.md)
- [`no-unsafe-member-access`](./no-unsafe-member-access.md)
- [`no-unsafe-return`](./no-unsafe-return.md)

## Further Reading

- TypeScript [`any` type](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#any)
- TypeScript's [`unknown` type](https://www.typescriptlang.org/docs/handbook/2/functions.html#unknown)
- TypeScript [`any` type documentation](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#any)
- TypeScript [`unknown` type release notes](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-0.html#new-unknown-top-type)
