import { ParserOptions, TransformOptions } from "@babel/core";
import { Plugin, ResolvedConfig } from "vite";

//#region src/index.d.ts
interface Options {
  include?: string | RegExp | Array<string | RegExp>;
  exclude?: string | RegExp | Array<string | RegExp>;
  /**
   * Control where the JSX factory is imported from.
   * https://esbuild.github.io/api/#jsx-import-source
   * @default 'react'
   */
  jsxImportSource?: string;
  /**
   * Note: Skipping React import with classic runtime is not supported from v4
   * @default "automatic"
   */
  jsxRuntime?: 'classic' | 'automatic';
  /**
   * Babel configuration applied in both dev and prod.
   */
  babel?: BabelOptions | ((id: string, options: {
    ssr?: boolean;
  }) => BabelOptions);
  /**
   * React Fast Refresh runtime URL prefix.
   * Useful in a module federation context to enable HMR by specifying
   * the host application URL in the Vite config of a remote application.
   * @example
   * reactRefreshHost: 'http://localhost:3000'
   */
  reactRefreshHost?: string;
  /**
   * If set, disables the recommendation to use `@vitejs/plugin-react-oxc`
   */
  disableOxcRecommendation?: boolean;
}
type BabelOptions = Omit<TransformOptions, 'ast' | 'filename' | 'root' | 'sourceFileName' | 'sourceMaps' | 'inputSourceMap'>;
/**
 * The object type used by the `options` passed to plugins with
 * an `api.reactBabel` method.
 */
interface ReactBabelOptions extends BabelOptions {
  plugins: Extract<BabelOptions['plugins'], any[]>;
  presets: Extract<BabelOptions['presets'], any[]>;
  overrides: Extract<BabelOptions['overrides'], any[]>;
  parserOpts: ParserOptions & {
    plugins: Extract<ParserOptions['plugins'], any[]>;
  };
}
type ReactBabelHook = (babelConfig: ReactBabelOptions, context: ReactBabelHookContext, config: ResolvedConfig) => void;
type ReactBabelHookContext = {
  ssr: boolean;
  id: string;
};
type ViteReactPluginApi = {
  /**
   * Manipulate the Babel options of `@vitejs/plugin-react`
   */
  reactBabel?: ReactBabelHook;
};
declare function viteReact(opts?: Options): Plugin[];
declare namespace viteReact {
  var preambleCode: string;
}
//#endregion
export { BabelOptions, Options, ReactBabelOptions, ViteReactPluginApi, viteReact as default };