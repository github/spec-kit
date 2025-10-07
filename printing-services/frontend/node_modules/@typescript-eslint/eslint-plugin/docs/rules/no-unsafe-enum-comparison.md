---
description: 'Disallow comparing an enum value with a non-enum value.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-unsafe-enum-comparison** for documentation.

The TypeScript compiler can be surprisingly lenient when working with enums. String enums are widely considered to be safer than number enums, but even string enums have some pitfalls. For example, it is allowed to compare enum values against literals:

```ts
enum Vegetable {
  Asparagus = 'asparagus',
}

declare const vegetable: Vegetable;

vegetable === 'asparagus'; // No error
```

The above code snippet should instead be written as `vegetable === Vegetable.Asparagus`. Allowing literals in comparisons subverts the point of using enums in the first place. By enforcing comparisons with properly typed enums:

- It makes a codebase more resilient to enum members changing values.
- It allows for code IDEs to use the "Rename Symbol" feature to quickly rename an enum.
- It aligns code to the proper enum semantics of referring to them by name and treating their values as implementation details.

## Examples

<!--tabs-->

### ❌ Incorrect

```ts
enum Fruit {
  Apple,
}

declare let fruit: Fruit;

fruit === 0;
```

```ts
enum Vegetable {
  Asparagus = 'asparagus',
}

declare let vegetable: Vegetable;

vegetable === 'asparagus';
```

### ✅ Correct

```ts
enum Fruit {
  Apple,
}

declare let fruit: Fruit;

fruit === Fruit.Apple;
```

```ts
enum Vegetable {
  Asparagus = 'asparagus',
}

declare let vegetable: Vegetable;

vegetable === Vegetable.Asparagus;
```

<!--/tabs-->

## When Not To Use It

If you don't mind number and/or literal string constants being compared against enums, you likely don't need this rule.

Separately, in the rare case of relying on an third party enums that are only imported as `type`s, it may be difficult to adhere to this rule.
You might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.
