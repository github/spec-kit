/// <reference types="node" />

import type { Agent } from 'node:http';
import type { BuildOptions as BuildOptions_2 } from 'esbuild';
import { ChunkMetadata } from "../../types/metadata.js";
import type { ClientRequest } from 'node:http';
import type { ClientRequestArgs } from 'node:http';
import { ConnectedPayload } from "../../types/hmrPayload.js";
import { CustomEventMap } from "../../types/customEvent.js";
import { CustomPayload } from "../../types/hmrPayload.js";
import type { CustomPluginOptions } from 'rollup';
import type { Duplex } from 'node:stream';
import type { DuplexOptions } from 'node:stream';
import { ErrorPayload } from "../../types/hmrPayload.js";
import { TransformOptions as EsbuildTransformOptions } from 'esbuild';
import { version as esbuildVersion } from 'esbuild';
import { EventEmitter } from 'node:events';
import * as events from 'node:events';
import type { ExistingRawSourceMap } from 'rollup';
import type * as fs from 'node:fs';
import { FullReloadPayload } from "../../types/hmrPayload.js";
import { GeneralImportGlobOptions } from "../../types/importGlob.js";
import type { GetManualChunk } from 'rollup';
import { HMRPayload } from "../../types/hmrPayload.js";
import * as http from 'node:http';
import { ImportGlobEagerFunction } from "../../types/importGlob.js";
import { ImportGlobFunction } from "../../types/importGlob.js";
import { ImportGlobOptions } from "../../types/importGlob.js";
import type { IncomingMessage } from 'node:http';
import { InferCustomEventPayload } from "../../types/customEvent.js";
import type { InputOption } from 'rollup';
import type { InputOptions } from 'rollup';
import { InvalidatePayload } from "../../types/customEvent.js";
import { KnownAsTypeMap } from "../../types/importGlob.js";
import type { LoadResult } from 'rollup';

import type { ModuleFormat } from 'rollup';
import type { ModuleInfo } from 'rollup';
import type * as net from 'node:net';
import type { ObjectHook } from 'rollup';
import type { OutgoingHttpHeaders } from 'node:http';
import type { OutputBundle } from 'rollup';
import type { OutputChunk } from 'rollup';
import type { PartialResolvedId } from 'rollup';
import type { Plugin as Plugin_3 } from 'rollup';
import type { PluginContext } from 'rollup';
import type { PluginHooks } from 'rollup';
import type * as PostCSS from 'postcss';
import { PrunePayload } from "../../types/hmrPayload.js";
import type { ResolveIdResult } from 'rollup';
import type * as Rollup from 'rollup';
import type { RollupError } from 'rollup';
import type { RollupOptions } from 'rollup';
import type { RollupOutput } from 'rollup';
import { VERSION as rollupVersion } from 'rollup';
import type { RollupWatcher } from 'rollup';
import type { SecureContextOptions } from 'node:tls';
import type { Server } from 'node:http';
import type { Server as Server_2 } from 'node:https';
import type { ServerOptions as ServerOptions_2 } from 'node:https';
import type { ServerResponse } from 'node:http';
import type { SourceDescription } from 'rollup';
import type { SourceMap } from 'rollup';
import type { SourceMapInput } from 'rollup';
import type * as stream from 'node:stream';
import type { TransformPluginContext } from 'rollup';
import type { TransformResult as TransformResult_2 } from 'rollup';
import type { TransformResult as TransformResult_3 } from 'esbuild';
import { Update } from "../../types/hmrPayload.js";
import { UpdatePayload } from "../../types/hmrPayload.js";
import type * as url from 'node:url';
import type { URL as URL_2 } from 'node:url';
import type { WatcherOptions } from 'rollup';
import type { ZlibOptions } from 'node:zlib';

export declare interface Alias {
    find: string | RegExp
    replacement: string
    /**
     * Instructs the plugin to use an alternative resolving algorithm,
     * rather than the Rollup's resolver.
     * @default null
     */
    customResolver?: ResolverFunction | ResolverObject | null
}

/**
 * Specifies an `Object`, or an `Array` of `Object`,
 * which defines aliases used to replace values in `import` or `require` statements.
 * With either format, the order of the entries is important,
 * in that the first defined rules are applied first.
 *
 * This is passed to \@rollup/plugin-alias as the "entries" field
 * https://github.com/rollup/plugins/tree/master/packages/alias#entries
 */
export declare type AliasOptions = readonly Alias[] | { [find: string]: string }

export declare type AnymatchFn = (testString: string) => boolean

export declare type AnymatchPattern = string | RegExp | AnymatchFn

/**
 * spa: include SPA fallback middleware and configure sirv with `single: true` in preview
 *
 * mpa: only include non-SPA HTML middlewares
 *
 * custom: don't include HTML middlewares
 */
export declare type AppType = 'spa' | 'mpa' | 'custom';

export declare interface AwaitWriteFinishOptions {
    /**
     * Amount of time in milliseconds for a file size to remain constant before emitting its event.
     */
    stabilityThreshold?: number

    /**
     * File size polling interval.
     */
    pollInterval?: number
}

/**
 * Bundles the app for production.
 * Returns a Promise containing the build result.
 */
export declare function build(inlineConfig?: InlineConfig): Promise<RollupOutput | RollupOutput[] | RollupWatcher>;

export declare function buildErrorMessage(err: RollupError, args?: string[], includeStack?: boolean): string;

export declare interface BuildOptions {
    /**
     * Compatibility transform target. The transform is performed with esbuild
     * and the lowest supported target is es2015/es6. Note this only handles
     * syntax transformation and does not cover polyfills (except for dynamic
     * import)
     *
     * Default: 'modules' - Similar to `@babel/preset-env`'s targets.esmodules,
     * transpile targeting browsers that natively support dynamic es module imports.
     * https://caniuse.com/es6-module-dynamic-import
     *
     * Another special value is 'esnext' - which only performs minimal transpiling
     * (for minification compat) and assumes native dynamic imports support.
     *
     * For custom targets, see https://esbuild.github.io/api/#target and
     * https://esbuild.github.io/content-types/#javascript for more details.
     * @default 'modules'
     */
    target?: 'modules' | EsbuildTransformOptions['target'] | false;
    /**
     * whether to inject module preload polyfill.
     * Note: does not apply to library mode.
     * @default true
     * @deprecated use `modulePreload.polyfill` instead
     */
    polyfillModulePreload?: boolean;
    /**
     * Configure module preload
     * Note: does not apply to library mode.
     * @default true
     */
    modulePreload?: boolean | ModulePreloadOptions;
    /**
     * Directory relative from `root` where build output will be placed. If the
     * directory exists, it will be removed before the build.
     * @default 'dist'
     */
    outDir?: string;
    /**
     * Directory relative from `outDir` where the built js/css/image assets will
     * be placed.
     * @default 'assets'
     */
    assetsDir?: string;
    /**
     * Static asset files smaller than this number (in bytes) will be inlined as
     * base64 strings. Default limit is `4096` (4kb). Set to `0` to disable.
     * @default 4096
     */
    assetsInlineLimit?: number;
    /**
     * Whether to code-split CSS. When enabled, CSS in async chunks will be
     * inlined as strings in the chunk and inserted via dynamically created
     * style tags when the chunk is loaded.
     * @default true
     */
    cssCodeSplit?: boolean;
    /**
     * An optional separate target for CSS minification.
     * As esbuild only supports configuring targets to mainstream
     * browsers, users may need this option when they are targeting
     * a niche browser that comes with most modern JavaScript features
     * but has poor CSS support, e.g. Android WeChat WebView, which
     * doesn't support the #RGBA syntax.
     * @default target
     */
    cssTarget?: EsbuildTransformOptions['target'] | false;
    /**
     * Override CSS minification specifically instead of defaulting to `build.minify`,
     * so you can configure minification for JS and CSS separately.
     * @default 'esbuild'
     */
    cssMinify?: boolean | 'esbuild' | 'lightningcss';
    /**
     * If `true`, a separate sourcemap file will be created. If 'inline', the
     * sourcemap will be appended to the resulting output file as data URI.
     * 'hidden' works like `true` except that the corresponding sourcemap
     * comments in the bundled files are suppressed.
     * @default false
     */
    sourcemap?: boolean | 'inline' | 'hidden';
    /**
     * Set to `false` to disable minification, or specify the minifier to use.
     * Available options are 'terser' or 'esbuild'.
     * @default 'esbuild'
     */
    minify?: boolean | 'terser' | 'esbuild';
    /**
     * Options for terser
     * https://terser.org/docs/api-reference#minify-options
     */
    terserOptions?: Terser.MinifyOptions;
    /**
     * Will be merged with internal rollup options.
     * https://rollupjs.org/configuration-options/
     */
    rollupOptions?: RollupOptions;
    /**
     * Options to pass on to `@rollup/plugin-commonjs`
     */
    commonjsOptions?: RollupCommonJSOptions;
    /**
     * Options to pass on to `@rollup/plugin-dynamic-import-vars`
     */
    dynamicImportVarsOptions?: RollupDynamicImportVarsOptions;
    /**
     * Whether to write bundle to disk
     * @default true
     */
    write?: boolean;
    /**
     * Empty outDir on write.
     * @default true when outDir is a sub directory of project root
     */
    emptyOutDir?: boolean | null;
    /**
     * Copy the public directory to outDir on write.
     * @default true
     * @experimental
     */
    copyPublicDir?: boolean;
    /**
     * Whether to emit a manifest.json under assets dir to map hash-less filenames
     * to their hashed versions. Useful when you want to generate your own HTML
     * instead of using the one generated by Vite.
     *
     * Example:
     *
     * ```json
     * {
     *   "main.js": {
     *     "file": "main.68fe3fad.js",
     *     "css": "main.e6b63442.css",
     *     "imports": [...],
     *     "dynamicImports": [...]
     *   }
     * }
     * ```
     * @default false
     */
    manifest?: boolean | string;
    /**
     * Build in library mode. The value should be the global name of the lib in
     * UMD mode. This will produce esm + cjs + umd bundle formats with default
     * configurations that are suitable for distributing libraries.
     * @default false
     */
    lib?: LibraryOptions | false;
    /**
     * Produce SSR oriented build. Note this requires specifying SSR entry via
     * `rollupOptions.input`.
     * @default false
     */
    ssr?: boolean | string;
    /**
     * Generate SSR manifest for determining style links and asset preload
     * directives in production.
     * @default false
     */
    ssrManifest?: boolean | string;
    /**
     * Emit assets during SSR.
     * @experimental
     * @default false
     */
    ssrEmitAssets?: boolean;
    /**
     * Set to false to disable reporting compressed chunk sizes.
     * Can slightly improve build speed.
     * @default true
     */
    reportCompressedSize?: boolean;
    /**
     * Adjust chunk size warning limit (in kbs).
     * @default 500
     */
    chunkSizeWarningLimit?: number;
    /**
     * Rollup watch options
     * https://rollupjs.org/configuration-options/#watch
     * @default null
     */
    watch?: WatcherOptions | null;
}

export { ChunkMetadata }

export declare interface CommonServerOptions {
    /**
     * Specify server port. Note if the port is already being used, Vite will
     * automatically try the next available port so this may not be the actual
     * port the server ends up listening on.
     */
    port?: number;
    /**
     * If enabled, vite will exit if specified port is already in use
     */
    strictPort?: boolean;
    /**
     * Specify which IP addresses the server should listen on.
     * Set to 0.0.0.0 to listen on all addresses, including LAN and public addresses.
     */
    host?: string | boolean;
    /**
     * The hostnames that Vite is allowed to respond to.
     * `localhost` and subdomains under `.localhost` and all IP addresses are allowed by default.
     * When using HTTPS, this check is skipped.
     *
     * If a string starts with `.`, it will allow that hostname without the `.` and all subdomains under the hostname.
     * For example, `.example.com` will allow `example.com`, `foo.example.com`, and `foo.bar.example.com`.
     *
     * If set to `true`, the server is allowed to respond to requests for any hosts.
     * This is not recommended as it will be vulnerable to DNS rebinding attacks.
     */
    allowedHosts?: string[] | true;
    /**
     * Enable TLS + HTTP/2.
     * Note: this downgrades to TLS only when the proxy option is also used.
     */
    https?: boolean | ServerOptions_2;
    /**
     * Open browser window on startup
     */
    open?: boolean | string;
    /**
     * Configure custom proxy rules for the dev server. Expects an object
     * of `{ key: options }` pairs.
     * Uses [`http-proxy`](https://github.com/http-party/node-http-proxy).
     * Full options [here](https://github.com/http-party/node-http-proxy#options).
     *
     * Example `vite.config.js`:
     * ``` js
     * module.exports = {
     *   proxy: {
     *     // string shorthand
     *     '/foo': 'http://localhost:4567/foo',
     *     // with options
     *     '/api': {
     *       target: 'http://jsonplaceholder.typicode.com',
     *       changeOrigin: true,
     *       rewrite: path => path.replace(/^\/api/, '')
     *     }
     *   }
     * }
     * ```
     */
    proxy?: Record<string, string | ProxyOptions>;
    /**
     * Configure CORS for the dev server.
     * Uses https://github.com/expressjs/cors.
     *
     * When enabling this option, **we recommend setting a specific value
     * rather than `true`** to avoid exposing the source code to untrusted origins.
     *
     * Set to `true` to allow all methods from any origin, or configure separately
     * using an object.
     *
     * @default false
     */
    cors?: CorsOptions | boolean;
    /**
     * Specify server response headers.
     */
    headers?: OutgoingHttpHeaders;
}

export declare interface ConfigEnv {
    command: 'build' | 'serve';
    mode: string;
    /**
     * @experimental
     */
    ssrBuild?: boolean;
}

export declare namespace Connect {
    export type ServerHandle = HandleFunction | http.Server

    export class IncomingMessage extends http.IncomingMessage {
        originalUrl?: http.IncomingMessage['url'] | undefined
    }

    export type NextFunction = (err?: any) => void

