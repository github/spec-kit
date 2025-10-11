---
description: 'Enforce using concise optional chain expressions instead of chained logical ands, negated logical ors, or empty objects.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/prefer-optional-chain** for documentation.

`?.` optional chain expressions provide `undefined` if an object is `null` or `undefined`.
Because the optional chain operator _only_ chains when the property value is `null` or `undefined`, it is much safer than relying upon logical AND operator chaining `&&`; which chains on any _truthy_ value.
It is also often less code to use `?.` optional chaining than `&&` truthiness checks.

This rule reports on code where an `&&` operator can be safely replaced with `?.` optional chaining.

## Examples

<!--tabs-->

### ❌ Incorrect

```ts
foo && foo.a && foo.a.b && foo.a.b.c;
foo && foo['a'] && foo['a'].b && foo['a'].b.c;
foo && foo.a && foo.a.b && foo.a.b.method && foo.a.b.method();

// With empty objects
(((foo || {}).a || {}).b || {}).c;
(((foo || {})['a'] || {}).b || {}).c;

// With negated `or`s
!foo || !foo.bar;
!foo || !foo[bar];
!foo || !foo.bar || !foo.bar.baz || !foo.bar.baz();

// this rule also supports converting chained strict nullish checks:
foo &&
  foo.a != null &&
  foo.a.b !== null &&
  foo.a.b.c != undefined &&
  foo.a.b.c.d !== undefined &&
  foo.a.b.c.d.e;
```

### ✅ Correct

```ts
foo?.a?.b?.c;
foo?.['a']?.b?.c;
foo?.a?.b?.method?.();

foo?.a?.b?.c?.d?.e;

!foo?.bar;
!foo?.[bar];
!foo?.bar?.baz?.();
```

<!--/tabs-->

## Options

In the context of the descriptions below a "loose boolean" operand is any operand that implicitly coerces the value to a boolean.
Specifically the argument of the not operator (`!loose`) or a bare value in a logical expression (`loose && looser`).

### `allowPotentiallyUnsafeFixesThatModifyTheReturnTypeIKnowWhatImDoing`

When this option is `true`, the rule will not provide an auto-fixer for cases where the return type of the expression would change. For example for the expression `!foo || foo.bar` the return type of the expression is `true | T`, however for the equivalent optional chain `foo?.bar` the return type of the expression is `undefined | T`. Thus changing the code from a logical expression to an optional chain expression has altered the type of the expression.

In some cases this distinction _may_ matter - which is why these fixers are considered unsafe - they may break the build! For example in the following code:

```ts option='{ "allowPotentiallyUnsafeFixesThatModifyTheReturnTypeIKnowWhatImDoing": true }' showPlaygroundButton
declare const foo: { bar: boolean } | null | undefined;
declare function acceptsBoolean(arg: boolean): void;

// ✅ typechecks succesfully as the expression only returns `boolean`
acceptsBoolean(foo != null && foo.bar);

// ❌ typechecks UNSUCCESSFULLY as the expression returns `boolean | undefined`
acceptsBoolean(foo?.bar);
```

This style of code isn't super common - which means having this option set to `true` _should_ be safe in most codebases. However we default it to `false` due to its unsafe nature. We have provided this option for convenience because it increases the autofix cases covered by the rule. If you set option to `true` the onus is entirely on you and your team to ensure that each fix is correct and safe and that it does not break the build.

When this option is `false` unsafe cases will have suggestion fixers provided instead of auto-fixers - meaning you can manually apply the fix using your IDE tooling.

### `checkAny`

When this option is `true` the rule will check operands that are typed as `any` when inspecting "loose boolean" operands.

<!--tabs-->

#### ❌ Incorrect for `checkAny: true`

```ts option='{ "checkAny": true }'
declare const thing: any;

thing && thing.toString();
```

#### ✅ Correct for `checkAny: false`

```ts option='{ "checkAny": false }'
declare const thing: any;

thing && thing.toString();
```

<!--/tabs-->

### `checkUnknown`

When this option is `true` the rule will check operands that are typed as `unknown` when inspecting "loose boolean" operands.

<!--tabs-->

#### ❌ Incorrect for `checkUnknown: true`

```ts option='{ "checkUnknown": true }'
declare const thing: unknown;

thing && thing.toString();
```

#### ✅ Correct for `checkUnknown: false`

```ts option='{ "checkUnknown": false }'
declare const thing: unknown;

thing && thing.toString();
```

<!--/tabs-->

### `checkString`

When this option is `true` the rule will check operands that are typed as `string` when inspecting "loose boolean" operands.

<!--tabs-->

#### ❌ Incorrect for `checkString: true`

```ts option='{ "checkString": true }'
declare const thing: string;

thing && thing.toString();
```

#### ✅ Correct for `checkString: false`

```ts option='{ "checkString": false }'
declare const thing: string;

thing && thing.toString();
```

<!--/tabs-->

### `checkNumber`

When this option is `true` the rule will check operands that are typed as `number` when inspecting "loose boolean" operands.

<!--tabs-->

#### ❌ Incorrect for `checkNumber: true`

```ts option='{ "checkNumber": true }'
declare const thing: number;

thing && thing.toString();
```

#### ✅ Correct for `checkNumber: false`

```ts option='{ "checkNumber": false }'
declare const thing: number;

thing && thing.toString();
```

<!--/tabs-->

### `checkBoolean`

When this option is `true` the rule will check operands that are typed as `boolean` when inspecting "loose boolean" operands.

<!--tabs-->

#### ❌ Incorrect for `checkBoolean: true`

```ts option='{ "checkBoolean": true }'
declare const thing: boolean;

thing && thing.toString();
```

#### ✅ Correct for `checkBoolean: false`

```ts option='{ "checkBoolean": false }'
declare const thing: boolean;

thing && thing.toString();
```

<!--/tabs-->

### `checkBigInt`

When this option is `true` the rule will check operands that are typed as `bigint` when inspecting "loose boolean" operands.

<!--tabs-->

#### ❌ Incorrect for `checkBigInt: true`

```ts option='{ "checkBigInt": true }'
declare const thing: bigint;

thing && thing.toString();
```

#### ✅ Correct for `checkBigInt: false`

```ts option='{ "checkBigInt": false }'
declare const thing: bigint;

thing && thing.toString();
```

<!--/tabs-->

### `requireNullish`

When this option is `true` the rule will skip operands that are not typed with `null` and/or `undefined` when inspecting "loose boolean" operands.

<!--tabs-->

#### ❌ Incorrect for `requireNullish: true`

```ts option='{ "requireNullish": true }'
declare const thing1: string | null;
thing1 && thing1.toString();
```

#### ✅ Correct for `requireNullish: true`

```ts option='{ "requireNullish": true }'
declare const thing1: string | null;
thing1?.toString();

declare const thing2: string;
thing2 && thing2.toString();
```

<!--/tabs-->

## When Not To Use It

If your project is not accurately typed, such as if it's in the process of being converted to TypeScript or is susceptible to [trade-offs in control flow analysis](https://github.com/Microsoft/TypeScript/issues/9998), it may be difficult to enable this rule for particularly non-type-safe areas of code.
You might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.

## Further Reading

- [TypeScript 3.7 Release Notes](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-7.html)
- [Optional Chaining Proposal](https://github.com/tc39/proposal-optional-chaining/)
