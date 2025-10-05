---
description: 'Disallow unused variables.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-unused-vars** for documentation.

This rule extends the base [`eslint/no-unused-vars`](https://eslint.org/docs/rules/no-unused-vars) rule.
It adds support for TypeScript features, such as types.

## Benefits Over TypeScript

TypeScript provides [`noUnusedLocals`](https://www.typescriptlang.org/tsconfig#noUnusedLocals) and [`noUnusedParameters`](https://www.typescriptlang.org/tsconfig#noUnusedParameters) compiler options that can report errors on unused local variables or parameters, respectively.
Those compiler options can be convenient to use if you don't want to set up ESLint and typescript-eslint.
However:

- These lint rules are more configurable than TypeScript's compiler options.
  - For example, the [`varsIgnorePattern` option](https://eslint.org/docs/latest/rules/no-unused-vars#varsignorepattern) can customize what names are always allowed to be exempted. TypeScript hardcodes its exemptions to names starting with `_`.
- [ESLint can be configured](https://eslint.org/docs/latest/use/configure/rules) within lines, files, and folders. TypeScript compiler options are linked to their TSConfig file.
- Many projects configure TypeScript's reported errors to block builds more aggressively than ESLint complaints. Blocking builds on unused variables can be inconvenient.

We generally recommend using `@typescript-eslint/no-unused-vars` to flag unused locals and parameters instead of TypeScript.

:::tip
Editors such as VS Code will still generally "grey out" unused variables even if `noUnusedLocals` and `noUnusedParameters` are not enabled in a project.
:::