    export type SimpleHandleFunction = (
    req: IncomingMessage,
    res: http.ServerResponse,
    ) => void
    export type NextHandleFunction = (
    req: IncomingMessage,
    res: http.ServerResponse,
    next: NextFunction,
    ) => void
    export type ErrorHandleFunction = (
    err: any,
    req: IncomingMessage,
    res: http.ServerResponse,
    next: NextFunction,
    ) => void
    export type HandleFunction =
    | SimpleHandleFunction
    | NextHandleFunction
    | ErrorHandleFunction

    export interface ServerStackItem {
        route: string
        handle: ServerHandle
    }

    export interface Server extends NodeJS.EventEmitter {
        (req: http.IncomingMessage, res: http.ServerResponse, next?: Function): void

        route: string
        stack: ServerStackItem[]

        /**
         * Utilize the given middleware `handle` to the given `route`,
         * defaulting to _/_. This "route" is the mount-point for the
         * middleware, when given a value other than _/_ the middleware
         * is only effective when that segment is present in the request's
         * pathname.
         *
         * For example if we were to mount a function at _/admin_, it would
         * be invoked on _/admin_, and _/admin/settings_, however it would
         * not be invoked for _/_, or _/posts_.
         */
        use(fn: NextHandleFunction): Server
        use(fn: HandleFunction): Server
        use(route: string, fn: NextHandleFunction): Server
        use(route: string, fn: HandleFunction): Server

        /**
         * Handle server requests, punting them down
         * the middleware stack.
         */
        handle(
        req: http.IncomingMessage,
        res: http.ServerResponse,
        next: Function,
        ): void

        /**
         * Listen for connections.
         *
         * This method takes the same arguments
         * as node's `http.Server#listen()`.
         *
         * HTTP and HTTPS:
         *
         * If you run your application both as HTTP
         * and HTTPS you may wrap them individually,
         * since your Connect "server" is really just
         * a JavaScript `Function`.
         *
         *      var connect = require('connect')
         *        , http = require('http')
         *        , https = require('https');
         *
         *      var app = connect();
         *
         *      http.createServer(app).listen(80);
         *      https.createServer(options, app).listen(443);
         */
        listen(
        port: number,
        hostname?: string,
        backlog?: number,
        callback?: Function,
        ): http.Server
        listen(port: number, hostname?: string, callback?: Function): http.Server
        listen(path: string, callback?: Function): http.Server
        listen(handle: any, listeningListener?: Function): http.Server
    }
}

export { ConnectedPayload }

/**
 * https://github.com/expressjs/cors#configuration-options
 */
export declare interface CorsOptions {
    /**
     * Configures the Access-Control-Allow-Origin CORS header.
     *
     * **We recommend setting a specific value rather than
     * `true`** to avoid exposing the source code to untrusted origins.
     */
    origin?: CorsOrigin | ((origin: string, cb: (err: Error, origins: CorsOrigin) => void) => void);
    methods?: string | string[];
    allowedHeaders?: string | string[];
    exposedHeaders?: string | string[];
    credentials?: boolean;
    maxAge?: number;
    preflightContinue?: boolean;
    optionsSuccessStatus?: number;
}

export declare type CorsOrigin = boolean | string | RegExp | (string | RegExp)[];

export declare const createFilter: (include?: FilterPattern, exclude?: FilterPattern, options?: {
    resolve?: string | false | null;
}) => (id: string | unknown) => boolean;

export declare function createLogger(level?: LogLevel, options?: LoggerOptions): Logger;

export declare function createServer(inlineConfig?: InlineConfig): Promise<ViteDevServer>;

declare interface CSSModulesConfig {
    /** The pattern to use when renaming class names and other identifiers. Default is `[hash]_[local]`. */
    pattern?: string,
    /** Whether to rename dashed identifiers, e.g. custom properties. */
    dashedIdents?: boolean
}

export declare interface CSSModulesOptions {
    getJSON?: (cssFileName: string, json: Record<string, string>, outputFileName: string) => void;
    scopeBehaviour?: 'global' | 'local';
    globalModulePaths?: RegExp[];
    generateScopedName?: string | ((name: string, filename: string, css: string) => string);
    hashPrefix?: string;
    /**
     * default: undefined
     */
    localsConvention?: 'camelCase' | 'camelCaseOnly' | 'dashes' | 'dashesOnly' | ((originalClassName: string, generatedClassName: string, inputFile: string) => string);
}

export declare interface CSSOptions {
    /**
     * Using lightningcss is an experimental option to handle CSS modules,
     * assets and imports via Lightning CSS. It requires to install it as a
     * peer dependency. This is incompatible with the use of preprocessors.
     *
     * @default 'postcss'
     * @experimental
     */
    transformer?: 'postcss' | 'lightningcss';
    /**
     * https://github.com/css-modules/postcss-modules
     */
    modules?: CSSModulesOptions | false;
    preprocessorOptions?: Record<string, any>;
    postcss?: string | (PostCSS.ProcessOptions & {
        plugins?: PostCSS.AcceptedPlugin[];
    });
    /**
     * Enables css sourcemaps during dev
     * @default false
     * @experimental
     */
    devSourcemap?: boolean;
    /**
     * @experimental
     */
    lightningcss?: LightningCSSOptions;
}

export { CustomEventMap }

export { CustomPayload }

/**
 * Type helper to make it easier to use vite.config.ts
 * accepts a direct {@link UserConfig} object, or a function that returns it.
 * The function receives a {@link ConfigEnv} object that exposes two properties:
 * `command` (either `'build'` or `'serve'`), and `mode`.
 */
export declare function defineConfig(config: UserConfig): UserConfig;

export declare function defineConfig(config: Promise<UserConfig>): Promise<UserConfig>;

export declare function defineConfig(config: UserConfigFnObject): UserConfigFnObject;

export declare function defineConfig(config: UserConfigExport): UserConfigExport;

export declare interface DepOptimizationConfig {
    /**
     * Force optimize listed dependencies (must be resolvable import paths,
     * cannot be globs).
     */
    include?: string[];
    /**
     * Do not optimize these dependencies (must be resolvable import paths,
     * cannot be globs).
     */
    exclude?: string[];
    /**
     * Forces ESM interop when importing these dependencies. Some legacy
     * packages advertise themselves as ESM but use `require` internally
     * @experimental
     */
    needsInterop?: string[];
    /**
     * Options to pass to esbuild during the dep scanning and optimization
     *
     * Certain options are omitted since changing them would not be compatible
     * with Vite's dep optimization.
     *
     * - `external` is also omitted, use Vite's `optimizeDeps.exclude` option
     * - `plugins` are merged with Vite's dep plugin
     *
     * https://esbuild.github.io/api
     */
    esbuildOptions?: Omit<BuildOptions_2, 'bundle' | 'entryPoints' | 'external' | 'write' | 'watch' | 'outdir' | 'outfile' | 'outbase' | 'outExtension' | 'metafile'>;
    /**
     * List of file extensions that can be optimized. A corresponding esbuild
     * plugin must exist to handle the specific extension.
     *
     * By default, Vite can optimize `.mjs`, `.js`, `.ts`, and `.mts` files. This option
     * allows specifying additional extensions.
     *
     * @experimental
     */
    extensions?: string[];
    /**
     * Disables dependencies optimizations, true disables the optimizer during
     * build and dev. Pass 'build' or 'dev' to only disable the optimizer in
     * one of the modes. Deps optimization is enabled by default in dev only.
     * @default 'build'
     * @experimental
     */
    disabled?: boolean | 'build' | 'dev';
    /**
     * Automatic dependency discovery. When `noDiscovery` is true, only dependencies
     * listed in `include` will be optimized. The scanner isn't run for cold start
     * in this case. CJS-only dependencies must be present in `include` during dev.
     * @default false
     * @experimental
     */
    noDiscovery?: boolean;
}

export declare interface DepOptimizationMetadata {
    /**
     * The main hash is determined by user config and dependency lockfiles.
     * This is checked on server startup to avoid unnecessary re-bundles.
     */
    hash: string;
    /**
     * The browser hash is determined by the main hash plus additional dependencies
     * discovered at runtime. This is used to invalidate browser requests to
     * optimized deps.
     */
    browserHash: string;
    /**
     * Metadata for each already optimized dependency
     */
    optimized: Record<string, OptimizedDepInfo>;
    /**
     * Metadata for non-entry optimized chunks and dynamic imports
     */
    chunks: Record<string, OptimizedDepInfo>;
    /**
     * Metadata for each newly discovered dependency after processing
     */
    discovered: Record<string, OptimizedDepInfo>;
    /**
     * OptimizedDepInfo list
     */
    depInfoList: OptimizedDepInfo[];
}

export declare type DepOptimizationOptions = DepOptimizationConfig & {
    /**
     * By default, Vite will crawl your `index.html` to detect dependencies that
     * need to be pre-bundled. If `build.rollupOptions.input` is specified, Vite
     * will crawl those entry points instead.
     *
     * If neither of these fit your needs, you can specify custom entries using
     * this option - the value should be a fast-glob pattern or array of patterns
     * (https://github.com/mrmlnc/fast-glob#basic-syntax) that are relative from
     * vite project root. This will overwrite default entries inference.
     */
    entries?: string | string[];
    /**
     * Force dep pre-optimization regardless of whether deps have changed.
     * @experimental
     */
    force?: boolean;
};

export declare interface DepOptimizationProcessing {
    promise: Promise<void>;
    resolve: () => void;
}

export declare interface DepOptimizationResult {
    metadata: DepOptimizationMetadata;
    /**
     * When doing a re-run, if there are newly discovered dependencies
     * the page reload will be delayed until the next rerun so we need
     * to be able to discard the result
     */
    commit: () => Promise<void>;
    cancel: () => void;
}

export declare interface DepsOptimizer {
    metadata: DepOptimizationMetadata;
    scanProcessing?: Promise<void>;
    registerMissingImport: (id: string, resolved: string) => OptimizedDepInfo;
    run: () => void;
    isOptimizedDepFile: (id: string) => boolean;
    isOptimizedDepUrl: (url: string) => boolean;
    getOptimizedDepId: (depInfo: OptimizedDepInfo) => string;
    delayDepsOptimizerUntil: (id: string, done: () => Promise<any>) => void;
    registerWorkersSource: (id: string) => void;
    resetRegisteredIds: () => void;
    ensureFirstRun: () => void;
    close: () => Promise<void>;
    options: DepOptimizationOptions;
}

declare interface Drafts {
    /** Whether to enable CSS nesting. */
    nesting?: boolean,
    /** Whether to enable @custom-media rules. */
    customMedia?: boolean
}

export { ErrorPayload }

export declare interface ESBuildOptions extends EsbuildTransformOptions {
    include?: string | RegExp | string[] | RegExp[];
    exclude?: string | RegExp | string[] | RegExp[];
    jsxInject?: string;
    /**
     * This option is not respected. Use `build.minify` instead.
     */
    minify?: never;
}

export { EsbuildTransformOptions }

export declare type ESBuildTransformResult = Omit<TransformResult_3, 'map'> & {
    map: SourceMap;
};

export { esbuildVersion }

export declare interface ExperimentalOptions {
    /**
     * Append fake `&lang.(ext)` when queries are specified, to preserve the file extension for following plugins to process.
     *
     * @experimental
     * @default false
     */
    importGlobRestoreExtension?: boolean;
    /**
     * Allow finegrain control over assets and public files paths
     *
     * @experimental
     */
    renderBuiltUrl?: RenderBuiltAssetUrl;
    /**
     * Enables support of HMR partial accept via `import.meta.hot.acceptExports`.
     *
     * @experimental
     * @default false
     */
    hmrPartialAccept?: boolean;
    /**
     * Skips SSR transform to make it easier to use Vite with Node ESM loaders.
     * @warning Enabling this will break normal operation of Vite's SSR in development mode.
     *
     * @experimental
     * @default false
     */
    skipSsrTransform?: boolean;
}

export declare type ExportsData = {
    hasImports: boolean;
    exports: readonly string[];
    jsxLoader?: boolean;
};

declare const enum Features {
    Nesting = 1,
    NotSelectorList = 2,
    DirSelector = 4,
    LangSelectorList = 8,
    IsSelector = 16,
    TextDecorationThicknessPercent = 32,
    MediaIntervalSyntax = 64,
    MediaRangeSyntax = 128,
    CustomMediaQueries = 256,
    ClampFunction = 512,
    ColorFunction = 1024,
    OklabColors = 2048,
    LabColors = 4096,
    P3Colors = 8192,
    HexAlphaColors = 16384,
    SpaceSeparatedColorNotation = 32768,
    FontFamilySystemUi = 65536,
    DoublePositionGradients = 131072,
    VendorPrefixes = 262144,
    LogicalProperties = 524288,
    Selectors = 31,
    MediaQueries = 448,
    Colors = 64512,
}

export declare interface FileSystemServeOptions {
    /**
     * Strictly restrict file accessing outside of allowing paths.
     *
     * Set to `false` to disable the warning
     *
     * @default true
     */
    strict?: boolean;
    /**
     * Restrict accessing files outside the allowed directories.
     *
     * Accepts absolute path or a path relative to project root.
     * Will try to search up for workspace root by default.
     */
    allow?: string[];
    /**
     * Restrict accessing files that matches the patterns.
     *
     * This will have higher priority than `allow`.
     * picomatch patterns are supported.
     *
     * @default ['.env', '.env.*', '*.crt', '*.pem']
     */
    deny?: string[];
}

/**
 * Inlined to keep `@rollup/pluginutils` in devDependencies
 */
export declare type FilterPattern = ReadonlyArray<string | RegExp> | string | RegExp | null;

export declare function formatPostcssSourceMap(rawMap: ExistingRawSourceMap, file: string): Promise<ExistingRawSourceMap>;

export declare class FSWatcher extends EventEmitter implements fs.FSWatcher {
    options: WatchOptions

    /**
     * Constructs a new FSWatcher instance with optional WatchOptions parameter.
     */
    constructor(options?: WatchOptions)

