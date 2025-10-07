import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { readFileSync } from "node:fs";
import * as vite from "vite";
import { createFilter } from "vite";
import { exactRegex, makeIdFiltersToMatchWithQuery } from "@rolldown/pluginutils";

//#region ../common/refresh-utils.ts
const runtimePublicPath = "/@react-refresh";
const reactCompRE = /extends\s+(?:React\.)?(?:Pure)?Component/;
const refreshContentRE = /\$RefreshReg\$\(/;
const preambleCode = `import { injectIntoGlobalHook } from "__BASE__${runtimePublicPath.slice(1)}";
injectIntoGlobalHook(window);
window.$RefreshReg$ = () => {};
window.$RefreshSig$ = () => (type) => type;`;
const getPreambleCode = (base) => preambleCode.replace("__BASE__", base);
const avoidSourceMapOption = Symbol();
function addRefreshWrapper(code, map, pluginName, id, reactRefreshHost = "") {
	const hasRefresh = refreshContentRE.test(code);
	const onlyReactComp = !hasRefresh && reactCompRE.test(code);
	const normalizedMap = map === avoidSourceMapOption ? null : map;
	if (!hasRefresh && !onlyReactComp) return {
		code,
		map: normalizedMap
	};
	const avoidSourceMap = map === avoidSourceMapOption;
	const newMap = typeof normalizedMap === "string" ? JSON.parse(normalizedMap) : normalizedMap;
	let newCode = code;
	if (hasRefresh) {
		const refreshHead = removeLineBreaksIfNeeded(`let prevRefreshReg;
let prevRefreshSig;

if (import.meta.hot && !inWebWorker) {
  if (!window.$RefreshReg$) {
    throw new Error(
      "${pluginName} can't detect preamble. Something is wrong."
    );
  }

  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = RefreshRuntime.getRefreshReg(${JSON.stringify(id)});
  window.$RefreshSig$ = RefreshRuntime.createSignatureFunctionForTransform;
}

`, avoidSourceMap);
		newCode = `${refreshHead}${newCode}

if (import.meta.hot && !inWebWorker) {
  window.$RefreshReg$ = prevRefreshReg;
  window.$RefreshSig$ = prevRefreshSig;
}
`;
		if (newMap) newMap.mappings = ";".repeat(16) + newMap.mappings;
	}
	const sharedHead = removeLineBreaksIfNeeded(`import * as RefreshRuntime from "${reactRefreshHost}${runtimePublicPath}";
const inWebWorker = typeof WorkerGlobalScope !== 'undefined' && self instanceof WorkerGlobalScope;

`, avoidSourceMap);
	newCode = `${sharedHead}${newCode}

if (import.meta.hot && !inWebWorker) {
  RefreshRuntime.__hmr_import(import.meta.url).then((currentExports) => {
    RefreshRuntime.registerExportsForReactRefresh(${JSON.stringify(id)}, currentExports);
    import.meta.hot.accept((nextExports) => {
      if (!nextExports) return;
      const invalidateMessage = RefreshRuntime.validateRefreshBoundaryAndEnqueueUpdate(${JSON.stringify(id)}, currentExports, nextExports);
      if (invalidateMessage) import.meta.hot.invalidate(invalidateMessage);
    });
  });
}
`;
	if (newMap) newMap.mappings = ";;;" + newMap.mappings;
	return {
		code: newCode,
		map: newMap
	};
}
function removeLineBreaksIfNeeded(code, enabled) {
	return enabled ? code.replace(/\n/g, "") : code;
}

//#endregion
//#region ../common/warning.ts
const silenceUseClientWarning = (userConfig) => ({ rollupOptions: { onwarn(warning, defaultHandler) {
	var _userConfig$build;
	if (warning.code === "MODULE_LEVEL_DIRECTIVE" && (warning.message.includes("use client") || warning.message.includes("use server"))) return;
	if (warning.code === "SOURCEMAP_ERROR" && warning.message.includes("resolve original location") && warning.pos === 0) return;
	if ((_userConfig$build = userConfig.build) === null || _userConfig$build === void 0 || (_userConfig$build = _userConfig$build.rollupOptions) === null || _userConfig$build === void 0 ? void 0 : _userConfig$build.onwarn) userConfig.build.rollupOptions.onwarn(warning, defaultHandler);
	else defaultHandler(warning);
} } });

//#endregion
//#region src/index.ts
const _dirname = dirname(fileURLToPath(import.meta.url));
const refreshRuntimePath = join(_dirname, "refresh-runtime.js");
let babel;
async function loadBabel() {
	if (!babel) babel = await import("@babel/core");
	return babel;
}
const defaultIncludeRE = /\.[tj]sx?$/;
const tsRE = /\.tsx?$/;
function viteReact(opts = {}) {
	var _opts$babel;
	const include = opts.include ?? defaultIncludeRE;
	const exclude = opts.exclude;
	const filter = createFilter(include, exclude);
	const jsxImportSource = opts.jsxImportSource ?? "react";
	const jsxImportRuntime = `${jsxImportSource}/jsx-runtime`;
	const jsxImportDevRuntime = `${jsxImportSource}/jsx-dev-runtime`;
	let runningInVite = false;
	let isProduction = true;
	let projectRoot = process.cwd();
	let skipFastRefresh = true;
	let runPluginOverrides;
	let staticBabelOptions;
	const importReactRE = /\bimport\s+(?:\*\s+as\s+)?React\b/;
	const viteBabel = {
		name: "vite:react-babel",
		enforce: "pre",
		config() {
			if (opts.jsxRuntime === "classic") if ("rolldownVersion" in vite) return { oxc: { jsx: {
				runtime: "classic",
				development: false
			} } };
			else return { esbuild: { jsx: "transform" } };
			else return {
				esbuild: {
					jsx: "automatic",
					jsxImportSource: opts.jsxImportSource
				},
				optimizeDeps: "rolldownVersion" in vite ? { rollupOptions: { jsx: { mode: "automatic" } } } : { esbuildOptions: { jsx: "automatic" } }
			};
		},
		configResolved(config) {
			runningInVite = true;
			projectRoot = config.root;
			isProduction = config.isProduction;
			skipFastRefresh = isProduction || config.command === "build" || config.server.hmr === false;
			if ("jsxPure" in opts) config.logger.warnOnce("[@vitejs/plugin-react] jsxPure was removed. You can configure esbuild.jsxSideEffects directly.");
			const hooks = config.plugins.map((plugin) => {
				var _plugin$api;
				return (_plugin$api = plugin.api) === null || _plugin$api === void 0 ? void 0 : _plugin$api.reactBabel;
			}).filter(defined);
			if ("rolldownVersion" in vite && !opts.babel && !hooks.length && !opts.disableOxcRecommendation) config.logger.warn("[vite:react-babel] We recommend switching to `@vitejs/plugin-react-oxc` for improved performance. More information at https://vite.dev/rolldown");
			if (hooks.length > 0) runPluginOverrides = (babelOptions, context) => {
				hooks.forEach((hook) => hook(babelOptions, context, config));
			};
			else if (typeof opts.babel !== "function") {
				staticBabelOptions = createBabelOptions(opts.babel);
				if (canSkipBabel(staticBabelOptions.plugins, staticBabelOptions) && skipFastRefresh && (opts.jsxRuntime === "classic" ? isProduction : true)) delete viteBabel.transform;
			}
		},
		options(options) {
			if (!runningInVite) {
				options.jsx = {
					mode: opts.jsxRuntime,
					importSource: opts.jsxImportSource
				};
				return options;
			}
		},
		transform: {
			filter: { id: {
				include: makeIdFiltersToMatchWithQuery(include),
				exclude: [...exclude ? makeIdFiltersToMatchWithQuery(ensureArray(exclude)) : [], /\/node_modules\//]
			} },
			async handler(code, id, options) {
				if (id.includes("/node_modules/")) return;
				const [filepath] = id.split("?");
				if (!filter(filepath)) return;
				const ssr = (options === null || options === void 0 ? void 0 : options.ssr) === true;
				const babelOptions = (() => {
					if (staticBabelOptions) return staticBabelOptions;
					const newBabelOptions = createBabelOptions(typeof opts.babel === "function" ? opts.babel(id, { ssr }) : opts.babel);
					runPluginOverrides === null || runPluginOverrides === void 0 || runPluginOverrides(newBabelOptions, {
						id,
						ssr
					});
					return newBabelOptions;
				})();
				const plugins = [...babelOptions.plugins];
				const isJSX = filepath.endsWith("x");
				const useFastRefresh = !skipFastRefresh && !ssr && (isJSX || (opts.jsxRuntime === "classic" ? importReactRE.test(code) : code.includes(jsxImportDevRuntime) || code.includes(jsxImportRuntime)));
				if (useFastRefresh) plugins.push([await loadPlugin("react-refresh/babel"), { skipEnvCheck: true }]);
				if (opts.jsxRuntime === "classic" && isJSX) {
					if (!isProduction) plugins.push(await loadPlugin("@babel/plugin-transform-react-jsx-self"), await loadPlugin("@babel/plugin-transform-react-jsx-source"));
				}
				if (canSkipBabel(plugins, babelOptions)) return;
				const parserPlugins = [...babelOptions.parserOpts.plugins];
				if (!filepath.endsWith(".ts")) parserPlugins.push("jsx");
				if (tsRE.test(filepath)) parserPlugins.push("typescript");
				const babel$1 = await loadBabel();
				const result = await babel$1.transformAsync(code, {
					...babelOptions,
					root: projectRoot,
					filename: id,
					sourceFileName: filepath,
					retainLines: getReactCompilerPlugin(plugins) != null ? false : !isProduction && isJSX && opts.jsxRuntime !== "classic",
					parserOpts: {
						...babelOptions.parserOpts,
						sourceType: "module",
						allowAwaitOutsideFunction: true,
						plugins: parserPlugins
					},
					generatorOpts: {
						...babelOptions.generatorOpts,
						importAttributesKeyword: "with",
						decoratorsBeforeExport: true
					},
					plugins,
					sourceMaps: true
				});
				if (result) {
					if (!useFastRefresh) return {
						code: result.code,
						map: result.map
					};
					return addRefreshWrapper(result.code, result.map, "@vitejs/plugin-react", id, opts.reactRefreshHost);
				}
			}
		}
	};
	const dependencies = [
		"react",
		"react-dom",
		jsxImportDevRuntime,
		jsxImportRuntime
	];
	const staticBabelPlugins = typeof opts.babel === "object" ? ((_opts$babel = opts.babel) === null || _opts$babel === void 0 ? void 0 : _opts$babel.plugins) ?? [] : [];
	const reactCompilerPlugin = getReactCompilerPlugin(staticBabelPlugins);
	if (reactCompilerPlugin != null) {
		const reactCompilerRuntimeModule = getReactCompilerRuntimeModule(reactCompilerPlugin);
		dependencies.push(reactCompilerRuntimeModule);
	}
	const viteReactRefresh = {
		name: "vite:react-refresh",
		enforce: "pre",
		config: (userConfig) => ({
			build: silenceUseClientWarning(userConfig),
			optimizeDeps: { include: dependencies },
			resolve: { dedupe: ["react", "react-dom"] }
		}),
		resolveId: {
			filter: { id: exactRegex(runtimePublicPath) },
			handler(id) {
				if (id === runtimePublicPath) return id;
			}
		},
		load: {
			filter: { id: exactRegex(runtimePublicPath) },
			handler(id) {
				if (id === runtimePublicPath) return readFileSync(refreshRuntimePath, "utf-8").replace(/__README_URL__/g, "https://github.com/vitejs/vite-plugin-react/tree/main/packages/plugin-react");
			}
		},
		transformIndexHtml(_, config) {
			if (!skipFastRefresh) return [{
				tag: "script",
				attrs: { type: "module" },
				children: getPreambleCode(config.server.config.base)
			}];
		}
	};
	return [viteBabel, viteReactRefresh];
}
viteReact.preambleCode = preambleCode;
function canSkipBabel(plugins, babelOptions) {
	return !(plugins.length || babelOptions.presets.length || babelOptions.configFile || babelOptions.babelrc);
}
const loadedPlugin = /* @__PURE__ */ new Map();
function loadPlugin(path) {
	const cached = loadedPlugin.get(path);
	if (cached) return cached;
	const promise = import(path).then((module) => {
		const value = module.default || module;
		loadedPlugin.set(path, value);
		return value;
	});
	loadedPlugin.set(path, promise);
	return promise;
}
function createBabelOptions(rawOptions) {
	var _babelOptions$parserO;
	const babelOptions = {
		babelrc: false,
		configFile: false,
		...rawOptions
	};
	babelOptions.plugins || (babelOptions.plugins = []);
	babelOptions.presets || (babelOptions.presets = []);
	babelOptions.overrides || (babelOptions.overrides = []);
	babelOptions.parserOpts || (babelOptions.parserOpts = {});
	(_babelOptions$parserO = babelOptions.parserOpts).plugins || (_babelOptions$parserO.plugins = []);
	return babelOptions;
}
function defined(value) {
	return value !== void 0;
}
function getReactCompilerPlugin(plugins) {
	return plugins.find((p) => p === "babel-plugin-react-compiler" || Array.isArray(p) && p[0] === "babel-plugin-react-compiler");
}
function getReactCompilerRuntimeModule(plugin) {
	let moduleName = "react/compiler-runtime";
	if (Array.isArray(plugin)) {
		var _plugin$, _plugin$2, _plugin$3;
		if (((_plugin$ = plugin[1]) === null || _plugin$ === void 0 ? void 0 : _plugin$.target) === "17" || ((_plugin$2 = plugin[1]) === null || _plugin$2 === void 0 ? void 0 : _plugin$2.target) === "18") moduleName = "react-compiler-runtime";
		else if (typeof ((_plugin$3 = plugin[1]) === null || _plugin$3 === void 0 ? void 0 : _plugin$3.runtimeModule) === "string") {
			var _plugin$4;
			moduleName = (_plugin$4 = plugin[1]) === null || _plugin$4 === void 0 ? void 0 : _plugin$4.runtimeModule;
		}
	}
	return moduleName;
}
function ensureArray(value) {
	return Array.isArray(value) ? value : [value];
}

//#endregion
export { viteReact as default };