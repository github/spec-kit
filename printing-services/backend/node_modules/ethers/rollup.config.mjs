
import { nodeResolve } from '@rollup/plugin-node-resolve';

function getConfig(opts) {
  if (opts == null) { opts = { }; }

  const file = `./dist/ethers${ (opts.suffix || "") }.js`;
  const exportConditions = [ "import", "default" ];
  const mainFields = [ "module", "main" ];
  if (opts.browser) { mainFields.unshift("browser"); }

  return {
    input: "./lib.esm/index.js",
    output: {
      file,
      banner: "const __$G = (typeof globalThis !== 'undefined' ? globalThis: typeof window !== 'undefined' ? window: typeof global !== 'undefined' ? global: typeof self !== 'undefined' ? self: {});",
      name: (opts.name || undefined),
      format: (opts.format || "esm"),
      sourcemap: true
    },
    context: "__$G",
    treeshake: true,
    plugins: [ nodeResolve({
        exportConditions,
        mainFields,
        modulesOnly: true,
        preferBuiltins: false
    }) ],
  };
}

export default [
  getConfig({ browser: true }),
  getConfig({ browser: true, suffix: ".umd", format: "umd", name: "ethers" }),
  {
    input: "./lib.esm/wordlists/wordlists-extra.js",
    output: {
      file: "./dist/wordlists-extra.js",
      format: "esm",
      sourcemap: true
    },
    treeshake: true,
    plugins: [ nodeResolve({
      exportConditions: [ "default", "module", "import" ],
      mainFields: [ "browser", "module", "main" ],
      modulesOnly: true,
      preferBuiltins: false
    }) ],
  }
];
