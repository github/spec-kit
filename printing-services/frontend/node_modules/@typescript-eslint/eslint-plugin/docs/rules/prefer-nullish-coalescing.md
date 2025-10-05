---
description: 'Enforce using the nullish coalescing operator instead of logical assignments or chaining.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/prefer-nullish-coalescing** for documentation.

The `??` nullish coalescing runtime operator allows providing a default value when dealing with `null` or `undefined`.
Because the nullish coalescing operator _only_ coalesces when the original value is `null` or `undefined`, it is much safer than relying upon logical OR operator chaining `||`, which coalesces on any _falsy_ value.

This rule reports when you may consider replacing:

- An `||` operator with `??`
- An `||=` operator with `??=`

:::caution
This rule will not work as expected if [`strictNullChecks`](https://www.typescriptlang.org/tsconfig#strictNullChecks) is not enabled.
:::

## Options

### `ignoreTernaryTests`

Setting this option to `true` will cause the rule to ignore any ternary expressions that could be simplified by using the nullish coalescing operator. This is set to `false` by default.

Incorrect code for `ignoreTernaryTests: false`, and correct code for `ignoreTernaryTests: true`:

```ts option='{ "ignoreTernaryTests": false }' showPlaygroundButton
const foo: any = 'bar';
foo !== undefined && foo !== null ? foo : 'a string';
foo === undefined || foo === null ? 'a string' : foo;
foo == undefined ? 'a string' : foo;
foo == null ? 'a string' : foo;

const foo: string | undefined = 'bar';
foo !== undefined ? foo : 'a string';
foo === undefined ? 'a string' : foo;

const foo: string | null = 'bar';
foo !== null ? foo : 'a string';
foo === null ? 'a string' : foo;
```

Correct code for `ignoreTernaryTests: false`:

```ts option='{ "ignoreTernaryTests": false }' showPlaygroundButton
const foo: any = 'bar';
foo ?? 'a string';
foo ?? 'a string';
foo ?? 'a string';
foo ?? 'a string';

const foo: string | undefined = 'bar';
foo ?? 'a string';
foo ?? 'a string';

const foo: string | null = 'bar';
foo ?? 'a string';
foo ?? 'a string';
```

### `ignoreConditionalTests`

Setting this option to `true` will cause the rule to ignore any cases that are located within a conditional test. This is set to `false` by default.

Generally expressions within conditional tests intentionally use the falsy fallthrough behavior of the logical or operator, meaning that fixing the operator to the nullish coalesce operator could cause bugs.

If you're looking to enforce stricter conditional tests, you should consider using the `strict-boolean-expressions` rule.

Incorrect code for `ignoreConditionalTests: false`, and correct code for `ignoreConditionalTests: true`:

```ts option='{ "ignoreConditionalTests": false }' showPlaygroundButton
declare const a: string | null;
declare const b: string | null;

if (a || b) {
}
if ((a ||= b)) {
}
while (a || b) {}
while ((a ||= b)) {}
do {} while (a || b);
for (let i = 0; a || b; i += 1) {}
a || b ? true : false;
```

Correct code for `ignoreConditionalTests: false`:

```ts option='{ "ignoreConditionalTests": false }' showPlaygroundButton
declare const a: string | null;
declare const b: string | null;

if (a ?? b) {
}
if ((a ??= b)) {
}
while (a ?? b) {}
while ((a ??= b)) {}
do {} while (a ?? b);
for (let i = 0; a ?? b; i += 1) {}
a ?? b ? true : false;
```

### `ignoreMixedLogicalExpressions`

Setting this option to `true` will cause the rule to ignore any logical or expressions that are part of a mixed logical expression (with `&&`). This is set to `false` by default.

Generally expressions within mixed logical expressions intentionally use the falsy fallthrough behavior of the logical or operator, meaning that fixing the operator to the nullish coalesce operator could cause bugs.

If you're looking to enforce stricter conditional tests, you should consider using the `strict-boolean-expressions` rule.

Incorrect code for `ignoreMixedLogicalExpressions: false`, and correct code for `ignoreMixedLogicalExpressions: true`:

```ts option='{ "ignoreMixedLogicalExpressions": false }' showPlaygroundButton
declare const a: string | null;
declare const b: string | null;
declare const c: string | null;
declare const d: string | null;

a || (b && c);
a ||= b && c;
(a && b) || c || d;
a || (b && c) || d;
a || (b && c && d);
```

Correct code for `ignoreMixedLogicalExpressions: false`:

```ts option='{ "ignoreMixedLogicalExpressions": false }' showPlaygroundButton
declare const a: string | null;
declare const b: string | null;
declare const c: string | null;
declare const d: string | null;

a ?? (b && c);
a ??= b && c;
(a && b) ?? c ?? d;
a ?? (b && c) ?? d;
a ?? (b && c && d);
```

**_NOTE:_** Errors for this specific case will be presented as suggestions (see below), instead of fixes. This is because it is not always safe to automatically convert `||` to `??` within a mixed logical expression, as we cannot tell the intended precedence of the operator. Note that by design, `??` requires parentheses when used with `&&` or `||` in the same expression.

### `ignorePrimitives`

If you would like to ignore expressions containing operands of certain primitive types that can be falsy then you may pass an object containing a boolean value for each primitive:

- `string: true`, ignores `null` or `undefined` unions with `string` (default: false).
- `number: true`, ignores `null` or `undefined` unions with `number` (default: false).
- `bigint: true`, ignores `null` or `undefined` unions with `bigint` (default: false).
- `boolean: true`, ignores `null` or `undefined` unions with `boolean` (default: false).

Incorrect code for `ignorePrimitives: { string: false }`, and correct code for `ignorePrimitives: { string: true }`:

```ts option='{ "ignorePrimitives": { "string": true } }' showPlaygroundButton
const foo: string | undefined = 'bar';
foo || 'a string';
```

Correct code for both `ignorePrimitives: { string: false }` and `ignorePrimitives: { string: true }`:

```ts option='{ "ignorePrimitives": { "string": true } }' showPlaygroundButton
const foo: string | undefined = 'bar';
foo ?? 'a string';
```

Also, if you would like to ignore all primitives types, you can set `ignorePrimitives: true`. It is equivalent to `ignorePrimitives: { string: true, number: true, bigint: true, boolean: true }`.

### `allowRuleToRunWithoutStrictNullChecksIKnowWhatIAmDoing`

If this is set to `false`, then the rule will error on every file whose `tsconfig.json` does _not_ have the `strictNullChecks` compiler option (or `strict`) set to `true`.

Without `strictNullChecks`, TypeScript essentially erases `undefined` and `null` from the types. This means when this rule inspects the types from a variable, **it will not be able to tell that the variable might be `null` or `undefined`**, which essentially makes this rule useless.

You should be using `strictNullChecks` to ensure complete type-safety in your codebase.

If for some reason you cannot turn on `strictNullChecks`, but still want to use this rule - you can use this option to allow it - but know that the behavior of this rule is _undefined_ with the compiler option turned off. We will not accept bug reports if you are using this option.

## When Not To Use It

If you are not using TypeScript 3.7 (or greater), then you will not be able to use this rule, as the operator is not supported.

## Further Reading

- [TypeScript 3.7 Release Notes](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-7.html)
- [Nullish Coalescing Operator Proposal](https://github.com/tc39/proposal-nullish-coalescing/)
