---
description: 'Enforce that class methods utilize `this`.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/class-methods-use-this** for documentation.

This rule extends the base [`eslint/class-methods-use-this`](https://eslint.org/docs/rules/class-methods-use-this) rule.
It adds support for ignoring `override` methods or methods on classes that implement an interface.

## Options

This rule adds the following options:

```ts
interface Options extends BaseClassMethodsUseThisOptions {
  ignoreOverrideMethods?: boolean;
  ignoreClassesThatImplementAnInterface?: boolean | 'public-fields';
}

const defaultOptions: Options = {
  ...baseClassMethodsUseThisOptions,
  ignoreOverrideMethods: false,
  ignoreClassesThatImplementAnInterface: false,
};
```

### `ignoreOverrideMethods`

Makes the rule to ignores any class member explicitly marked with `override`.

Example of a correct code when `ignoreOverrideMethods` is set to `true`:

```ts option='{ "ignoreOverrideMethods": true }' showPlaygroundButton
class X {
  override method() {}
  override property = () => {};
}
```

### `ignoreClassesThatImplementAnInterface`

Makes the rule ignore class members that are defined within a class that `implements` a type.
If specified, it can be either:

- `true`: Ignore all classes that implement an interface
- `'public-fields'`: Ignore only the public fields of classes that implement an interface

It's important to note that this option does not only apply to members defined in the interface as that would require type information.

#### `true`

Example of a correct code when `ignoreClassesThatImplementAnInterface` is set to `true`:

```ts option='{ "ignoreClassesThatImplementAnInterface": true }' showPlaygroundButton
class X implements Y {
  method() {}
  property = () => {};
}
```

#### `'public-fields'`

Example of a incorrect code when `ignoreClassesThatImplementAnInterface` is set to `'public-fields'`:

<!--tabs-->

##### ❌ Incorrect

```ts
class X implements Y {
  method() {}
  property = () => {};

  private privateMethod() {}
  private privateProperty = () => {};

  protected privateMethod() {}
  protected privateProperty = () => {};
}
```

##### ✅ Correct

```ts
class X implements Y {
  method() {}
  property = () => {};
}
```

## When Not To Use It

If your project dynamically changes `this` scopes around in a way TypeScript has difficulties modeling, this rule may not be viable to use.
You might consider using [ESLint disable comments](https://eslint.org/docs/latest/use/configure/rules#using-configuration-comments-1) for those specific situations instead of completely disabling this rule.
