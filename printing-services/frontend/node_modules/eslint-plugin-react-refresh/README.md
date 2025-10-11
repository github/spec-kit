# eslint-plugin-react-refresh [![npm](https://img.shields.io/npm/v/eslint-plugin-react-refresh)](https://www.npmjs.com/package/eslint-plugin-react-refresh)

Validate that your components can safely be updated with Fast Refresh.

## Explainer

"Fast Refresh", also known as "hot reloading", is a feature in many modern bundlers.
If you update some React component(s) on disk, then the bundler will know to update only the impacted parts of your page -- without a full page reload.

`eslint-plugin-react-refresh` enforces that your components are structured in a way that integrations such as [react-refresh](https://www.npmjs.com/package/react-refresh) expect.

### Limitations

⚠️ To avoid false positives, by default this plugin is only applied on `tsx` & `jsx` files. See [Options](#options) to run on JS files. ⚠️

The plugin relies on naming conventions (i.e. use PascalCase for components, camelCase for util functions). This is why there are some limitations:

- `export *` are not supported and will be reported as an error
- Anonymous function are not supported (i.e `export default function() {}`)
- Class components are not supported
- All-uppercase function export is considered an error when not using direct named export (ex `const CMS = () => <></>; export { CMS }`)

## Installation

```sh
npm i -D eslint-plugin-react-refresh
```

## Usage

This plugin provides a single rule, `react-refresh/only-export-components`. There are multiple ways to enable it.

### Recommended config

```js
import { defineConfig } from "eslint/config";
import reactRefresh from "eslint-plugin-react-refresh";

export default defineConfig(
  /* Main config */
  reactRefresh.configs.recommended,
);
```

### Vite config

This enables the `allowConstantExport` option which is supported by Vite React plugins.

```js
import { defineConfig } from "eslint/config";
import reactRefresh from "eslint-plugin-react-refresh";

export default defineConfig(
  /* Main config */
  reactRefresh.configs.vite,
);
```

### Next config <small>(v0.4.21)</small>

This allows exports like `fetchCache` and `revalidate` which are used in Page or Layout components and don't trigger a full page reload.

```js
import { defineConfig } from "eslint/config";
import reactRefresh from "eslint-plugin-react-refresh";

export default defineConfig(
  /* Main config */
  reactRefresh.configs.next,
);
```

### Without config

```js
import { defineConfig } from "eslint/config";
import reactRefresh from "eslint-plugin-react-refresh";

export default defineConfig({
  // in main config for TSX/JSX source files
  plugins: {
    "react-refresh": reactRefresh,
  },
  rules: {
    "react-refresh/only-export-components": "error",
  },
});
```

### Legacy config

```jsonc
{
  "plugins": ["react-refresh"],
  "rules": {
    "react-refresh/only-export-components": "error",
  },
}
```

## Examples

These examples are from enabling `react-refresh/only-exports-components`.

### Fail

```jsx
export const foo = () => {};
export const Bar = () => <></>;
```

```jsx
export default function () {}
export default compose()(MainComponent)
```

```jsx
export * from "./foo";
```

```jsx
const Tab = () => {};
export const tabs = [<Tab />, <Tab />];
```

```jsx
const App = () => {};
createRoot(document.getElementById("root")).render(<App />);
```

### Pass

```jsx
export default function Foo() {
  return <></>;
}
```

```jsx
const foo = () => {};
export const Bar = () => <></>;
```

```jsx
import { App } from "./App";
createRoot(document.getElementById("root")).render(<App />);
```

## Options

These options are all present on `react-refresh/only-exports-components`.

```ts
interface Options {
  allowExportNames?: string[];
  allowConstantExport?: boolean;
  customHOCs?: string[];
  checkJS?: boolean;
}

const defaultOptions: Options = {
  allowExportNames: [],
  allowConstantExport: false,
  customHOCs: [],
  checkJS: false,
};
```

### allowExportNames <small>(v0.4.4)</small>

> Default: `[]`

If you use a framework that handles HMR of some specific exports, you can use this option to avoid warning for them.

Example for [Remix](https://remix.run/docs/en/main/discussion/hot-module-replacement#supported-exports):

```json
{
  "react-refresh/only-export-components": [
    "error",
    { "allowExportNames": ["meta", "links", "headers", "loader", "action"] }
  ]
}
```

### allowConstantExport <small>(v0.4.0)</small>

> Default: `false` (`true` in `vite` config)

Don't warn when a constant (string, number, boolean, templateLiteral) is exported aside one or more components.

This should be enabled if the fast refresh implementation correctly handles this case (HMR when the constant doesn't change, propagate update to importers when the constant changes.). Vite supports it, PR welcome if you notice other integrations works well.

```json
{
  "react-refresh/only-export-components": [
    "error",
    { "allowConstantExport": true }
  ]
}
```

Enabling this option allows code such as the following:

```jsx
export const CONSTANT = 3;
export const Foo = () => <></>;
```

### checkJS <small>(v0.3.3)</small>

> Default: `false`

If you're using JSX inside `.js` files (which I don't recommend because it forces you to configure every tool you use to switch the parser), you can still use the plugin by enabling this option. To reduce the number of false positive, only files importing `react` are checked.

```json
{
  "react-refresh/only-export-components": ["error", { "checkJS": true }]
}
```

### customHOCs <small>(v0.4.15)</small>

If you're exporting a component wrapped in a custom HOC, you can use this option to avoid false positives.

```json
{
  "react-refresh/only-export-components": [
    "error",
    { "customHOCs": ["observer", "withAuth"] }
  ]
}
```
