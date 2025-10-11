---
description: 'Enforce a maximum number of parameters in function definitions.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/max-params** for documentation.

This rule extends the base [`eslint/max-params`](https://eslint.org/docs/rules/max-params) rule.
This version adds support for TypeScript `this` parameters so they won't be counted as a parameter.
