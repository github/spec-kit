# @vitejs/plugin-react [![npm](https://img.shields.io/npm/v/@vitejs/plugin-react.svg)](https://npmjs.com/package/@vitejs/plugin-react)

The default Vite plugin for React projects.

- enable [Fast Refresh](https://www.npmjs.com/package/react-refresh) in development (requires react >= 16.9)
- use the [automatic JSX runtime](https://legacy.reactjs.org/blog/2020/09/22/introducing-the-new-jsx-transform.html)
- use custom Babel plugins/presets
- small installation size

```js
// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
```

## Options

### include/exclude

Includes `.js`, `.jsx`, `.ts` & `.tsx` by default. This option can be used to add fast refresh to `.mdx` files:

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import mdx from '@mdx-js/rollup'

export default defineConfig({
  plugins: [
    { enforce: 'pre', ...mdx() },
    react({ include: /\.(mdx|js|jsx|ts|tsx)$/ }),
  ],
})
```

> `node_modules` are never processed by this plugin (but esbuild will)

### jsxImportSource

Control where the JSX factory is imported from. Default to `'react'`

```js
react({ jsxImportSource: '@emotion/react' })
```

### jsxRuntime

By default, the plugin uses the [automatic JSX runtime](https://legacy.reactjs.org/blog/2020/09/22/introducing-the-new-jsx-transform.html). However, if you encounter any issues, you may opt out using the `jsxRuntime` option.

```js
react({ jsxRuntime: 'classic' })
```

### babel

The `babel` option lets you add plugins, presets, and [other configuration](https://babeljs.io/docs/en/options) to the Babel transformation performed on each included file.

```js
react({
  babel: {
    presets: [...],
    // Your plugins run before any built-in transform (eg: Fast Refresh)
    plugins: [...],
    // Use .babelrc files
    babelrc: true,
    // Use babel.config.js files
    configFile: true,
  }
})
```

Note: When not using plugins, only esbuild is used for production builds, resulting in faster builds.

#### Proposed syntax

If you are using ES syntax that are still in proposal status (e.g. class properties), you can selectively enable them with the `babel.parserOpts.plugins` option:

```js
react({
  babel: {
    parserOpts: {
      plugins: ['decorators-legacy'],
    },
  },
})
```

This option does not enable _code transformation_. That is handled by esbuild.

**Note:** TypeScript syntax is handled automatically.

Here's the [complete list of Babel parser plugins](https://babeljs.io/docs/en/babel-parser#ecmascript-proposalshttpsgithubcombabelproposals).

### reactRefreshHost

The `reactRefreshHost` option is only necessary in a module federation context. It enables HMR to work between a remote & host application. In your remote Vite config, you would add your host origin:

```js
react({ reactRefreshHost: 'http://localhost:3000' })
```

Under the hood, this simply updates the React Fash Refresh runtime URL from `/@react-refresh` to `http://localhost:3000/@react-refresh` to ensure there is only one Refresh runtime across the whole application. Note that if you define `base` option in the host application, you need to include it in the option, like: `http://localhost:3000/{base}`.

## Middleware mode

In [middleware mode](https://vite.dev/config/server-options.html#server-middlewaremode), you should make sure your entry `index.html` file is transformed by Vite. Here's an example for an Express server:

```js
app.get('/', async (req, res, next) => {
  try {
    let html = fs.readFileSync(path.resolve(root, 'index.html'), 'utf-8')

    // Transform HTML using Vite plugins.
    html = await viteServer.transformIndexHtml(req.url, html)

    res.send(html)
  } catch (e) {
    return next(e)
  }
})
```

Otherwise, you'll probably get this error:

```
Uncaught Error: @vitejs/plugin-react can't detect preamble. Something is wrong.
```

### disableOxcRecommendation

If set, disables the recommendation to use `@vitejs/plugin-react-oxc` (which is shown when `rolldown-vite` is detected and `babel` is not configured).

## Consistent components exports

For React refresh to work correctly, your file should only export React components. You can find a good explanation in the [Gatsby docs](https://www.gatsbyjs.com/docs/reference/local-development/fast-refresh/#how-it-works).

If an incompatible change in exports is found, the module will be invalidated and HMR will propagate. To make it easier to export simple constants alongside your component, the module is only invalidated when their value changes.

You can catch mistakes and get more detailed warning with this [eslint rule](https://github.com/ArnaudBarre/eslint-plugin-react-refresh).