    /**
     * Add files, directories, or glob patterns for tracking. Takes an array of strings or just one
     * string.
     */
    add(paths: string | ReadonlyArray<string>): this

    /**
     * Stop watching files, directories, or glob patterns. Takes an array of strings or just one
     * string.
     */
    unwatch(paths: string | ReadonlyArray<string>): this

    /**
     * Returns an object representing all the paths on the file system being watched by this
     * `FSWatcher` instance. The object's keys are all the directories (using absolute paths unless
     * the `cwd` option was used), and the values are arrays of the names of the items contained in
     * each directory.
     */
    getWatched(): {
        [directory: string]: string[]
    }

    /**
     * Removes all listeners from watched files.
     */
    close(): Promise<void>

    on(
    event: 'add' | 'addDir' | 'change',
    listener: (path: string, stats?: fs.Stats) => void,
    ): this

    on(
    event: 'all',
    listener: (
    eventName: 'add' | 'addDir' | 'change' | 'unlink' | 'unlinkDir',
    path: string,
    stats?: fs.Stats,
    ) => void,
    ): this

    /**
     * Error occurred
     */
    on(event: 'error', listener: (error: Error) => void): this

    /**
     * Exposes the native Node `fs.FSWatcher events`
     */
    on(
    event: 'raw',
    listener: (eventName: string, path: string, details: any) => void,
    ): this

    /**
     * Fires when the initial scan is complete
     */
    on(event: 'ready', listener: () => void): this

    on(event: 'unlink' | 'unlinkDir', listener: (path: string) => void): this

    on(event: string, listener: (...args: any[]) => void): this
}

export { FullReloadPayload }

export { GeneralImportGlobOptions }

export declare function getDepOptimizationConfig(config: ResolvedConfig, ssr: boolean): DepOptimizationConfig;

export declare interface HmrContext {
    file: string;
    timestamp: number;
    modules: Array<ModuleNode>;
    read: () => string | Promise<string>;
    server: ViteDevServer;
}

export declare interface HmrOptions {
    protocol?: string;
    host?: string;
    port?: number;
    clientPort?: number;
    path?: string;
    timeout?: number;
    overlay?: boolean;
    server?: Server;
}

export { HMRPayload }

export declare type HookHandler<T> = T extends ObjectHook<infer H> ? H : T;

export declare interface HtmlTagDescriptor {
    tag: string;
    attrs?: Record<string, string | boolean | undefined>;
    children?: string | HtmlTagDescriptor[];
    /**
     * default: 'head-prepend'
     */
    injectTo?: 'head' | 'body' | 'head-prepend' | 'body-prepend';
}

export declare namespace HttpProxy {
    export type ProxyTarget = ProxyTargetUrl | ProxyTargetDetailed

    export type ProxyTargetUrl = string | Partial<url.Url>

    export interface ProxyTargetDetailed {
        host: string
        port: number
        protocol?: string | undefined
        hostname?: string | undefined
        socketPath?: string | undefined
        key?: string | undefined
        passphrase?: string | undefined
        pfx?: Buffer | string | undefined
        cert?: string | undefined
        ca?: string | undefined
        ciphers?: string | undefined
        secureProtocol?: string | undefined
    }

    export type ErrorCallback = (
    err: Error,
    req: http.IncomingMessage,
    res: http.ServerResponse,
    target?: ProxyTargetUrl,
    ) => void

    export class Server extends events.EventEmitter {
        /**
         * Creates the proxy server with specified options.
         * @param options - Config object passed to the proxy
         */
        constructor(options?: ServerOptions)

        /**
         * Used for proxying regular HTTP(S) requests
         * @param req - Client request.
         * @param res - Client response.
         * @param options - Additional options.
         */
        web(
        req: http.IncomingMessage,
        res: http.ServerResponse,
        options?: ServerOptions,
        callback?: ErrorCallback,
        ): void

        /**
         * Used for proxying regular HTTP(S) requests
         * @param req - Client request.
         * @param socket - Client socket.
         * @param head - Client head.
         * @param options - Additional options.
         */
        ws(
        req: http.IncomingMessage,
        socket: unknown,
        head: unknown,
        options?: ServerOptions,
        callback?: ErrorCallback,
        ): void

        /**
         * A function that wraps the object in a webserver, for your convenience
         * @param port - Port to listen on
         */
        listen(port: number): Server

        /**
         * A function that closes the inner webserver and stops listening on given port
         */
        close(callback?: () => void): void

        /**
         * Creates the proxy server with specified options.
         * @param options - Config object passed to the proxy
         * @returns Proxy object with handlers for `ws` and `web` requests
         */
        static createProxyServer(options?: ServerOptions): Server

        /**
         * Creates the proxy server with specified options.
         * @param options - Config object passed to the proxy
         * @returns Proxy object with handlers for `ws` and `web` requests
         */
        static createServer(options?: ServerOptions): Server

        /**
         * Creates the proxy server with specified options.
         * @param options - Config object passed to the proxy
         * @returns Proxy object with handlers for `ws` and `web` requests
         */
        static createProxy(options?: ServerOptions): Server

        addListener(event: string, listener: () => void): this
        on(event: string, listener: () => void): this
        on(event: 'error', listener: ErrorCallback): this
        on(
        event: 'start',
        listener: (
        req: http.IncomingMessage,
        res: http.ServerResponse,
        target: ProxyTargetUrl,
        ) => void,
        ): this
        on(
        event: 'proxyReq',
        listener: (
        proxyReq: http.ClientRequest,
        req: http.IncomingMessage,
        res: http.ServerResponse,
        options: ServerOptions,
        ) => void,
        ): this
        on(
        event: 'proxyRes',
        listener: (
        proxyRes: http.IncomingMessage,
        req: http.IncomingMessage,
        res: http.ServerResponse,
        ) => void,
        ): this
        on(
        event: 'proxyReqWs',
        listener: (
        proxyReq: http.ClientRequest,
        req: http.IncomingMessage,
        socket: net.Socket,
        options: ServerOptions,
        head: any,
        ) => void,
        ): this
        on(
        event: 'econnreset',
        listener: (
        err: Error,
        req: http.IncomingMessage,
        res: http.ServerResponse,
        target: ProxyTargetUrl,
        ) => void,
        ): this
        on(
        event: 'end',
        listener: (
        req: http.IncomingMessage,
        res: http.ServerResponse,
        proxyRes: http.IncomingMessage,
        ) => void,
        ): this
        on(
        event: 'close',
        listener: (
        proxyRes: http.IncomingMessage,
        proxySocket: net.Socket,
        proxyHead: any,
        ) => void,
        ): this

        once(event: string, listener: () => void): this
        removeListener(event: string, listener: () => void): this
        removeAllListeners(event?: string): this
        getMaxListeners(): number
        setMaxListeners(n: number): this
        listeners(event: string): Array<() => void>
        emit(event: string, ...args: any[]): boolean
        listenerCount(type: string): number
    }

    export interface ServerOptions {
        /** URL string to be parsed with the url module. */
        target?: ProxyTarget | undefined
        /** URL string to be parsed with the url module. */
        forward?: ProxyTargetUrl | undefined
        /** Object to be passed to http(s).request. */
        agent?: any
        /** Object to be passed to https.createServer(). */
        ssl?: any
        /** If you want to proxy websockets. */
        ws?: boolean | undefined
        /** Adds x- forward headers. */
        xfwd?: boolean | undefined
        /** Verify SSL certificate. */
        secure?: boolean | undefined
        /** Explicitly specify if we are proxying to another proxy. */
        toProxy?: boolean | undefined
        /** Specify whether you want to prepend the target's path to the proxy path. */
        prependPath?: boolean | undefined
        /** Specify whether you want to ignore the proxy path of the incoming request. */
        ignorePath?: boolean | undefined
        /** Local interface string to bind for outgoing connections. */
        localAddress?: string | undefined
        /** Changes the origin of the host header to the target URL. */
        changeOrigin?: boolean | undefined
        /** specify whether you want to keep letter case of response header key */
        preserveHeaderKeyCase?: boolean | undefined
        /** Basic authentication i.e. 'user:password' to compute an Authorization header. */
        auth?: string | undefined
        /** Rewrites the location hostname on (301 / 302 / 307 / 308) redirects, Default: null. */
        hostRewrite?: string | undefined
        /** Rewrites the location host/ port on (301 / 302 / 307 / 308) redirects based on requested host/ port.Default: false. */
        autoRewrite?: boolean | undefined
        /** Rewrites the location protocol on (301 / 302 / 307 / 308) redirects to 'http' or 'https'.Default: null. */
        protocolRewrite?: string | undefined
        /** rewrites domain of set-cookie headers. */
        cookieDomainRewrite?:
        | false
        | string
        | { [oldDomain: string]: string }
        | undefined
        /** rewrites path of set-cookie headers. Default: false */
        cookiePathRewrite?:
        | false
        | string
        | { [oldPath: string]: string }
        | undefined
        /** object with extra headers to be added to target requests. */
        headers?: { [header: string]: string } | undefined
        /** Timeout (in milliseconds) when proxy receives no response from target. Default: 120000 (2 minutes) */
        proxyTimeout?: number | undefined
        /** Timeout (in milliseconds) for incoming requests */
        timeout?: number | undefined
        /** Specify whether you want to follow redirects. Default: false */
        followRedirects?: boolean | undefined
        /** If set to true, none of the webOutgoing passes are called and it's your responsibility to appropriately return the response by listening and acting on the proxyRes event */
        selfHandleResponse?: boolean | undefined
        /** Buffer */
        buffer?: stream.Stream | undefined
    }
}

export { ImportGlobEagerFunction }

export { ImportGlobFunction }

export { ImportGlobOptions }

export declare type IndexHtmlTransform = IndexHtmlTransformHook | {
    order?: 'pre' | 'post' | null;
    /**
     * @deprecated renamed to `order`
     */
    enforce?: 'pre' | 'post';
    /**
     * @deprecated renamed to `handler`
     */
    transform: IndexHtmlTransformHook;
} | {
    order?: 'pre' | 'post' | null;
    /**
     * @deprecated renamed to `order`
     */
    enforce?: 'pre' | 'post';
    handler: IndexHtmlTransformHook;
};

export declare interface IndexHtmlTransformContext {
    /**
     * public path when served
     */
    path: string;
    /**
     * filename on disk
     */
    filename: string;
    server?: ViteDevServer;
    bundle?: OutputBundle;
    chunk?: OutputChunk;
    originalUrl?: string;
}

export declare type IndexHtmlTransformHook = (this: void, html: string, ctx: IndexHtmlTransformContext) => IndexHtmlTransformResult | void | Promise<IndexHtmlTransformResult | void>;

export declare type IndexHtmlTransformResult = string | HtmlTagDescriptor[] | {
    html: string;
    tags: HtmlTagDescriptor[];
};

export { InferCustomEventPayload }

export declare interface InlineConfig extends UserConfig {
    configFile?: string | false;
    envFile?: false;
}

export declare interface InternalResolveOptions extends Required<ResolveOptions> {
    root: string;
    isBuild: boolean;
    isProduction: boolean;
    ssrConfig?: SSROptions;
    packageCache?: PackageCache;
    /**
     * src code mode also attempts the following:
     * - resolving /xxx as URLs
     * - resolving bare imports from optimized deps
     */
    asSrc?: boolean;
    tryIndex?: boolean;
    tryPrefix?: string;
    preferRelative?: boolean;
    isRequire?: boolean;
    isFromTsImporter?: boolean;
    tryEsmOnly?: boolean;
    scan?: boolean;
    ssrOptimizeCheck?: boolean;
    getDepsOptimizer?: (ssr: boolean) => DepsOptimizer | undefined;
    shouldExternalize?: (id: string, importer?: string) => boolean | undefined;
    /* Excluded from this release type: idOnly */
}

export { InvalidatePayload }

export declare const isCSSRequest: (request: string) => boolean;

export declare function isDepsOptimizerEnabled(config: ResolvedConfig, ssr: boolean): boolean;

export declare function isFileLoadingAllowed(server: ViteDevServer, filePath: string): boolean;

/**
 * Check if the url is allowed to be served, via the `server.fs` config.
 * @deprecated Use the `isFileLoadingAllowed` function instead.
 */
export declare function isFileServingAllowed(url: string, server: ViteDevServer): boolean;

export declare interface JsonOptions {
    /**
     * Generate a named export for every property of the JSON object
     * @default true
     */
    namedExports?: boolean;
    /**
     * Generate performant output as JSON.parse("stringified").
     * Enabling this will disable namedExports.
     * @default false
     */
    stringify?: boolean;
}

export { KnownAsTypeMap }

export declare interface LegacyOptions {
    /**
     * Revert vite build --ssr to the v2.9 strategy. Use CJS SSR build and v2.9 externalization heuristics
     *
     * @experimental
     * @deprecated
     * @default false
     */
    buildSsrCjsExternalHeuristics?: boolean;
    /**
     * In Vite 6.0.8 / 5.4.11 / 4.5.5 and below, WebSocket server was able to connect from any web pages. However,
     * that could be exploited by a malicious web page.
     *
     * In Vite 6.0.9+ / 5.4.12+ / 4.5.6+ the WebSocket server now requires a token to connect from a web page.
     * But this may break some plugins and frameworks that connects to the WebSocket server
     * on their own. Enabling this option will make Vite skip the token check.
     *
     * **We do not recommend enabling this option unless you are sure that you are fine with
     * that security weakness.**
     */
    skipWebSocketTokenCheck?: boolean;
}

export declare type LibraryFormats = 'es' | 'cjs' | 'umd' | 'iife';

export declare interface LibraryOptions {
    /**
     * Path of library entry
     */
    entry: InputOption;
    /**
     * The name of the exposed global variable. Required when the `formats` option includes
     * `umd` or `iife`
     */
    name?: string;
    /**
     * Output bundle formats
     * @default ['es', 'umd']
     */
    formats?: LibraryFormats[];
    /**
     * The name of the package file output. The default file name is the name option
     * of the project package.json. It can also be defined as a function taking the
     * format as an argument.
     */
    fileName?: string | ((format: ModuleFormat, entryName: string) => string);
}

