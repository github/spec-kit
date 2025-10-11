---
description: 'Require `Array#sort` and `Array#toSorted` calls to always provide a `compareFunction`.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/require-array-sort-compare** for documentation.

When called without a compare function, `Array#sort()` and `Array#toSorted()` converts all non-undefined array elements into strings and then compares said strings based off their UTF-16 code units [[ECMA specification](https://www.ecma-international.org/ecma-262/9.0/#sec-sortcompare)].

The result is that elements are sorted alphabetically, regardless of their type.
For example, when sorting numbers, this results in a "10 before 2" order:

```ts
[1, 2, 3, 10, 20, 30].sort(); //→ [1, 10, 2, 20, 3, 30]
```

This rule reports on any call to the sort methods that do not provide a `compare` argument.

## Examples

This rule aims to ensure all calls of the native sort methods provide a `compareFunction`, while ignoring calls to user-defined methods.

<!--tabs-->

### ❌ Incorrect

```ts
const array: any[];
const stringArray: string[];

array.sort();

// String arrays should be sorted using `String#localeCompare`.
stringArray.sort();
```

### ✅ Correct

```ts
const array: any[];
const userDefinedType: { sort(): void };

array.sort((a, b) => a - b);
array.sort((a, b) => a.localeCompare(b));

userDefinedType.sort();
```

## Options

### `ignoreStringArrays`

Examples of code for this rule with `{ ignoreStringArrays: true }`:

<!--tabs-->

#### ❌ Incorrect

```ts option='{ "ignoreStringArrays": true }'
const one = 1;
const two = 2;
const three = 3;
[one, two, three].sort();
```

#### ✅ Correct

```ts option='{ "ignoreStringArrays": true }'
const one = '1';
const two = '2';
const three = '3';
[one, two, three].sort();
```

## When Not To Use It

If you intentionally want your arrays to be always sorted in a string-like manner, you can turn this rule off safely.
