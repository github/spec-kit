---
description: 'Disallow empty functions.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-empty-function** for documentation.

This rule extends the base [`eslint/no-empty-function`](https://eslint.org/docs/rules/no-empty-function) rule.
It adds support for handling TypeScript specific code that would otherwise trigger the rule.

One example of valid TypeScript specific code that would otherwise trigger the `no-empty-function` rule is the use of [parameter properties](https://www.typescriptlang.org/docs/handbook/classes.html#parameter-properties) in constructor functions.

## Options

This rule adds the following options:

```ts
type AdditionalAllowOptionEntries =
  | 'private-constructors'
  | 'protected-constructors'
  | 'decoratedFunctions'
  | 'overrideMethods';

type AllowOptionEntries =
  | BaseNoEmptyFunctionAllowOptionEntries
  | AdditionalAllowOptionEntries;

interface Options extends BaseNoEmptyFunctionOptions {
  allow?: Array<AllowOptionEntries>;
}
const defaultOptions: Options = {
  ...baseNoEmptyFunctionDefaultOptions,
  allow: [],
};
```

### allow: `private-constructors`

Examples of correct code for the `{ "allow": ["private-constructors"] }` option:

```ts option='{ "allow": ["private-constructors"] }' showPlaygroundButton
class Foo {
  private constructor() {}
}
```

### allow: `protected-constructors`

Examples of correct code for the `{ "allow": ["protected-constructors"] }` option:

```ts option='{ "allow": ["protected-constructors"] }' showPlaygroundButton
class Foo {
  protected constructor() {}
}
```

### allow: `decoratedFunctions`

Examples of correct code for the `{ "allow": ["decoratedFunctions"] }` option:

```ts option='{ "allow": ["decoratedFunctions"] }' showPlaygroundButton
class Foo {
  @decorator()
  foo() {}
}
```

### allow: `overrideMethods`

Examples of correct code for the `{ "allow": ["overrideMethods"] }` option:

```ts option='{ "allow": ["overrideMethods"] }' showPlaygroundButton
abstract class Base {
  protected greet(): void {
    console.log('Hello!');
  }
}

class Foo extends Base {
  protected override greet(): void {}
}
```

## When Not To Use It

If you are working with external APIs that require functions even if they do nothing, then you may want to avoid this rule.
You might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.

Test code often violates this rule as well.
If your testing setup doesn't support "mock" or "spy" functions such as [`jest.fn()`](https://jestjs.io/docs/mock-functions), [`sinon.spy()`](https://sinonjs.org/releases/latest/spies), or [`vi.fn()`](https://vitest.dev/guide/mocking.html), you may wish to disable this rule in test files.
Again, if those cases aren't extremely common, you might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule in test files.