/**
 * Options are spread, so you can also use options that are not typed here like
 * visitor (not exposed because it would impact too much the bundle size)
 */
export declare type LightningCSSOptions = {
    targets?: Targets
    include?: Features
    exclude?: Features
    drafts?: Drafts
    nonStandard?: NonStandard
    pseudoClasses?: PseudoClasses
    unusedSymbols?: string[]
    cssModules?: CSSModulesConfig
}

export declare function loadConfigFromFile(configEnv: ConfigEnv, configFile?: string, configRoot?: string, logLevel?: LogLevel): Promise<{
    path: string;
    config: UserConfig;
    dependencies: string[];
} | null>;

export declare function loadEnv(mode: string, envDir: string, prefixes?: string | string[]): Record<string, string>;

export declare interface LogErrorOptions extends LogOptions {
    error?: Error | RollupError | null;
}

export declare interface Logger {
    info(msg: string, options?: LogOptions): void;
    warn(msg: string, options?: LogOptions): void;
    warnOnce(msg: string, options?: LogOptions): void;
    error(msg: string, options?: LogErrorOptions): void;
    clearScreen(type: LogType): void;
    hasErrorLogged(error: Error | RollupError): boolean;
    hasWarned: boolean;
}

export declare interface LoggerOptions {
    prefix?: string;
    allowClearScreen?: boolean;
    customLogger?: Logger;
}

export declare type LogLevel = LogType | 'silent';

export declare interface LogOptions {
    clear?: boolean;
    timestamp?: boolean;
}

export declare type LogType = 'error' | 'warn' | 'info';

export declare type Manifest = Record<string, ManifestChunk>;

export declare interface ManifestChunk {
    src?: string;
    file: string;
    css?: string[];
    assets?: string[];
    isEntry?: boolean;
    isDynamicEntry?: boolean;
    imports?: string[];
    dynamicImports?: string[];
}

export declare type MapToFunction<T> = T extends Function ? T : never

export declare type Matcher = AnymatchPattern | AnymatchPattern[]

export declare function mergeAlias(a?: AliasOptions, b?: AliasOptions): AliasOptions | undefined;

export declare function mergeConfig<D extends Record<string, any>, O extends Record<string, any>>(defaults: D extends Function ? never : D, overrides: O extends Function ? never : O, isRoot?: boolean): Record<string, any>;

export declare class ModuleGraph {
    private resolveId;
    urlToModuleMap: Map<string, ModuleNode>;
    idToModuleMap: Map<string, ModuleNode>;
    fileToModulesMap: Map<string, Set<ModuleNode>>;
    safeModulesPath: Set<string>;
    /* Excluded from this release type: _unresolvedUrlToModuleMap */
    /* Excluded from this release type: _ssrUnresolvedUrlToModuleMap */
    constructor(resolveId: (url: string, ssr: boolean) => Promise<PartialResolvedId | null>);
    getModuleByUrl(rawUrl: string, ssr?: boolean): Promise<ModuleNode | undefined>;
    getModuleById(id: string): ModuleNode | undefined;
    getModulesByFile(file: string): Set<ModuleNode> | undefined;
    onFileChange(file: string): void;
    invalidateModule(mod: ModuleNode, seen?: Set<ModuleNode>, timestamp?: number, isHmr?: boolean, hmrBoundaries?: ModuleNode[]): void;
    invalidateAll(): void;
    /**
     * Update the module graph based on a module's updated imports information
     * If there are dependencies that no longer have any importers, they are
     * returned as a Set.
     */
    updateModuleInfo(mod: ModuleNode, importedModules: Set<string | ModuleNode>, importedBindings: Map<string, Set<string>> | null, acceptedModules: Set<string | ModuleNode>, acceptedExports: Set<string> | null, isSelfAccepting: boolean, ssr?: boolean): Promise<Set<ModuleNode> | undefined>;
    ensureEntryFromUrl(rawUrl: string, ssr?: boolean, setIsSelfAccepting?: boolean): Promise<ModuleNode>;
    /* Excluded from this release type: _ensureEntryFromUrl */
    createFileOnlyEntry(file: string): ModuleNode;
    resolveUrl(url: string, ssr?: boolean): Promise<ResolvedUrl>;
    /* Excluded from this release type: _getUnresolvedUrlToModule */
    /* Excluded from this release type: _setUnresolvedUrlToModule */
    /* Excluded from this release type: _resolveUrl */
}

export declare class ModuleNode {
    /**
     * Public served url path, starts with /
     */
    url: string;
    /**
     * Resolved file system path + query
     */
    id: string | null;
    file: string | null;
    type: 'js' | 'css';
    info?: ModuleInfo;
    meta?: Record<string, any>;
    importers: Set<ModuleNode>;
    clientImportedModules: Set<ModuleNode>;
    ssrImportedModules: Set<ModuleNode>;
    acceptedHmrDeps: Set<ModuleNode>;
    acceptedHmrExports: Set<string> | null;
    importedBindings: Map<string, Set<string>> | null;
    isSelfAccepting?: boolean;
    transformResult: TransformResult | null;
    ssrTransformResult: TransformResult | null;
    ssrModule: Record<string, any> | null;
    ssrError: Error | null;
    lastHMRTimestamp: number;
    lastInvalidationTimestamp: number;
    /**
     * @param setIsSelfAccepting - set `false` to set `isSelfAccepting` later. e.g. #7870
     */
    constructor(url: string, setIsSelfAccepting?: boolean);
    get importedModules(): Set<ModuleNode>;
}

export declare interface ModulePreloadOptions {
    /**
     * Whether to inject a module preload polyfill.
     * Note: does not apply to library mode.
     * @default true
     */
    polyfill?: boolean;
    /**
     * Resolve the list of dependencies to preload for a given dynamic import
     * @experimental
     */
    resolveDependencies?: ResolveModulePreloadDependenciesFn;
}

declare interface NonStandard {
    /** Whether to enable the non-standard >>> and /deep/ selector combinators used by Angular and Vue. */
    deepSelectorCombinator?: boolean
}

export declare function normalizePath(id: string): string;

export declare interface OptimizedDepInfo {
    id: string;
    file: string;
    src?: string;
    needsInterop?: boolean;
    browserHash?: string;
    fileHash?: string;
    /**
     * During optimization, ids can still be resolved to their final location
     * but the bundles may not yet be saved to disk
     */
    processing?: Promise<void>;
    /**
     * ExportData cache, discovered deps will parse the src entry to get exports
     * data used both to define if interop is needed and when pre-bundling
     */
    exportsData?: Promise<ExportsData>;
}

/**
 * Scan and optimize dependencies within a project.
 * Used by Vite CLI when running `vite optimize`.
 */
export declare function optimizeDeps(config: ResolvedConfig, force?: boolean | undefined, asCommand?: boolean): Promise<DepOptimizationMetadata>;

/** Cache for package.json resolution and package.json contents */
export declare type PackageCache = Map<string, PackageData>;

export declare interface PackageData {
    dir: string;
    hasSideEffects: (id: string) => boolean | 'no-treeshake';
    webResolvedImports: Record<string, string | undefined>;
    nodeResolvedImports: Record<string, string | undefined>;
    setResolvedCache: (key: string, entry: string, targetWeb: boolean) => void;
    getResolvedCache: (key: string, targetWeb: boolean) => string | undefined;
    data: {
        [field: string]: any;
        name: string;
        type: string;
        version: string;
        main: string;
        module: string;
        browser: string | Record<string, string | false>;
        exports: string | Record<string, any> | string[];
        imports: Record<string, any>;
        dependencies: Record<string, string>;
    };
}

/**
 * Vite plugins extends the Rollup plugin interface with a few extra
 * vite-specific options. A valid vite plugin is also a valid Rollup plugin.
 * On the contrary, a Rollup plugin may or may NOT be a valid vite universal
 * plugin, since some Rollup features do not make sense in an unbundled
 * dev server context. That said, as long as a rollup plugin doesn't have strong
 * coupling between its bundle phase and output phase hooks then it should
 * just work (that means, most of them).
 *
 * By default, the plugins are run during both serve and build. When a plugin
 * is applied during serve, it will only run **non output plugin hooks** (see
 * rollup type definition of {@link rollup#PluginHooks}). You can think of the
 * dev server as only running `const bundle = rollup.rollup()` but never calling
 * `bundle.generate()`.
 *
 * A plugin that expects to have different behavior depending on serve/build can
 * export a factory function that receives the command being run via options.
 *
 * If a plugin should be applied only for server or build, a function format
 * config file can be used to conditional determine the plugins to use.
 */
declare interface Plugin_2 extends Plugin_3 {
    /**
     * Enforce plugin invocation tier similar to webpack loaders.
     *
     * Plugin invocation order:
     * - alias resolution
     * - `enforce: 'pre'` plugins
     * - vite core plugins
     * - normal plugins
     * - vite build plugins
     * - `enforce: 'post'` plugins
     * - vite build post plugins
     */
    enforce?: 'pre' | 'post';
    /**
     * Apply the plugin only for serve or build, or on certain conditions.
     */
    apply?: 'serve' | 'build' | ((this: void, config: UserConfig, env: ConfigEnv) => boolean);
    /**
     * Modify vite config before it's resolved. The hook can either mutate the
     * passed-in config directly, or return a partial config object that will be
     * deeply merged into existing config.
     *
     * Note: User plugins are resolved before running this hook so injecting other
     * plugins inside  the `config` hook will have no effect.
     */
    config?: ObjectHook<(this: void, config: UserConfig, env: ConfigEnv) => UserConfig | null | void | Promise<UserConfig | null | void>>;
    /**
     * Use this hook to read and store the final resolved vite config.
     */
    configResolved?: ObjectHook<(this: void, config: ResolvedConfig) => void | Promise<void>>;
    /**
     * Configure the vite server. The hook receives the {@link ViteDevServer}
     * instance. This can also be used to store a reference to the server
     * for use in other hooks.
     *
     * The hooks will be called before internal middlewares are applied. A hook
     * can return a post hook that will be called after internal middlewares
     * are applied. Hook can be async functions and will be called in series.
     */
    configureServer?: ObjectHook<ServerHook>;
    /**
     * Configure the preview server. The hook receives the {@link PreviewServerForHook}
     * instance. This can also be used to store a reference to the server
     * for use in other hooks.
     *
     * The hooks are called before other middlewares are applied. A hook can
     * return a post hook that will be called after other middlewares are
     * applied. Hooks can be async functions and will be called in series.
     */
    configurePreviewServer?: ObjectHook<PreviewServerHook>;
    /**
     * Transform index.html.
     * The hook receives the following arguments:
     *
     * - html: string
     * - ctx?: vite.ServerContext (only present during serve)
     * - bundle?: rollup.OutputBundle (only present during build)
     *
     * It can either return a transformed string, or a list of html tag
     * descriptors that will be injected into the `<head>` or `<body>`.
     *
     * By default the transform is applied **after** vite's internal html
     * transform. If you need to apply the transform before vite, use an object:
     * `{ order: 'pre', handler: hook }`
     */
    transformIndexHtml?: IndexHtmlTransform;
    /**
     * Perform custom handling of HMR updates.
     * The handler receives a context containing changed filename, timestamp, a
     * list of modules affected by the file change, and the dev server instance.
     *
     * - The hook can return a filtered list of modules to narrow down the update.
     *   e.g. for a Vue SFC, we can narrow down the part to update by comparing
     *   the descriptors.
     *
     * - The hook can also return an empty array and then perform custom updates
     *   by sending a custom hmr payload via server.ws.send().
     *
     * - If the hook doesn't return a value, the hmr update will be performed as
     *   normal.
     */
    handleHotUpdate?: ObjectHook<(this: void, ctx: HmrContext) => Array<ModuleNode> | void | Promise<Array<ModuleNode> | void>>;
    /**
     * extend hooks with ssr flag
     */
    resolveId?: ObjectHook<(this: PluginContext, source: string, importer: string | undefined, options: {
        assertions: Record<string, string>;
        custom?: CustomPluginOptions;
        ssr?: boolean;
        /* Excluded from this release type: scan */
        isEntry: boolean;
    }) => Promise<ResolveIdResult> | ResolveIdResult>;
    load?: ObjectHook<(this: PluginContext, id: string, options?: {
        ssr?: boolean;
    }) => Promise<LoadResult> | LoadResult>;
    transform?: ObjectHook<(this: TransformPluginContext, code: string, id: string, options?: {
        ssr?: boolean;
    }) => Promise<TransformResult_2> | TransformResult_2>;
}
export { Plugin_2 as Plugin }

export declare interface PluginContainer {
    options: InputOptions;
    getModuleInfo(id: string): ModuleInfo | null;
    buildStart(options: InputOptions): Promise<void>;
    resolveId(id: string, importer?: string, options?: {
        assertions?: Record<string, string>;
        custom?: CustomPluginOptions;
        skip?: Set<Plugin_2>;
        ssr?: boolean;
        /* Excluded from this release type: scan */
        isEntry?: boolean;
    }): Promise<PartialResolvedId | null>;
    transform(code: string, id: string, options?: {
        inMap?: SourceDescription['map'];
        ssr?: boolean;
    }): Promise<{
        code: string;
        map: SourceMap | null;
    }>;
    load(id: string, options?: {
        ssr?: boolean;
    }): Promise<LoadResult | null>;
    close(): Promise<void>;
}

export declare interface PluginHookUtils {
    getSortedPlugins: (hookName: keyof Plugin_2) => Plugin_2[];
    getSortedPluginHooks: <K extends keyof Plugin_2>(hookName: K) => NonNullable<HookHandler<Plugin_2[K]>>[];
}

export declare type PluginOption = Plugin_2 | false | null | undefined | PluginOption[] | Promise<Plugin_2 | false | null | undefined | PluginOption[]>;

/**
 * @experimental
 */
export declare function preprocessCSS(code: string, filename: string, config: ResolvedConfig): Promise<PreprocessCSSResult>;

