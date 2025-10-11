/* eslint-disable no-restricted-globals */

// type utils
module.exports.defineConfig = (config) => config

// proxy cjs utils (sync functions)
Object.assign(module.exports, require('./dist/node-cjs/publicUtils.cjs'))

// async functions, can be redirect from ESM build
const asyncFunctions = [
  'build',
  'createServer',
  'preview',
  'transformWithEsbuild',
  'resolveConfig',
  'optimizeDeps',
  'formatPostcssSourceMap',
  'loadConfigFromFile',
  'preprocessCSS',
]
asyncFunctions.forEach((name) => {
  module.exports[name] = (...args) =>
    import('./dist/node/index.js').then((i) => i[name](...args))
})

// some sync functions are marked not supported due to their complexity and uncommon usage
const unsupportedCJS = ['resolvePackageEntry', 'resolvePackageData']
unsupportedCJS.forEach((name) => {
  module.exports[name] = () => {
    throw new Error(
      `"${name}" is not supported in CJS build of Vite 4.\nPlease use ESM or dynamic imports \`const { ${name} } = await import('vite')\`.`,
    )
  }
})
