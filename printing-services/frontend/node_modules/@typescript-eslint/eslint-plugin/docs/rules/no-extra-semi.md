---
description: 'Disallow unnecessary semicolons.'
---

> 🛑 This file is source code, not the primary documentation location! 🛑
>
> See **https://typescript-eslint.io/rules/no-extra-semi** for documentation.

This rule extends the base [`eslint/no-extra-semi`](https://eslint.org/docs/rules/no-extra-semi) rule.
It adds support for class properties.

Note that this rule is classified as a "Suggestion" rule instead of a "Layout & Formatting" rule because [adding extra semi-colons actually changes the AST of the program](https://typescript-eslint.io/play/#ts=5.1.6&showAST=es&fileType=.ts&code=MYewdgzgLgBAHjAvDAjAbg0A&eslintrc=N4KABGBEBOCuA2BTAzpAXGUEKQHYHsBaRADwBdoBDQ5RAWwEt0p8AzVyAGnG0gAEyATwAOKAMbQGwssWTwGuMgHoCxclRr0mGSImjR80SDwC%2BIE0A&tsconfig=&tokens=false). With that said, modern TypeScript formatters will remove extra semi-colons automatically during the formatting process. Thus, if you [use a formatter](/linting/troubleshooting/formatting), then enabling this rule is probably unnecessary.