export declare interface PreprocessCSSResult {
    code: string;
    map?: SourceMapInput;
    modules?: Record<string, string>;
    deps?: Set<string>;
}

/**
 * Starts the Vite server in preview mode, to simulate a production deployment
 */
export declare function preview(inlineConfig?: InlineConfig): Promise<PreviewServer>;

export declare interface PreviewOptions extends CommonServerOptions {
}

export declare interface PreviewServer extends PreviewServerForHook {
    resolvedUrls: ResolvedServerUrls;
}

export declare interface PreviewServerForHook {
    /**
     * The resolved vite config object
     */
    config: ResolvedConfig;
    /**
     * A connect app instance.
     * - Can be used to attach custom middlewares to the preview server.
     * - Can also be used as the handler function of a custom http server
     *   or as a middleware in any connect-style Node.js frameworks
     *
     * https://github.com/senchalabs/connect#use-middleware
     */
    middlewares: Connect.Server;
    /**
     * native Node http server instance
     */
    httpServer: http.Server;
    /**
     * The resolved urls Vite prints on the CLI
     */
    resolvedUrls: ResolvedServerUrls | null;
    /**
     * Print server urls
     */
    printUrls(): void;
}

export declare type PreviewServerHook = (this: void, server: PreviewServerForHook) => (() => void) | void | Promise<(() => void) | void>;

export declare interface ProxyOptions extends HttpProxy.ServerOptions {
    /**
     * rewrite path
     */
    rewrite?: (path: string) => string;
    /**
     * configure the proxy server (e.g. listen to events)
     */
    configure?: (proxy: HttpProxy.Server, options: ProxyOptions) => void;
    /**
     * webpack-dev-server style bypass function
     */
    bypass?: (req: http.IncomingMessage, res: http.ServerResponse, options: ProxyOptions) => void | null | undefined | false | string;
}

export { PrunePayload }

declare interface PseudoClasses {
    hover?: string,
    active?: string,
    focus?: string,
    focusVisible?: string,
    focusWithin?: string
}

export declare type RenderBuiltAssetUrl = (filename: string, type: {
    type: 'asset' | 'public';
    hostId: string;
    hostType: 'js' | 'css' | 'html';
    ssr: boolean;
}) => string | {
    relative?: boolean;
    runtime?: string;
} | undefined;

/**
 * Resolve base url. Note that some users use Vite to build for non-web targets like
 * electron or expects to deploy
 */
export declare function resolveBaseUrl(base: string | undefined, isBuild: boolean, logger: Logger): string;

export declare function resolveConfig(inlineConfig: InlineConfig, command: 'build' | 'serve', defaultMode?: string, defaultNodeEnv?: string): Promise<ResolvedConfig>;

export declare interface ResolvedBuildOptions extends Required<Omit<BuildOptions, 'polyfillModulePreload'>> {
    modulePreload: false | ResolvedModulePreloadOptions;
}

export declare type ResolvedConfig = Readonly<Omit<UserConfig, 'plugins' | 'css' | 'assetsInclude' | 'optimizeDeps' | 'worker' | 'build'> & {
    configFile: string | undefined;
    configFileDependencies: string[];
    inlineConfig: InlineConfig;
    root: string;
    base: string;
    /* Excluded from this release type: rawBase */
    publicDir: string;
    cacheDir: string;
    command: 'build' | 'serve';
    mode: string;
    isWorker: boolean;
    /* Excluded from this release type: mainConfig */
    isProduction: boolean;
    envDir: string;
    env: Record<string, any>;
    resolve: Required<ResolveOptions> & {
        alias: Alias[];
    };
    plugins: readonly Plugin_2[];
    css: ResolvedCSSOptions | undefined;
    esbuild: ESBuildOptions | false;
    server: ResolvedServerOptions;
    build: ResolvedBuildOptions;
    preview: ResolvedPreviewOptions;
    ssr: ResolvedSSROptions;
    assetsInclude: (file: string) => boolean;
    logger: Logger;
    createResolver: (options?: Partial<InternalResolveOptions>) => ResolveFn;
    optimizeDeps: DepOptimizationOptions;
    /* Excluded from this release type: packageCache */
    worker: ResolveWorkerOptions;
    appType: AppType;
    experimental: ExperimentalOptions;
    /**
     * The token to connect to the WebSocket server from browsers.
     *
     * We recommend using `import.meta.hot` rather than connecting
     * to the WebSocket server directly.
     * If you have a usecase that requires connecting to the WebSocket
     * server, please create an issue so that we can discuss.
     *
     * @deprecated use `import.meta.hot`
     */
    webSocketToken: string;
    /* Excluded from this release type: additionalAllowedHosts */
} & PluginHookUtils>;

export declare type ResolvedCSSOptions = Omit<CSSOptions, 'lightningcss'> & {
    lightningcss?: LightningCSSOptions & {
        targets: LightningCSSOptions['targets'];
    };
};

export declare interface ResolvedModulePreloadOptions {
    polyfill: boolean;
    resolveDependencies?: ResolveModulePreloadDependenciesFn;
}

export declare interface ResolvedPreviewOptions extends PreviewOptions {
}

export declare interface ResolvedServerOptions extends ServerOptions {
    fs: Required<FileSystemServeOptions>;
    middlewareMode: boolean;
    sourcemapIgnoreList: Exclude<ServerOptions['sourcemapIgnoreList'], false | undefined>;
}

export declare interface ResolvedServerUrls {
    local: string[];
    network: string[];
}

export declare interface ResolvedSSROptions extends SSROptions {
    target: SSRTarget;
    format: SSRFormat;
    optimizeDeps: SsrDepOptimizationOptions;
}

export declare type ResolvedUrl = [
url: string,
resolvedId: string,
meta: object | null | undefined
];

export declare function resolveEnvPrefix({ envPrefix, }: UserConfig): string[];

export declare type ResolveFn = (id: string, importer?: string, aliasOnly?: boolean, ssr?: boolean) => Promise<string | undefined>;

export declare type ResolveModulePreloadDependenciesFn = (filename: string, deps: string[], context: {
    hostId: string;
    hostType: 'html' | 'js';
}) => string[];

export declare interface ResolveOptions {
    /**
     * @default ['module', 'jsnext:main', 'jsnext']
     */
    mainFields?: string[];
    /**
     * @deprecated In future, `mainFields` should be used instead.
     * @default true
     */
    browserField?: boolean;
    conditions?: string[];
    /**
     * @default ['.mjs', '.js', '.mts', '.ts', '.jsx', '.tsx', '.json']
     */
    extensions?: string[];
    dedupe?: string[];
    /**
     * @default false
     */
    preserveSymlinks?: boolean;
}

export declare function resolvePackageData(pkgName: string, basedir: string, preserveSymlinks?: boolean, packageCache?: PackageCache): PackageData | null;

export declare function resolvePackageEntry(id: string, { dir, data, setResolvedCache, getResolvedCache }: PackageData, targetWeb: boolean, options: InternalResolveOptions): string | undefined;

export declare type ResolverFunction = MapToFunction<PluginHooks['resolveId']>

export declare interface ResolverObject {
    buildStart?: PluginHooks['buildStart']
    resolveId: ResolverFunction
}

export declare interface ResolveWorkerOptions extends PluginHookUtils {
    format: 'es' | 'iife';
    plugins: Plugin_2[];
    rollupOptions: RollupOptions;
}

export { Rollup }

/**
 * https://github.com/rollup/plugins/blob/master/packages/commonjs/types/index.d.ts
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file at
 * https://github.com/rollup/plugins/blob/master/LICENSE
 */
export declare interface RollupCommonJSOptions {
    /**
     * A minimatch pattern, or array of patterns, which specifies the files in
     * the build the plugin should operate on. By default, all files with
     * extension `".cjs"` or those in `extensions` are included, but you can
     * narrow this list by only including specific files. These files will be
     * analyzed and transpiled if either the analysis does not find ES module
     * specific statements or `transformMixedEsModules` is `true`.
     * @default undefined
     */
    include?: string | RegExp | readonly (string | RegExp)[]
    /**
     * A minimatch pattern, or array of patterns, which specifies the files in
     * the build the plugin should _ignore_. By default, all files with
     * extensions other than those in `extensions` or `".cjs"` are ignored, but you
     * can exclude additional files. See also the `include` option.
     * @default undefined
     */
    exclude?: string | RegExp | readonly (string | RegExp)[]
    /**
     * For extensionless imports, search for extensions other than .js in the
     * order specified. Note that you need to make sure that non-JavaScript files
     * are transpiled by another plugin first.
     * @default [ '.js' ]
     */
    extensions?: ReadonlyArray<string>
    /**
     * If true then uses of `global` won't be dealt with by this plugin
     * @default false
     */
    ignoreGlobal?: boolean
    /**
     * If false, skips source map generation for CommonJS modules. This will
     * improve performance.
     * @default true
     */
    sourceMap?: boolean
    /**
     * Some `require` calls cannot be resolved statically to be translated to
     * imports.
     * When this option is set to `false`, the generated code will either
     * directly throw an error when such a call is encountered or, when
     * `dynamicRequireTargets` is used, when such a call cannot be resolved with a
     * configured dynamic require target.
     * Setting this option to `true` will instead leave the `require` call in the
     * code or use it as a fallback for `dynamicRequireTargets`.
     * @default false
     */
    ignoreDynamicRequires?: boolean
    /**
     * Instructs the plugin whether to enable mixed module transformations. This
     * is useful in scenarios with modules that contain a mix of ES `import`
     * statements and CommonJS `require` expressions. Set to `true` if `require`
     * calls should be transformed to imports in mixed modules, or `false` if the
     * `require` expressions should survive the transformation. The latter can be
     * important if the code contains environment detection, or you are coding
     * for an environment with special treatment for `require` calls such as
     * ElectronJS. See also the `ignore` option.
     * @default false
     */
    transformMixedEsModules?: boolean
    /**
     * By default, this plugin will try to hoist `require` statements as imports
     * to the top of each file. While this works well for many code bases and
     * allows for very efficient ESM output, it does not perfectly capture
     * CommonJS semantics as the order of side effects like log statements may
     * change. But it is especially problematic when there are circular `require`
     * calls between CommonJS modules as those often rely on the lazy execution of
     * nested `require` calls.
     *
     * Setting this option to `true` will wrap all CommonJS files in functions
     * which are executed when they are required for the first time, preserving
     * NodeJS semantics. Note that this can have an impact on the size and
     * performance of the generated code.
     *
     * The default value of `"auto"` will only wrap CommonJS files when they are
     * part of a CommonJS dependency cycle, e.g. an index file that is required by
     * many of its dependencies. All other CommonJS files are hoisted. This is the
     * recommended setting for most code bases.
     *
     * `false` will entirely prevent wrapping and hoist all files. This may still
     * work depending on the nature of cyclic dependencies but will often cause
     * problems.
     *
     * You can also provide a minimatch pattern, or array of patterns, to only
     * specify a subset of files which should be wrapped in functions for proper
     * `require` semantics.
     *
     * `"debug"` works like `"auto"` but after bundling, it will display a warning
     * containing a list of ids that have been wrapped which can be used as
     * minimatch pattern for fine-tuning.
     * @default "auto"
     */
    strictRequires?: boolean | string | RegExp | readonly (string | RegExp)[]
    /**
     * Sometimes you have to leave require statements unconverted. Pass an array
     * containing the IDs or a `id => boolean` function.
     * @default []
     */
    ignore?: ReadonlyArray<string> | ((id: string) => boolean)
    /**
     * In most cases, where `require` calls are inside a `try-catch` clause,
     * they should be left unconverted as it requires an optional dependency
     * that may or may not be installed beside the rolled up package.
     * Due to the conversion of `require` to a static `import` - the call is
     * hoisted to the top of the file, outside the `try-catch` clause.
     *
     * - `true`: Default. All `require` calls inside a `try` will be left unconverted.
     * - `false`: All `require` calls inside a `try` will be converted as if the
     *   `try-catch` clause is not there.
     * - `remove`: Remove all `require` calls from inside any `try` block.
     * - `string[]`: Pass an array containing the IDs to left unconverted.
     * - `((id: string) => boolean|'remove')`: Pass a function that controls
     *   individual IDs.
     *
     * @default true
     */
    ignoreTryCatch?:
    | boolean
    | 'remove'
    | ReadonlyArray<string>
    | ((id: string) => boolean | 'remove')
    /**
     * Controls how to render imports from external dependencies. By default,
     * this plugin assumes that all external dependencies are CommonJS. This
     * means they are rendered as default imports to be compatible with e.g.
     * NodeJS where ES modules can only import a default export from a CommonJS
     * dependency.
     *
     * If you set `esmExternals` to `true`, this plugin assumes that all
     * external dependencies are ES modules and respect the
     * `requireReturnsDefault` option. If that option is not set, they will be
     * rendered as namespace imports.
     *
     * You can also supply an array of ids to be treated as ES modules, or a
     * function that will be passed each external id to determine whether it is
     * an ES module.
     * @default false
     */
    esmExternals?: boolean | ReadonlyArray<string> | ((id: string) => boolean)
    /**
     * Controls what is returned when requiring an ES module from a CommonJS file.
     * When using the `esmExternals` option, this will also apply to external
     * modules. By default, this plugin will render those imports as namespace
     * imports i.e.
     *
     * ```js
     * // input
     * const foo = require('foo');
     *
     * // output
     * import * as foo from 'foo';
     * ```
     *
     * However, there are some situations where this may not be desired.
     * For these situations, you can change Rollup's behaviour either globally or
     * per module. To change it globally, set the `requireReturnsDefault` option
     * to one of the following values:
     *
     * - `false`: This is the default, requiring an ES module returns its
     *   namespace. This is the only option that will also add a marker
     *   `__esModule: true` to the namespace to support interop patterns in
     *   CommonJS modules that are transpiled ES modules.
     * - `"namespace"`: Like `false`, requiring an ES module returns its
     *   namespace, but the plugin does not add the `__esModule` marker and thus
     *   creates more efficient code. For external dependencies when using
     *   `esmExternals: true`, no additional interop code is generated.
     * - `"auto"`: This is complementary to how `output.exports: "auto"` works in
     *   Rollup: If a module has a default export and no named exports, requiring
     *   that module returns the default export. In all other cases, the namespace
     *   is returned. For external dependencies when using `esmExternals: true`, a
     *   corresponding interop helper is added.
     * - `"preferred"`: If a module has a default export, requiring that module
     *   always returns the default export, no matter whether additional named
     *   exports exist. This is similar to how previous versions of this plugin
     *   worked. Again for external dependencies when using `esmExternals: true`,
     *   an interop helper is added.
     * - `true`: This will always try to return the default export on require
     *   without checking if it actually exists. This can throw at build time if
     *   there is no default export. This is how external dependencies are handled
     *   when `esmExternals` is not used. The advantage over the other options is
     *   that, like `false`, this does not add an interop helper for external
     *   dependencies, keeping the code lean.
     *
     * To change this for individual modules, you can supply a function for
     * `requireReturnsDefault` instead. This function will then be called once for
     * each required ES module or external dependency with the corresponding id
     * and allows you to return different values for different modules.
     * @default false
     */
    requireReturnsDefault?:
    | boolean
    | 'auto'
    | 'preferred'
    | 'namespace'
    | ((id: string) => boolean | 'auto' | 'preferred' | 'namespace')

