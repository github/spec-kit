---
title: Overview
sidebar_label: Overview
pagination_next: null
pagination_prev: null
slug: /
---

`@typescript-eslint/eslint-plugin` includes over 100 rules that detect best practice violations, bugs, and/or stylistic issues specifically for TypeScript code. All of our rules are listed below.

:::tip
Instead of enabling rules one by one, we recommend using one of [our pre-defined configs](/linting/configs) to enable a large set of recommended rules.
:::

## Rules

The rules are listed in alphabetical order. You can optionally filter them based on these categories:

import RulesTable from "@site/src/components/RulesTable";

<RulesTable />

## Filtering

### Config Group (⚙️)

"Config Group" refers to the [pre-defined config](/linting/configs) that includes the rule. Extending from a configuration preset allow for enabling a large set of recommended rules all at once.

### Metadata

- `🔧 fixable` refers to whether the rule contains an [ESLint `--fix` auto-fixer](https://eslint.org/docs/latest/use/command-line-interface#--fix).
- `💡 has suggestions` refers to whether the rule contains an ESLint suggestion fixer.
  - Sometimes, it is not safe to automatically fix the code with an auto-fixer. But in these cases, we often have a good guess of what the correct fix should be, and we can provide it as a suggestion to the developer.
- `💭 requires type information` refers to whether the rule requires [typed linting](/linting/typed-linting).
- `🧱 extension rule` means that the rule is an extension of an [core ESLint rule](https://eslint.org/docs/latest/rules) (see [Extension Rules](#extension-rules)).
- `📐 formatting rule` means that the rule has to do with formatting.
  - We [strongly recommend against using ESLint for formatting](/linting/troubleshooting/formatting).
  - Soon, formatting rules will be moved to the [ESLint stylistic plugin](https://eslint.style).
- `💀 deprecated rule` means that the rule should no longer be used and will be removed from the plugin in a future version.

## Extension Rules

Some core ESLint rules do not support TypeScript syntax: either they crash, ignore the syntax, or falsely report against it.
In these cases, we create what we call an "extension rule": a rule within our plugin that has the same functionality, but also supports TypeScript.

Extension rules generally completely replace the base rule from ESLint core.
If the base rule is enabled in a config you extend from, you'll need to disable the base rule:

```js
module.exports = {
  extends: ['eslint:recommended'],
  rules: {
    // Note: you must disable the base rule as it can report incorrect errors
    'no-unused-vars': 'off',
    '@typescript-eslint/no-unused-vars': 'error',
  },
};
```

[Search for `🧱 extension rule`s](?=extension#rules) in this page to see all extension rules.
