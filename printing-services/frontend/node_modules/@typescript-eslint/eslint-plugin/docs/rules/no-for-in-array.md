---
description: 'Disallow iterating over an array with a for-in loop.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-for-in-array** for documentation.

A for-in loop (`for (const i in o)`) iterates over the properties of an Object.
While it is legal to use for-in loops with array values, it is not common. There are several potential bugs with this:

1. It iterates over all enumerable properties, including non-index ones and the entire prototype chain. For example, [`RegExp.prototype.exec`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp/exec) returns an array with additional properties, and `for-in` will iterate over them. Some libraries or even your own code may add additional methods to `Array.prototype` (either as polyfill or as custom methods), and if not done properly, they may be iterated over as well.
2. It skips holes in the array. While sparse arrays are rare and advised against, they are still possible and your code should be able to handle them.
3. The "index" is returned as a string, not a number. This can be caught by TypeScript, but can still lead to subtle bugs.

You may have confused for-in with for-of, which iterates over the elements of the array. If you actually need the index, use a regular `for` loop or the `forEach` method.

## Examples

<!--tabs-->

### ❌ Incorrect

```ts
declare const array: string[];

for (const i in array) {
  console.log(array[i]);
}

for (const i in array) {
  console.log(i, array[i]);
}
```

### ✅ Correct

```ts
declare const array: string[];

for (const value of array) {
  console.log(value);
}

for (let i = 0; i < array.length; i += 1) {
  console.log(i, array[i]);
}

array.forEach((value, i) => {
  console.log(i, value);
});

for (const [i, value] of array.entries()) {
  console.log(i, value);
}
```

## When Not To Use It

If your project is a rare one that intentionally loops over string indices of arrays, you can turn off this rule.
You might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.