    /**
     * @default "auto"
     */
    defaultIsModuleExports?: boolean | 'auto' | ((id: string) => boolean | 'auto')
    /**
     * Some modules contain dynamic `require` calls, or require modules that
     * contain circular dependencies, which are not handled well by static
     * imports. Including those modules as `dynamicRequireTargets` will simulate a
     * CommonJS (NodeJS-like) environment for them with support for dynamic
     * dependencies. It also enables `strictRequires` for those modules.
     *
     * Note: In extreme cases, this feature may result in some paths being
     * rendered as absolute in the final bundle. The plugin tries to avoid
     * exposing paths from the local machine, but if you are `dynamicRequirePaths`
     * with paths that are far away from your project's folder, that may require
     * replacing strings like `"/Users/John/Desktop/foo-project/"` -\> `"/"`.
     */
    dynamicRequireTargets?: string | ReadonlyArray<string>
    /**
     * To avoid long paths when using the `dynamicRequireTargets` option, you can use this option to specify a directory
     * that is a common parent for all files that use dynamic require statements. Using a directory higher up such as `/`
     * may lead to unnecessarily long paths in the generated code and may expose directory names on your machine like your
     * home directory name. By default, it uses the current working directory.
     */
    dynamicRequireRoot?: string
}

export declare interface RollupDynamicImportVarsOptions {
    /**
     * Files to include in this plugin (default all).
     * @default []
     */
    include?: string | RegExp | (string | RegExp)[]
    /**
     * Files to exclude in this plugin (default none).
     * @default []
     */
    exclude?: string | RegExp | (string | RegExp)[]
    /**
     * By default, the plugin quits the build process when it encounters an error. If you set this option to true, it will throw a warning instead and leave the code untouched.
     * @default false
     */
    warnOnError?: boolean
}

export { rollupVersion }

/**
 * Search up for the nearest workspace root
 */
export declare function searchForWorkspaceRoot(current: string, root?: string): string;

export declare function send(req: IncomingMessage, res: ServerResponse, content: string | Buffer, type: string, options: SendOptions): void;

export declare interface SendOptions {
    etag?: string;
    cacheControl?: string;
    headers?: OutgoingHttpHeaders;
    map?: SourceMap | null;
}

export declare type ServerHook = (this: void, server: ViteDevServer) => (() => void) | void | Promise<(() => void) | void>;

export declare interface ServerOptions extends CommonServerOptions {
    /**
     * Configure HMR-specific options (port, host, path & protocol)
     */
    hmr?: HmrOptions | boolean;
    /**
     * chokidar watch options
     * https://github.com/paulmillr/chokidar#api
     */
    watch?: WatchOptions;
    /**
     * Create Vite dev server to be used as a middleware in an existing server
     * @default false
     */
    middlewareMode?: boolean | 'html' | 'ssr';
    /**
     * Options for files served via '/\@fs/'.
     */
    fs?: FileSystemServeOptions;
    /**
     * Origin for the generated asset URLs.
     *
     * @example `http://127.0.0.1:8080`
     */
    origin?: string;
    /**
     * Pre-transform known direct imports
     * @default true
     */
    preTransformRequests?: boolean;
    /**
     * Whether or not to ignore-list source files in the dev server sourcemap, used to populate
     * the [`x_google_ignoreList` source map extension](https://developer.chrome.com/blog/devtools-better-angular-debugging/#the-x_google_ignorelist-source-map-extension).
     *
     * By default, it excludes all paths containing `node_modules`. You can pass `false` to
     * disable this behavior, or, for full control, a function that takes the source path and
     * sourcemap path and returns whether to ignore the source path.
     */
    sourcemapIgnoreList?: false | ((sourcePath: string, sourcemapPath: string) => boolean);
    /**
     * Force dep pre-optimization regardless of whether deps have changed.
     *
     * @deprecated Use optimizeDeps.force instead, this option may be removed
     * in a future minor version without following semver
     */
    force?: boolean;
}

export declare function sortUserPlugins(plugins: (Plugin_2 | Plugin_2[])[] | undefined): [Plugin_2[], Plugin_2[], Plugin_2[]];

export declare function splitVendorChunk(options?: {
    cache?: SplitVendorChunkCache;
}): GetManualChunk;

export declare class SplitVendorChunkCache {
    cache: Map<string, boolean>;
    constructor();
    reset(): void;
}

export declare function splitVendorChunkPlugin(): Plugin_2;

export declare type SsrDepOptimizationOptions = DepOptimizationConfig;

export declare type SSRFormat = 'esm' | 'cjs';

export declare interface SSROptions {
    noExternal?: string | RegExp | (string | RegExp)[] | true;
    external?: string[];
    /**
     * Define the target for the ssr build. The browser field in package.json
     * is ignored for node but used if webworker is the target
     * @default 'node'
     */
    target?: SSRTarget;
    /**
     * Define the format for the ssr build. Since Vite v3 the SSR build generates ESM by default.
     * `'cjs'` can be selected to generate a CJS build, but it isn't recommended. This option is
     * left marked as experimental to give users more time to update to ESM. CJS builds requires
     * complex externalization heuristics that aren't present in the ESM format.
     * @experimental
     * @deprecated
     * @default 'esm'
     */
    format?: SSRFormat;
    /**
     * Control over which dependencies are optimized during SSR and esbuild options
     * During build:
     *   no external CJS dependencies are optimized by default
     * During dev:
     *   explicit no external CJS dependencies are optimized by default
     * @experimental
     */
    optimizeDeps?: SsrDepOptimizationOptions;
    resolve?: {
        /**
         * Conditions that are used in the plugin pipeline. The default value is the root config's `resolve.conditions`.
         *
         * Use this to override the default ssr conditions for the ssr build.
         *
         * @default rootConfig.resolve.conditions
         */
        conditions?: string[];
        /**
         * Conditions that are used during ssr import (including `ssrLoadModule`) of externalized dependencies.
         *
         * @default []
         */
        externalConditions?: string[];
    };
}

export declare type SSRTarget = 'node' | 'webworker';

declare interface Targets {
    android?: number,
    chrome?: number,
    edge?: number,
    firefox?: number,
    ie?: number,
    ios_saf?: number,
    opera?: number,
    safari?: number,
    samsung?: number
}

export declare namespace Terser {
    export type ECMA = 5 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020

    export interface ParseOptions {
        bare_returns?: boolean
        /** @deprecated legacy option. Currently, all supported EcmaScript is valid to parse. */
        ecma?: ECMA
        html5_comments?: boolean
        shebang?: boolean
    }

    export interface CompressOptions {
        arguments?: boolean
        arrows?: boolean
        booleans_as_integers?: boolean
        booleans?: boolean
        collapse_vars?: boolean
        comparisons?: boolean
        computed_props?: boolean
        conditionals?: boolean
        dead_code?: boolean
        defaults?: boolean
        directives?: boolean
        drop_console?: boolean
        drop_debugger?: boolean
        ecma?: ECMA
        evaluate?: boolean
        expression?: boolean
        global_defs?: object
        hoist_funs?: boolean
        hoist_props?: boolean
        hoist_vars?: boolean
        ie8?: boolean
        if_return?: boolean
        inline?: boolean | InlineFunctions
        join_vars?: boolean
        keep_classnames?: boolean | RegExp
        keep_fargs?: boolean
        keep_fnames?: boolean | RegExp
        keep_infinity?: boolean
        loops?: boolean
        module?: boolean
        negate_iife?: boolean
        passes?: number
        properties?: boolean
        pure_funcs?: string[]
        pure_getters?: boolean | 'strict'
        reduce_funcs?: boolean
        reduce_vars?: boolean
        sequences?: boolean | number
        side_effects?: boolean
        switches?: boolean
        toplevel?: boolean
        top_retain?: null | string | string[] | RegExp
        typeofs?: boolean
        unsafe_arrows?: boolean
        unsafe?: boolean
        unsafe_comps?: boolean
        unsafe_Function?: boolean
        unsafe_math?: boolean
        unsafe_symbols?: boolean
        unsafe_methods?: boolean
        unsafe_proto?: boolean
        unsafe_regexp?: boolean
        unsafe_undefined?: boolean
        unused?: boolean
    }

    export enum InlineFunctions {
        Disabled = 0,
        SimpleFunctions = 1,
        WithArguments = 2,
        WithArgumentsAndVariables = 3,
    }

    export interface MangleOptions {
        eval?: boolean
        keep_classnames?: boolean | RegExp
        keep_fnames?: boolean | RegExp
        module?: boolean
        nth_identifier?: SimpleIdentifierMangler | WeightedIdentifierMangler
        properties?: boolean | ManglePropertiesOptions
        reserved?: string[]
        safari10?: boolean
        toplevel?: boolean
    }

    /**
     * An identifier mangler for which the output is invariant with respect to the source code.
     */
    export interface SimpleIdentifierMangler {
        /**
         * Obtains the nth most favored (usually shortest) identifier to rename a variable to.
         * The mangler will increment n and retry until the return value is not in use in scope, and is not a reserved word.
         * This function is expected to be stable; Evaluating get(n) === get(n) should always return true.
         * @param n - The ordinal of the identifier.
         */
        get(n: number): string
    }

    /**
     * An identifier mangler that leverages character frequency analysis to determine identifier precedence.
     */
    export interface WeightedIdentifierMangler extends SimpleIdentifierMangler {
        /**
         * Modifies the internal weighting of the input characters by the specified delta.
         * Will be invoked on the entire printed AST, and then deduct mangleable identifiers.
         * @param chars - The characters to modify the weighting of.
         * @param delta - The numeric weight to add to the characters.
         */
        consider(chars: string, delta: number): number
        /**
         * Resets character weights.
         */
        reset(): void
        /**
         * Sorts identifiers by character frequency, in preparation for calls to get(n).
         */
        sort(): void
    }

    export interface ManglePropertiesOptions {
        builtins?: boolean
        debug?: boolean
        keep_quoted?: boolean | 'strict'
        nth_identifier?: SimpleIdentifierMangler | WeightedIdentifierMangler
        regex?: RegExp | string
        reserved?: string[]
    }

    export interface FormatOptions {
        ascii_only?: boolean
        /** @deprecated Not implemented anymore */
        beautify?: boolean
        braces?: boolean
        comments?:
        | boolean
        | 'all'
        | 'some'
        | RegExp
        | ((
        node: any,
        comment: {
            value: string
            type: 'comment1' | 'comment2' | 'comment3' | 'comment4'
            pos: number
            line: number
            col: number
        },
        ) => boolean)
        ecma?: ECMA
        ie8?: boolean
        keep_numbers?: boolean
        indent_level?: number
        indent_start?: number
        inline_script?: boolean
        keep_quoted_props?: boolean
        max_line_len?: number | false
        preamble?: string
        preserve_annotations?: boolean
        quote_keys?: boolean
        quote_style?: OutputQuoteStyle
        safari10?: boolean
        semicolons?: boolean
        shebang?: boolean
        shorthand?: boolean
        source_map?: SourceMapOptions
        webkit?: boolean
        width?: number
        wrap_iife?: boolean
        wrap_func_args?: boolean
    }

    export enum OutputQuoteStyle {
        PreferDouble = 0,
        AlwaysSingle = 1,
        AlwaysDouble = 2,
        AlwaysOriginal = 3,
    }

    export interface MinifyOptions {
        compress?: boolean | CompressOptions
        ecma?: ECMA
        enclose?: boolean | string
        ie8?: boolean
        keep_classnames?: boolean | RegExp
        keep_fnames?: boolean | RegExp
        mangle?: boolean | MangleOptions
        module?: boolean
        nameCache?: object
        format?: FormatOptions
        /** @deprecated deprecated */
        output?: FormatOptions
        parse?: ParseOptions
        safari10?: boolean
        sourceMap?: boolean | SourceMapOptions
        toplevel?: boolean
    }

    export interface MinifyOutput {
        code?: string
        map?: object | string
        decoded_map?: object | null
    }

    export interface SourceMapOptions {
        /** Source map object, 'inline' or source map file content */
        content?: object | string
        includeSources?: boolean
        filename?: string
        root?: string
        url?: string | 'inline'
    }
}

export declare interface TransformOptions {
    ssr?: boolean;
    html?: boolean;
    /* Excluded from this release type: allowId */
}

export declare interface TransformResult {
    code: string;
    map: SourceMap | null;
    etag?: string;
    deps?: string[];
    dynamicDeps?: string[];
}

export declare function transformWithEsbuild(code: string, filename: string, options?: EsbuildTransformOptions, inMap?: object): Promise<ESBuildTransformResult>;

export { Update }

export { UpdatePayload }

