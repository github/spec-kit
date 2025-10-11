---
description: 'Require switch-case statements to be exhaustive.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/switch-exhaustiveness-check** for documentation.

When working with union types or enums in TypeScript, it's common to want to write a `switch` statement intended to contain a `case` for each possible type in the union or the enum.
However, if the union type or the enum changes, it's easy to forget to modify the cases to account for any new types.

This rule reports when a `switch` statement over a value typed as a union of literals or as an enum is missing a case for any of those literal types and does not have a `default` clause.

## Options

### `allowDefaultCaseForExhaustiveSwitch`

Defaults to true. If set to false, this rule will also report when a `switch` statement has a case for everything in a union and _also_ contains a `default` case. Thus, by setting this option to false, the rule becomes stricter.

When a `switch` statement over a union type is exhaustive, a final `default` case would be a form of dead code.
Additionally, if a new value is added to the union type, a `default` would prevent the `switch-exhaustiveness-check` rule from reporting on the new case not being handled in the `switch` statement.

#### `allowDefaultCaseForExhaustiveSwitch` Caveats

It can sometimes be useful to include a redundant `default` case on an exhaustive `switch` statement if it's possible for values to have types not represented by the union type.
For example, in applications that can have version mismatches between clients and servers, it's possible for a server running a newer software version to send a value not recognized by the client's older typings.

If your project has a small number of intentionally redundant `default` cases, you might want to use an [inline ESLint disable comment](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for each of them.

If your project has many intentionally redundant `default` cases, you may want to disable `allowDefaultCaseForExhaustiveSwitch` and use the [`default-case` core ESLint rule](https://eslint.org/docs/latest/rules/default-case) along with [a `satisfies never` check](https://www.typescriptlang.org/play?#code/C4TwDgpgBAYgTgVwJbCgXigcgIZjAGwkygB8sAjbAO2u0wG4AoRgMwSoGNgkB7KqBAGcI8ZMAAULRCgBcsacACUcwcDhIqAcygBvRlCiCA7ig4ALKJIWLd+g1A7ZhWXASJy99+3AjAEcfhw8QgApZA4iJi8AX2YvR2dMShoaTA87Lx8-AIpaGjCkCIYMqFiSgBMIFmwEfGB0rwMpMUNsbkEWJAhBKCoIADcIOCjGrP9A9gBrKh4jKgKikYNY5cZYoA).

### `requireDefaultForNonUnion`

Defaults to false. It set to true, this rule will also report when a `switch` statement switches over a non-union type (like a `number` or `string`, for example) and that `switch` statement does not have a `default` case. Thus, by setting this option to true, the rule becomes stricter.

This is generally desirable so that `number` and `string` switches will be subject to the same exhaustive checks that your other switches are.

Examples of additional **incorrect** code for this rule with `{ requireDefaultForNonUnion: true }`:

```ts option='{ "requireDefaultForNonUnion": true }' showPlaygroundButton
const value: number = Math.floor(Math.random() * 3);

switch (value) {
  case 0:
    return 0;
  case 1:
    return 1;
}
```

Since `value` is a non-union type it requires the switch case to have a default clause only with `requireDefaultForNonUnion` enabled.

<!--/tabs-->

## Examples

When the switch doesn't have exhaustive cases, either filling them all out or adding a default will correct the rule's complaint.

Here are some examples of code working with a union of literals:

<!--tabs-->

### ❌ Incorrect

```ts
type Day =
  | 'Monday'
  | 'Tuesday'
  | 'Wednesday'
  | 'Thursday'
  | 'Friday'
  | 'Saturday'
  | 'Sunday';

declare const day: Day;
let result = 0;

switch (day) {
  case 'Monday':
    result = 1;
    break;
}
```

### ✅ Correct

```ts
type Day =
  | 'Monday'
  | 'Tuesday'
  | 'Wednesday'
  | 'Thursday'
  | 'Friday'
  | 'Saturday'
  | 'Sunday';

declare const day: Day;
let result = 0;

switch (day) {
  case 'Monday':
    result = 1;
    break;
  case 'Tuesday':
    result = 2;
    break;
  case 'Wednesday':
    result = 3;
    break;
  case 'Thursday':
    result = 4;
    break;
  case 'Friday':
    result = 5;
    break;
  case 'Saturday':
    result = 6;
    break;
  case 'Sunday':
    result = 7;
    break;
}
```

### ✅ Correct

```ts
type Day =
  | 'Monday'
  | 'Tuesday'
  | 'Wednesday'
  | 'Thursday'
  | 'Friday'
  | 'Saturday'
  | 'Sunday';

declare const day: Day;
let result = 0;

switch (day) {
  case 'Monday':
    result = 1;
    break;
  default:
    result = 42;
}
```

<!--/tabs-->

Likewise, here are some examples of code working with an enum:

<!--tabs-->

### ❌ Incorrect

```ts
enum Fruit {
  Apple,
  Banana,
  Cherry,
}

declare const fruit: Fruit;

switch (fruit) {
  case Fruit.Apple:
    console.log('an apple');
    break;
}
```

### ✅ Correct

```ts
enum Fruit {
  Apple,
  Banana,
  Cherry,
}

declare const fruit: Fruit;

switch (fruit) {
  case Fruit.Apple:
    console.log('an apple');
    break;

  case Fruit.Banana:
    console.log('a banana');
    break;

  case Fruit.Cherry:
    console.log('a cherry');
    break;
}
```

### ✅ Correct

```ts
enum Fruit {
  Apple,
  Banana,
  Cherry,
}

declare const fruit: Fruit;

switch (fruit) {
  case Fruit.Apple:
    console.log('an apple');
    break;

  default:
    console.log('a fruit');
    break;
}
```

<!--/tabs-->

## When Not To Use It

If you don't frequently `switch` over union types or enums with many parts, or intentionally wish to leave out some parts, this rule may not be for you.
