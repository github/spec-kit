---
description: 'Disallow using the `delete` operator on array values.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-array-delete** for documentation.

When using the `delete` operator with an array value, the array's `length` property is not affected,
but the element at the specified index is removed and leaves an empty slot in the array.
This is likely to lead to unexpected behavior. As mentioned in the
[MDN documentation](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/delete#deleting_array_elements),
the recommended way to remove an element from an array is by using the
[`Array#splice`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/splice) method.

## Examples

<!--tabs-->

### ❌ Incorrect

```ts
declare const arr: number[];

delete arr[0];
```

### ✅ Correct

```ts
declare const arr: number[];

arr.splice(0, 1);
```

<!--/tabs-->

## When Not To Use It

When you want to allow the delete operator with array expressions.