export declare interface UserConfig {
    /**
     * Project root directory. Can be an absolute path, or a path relative from
     * the location of the config file itself.
     * @default process.cwd()
     */
    root?: string;
    /**
     * Base public path when served in development or production.
     * @default '/'
     */
    base?: string;
    /**
     * Directory to serve as plain static assets. Files in this directory are
     * served and copied to build dist dir as-is without transform. The value
     * can be either an absolute file system path or a path relative to project root.
     *
     * Set to `false` or an empty string to disable copied static assets to build dist dir.
     * @default 'public'
     */
    publicDir?: string | false;
    /**
     * Directory to save cache files. Files in this directory are pre-bundled
     * deps or some other cache files that generated by vite, which can improve
     * the performance. You can use `--force` flag or manually delete the directory
     * to regenerate the cache files. The value can be either an absolute file
     * system path or a path relative to project root.
     * Default to `.vite` when no `package.json` is detected.
     * @default 'node_modules/.vite'
     */
    cacheDir?: string;
    /**
     * Explicitly set a mode to run in. This will override the default mode for
     * each command, and can be overridden by the command line --mode option.
     */
    mode?: string;
    /**
     * Define global variable replacements.
     * Entries will be defined on `window` during dev and replaced during build.
     */
    define?: Record<string, any>;
    /**
     * Array of vite plugins to use.
     */
    plugins?: PluginOption[];
    /**
     * Configure resolver
     */
    resolve?: ResolveOptions & {
        alias?: AliasOptions;
    };
    /**
     * CSS related options (preprocessors and CSS modules)
     */
    css?: CSSOptions;
    /**
     * JSON loading options
     */
    json?: JsonOptions;
    /**
     * Transform options to pass to esbuild.
     * Or set to `false` to disable esbuild.
     */
    esbuild?: ESBuildOptions | false;
    /**
     * Specify additional picomatch patterns to be treated as static assets.
     */
    assetsInclude?: string | RegExp | (string | RegExp)[];
    /**
     * Server specific options, e.g. host, port, https...
     */
    server?: ServerOptions;
    /**
     * Build specific options
     */
    build?: BuildOptions;
    /**
     * Preview specific options, e.g. host, port, https...
     */
    preview?: PreviewOptions;
    /**
     * Dep optimization options
     */
    optimizeDeps?: DepOptimizationOptions;
    /**
     * SSR specific options
     */
    ssr?: SSROptions;
    /**
     * Experimental features
     *
     * Features under this field could change in the future and might NOT follow semver.
     * Please be careful and always pin Vite's version when using them.
     * @experimental
     */
    experimental?: ExperimentalOptions;
    /**
     * Legacy options
     *
     * Features under this field only follow semver for patches, they could be removed in a
     * future minor version. Please always pin Vite's version to a minor when using them.
     */
    legacy?: LegacyOptions;
    /**
     * Log level.
     * @default 'info'
     */
    logLevel?: LogLevel;
    /**
     * Custom logger.
     */
    customLogger?: Logger;
    /**
     * @default true
     */
    clearScreen?: boolean;
    /**
     * Environment files directory. Can be an absolute path, or a path relative from
     * root.
     * @default root
     */
    envDir?: string;
    /**
     * Env variables starts with `envPrefix` will be exposed to your client source code via import.meta.env.
     * @default 'VITE_'
     */
    envPrefix?: string | string[];
    /**
     * Worker bundle options
     */
    worker?: {
        /**
         * Output format for worker bundle
         * @default 'iife'
         */
        format?: 'es' | 'iife';
        /**
         * Vite plugins that apply to worker bundle
         */
        plugins?: PluginOption[];
        /**
         * Rollup options to build worker bundle
         */
        rollupOptions?: Omit<RollupOptions, 'plugins' | 'input' | 'onwarn' | 'preserveEntrySignatures'>;
    };
    /**
     * Whether your application is a Single Page Application (SPA),
     * a Multi-Page Application (MPA), or Custom Application (SSR
     * and frameworks with custom HTML handling)
     * @default 'spa'
     */
    appType?: AppType;
}

export declare type UserConfigExport = UserConfig | Promise<UserConfig> | UserConfigFnObject | UserConfigFnPromise | UserConfigFn;

export declare type UserConfigFn = (env: ConfigEnv) => UserConfig | Promise<UserConfig>;

export declare type UserConfigFnObject = (env: ConfigEnv) => UserConfig;

export declare type UserConfigFnPromise = (env: ConfigEnv) => Promise<UserConfig>;

export declare const version: string;

export declare interface ViteDevServer {
    /**
     * The resolved vite config object
     */
    config: ResolvedConfig;
    /**
     * A connect app instance.
     * - Can be used to attach custom middlewares to the dev server.
     * - Can also be used as the handler function of a custom http server
     *   or as a middleware in any connect-style Node.js frameworks
     *
     * https://github.com/senchalabs/connect#use-middleware
     */
    middlewares: Connect.Server;
    /**
     * native Node http server instance
     * will be null in middleware mode
     */
    httpServer: http.Server | null;
    /**
     * chokidar watcher instance
     * https://github.com/paulmillr/chokidar#api
     */
    watcher: FSWatcher;
    /**
     * web socket server with `send(payload)` method
     */
    ws: WebSocketServer;
    /**
     * Rollup plugin container that can run plugin hooks on a given file
     */
    pluginContainer: PluginContainer;
    /**
     * Module graph that tracks the import relationships, url to file mapping
     * and hmr state.
     */
    moduleGraph: ModuleGraph;
    /**
     * The resolved urls Vite prints on the CLI. null in middleware mode or
     * before `server.listen` is called.
     */
    resolvedUrls: ResolvedServerUrls | null;
    /**
     * Programmatically resolve, load and transform a URL and get the result
     * without going through the http request pipeline.
     */
    transformRequest(url: string, options?: TransformOptions): Promise<TransformResult | null>;
    /**
     * Apply vite built-in HTML transforms and any plugin HTML transforms.
     */
    transformIndexHtml(url: string, html: string, originalUrl?: string): Promise<string>;
    /**
     * Transform module code into SSR format.
     */
    ssrTransform(code: string, inMap: SourceMap | null, url: string, originalCode?: string): Promise<TransformResult | null>;
    /**
     * Load a given URL as an instantiated module for SSR.
     */
    ssrLoadModule(url: string, opts?: {
        fixStacktrace?: boolean;
    }): Promise<Record<string, any>>;
    /**
     * Returns a fixed version of the given stack
     */
    ssrRewriteStacktrace(stack: string): string;
    /**
     * Mutates the given SSR error by rewriting the stacktrace
     */
    ssrFixStacktrace(e: Error): void;
    /**
     * Triggers HMR for a module in the module graph. You can use the `server.moduleGraph`
     * API to retrieve the module to be reloaded. If `hmr` is false, this is a no-op.
     */
    reloadModule(module: ModuleNode): Promise<void>;
    /**
     * Start the server.
     */
    listen(port?: number, isRestart?: boolean): Promise<ViteDevServer>;
    /**
     * Stop the server.
     */
    close(): Promise<void>;
    /**
     * Print server urls
     */
    printUrls(): void;
    /**
     * Restart the server.
     *
     * @param forceOptimize - force the optimizer to re-bundle, same as --force cli flag
     */
    restart(forceOptimize?: boolean): Promise<void>;
    /**
     * Open browser
     */
    openBrowser(): void;
    /* Excluded from this release type: _importGlobMap */
    /* Excluded from this release type: _ssrExternals */
    /* Excluded from this release type: _restartPromise */
    /* Excluded from this release type: _forceOptimizeOnRestart */
    /* Excluded from this release type: _pendingRequests */
    /* Excluded from this release type: _fsDenyGlob */
    /* Excluded from this release type: _shortcutsOptions */
}

export declare interface WatchOptions {
    /**
     * Indicates whether the process should continue to run as long as files are being watched. If
     * set to `false` when using `fsevents` to watch, no more events will be emitted after `ready`,
     * even if the process continues to run.
     */
    persistent?: boolean

    /**
     * ([anymatch](https://github.com/micromatch/anymatch)-compatible definition) Defines files/paths to
     * be ignored. The whole relative or absolute path is tested, not just filename. If a function
     * with two arguments is provided, it gets called twice per path - once with a single argument
     * (the path), second time with two arguments (the path and the
     * [`fs.Stats`](https://nodejs.org/api/fs.html#fs_class_fs_stats) object of that path).
     */
    ignored?: Matcher

    /**
     * If set to `false` then `add`/`addDir` events are also emitted for matching paths while
     * instantiating the watching as chokidar discovers these file paths (before the `ready` event).
     */
    ignoreInitial?: boolean

    /**
     * When `false`, only the symlinks themselves will be watched for changes instead of following
     * the link references and bubbling events through the link's path.
     */
    followSymlinks?: boolean

    /**
     * The base directory from which watch `paths` are to be derived. Paths emitted with events will
     * be relative to this.
     */
    cwd?: string

    /**
     * If set to true then the strings passed to .watch() and .add() are treated as literal path
     * names, even if they look like globs.
     *
     * @default false
     */
    disableGlobbing?: boolean

    /**
     * Whether to use fs.watchFile (backed by polling), or fs.watch. If polling leads to high CPU
     * utilization, consider setting this to `false`. It is typically necessary to **set this to
     * `true` to successfully watch files over a network**, and it may be necessary to successfully
     * watch files in other non-standard situations. Setting to `true` explicitly on OS X overrides
     * the `useFsEvents` default.
     */
    usePolling?: boolean

    /**
     * Whether to use the `fsevents` watching interface if available. When set to `true` explicitly
     * and `fsevents` is available this supersedes the `usePolling` setting. When set to `false` on
     * OS X, `usePolling: true` becomes the default.
     */
    useFsEvents?: boolean

    /**
     * If relying upon the [`fs.Stats`](https://nodejs.org/api/fs.html#fs_class_fs_stats) object that
     * may get passed with `add`, `addDir`, and `change` events, set this to `true` to ensure it is
     * provided even in cases where it wasn't already available from the underlying watch events.
     */
    alwaysStat?: boolean

    /**
     * If set, limits how many levels of subdirectories will be traversed.
     */
    depth?: number

    /**
     * Interval of file system polling.
     */
    interval?: number

    /**
     * Interval of file system polling for binary files. ([see list of binary extensions](https://gi
     * thub.com/sindresorhus/binary-extensions/blob/master/binary-extensions.json))
     */
    binaryInterval?: number

    /**
     *  Indicates whether to watch files that don't have read permissions if possible. If watching
     *  fails due to `EPERM` or `EACCES` with this set to `true`, the errors will be suppressed
     *  silently.
     */
    ignorePermissionErrors?: boolean

    /**
     * `true` if `useFsEvents` and `usePolling` are `false`. Automatically filters out artifacts
     * that occur when using editors that use "atomic writes" instead of writing directly to the
     * source file. If a file is re-added within 100 ms of being deleted, Chokidar emits a `change`
     * event rather than `unlink` then `add`. If the default of 100 ms does not work well for you,
     * you can override it by setting `atomic` to a custom value, in milliseconds.
     */
    atomic?: boolean | number

    /**
     * can be set to an object in order to adjust timing params:
     */
    awaitWriteFinish?: AwaitWriteFinishOptions | boolean
}

declare class WebSocket_2 extends EventEmitter {
    /** The connection is not yet open. */
    static readonly CONNECTING: 0
    /** The connection is open and ready to communicate. */
    static readonly OPEN: 1
    /** The connection is in the process of closing. */
    static readonly CLOSING: 2
    /** The connection is closed. */
    static readonly CLOSED: 3

    binaryType: 'nodebuffer' | 'arraybuffer' | 'fragments'
    readonly bufferedAmount: number
    readonly extensions: string
    /** Indicates whether the websocket is paused */
    readonly isPaused: boolean
    readonly protocol: string
    /** The current state of the connection */
    readonly readyState:
    | typeof WebSocket_2.CONNECTING
    | typeof WebSocket_2.OPEN
    | typeof WebSocket_2.CLOSING
    | typeof WebSocket_2.CLOSED
    readonly url: string

    /** The connection is not yet open. */
    readonly CONNECTING: 0
    /** The connection is open and ready to communicate. */
    readonly OPEN: 1
    /** The connection is in the process of closing. */
    readonly CLOSING: 2
    /** The connection is closed. */
    readonly CLOSED: 3

    onopen: ((event: WebSocket_2.Event) => void) | null
    onerror: ((event: WebSocket_2.ErrorEvent) => void) | null
    onclose: ((event: WebSocket_2.CloseEvent) => void) | null
    onmessage: ((event: WebSocket_2.MessageEvent) => void) | null

    constructor(address: null)
    constructor(
    address: string | URL_2,
    options?: WebSocket_2.ClientOptions | ClientRequestArgs,
    )
    constructor(
    address: string | URL_2,
    protocols?: string | string[],
    options?: WebSocket_2.ClientOptions | ClientRequestArgs,
    )

    close(code?: number, data?: string | Buffer): void
    ping(data?: any, mask?: boolean, cb?: (err: Error) => void): void
    pong(data?: any, mask?: boolean, cb?: (err: Error) => void): void
    send(data: any, cb?: (err?: Error) => void): void
    send(
    data: any,
    options: {
        mask?: boolean | undefined
        binary?: boolean | undefined
        compress?: boolean | undefined
        fin?: boolean | undefined
    },
    cb?: (err?: Error) => void,
    ): void
    terminate(): void

    /**
     * Pause the websocket causing it to stop emitting events. Some events can still be
     * emitted after this is called, until all buffered data is consumed. This method
     * is a noop if the ready state is `CONNECTING` or `CLOSED`.
     */
    pause(): void
    /**
     * Make a paused socket resume emitting events. This method is a noop if the ready
     * state is `CONNECTING` or `CLOSED`.
     */
    resume(): void

