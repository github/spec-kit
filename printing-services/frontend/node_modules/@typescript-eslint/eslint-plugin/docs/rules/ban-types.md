---
description: 'Disallow certain types.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/ban-types** for documentation.

Some built-in types have aliases, while some types are considered dangerous or harmful.
It's often a good idea to ban certain types to help with consistency and safety.

This rule bans specific types and can suggest alternatives.
Note that it does not ban the corresponding runtime objects from being used.

## Examples

Examples of code with the default options:

<!--tabs-->

### ❌ Incorrect

```ts
// use lower-case primitives for consistency
const str: String = 'foo';
const bool: Boolean = true;
const num: Number = 1;
const symb: Symbol = Symbol('foo');
const bigInt: BigInt = 1n;

// use a proper function type
const func: Function = () => 1;

// use safer object types
const lowerObj: Object = {};
const capitalObj: Object = { a: 'string' };

const curly1: {} = 1;
const curly2: {} = { a: 'string' };
```

### ✅ Correct

```ts
// use lower-case primitives for consistency
const str: string = 'foo';
const bool: boolean = true;
const num: number = 1;
const symb: symbol = Symbol('foo');
const bigInt: bigint = 1n;

// use a proper function type
const func: () => number = () => 1;

// use safer object types
const lowerObj: object = {};
const capitalObj: { a: string } = { a: 'string' };

const curly1: number = 1;
const curly2: Record<'a', string> = { a: 'string' };
```

## Options

The default options provide a set of "best practices", intended to provide safety and standardization in your codebase:

- Don't use the upper-case primitive types, you should use the lower-case types for consistency.
- Avoid the `Function` type, as it provides little safety for the following reasons:
  - It provides no type safety when calling the value, which means it's easy to provide the wrong arguments.
  - It accepts class declarations, which will fail when called, as they are called without the `new` keyword.
- Avoid the `Object` and `{}` types, as they mean "any non-nullish value".
  - This is a point of confusion for many developers, who think it means "any object type".
  - See [this comment for more information](https://github.com/typescript-eslint/typescript-eslint/issues/2063#issuecomment-675156492).

<details>
<summary>Default Options</summary>

<!-- Inject default options -->

</details>

### `types`

An object whose keys are the types you want to ban, and the values are error messages.

The type can either be a type name literal (`Foo`), a type name with generic parameter instantiation(s) (`Foo<Bar>`), the empty object literal (`{}`), or the empty tuple type (`[]`).

The values can be:

- A string, which is the error message to be reported; or
- `false` to specifically un-ban this type (useful when you are using `extendDefaults`); or
- An object with the following properties:
  - `message: string` - the message to display when the type is matched.
  - `fixWith?: string` - a string to replace the banned type with when the fixer is run. If this is omitted, no fix will be done.
  - `suggest?: string[]` - a list of suggested replacements for the banned type.

### `extendDefaults`

If you're specifying custom `types`, you can set this to `true` to extend the default `types` configuration. This is a convenience option to save you copying across the defaults when adding another type.

If this is `false`, the rule will _only_ use the types defined in your configuration.

Example configuration:

```jsonc
{
  "@typescript-eslint/ban-types": [
    "error",
    {
      "types": {
        // add a custom message to help explain why not to use it
        "Foo": "Don't use Foo because it is unsafe",

        // add a custom message, AND tell the plugin how to fix it
        "OldAPI": {
          "message": "Use NewAPI instead",
          "fixWith": "NewAPI",
        },

        // un-ban a type that's banned by default
        "{}": false,
      },
      "extendDefaults": true,
    },
  ],
}
```

## When Not To Use It

If your project is a rare one that intentionally deals with the class equivalents of primitives, it might not be worthwhile to enable the default `ban-types` options.
You might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.