    // HTML5 WebSocket events
    addEventListener(
    method: 'message',
    cb: (event: WebSocket_2.MessageEvent) => void,
    options?: WebSocket_2.EventListenerOptions,
    ): void
    addEventListener(
    method: 'close',
    cb: (event: WebSocket_2.CloseEvent) => void,
    options?: WebSocket_2.EventListenerOptions,
    ): void
    addEventListener(
    method: 'error',
    cb: (event: WebSocket_2.ErrorEvent) => void,
    options?: WebSocket_2.EventListenerOptions,
    ): void
    addEventListener(
    method: 'open',
    cb: (event: WebSocket_2.Event) => void,
    options?: WebSocket_2.EventListenerOptions,
    ): void

    removeEventListener(
    method: 'message',
    cb: (event: WebSocket_2.MessageEvent) => void,
    ): void
    removeEventListener(
    method: 'close',
    cb: (event: WebSocket_2.CloseEvent) => void,
    ): void
    removeEventListener(
    method: 'error',
    cb: (event: WebSocket_2.ErrorEvent) => void,
    ): void
    removeEventListener(
    method: 'open',
    cb: (event: WebSocket_2.Event) => void,
    ): void

    // Events
    on(
    event: 'close',
    listener: (this: WebSocket_2, code: number, reason: Buffer) => void,
    ): this
    on(event: 'error', listener: (this: WebSocket_2, err: Error) => void): this
    on(
    event: 'upgrade',
    listener: (this: WebSocket_2, request: IncomingMessage) => void,
    ): this
    on(
    event: 'message',
    listener: (
    this: WebSocket_2,
    data: WebSocket_2.RawData,
    isBinary: boolean,
    ) => void,
    ): this
    on(event: 'open', listener: (this: WebSocket_2) => void): this
    on(
    event: 'ping' | 'pong',
    listener: (this: WebSocket_2, data: Buffer) => void,
    ): this
    on(
    event: 'unexpected-response',
    listener: (
    this: WebSocket_2,
    request: ClientRequest,
    response: IncomingMessage,
    ) => void,
    ): this
    on(
    event: string | symbol,
    listener: (this: WebSocket_2, ...args: any[]) => void,
    ): this

    once(
    event: 'close',
    listener: (this: WebSocket_2, code: number, reason: Buffer) => void,
    ): this
    once(event: 'error', listener: (this: WebSocket_2, err: Error) => void): this
    once(
    event: 'upgrade',
    listener: (this: WebSocket_2, request: IncomingMessage) => void,
    ): this
    once(
    event: 'message',
    listener: (
    this: WebSocket_2,
    data: WebSocket_2.RawData,
    isBinary: boolean,
    ) => void,
    ): this
    once(event: 'open', listener: (this: WebSocket_2) => void): this
    once(
    event: 'ping' | 'pong',
    listener: (this: WebSocket_2, data: Buffer) => void,
    ): this
    once(
    event: 'unexpected-response',
    listener: (
    this: WebSocket_2,
    request: ClientRequest,
    response: IncomingMessage,
    ) => void,
    ): this
    once(
    event: string | symbol,
    listener: (this: WebSocket_2, ...args: any[]) => void,
    ): this

    off(
    event: 'close',
    listener: (this: WebSocket_2, code: number, reason: Buffer) => void,
    ): this
    off(event: 'error', listener: (this: WebSocket_2, err: Error) => void): this
    off(
    event: 'upgrade',
    listener: (this: WebSocket_2, request: IncomingMessage) => void,
    ): this
    off(
    event: 'message',
    listener: (
    this: WebSocket_2,
    data: WebSocket_2.RawData,
    isBinary: boolean,
    ) => void,
    ): this
    off(event: 'open', listener: (this: WebSocket_2) => void): this
    off(
    event: 'ping' | 'pong',
    listener: (this: WebSocket_2, data: Buffer) => void,
    ): this
    off(
    event: 'unexpected-response',
    listener: (
    this: WebSocket_2,
    request: ClientRequest,
    response: IncomingMessage,
    ) => void,
    ): this
    off(
    event: string | symbol,
    listener: (this: WebSocket_2, ...args: any[]) => void,
    ): this

    addListener(
    event: 'close',
    listener: (code: number, reason: Buffer) => void,
    ): this
    addListener(event: 'error', listener: (err: Error) => void): this
    addListener(
    event: 'upgrade',
    listener: (request: IncomingMessage) => void,
    ): this
    addListener(
    event: 'message',
    listener: (data: WebSocket_2.RawData, isBinary: boolean) => void,
    ): this
    addListener(event: 'open', listener: () => void): this
    addListener(event: 'ping' | 'pong', listener: (data: Buffer) => void): this
    addListener(
    event: 'unexpected-response',
    listener: (request: ClientRequest, response: IncomingMessage) => void,
    ): this
    addListener(event: string | symbol, listener: (...args: any[]) => void): this

    removeListener(
    event: 'close',
    listener: (code: number, reason: Buffer) => void,
    ): this
    removeListener(event: 'error', listener: (err: Error) => void): this
    removeListener(
    event: 'upgrade',
    listener: (request: IncomingMessage) => void,
    ): this
    removeListener(
    event: 'message',
    listener: (data: WebSocket_2.RawData, isBinary: boolean) => void,
    ): this
    removeListener(event: 'open', listener: () => void): this
    removeListener(event: 'ping' | 'pong', listener: (data: Buffer) => void): this
    removeListener(
    event: 'unexpected-response',
    listener: (request: ClientRequest, response: IncomingMessage) => void,
    ): this
    removeListener(
    event: string | symbol,
    listener: (...args: any[]) => void,
    ): this
}

declare namespace WebSocket_2 {
    /**
     * Data represents the raw message payload received over the WebSocket.
     */
    type RawData = Buffer | ArrayBuffer | Buffer[]

    /**
     * Data represents the message payload received over the WebSocket.
     */
    type Data = string | Buffer | ArrayBuffer | Buffer[]

    /**
     * CertMeta represents the accepted types for certificate & key data.
     */
    type CertMeta = string | string[] | Buffer | Buffer[]

    /**
     * VerifyClientCallbackSync is a synchronous callback used to inspect the
     * incoming message. The return value (boolean) of the function determines
     * whether or not to accept the handshake.
     */
    type VerifyClientCallbackSync = (info: {
        origin: string
        secure: boolean
        req: IncomingMessage
    }) => boolean

    /**
     * VerifyClientCallbackAsync is an asynchronous callback used to inspect the
     * incoming message. The return value (boolean) of the function determines
     * whether or not to accept the handshake.
     */
    type VerifyClientCallbackAsync = (
    info: { origin: string; secure: boolean; req: IncomingMessage },
    callback: (
    res: boolean,
    code?: number,
    message?: string,
    headers?: OutgoingHttpHeaders,
    ) => void,
    ) => void

    interface ClientOptions extends SecureContextOptions {
        protocol?: string | undefined
        followRedirects?: boolean | undefined
        generateMask?(mask: Buffer): void
        handshakeTimeout?: number | undefined
        maxRedirects?: number | undefined
        perMessageDeflate?: boolean | PerMessageDeflateOptions | undefined
        localAddress?: string | undefined
        protocolVersion?: number | undefined
        headers?: { [key: string]: string } | undefined
        origin?: string | undefined
        agent?: Agent | undefined
        host?: string | undefined
        family?: number | undefined
        checkServerIdentity?(servername: string, cert: CertMeta): boolean
        rejectUnauthorized?: boolean | undefined
        maxPayload?: number | undefined
        skipUTF8Validation?: boolean | undefined
    }

    interface PerMessageDeflateOptions {
        serverNoContextTakeover?: boolean | undefined
        clientNoContextTakeover?: boolean | undefined
        serverMaxWindowBits?: number | undefined
        clientMaxWindowBits?: number | undefined
        zlibDeflateOptions?:
        | {
            flush?: number | undefined
            finishFlush?: number | undefined
            chunkSize?: number | undefined
            windowBits?: number | undefined
            level?: number | undefined
            memLevel?: number | undefined
            strategy?: number | undefined
            dictionary?: Buffer | Buffer[] | DataView | undefined
            info?: boolean | undefined
        }
        | undefined
        zlibInflateOptions?: ZlibOptions | undefined
        threshold?: number | undefined
        concurrencyLimit?: number | undefined
    }

    interface Event {
        type: string
        target: WebSocket
    }

    interface ErrorEvent {
        error: any
        message: string
        type: string
        target: WebSocket
    }

    interface CloseEvent {
        wasClean: boolean
        code: number
        reason: string
        type: string
        target: WebSocket
    }

    interface MessageEvent {
        data: Data
        type: string
        target: WebSocket
    }

    interface EventListenerOptions {
        once?: boolean | undefined
    }

    interface ServerOptions {
        host?: string | undefined
        port?: number | undefined
        backlog?: number | undefined
        server?: Server | Server_2 | undefined
        verifyClient?:
        | VerifyClientCallbackAsync
        | VerifyClientCallbackSync
        | undefined
        handleProtocols?: (
        protocols: Set<string>,
        request: IncomingMessage,
        ) => string | false
        path?: string | undefined
        noServer?: boolean | undefined
        clientTracking?: boolean | undefined
        perMessageDeflate?: boolean | PerMessageDeflateOptions | undefined
        maxPayload?: number | undefined
        skipUTF8Validation?: boolean | undefined
        WebSocket?: typeof WebSocket.WebSocket | undefined
    }

    interface AddressInfo {
        address: string
        family: string
        port: number
    }

    // WebSocket Server
    class Server<T extends WebSocket = WebSocket> extends EventEmitter {
        options: ServerOptions
        path: string
        clients: Set<T>

        constructor(options?: ServerOptions, callback?: () => void)

        address(): AddressInfo | string
        close(cb?: (err?: Error) => void): void
        handleUpgrade(
        request: IncomingMessage,
        socket: Duplex,
        upgradeHead: Buffer,
        callback: (client: T, request: IncomingMessage) => void,
        ): void
        shouldHandle(request: IncomingMessage): boolean | Promise<boolean>

        // Events
        on(
        event: 'connection',
        cb: (this: Server<T>, socket: T, request: IncomingMessage) => void,
        ): this
        on(event: 'error', cb: (this: Server<T>, error: Error) => void): this
        on(
        event: 'headers',
        cb: (
        this: Server<T>,
        headers: string[],
        request: IncomingMessage,
        ) => void,
        ): this
        on(event: 'close' | 'listening', cb: (this: Server<T>) => void): this
        on(
        event: string | symbol,
        listener: (this: Server<T>, ...args: any[]) => void,
        ): this

        once(
        event: 'connection',
        cb: (this: Server<T>, socket: T, request: IncomingMessage) => void,
        ): this
        once(event: 'error', cb: (this: Server<T>, error: Error) => void): this
        once(
        event: 'headers',
        cb: (
        this: Server<T>,
        headers: string[],
        request: IncomingMessage,
        ) => void,
        ): this
        once(event: 'close' | 'listening', cb: (this: Server<T>) => void): this
        once(
        event: string | symbol,
        listener: (this: Server<T>, ...args: any[]) => void,
        ): this

        off(
        event: 'connection',
        cb: (this: Server<T>, socket: T, request: IncomingMessage) => void,
        ): this
        off(event: 'error', cb: (this: Server<T>, error: Error) => void): this
        off(
        event: 'headers',
        cb: (
        this: Server<T>,
        headers: string[],
        request: IncomingMessage,
        ) => void,
        ): this
        off(event: 'close' | 'listening', cb: (this: Server<T>) => void): this
        off(
        event: string | symbol,
        listener: (this: Server<T>, ...args: any[]) => void,
        ): this

        addListener(
        event: 'connection',
        cb: (client: T, request: IncomingMessage) => void,
        ): this
        addListener(event: 'error', cb: (err: Error) => void): this
        addListener(
        event: 'headers',
        cb: (headers: string[], request: IncomingMessage) => void,
        ): this
        addListener(event: 'close' | 'listening', cb: () => void): this
        addListener(
        event: string | symbol,
        listener: (...args: any[]) => void,
        ): this

        removeListener(event: 'connection', cb: (client: T) => void): this
        removeListener(event: 'error', cb: (err: Error) => void): this
        removeListener(
        event: 'headers',
        cb: (headers: string[], request: IncomingMessage) => void,
        ): this
        removeListener(event: 'close' | 'listening', cb: () => void): this
        removeListener(
        event: string | symbol,
        listener: (...args: any[]) => void,
        ): this
    }

    const WebSocketServer: typeof Server
    interface WebSocketServer extends Server {} // tslint:disable-line no-empty-interface
    const WebSocket: typeof WebSocketAlias
    interface WebSocket extends WebSocketAlias {} // tslint:disable-line no-empty-interface

    // WebSocket stream
    function createWebSocketStream(
    websocket: WebSocket,
    options?: DuplexOptions,
    ): Duplex
}
export { WebSocket_2 as WebSocket }

export declare const WebSocketAlias: typeof WebSocket_2;

export declare interface WebSocketAlias extends WebSocket_2 {}

export declare interface WebSocketClient {
    /**
     * Send event to the client
     */
    send(payload: HMRPayload): void;
    /**
     * Send custom event
     */
    send(event: string, payload?: CustomPayload['data']): void;
    /**
     * The raw WebSocket instance
     * @advanced
     */
    socket: WebSocket_2;
}

export declare type WebSocketCustomListener<T> = (data: T, client: WebSocketClient) => void;

export declare interface WebSocketServer {
    /**
     * Listen on port and host
     */
    listen(): void;
    /**
     * Get all connected clients.
     */
    clients: Set<WebSocketClient>;
    /**
     * Broadcast events to all clients
     */
    send(payload: HMRPayload): void;
    /**
     * Send custom event
     */
    send<T extends string>(event: T, payload?: InferCustomEventPayload<T>): void;
    /**
     * Disconnect all clients and terminate the server.
     */
    close(): Promise<void>;
    /**
     * Handle custom event emitted by `import.meta.hot.send`
     */
    on: WebSocket_2.Server['on'] & {
        <T extends string>(event: T, listener: WebSocketCustomListener<InferCustomEventPayload<T>>): void;
    };
    /**
     * Unregister event listener.
     */
    off: WebSocket_2.Server['off'] & {
        (event: string, listener: Function): void;
    };
}

export { }
