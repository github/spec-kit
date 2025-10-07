export const VERSION: string;

// utils
type NullValue = null | undefined | void;
type MaybeArray<T> = T | T[];
type MaybePromise<T> = T | Promise<T>;

type PartialNull<T> = {
	[P in keyof T]: T[P] | null;
};

export interface RollupError extends RollupLog {
	name?: string;
	stack?: string;
	watchFiles?: string[];
}

export type RollupWarning = RollupLog;

export interface RollupLog {
	binding?: string;
	cause?: unknown;
	code?: string;
	exporter?: string;
	frame?: string;
	hook?: string;
	id?: string;
	ids?: string[];
	loc?: {
		column: number;
		file?: string;
		line: number;
	};
	message: string;
	meta?: any;
	names?: string[];
	plugin?: string;
	pluginCode?: unknown;
	pos?: number;
	reexporter?: string;
	stack?: string;
	url?: string;
}

export type LogLevel = 'warn' | 'info' | 'debug';
export type LogLevelOption = LogLevel | 'silent';

export type SourceMapSegment =
	| [number]
	| [number, number, number, number]
	| [number, number, number, number, number];

export interface ExistingDecodedSourceMap {
	file?: string;
	readonly mappings: SourceMapSegment[][];
	names: string[];
	sourceRoot?: string;
	sources: string[];
	sourcesContent?: (string | null)[];
	version: number;
	x_google_ignoreList?: number[];
}

export interface ExistingRawSourceMap {
	file?: string;
	mappings: string;
	names: string[];
	sourceRoot?: string;
	sources: string[];
	sourcesContent?: (string | null)[];
	version: number;
	x_google_ignoreList?: number[];
}

export type DecodedSourceMapOrMissing =
	| {
			missing: true;
			plugin: string;
	  }
	| (ExistingDecodedSourceMap & { missing?: false });

export interface SourceMap {
	file: string;
	mappings: string;
	names: string[];
	sources: string[];
	sourcesContent: (string | null)[];
	version: number;
	toString(): string;
	toUrl(): string;
}

export type SourceMapInput = ExistingRawSourceMap | string | null | { mappings: '' };

interface ModuleOptions {
	assertions: Record<string, string>;
	meta: CustomPluginOptions;
	moduleSideEffects: boolean | 'no-treeshake';
	syntheticNamedExports: boolean | string;
}

export interface SourceDescription extends Partial<PartialNull<ModuleOptions>> {
	ast?: AcornNode;
	code: string;
	map?: SourceMapInput;
}

export interface TransformModuleJSON {
	ast?: AcornNode;
	code: string;
	// note if plugins use new this.cache to opt-out auto transform cache
	customTransformCache: boolean;
	originalCode: string;
	originalSourcemap: ExistingDecodedSourceMap | null;
	sourcemapChain: DecodedSourceMapOrMissing[];
	transformDependencies: string[];
}

export interface ModuleJSON extends TransformModuleJSON, ModuleOptions {
	ast: AcornNode;
	dependencies: string[];
	id: string;
	resolvedIds: ResolvedIdMap;
	transformFiles: EmittedFile[] | undefined;
}

export interface PluginCache {
	delete(id: string): boolean;
	get<T = any>(id: string): T;
	has(id: string): boolean;
	set<T = any>(id: string, value: T): void;
}

export type LoggingFunction = (log: RollupLog | string | (() => RollupLog | string)) => void;

export interface MinimalPluginContext {
	debug: LoggingFunction;
	error: (error: RollupError | string) => never;
	info: LoggingFunction;
	meta: PluginContextMeta;
	warn: LoggingFunction;
}

export interface EmittedAsset {
	fileName?: string;
	name?: string;
	needsCodeReference?: boolean;
	source?: string | Uint8Array;
	type: 'asset';
}

export interface EmittedChunk {
	fileName?: string;
	id: string;
	implicitlyLoadedAfterOneOf?: string[];
	importer?: string;
	name?: string;
	preserveSignature?: PreserveEntrySignaturesOption;
	type: 'chunk';
}

export interface EmittedPrebuiltChunk {
	code: string;
	exports?: string[];
	fileName: string;
	map?: SourceMap;
	sourcemapFileName?: string;
	type: 'prebuilt-chunk';
}

export type EmittedFile = EmittedAsset | EmittedChunk | EmittedPrebuiltChunk;

export type EmitFile = (emittedFile: EmittedFile) => string;

interface ModuleInfo extends ModuleOptions {
	ast: AcornNode | null;
	code: string | null;
	dynamicImporters: readonly string[];
	dynamicallyImportedIdResolutions: readonly ResolvedId[];
	dynamicallyImportedIds: readonly string[];
	exportedBindings: Record<string, string[]> | null;
	exports: string[] | null;
	hasDefaultExport: boolean | null;
	/** @deprecated Use `moduleSideEffects` instead */
	hasModuleSideEffects: boolean | 'no-treeshake';
	id: string;
	implicitlyLoadedAfterOneOf: readonly string[];
	implicitlyLoadedBefore: readonly string[];
	importedIdResolutions: readonly ResolvedId[];
	importedIds: readonly string[];
	importers: readonly string[];
	isEntry: boolean;
	isExternal: boolean;
	isIncluded: boolean | null;
}

export type GetModuleInfo = (moduleId: string) => ModuleInfo | null;

export interface CustomPluginOptions {
	[plugin: string]: any;
}

type LoggingFunctionWithPosition = (
	log: RollupLog | string | (() => RollupLog | string),
	pos?: number | { column: number; line: number }
) => void;

export interface PluginContext extends MinimalPluginContext {
	addWatchFile: (id: string) => void;
	cache: PluginCache;
	debug: LoggingFunction;
	emitFile: EmitFile;
	error: (error: RollupError | string) => never;
	getFileName: (fileReferenceId: string) => string;
	getModuleIds: () => IterableIterator<string>;
	getModuleInfo: GetModuleInfo;
	getWatchFiles: () => string[];
	info: LoggingFunction;
	load: (
		options: { id: string; resolveDependencies?: boolean } & Partial<PartialNull<ModuleOptions>>
	) => Promise<ModuleInfo>;
	/** @deprecated Use `this.getModuleIds` instead */
	moduleIds: IterableIterator<string>;
	parse: (input: string, options?: any) => AcornNode;
	resolve: (
		source: string,
		importer?: string,
		options?: {
			assertions?: Record<string, string>;
			custom?: CustomPluginOptions;
			isEntry?: boolean;
			skipSelf?: boolean;
		}
	) => Promise<ResolvedId | null>;
	setAssetSource: (assetReferenceId: string, source: string | Uint8Array) => void;
	warn: LoggingFunction;
}

export interface PluginContextMeta {
	rollupVersion: string;
	watchMode: boolean;
}

export interface ResolvedId extends ModuleOptions {
	external: boolean | 'absolute';
	id: string;
	resolvedBy: string;
}

export interface ResolvedIdMap {
	[key: string]: ResolvedId;
}

interface PartialResolvedId extends Partial<PartialNull<ModuleOptions>> {
	external?: boolean | 'absolute' | 'relative';
	id: string;
	resolvedBy?: string;
}

export type ResolveIdResult = string | NullValue | false | PartialResolvedId;

export type ResolveIdResultWithoutNullValue = string | false | PartialResolvedId;

export type ResolveIdHook = (
	this: PluginContext,
	source: string,
	importer: string | undefined,
	options: { assertions: Record<string, string>; custom?: CustomPluginOptions; isEntry: boolean }
) => ResolveIdResult;

export type ShouldTransformCachedModuleHook = (
	this: PluginContext,
	options: {
		ast: AcornNode;
		code: string;
		id: string;
		meta: CustomPluginOptions;
		moduleSideEffects: boolean | 'no-treeshake';
		resolvedSources: ResolvedIdMap;
		syntheticNamedExports: boolean | string;
	}
) => boolean | NullValue;

export type IsExternal = (
	source: string,
	importer: string | undefined,
	isResolved: boolean
) => boolean;

export type IsPureModule = (id: string) => boolean | NullValue;

export type HasModuleSideEffects = (id: string, external: boolean) => boolean;

export type LoadResult = SourceDescription | string | NullValue;

export type LoadHook = (this: PluginContext, id: string) => LoadResult;

export interface TransformPluginContext extends PluginContext {
	debug: LoggingFunctionWithPosition;
	error: (error: RollupError | string, pos?: number | { column: number; line: number }) => never;
	getCombinedSourcemap: () => SourceMap;
	info: LoggingFunctionWithPosition;
	warn: LoggingFunctionWithPosition;
}

export type TransformResult = string | NullValue | Partial<SourceDescription>;

export type TransformHook = (
	this: TransformPluginContext,
	code: string,
	id: string
) => TransformResult;

export type ModuleParsedHook = (this: PluginContext, info: ModuleInfo) => void;

export type RenderChunkHook = (
	this: PluginContext,
	code: string,
	chunk: RenderedChunk,
	options: NormalizedOutputOptions,
	meta: { chunks: Record<string, RenderedChunk> }
) => { code: string; map?: SourceMapInput } | string | NullValue;

export type ResolveDynamicImportHook = (
	this: PluginContext,
	specifier: string | AcornNode,
	importer: string,
	options: { assertions: Record<string, string> }
) => ResolveIdResult;

export type ResolveImportMetaHook = (
	this: PluginContext,
	property: string | null,
	options: { chunkId: string; format: InternalModuleFormat; moduleId: string }
) => string | NullValue;

export type ResolveFileUrlHook = (
	this: PluginContext,
	options: {
		chunkId: string;
		fileName: string;
		format: InternalModuleFormat;
		moduleId: string;
		referenceId: string;
		relativePath: string;
	}
) => string | NullValue;

export type AddonHookFunction = (
	this: PluginContext,
	chunk: RenderedChunk
) => string | Promise<string>;
export type AddonHook = string | AddonHookFunction;

export type ChangeEvent = 'create' | 'update' | 'delete';
export type WatchChangeHook = (
	this: PluginContext,
	id: string,
	change: { event: ChangeEvent }
) => void;

/**
 * use this type for plugin annotation
 * @example
 * ```ts
 * interface Options {
 * ...
 * }
 * const myPlugin: PluginImpl<Options> = (options = {}) => { ... }
 * ```
 */
// eslint-disable-next-line @typescript-eslint/ban-types
export type PluginImpl<O extends object = object, A = any> = (options?: O) => Plugin<A>;

export interface OutputBundle {
	[fileName: string]: OutputAsset | OutputChunk;
}

export interface FunctionPluginHooks {
	augmentChunkHash: (this: PluginContext, chunk: RenderedChunk) => string | void;
	buildEnd: (this: PluginContext, error?: Error) => void;
	buildStart: (this: PluginContext, options: NormalizedInputOptions) => void;
	closeBundle: (this: PluginContext) => void;
	closeWatcher: (this: PluginContext) => void;
	generateBundle: (
		this: PluginContext,
		options: NormalizedOutputOptions,
		bundle: OutputBundle,
		isWrite: boolean
	) => void;
	load: LoadHook;
	moduleParsed: ModuleParsedHook;
	onLog: (this: MinimalPluginContext, level: LogLevel, log: RollupLog) => boolean | NullValue;
	options: (this: MinimalPluginContext, options: InputOptions) => InputOptions | NullValue;
	outputOptions: (this: PluginContext, options: OutputOptions) => OutputOptions | NullValue;
	renderChunk: RenderChunkHook;
	renderDynamicImport: (
		this: PluginContext,
		options: {
			customResolution: string | null;
			format: InternalModuleFormat;
			moduleId: string;
			targetModuleId: string | null;
		}
	) => { left: string; right: string } | NullValue;
	renderError: (this: PluginContext, error?: Error) => void;
	renderStart: (
		this: PluginContext,
		outputOptions: NormalizedOutputOptions,
		inputOptions: NormalizedInputOptions
	) => void;
	resolveDynamicImport: ResolveDynamicImportHook;
	resolveFileUrl: ResolveFileUrlHook;
	resolveId: ResolveIdHook;
	resolveImportMeta: ResolveImportMetaHook;
	shouldTransformCachedModule: ShouldTransformCachedModuleHook;
	transform: TransformHook;
	watchChange: WatchChangeHook;
	writeBundle: (
		this: PluginContext,
		options: NormalizedOutputOptions,
		bundle: OutputBundle
	) => void;
}

export type OutputPluginHooks =
	| 'augmentChunkHash'
	| 'generateBundle'
	| 'outputOptions'
	| 'renderChunk'
	| 'renderDynamicImport'
	| 'renderError'
	| 'renderStart'
	| 'resolveFileUrl'
	| 'resolveImportMeta'
	| 'writeBundle';

export type InputPluginHooks = Exclude<keyof FunctionPluginHooks, OutputPluginHooks>;

export type SyncPluginHooks =
	| 'augmentChunkHash'
	| 'onLog'
	| 'outputOptions'
	| 'renderDynamicImport'
	| 'resolveFileUrl'
	| 'resolveImportMeta';

export type AsyncPluginHooks = Exclude<keyof FunctionPluginHooks, SyncPluginHooks>;

export type FirstPluginHooks =
	| 'load'
	| 'renderDynamicImport'
	| 'resolveDynamicImport'
	| 'resolveFileUrl'
	| 'resolveId'
	| 'resolveImportMeta'
	| 'shouldTransformCachedModule';

export type SequentialPluginHooks =
	| 'augmentChunkHash'
	| 'generateBundle'
	| 'onLog'
	| 'options'
	| 'outputOptions'
	| 'renderChunk'
	| 'transform';

export type ParallelPluginHooks = Exclude<
	keyof FunctionPluginHooks | AddonHooks,
	FirstPluginHooks | SequentialPluginHooks
>;

export type AddonHooks = 'banner' | 'footer' | 'intro' | 'outro';

type MakeAsync<Function_> = Function_ extends (
	this: infer This,
	...parameters: infer Arguments
) => infer Return
	? (this: This, ...parameters: Arguments) => Return | Promise<Return>
	: never;

// eslint-disable-next-line @typescript-eslint/ban-types
type ObjectHook<T, O = {}> = T | ({ handler: T; order?: 'pre' | 'post' | null } & O);

export type PluginHooks = {
	[K in keyof FunctionPluginHooks]: ObjectHook<
		K extends AsyncPluginHooks ? MakeAsync<FunctionPluginHooks[K]> : FunctionPluginHooks[K],
		// eslint-disable-next-line @typescript-eslint/ban-types
		K extends ParallelPluginHooks ? { sequential?: boolean } : {}
	>;
};

export interface OutputPlugin
	extends Partial<{ [K in OutputPluginHooks]: PluginHooks[K] }>,
		Partial<{ [K in AddonHooks]: ObjectHook<AddonHook> }> {
	cacheKey?: string;
	name: string;
	version?: string;
}

export interface Plugin<A = any> extends OutputPlugin, Partial<PluginHooks> {
	// for inter-plugin communication
	api?: A;
}

export type TreeshakingPreset = 'smallest' | 'safest' | 'recommended';

export interface NormalizedTreeshakingOptions {
	annotations: boolean;
	correctVarValueBeforeDeclaration: boolean;
	manualPureFunctions: readonly string[];
	moduleSideEffects: HasModuleSideEffects;
	propertyReadSideEffects: boolean | 'always';
	tryCatchDeoptimization: boolean;
	unknownGlobalSideEffects: boolean;
}

export interface TreeshakingOptions
	extends Partial<Omit<NormalizedTreeshakingOptions, 'moduleSideEffects'>> {
	moduleSideEffects?: ModuleSideEffectsOption;
	preset?: TreeshakingPreset;
}

interface ManualChunkMeta {
	getModuleIds: () => IterableIterator<string>;
	getModuleInfo: GetModuleInfo;
}
export type GetManualChunk = (id: string, meta: ManualChunkMeta) => string | NullValue;

export type ExternalOption =
	| (string | RegExp)[]
	| string
	| RegExp
	| ((source: string, importer: string | undefined, isResolved: boolean) => boolean | NullValue);

export type GlobalsOption = { [name: string]: string } | ((name: string) => string);

export type InputOption = string | string[] | { [entryAlias: string]: string };

export type ManualChunksOption = { [chunkAlias: string]: string[] } | GetManualChunk;

export type LogHandlerWithDefault = (
	level: LogLevel,
	log: RollupLog,
	defaultHandler: LogOrStringHandler
) => void;

export type LogOrStringHandler = (level: LogLevel | 'error', log: RollupLog | string) => void;

export type LogHandler = (level: LogLevel, log: RollupLog) => void;

export type ModuleSideEffectsOption = boolean | 'no-external' | string[] | HasModuleSideEffects;

export type PreserveEntrySignaturesOption = false | 'strict' | 'allow-extension' | 'exports-only';

export type SourcemapPathTransformOption = (
	relativeSourcePath: string,
	sourcemapPath: string
) => string;

export type SourcemapIgnoreListOption = (
	relativeSourcePath: string,
	sourcemapPath: string
) => boolean;

export type InputPluginOption = MaybePromise<Plugin | NullValue | false | InputPluginOption[]>;

export interface InputOptions {
	acorn?: Record<string, unknown>;
	acornInjectPlugins?: ((...arguments_: any[]) => unknown)[] | ((...arguments_: any[]) => unknown);
	cache?: boolean | RollupCache;
	context?: string;
	experimentalCacheExpiry?: number;
	experimentalLogSideEffects?: boolean;
	external?: ExternalOption;
	/** @deprecated Use the "inlineDynamicImports" output option instead. */
	inlineDynamicImports?: boolean;
	input?: InputOption;
	logLevel?: LogLevelOption;
	makeAbsoluteExternalsRelative?: boolean | 'ifRelativeSource';
	/** @deprecated Use the "manualChunks" output option instead. */
	manualChunks?: ManualChunksOption;
	maxParallelFileOps?: number;
	/** @deprecated Use the "maxParallelFileOps" option instead. */
	maxParallelFileReads?: number;
	moduleContext?: ((id: string) => string | NullValue) | { [id: string]: string };
	onLog?: LogHandlerWithDefault;
	onwarn?: WarningHandlerWithDefault;
	perf?: boolean;
	plugins?: InputPluginOption;
	preserveEntrySignatures?: PreserveEntrySignaturesOption;
	/** @deprecated Use the "preserveModules" output option instead. */
	preserveModules?: boolean;
	preserveSymlinks?: boolean;
	shimMissingExports?: boolean;
	strictDeprecations?: boolean;
	treeshake?: boolean | TreeshakingPreset | TreeshakingOptions;
	watch?: WatcherOptions | false;
}

export interface InputOptionsWithPlugins extends InputOptions {
	plugins: Plugin[];
}

export interface NormalizedInputOptions {
	acorn: Record<string, unknown>;
	acornInjectPlugins: (() => unknown)[];
	cache: false | undefined | RollupCache;
	context: string;
	experimentalCacheExpiry: number;
	experimentalLogSideEffects: boolean;
	external: IsExternal;
	/** @deprecated Use the "inlineDynamicImports" output option instead. */
	inlineDynamicImports: boolean | undefined;
	input: string[] | { [entryAlias: string]: string };
	logLevel: LogLevelOption;
	makeAbsoluteExternalsRelative: boolean | 'ifRelativeSource';
	/** @deprecated Use the "manualChunks" output option instead. */
	manualChunks: ManualChunksOption | undefined;
	maxParallelFileOps: number;
	/** @deprecated Use the "maxParallelFileOps" option instead. */
	maxParallelFileReads: number;
	moduleContext: (id: string) => string;
	onLog: LogHandler;
	onwarn: (warning: RollupLog) => void;
	perf: boolean;
	plugins: Plugin[];
	preserveEntrySignatures: PreserveEntrySignaturesOption;
	/** @deprecated Use the "preserveModules" output option instead. */
	preserveModules: boolean | undefined;
	preserveSymlinks: boolean;
	shimMissingExports: boolean;
	strictDeprecations: boolean;
	treeshake: false | NormalizedTreeshakingOptions;
}

export type InternalModuleFormat = 'amd' | 'cjs' | 'es' | 'iife' | 'system' | 'umd';

export type ModuleFormat = InternalModuleFormat | 'commonjs' | 'esm' | 'module' | 'systemjs';

type GeneratedCodePreset = 'es5' | 'es2015';

interface NormalizedGeneratedCodeOptions {
	arrowFunctions: boolean;
	constBindings: boolean;
	objectShorthand: boolean;
	reservedNamesAsProps: boolean;
	symbols: boolean;
}

interface GeneratedCodeOptions extends Partial<NormalizedGeneratedCodeOptions> {
	preset?: GeneratedCodePreset;
}

export type OptionsPaths = Record<string, string> | ((id: string) => string);

export type InteropType = 'compat' | 'auto' | 'esModule' | 'default' | 'defaultOnly';

export type GetInterop = (id: string | null) => InteropType;

export type AmdOptions = (
	| {
			autoId?: false;
			id: string;
	  }
	| {
			autoId: true;
			basePath?: string;
			id?: undefined;
	  }
	| {
			autoId?: false;
			id?: undefined;
	  }
) & {
	define?: string;
	forceJsExtensionForImports?: boolean;
};

export type NormalizedAmdOptions = (
	| {
			autoId: false;
			id?: string;
	  }
	| {
			autoId: true;
			basePath: string;
	  }
) & {
	define: string;
	forceJsExtensionForImports: boolean;
};

type AddonFunction = (chunk: RenderedChunk) => string | Promise<string>;

type OutputPluginOption = MaybePromise<OutputPlugin | NullValue | false | OutputPluginOption[]>;

export interface OutputOptions {
	amd?: AmdOptions;
	assetFileNames?: string | ((chunkInfo: PreRenderedAsset) => string);
	banner?: string | AddonFunction;
	chunkFileNames?: string | ((chunkInfo: PreRenderedChunk) => string);
	compact?: boolean;
	// only required for bundle.write
	dir?: string;
	/** @deprecated Use the "renderDynamicImport" plugin hook instead. */
	dynamicImportFunction?: string;
	dynamicImportInCjs?: boolean;
	entryFileNames?: string | ((chunkInfo: PreRenderedChunk) => string);
	esModule?: boolean | 'if-default-prop';
	/** @deprecated This option is no longer needed and ignored. */
	experimentalDeepDynamicChunkOptimization?: boolean;
	experimentalMinChunkSize?: number;
	exports?: 'default' | 'named' | 'none' | 'auto';
	extend?: boolean;
	externalImportAssertions?: boolean;
	externalLiveBindings?: boolean;
	// only required for bundle.write
	file?: string;
	footer?: string | AddonFunction;
	format?: ModuleFormat;
	freeze?: boolean;
	generatedCode?: GeneratedCodePreset | GeneratedCodeOptions;
	globals?: GlobalsOption;
	hoistTransitiveImports?: boolean;
	indent?: string | boolean;
	inlineDynamicImports?: boolean;
	interop?: InteropType | GetInterop;
	intro?: string | AddonFunction;
	manualChunks?: ManualChunksOption;
	minifyInternalExports?: boolean;
	name?: string;
	/** @deprecated Use "generatedCode.symbols" instead. */
	namespaceToStringTag?: boolean;
	noConflict?: boolean;
	outro?: string | AddonFunction;
	paths?: OptionsPaths;
	plugins?: OutputPluginOption;
	/** @deprecated Use "generatedCode.constBindings" instead. */
	preferConst?: boolean;
	preserveModules?: boolean;
	preserveModulesRoot?: string;
	sanitizeFileName?: boolean | ((fileName: string) => string);
	sourcemap?: boolean | 'inline' | 'hidden';
	sourcemapBaseUrl?: string;
	sourcemapExcludeSources?: boolean;
	sourcemapFile?: string;
	sourcemapFileNames?: string | ((chunkInfo: PreRenderedChunk) => string);
	sourcemapIgnoreList?: boolean | SourcemapIgnoreListOption;
	sourcemapPathTransform?: SourcemapPathTransformOption;
	strict?: boolean;
	systemNullSetters?: boolean;
	validate?: boolean;
}

export interface NormalizedOutputOptions {
	amd: NormalizedAmdOptions;
	assetFileNames: string | ((chunkInfo: PreRenderedAsset) => string);
	banner: AddonFunction;
	chunkFileNames: string | ((chunkInfo: PreRenderedChunk) => string);
	compact: boolean;
	dir: string | undefined;
	/** @deprecated Use the "renderDynamicImport" plugin hook instead. */
	dynamicImportFunction: string | undefined;
	dynamicImportInCjs: boolean;
	entryFileNames: string | ((chunkInfo: PreRenderedChunk) => string);
	esModule: boolean | 'if-default-prop';
	/** @deprecated This option is no longer needed and ignored. */
	experimentalDeepDynamicChunkOptimization: boolean;
	experimentalMinChunkSize: number;
	exports: 'default' | 'named' | 'none' | 'auto';
	extend: boolean;
	externalImportAssertions: boolean;
	externalLiveBindings: boolean;
	file: string | undefined;
	footer: AddonFunction;
	format: InternalModuleFormat;
	freeze: boolean;
	generatedCode: NormalizedGeneratedCodeOptions;
	globals: GlobalsOption;
	hoistTransitiveImports: boolean;
	indent: true | string;
	inlineDynamicImports: boolean;
	interop: GetInterop;
	intro: AddonFunction;
	manualChunks: ManualChunksOption;
	minifyInternalExports: boolean;
	name: string | undefined;
	/** @deprecated Use "generatedCode.symbols" instead. */
	namespaceToStringTag: boolean;
	noConflict: boolean;
	outro: AddonFunction;
	paths: OptionsPaths;
	plugins: OutputPlugin[];
	/** @deprecated Use "generatedCode.constBindings" instead. */
	preferConst: boolean;
	preserveModules: boolean;
	preserveModulesRoot: string | undefined;
	sanitizeFileName: (fileName: string) => string;
	sourcemap: boolean | 'inline' | 'hidden';
	sourcemapBaseUrl: string | undefined;
	sourcemapExcludeSources: boolean;
	sourcemapFile: string | undefined;
	sourcemapFileNames: string | ((chunkInfo: PreRenderedChunk) => string) | undefined;
	sourcemapIgnoreList: SourcemapIgnoreListOption;
	sourcemapPathTransform: SourcemapPathTransformOption | undefined;
	strict: boolean;
	systemNullSetters: boolean;
	validate: boolean;
}

export type WarningHandlerWithDefault = (
	warning: RollupLog,
	defaultHandler: LoggingFunction
) => void;

export interface SerializedTimings {
	[label: string]: [number, number, number];
}

export interface PreRenderedAsset {
	name: string | undefined;
	source: string | Uint8Array;
	type: 'asset';
}

export interface OutputAsset extends PreRenderedAsset {
	fileName: string;
	needsCodeReference: boolean;
}

export interface RenderedModule {
	readonly code: string | null;
	originalLength: number;
	removedExports: string[];
	renderedExports: string[];
	renderedLength: number;
}

export interface PreRenderedChunk {
	exports: string[];
	facadeModuleId: string | null;
	isDynamicEntry: boolean;
	isEntry: boolean;
	isImplicitEntry: boolean;
	moduleIds: string[];
	name: string;
	type: 'chunk';
}

export interface RenderedChunk extends PreRenderedChunk {
	dynamicImports: string[];
	fileName: string;
	implicitlyLoadedBefore: string[];
	importedBindings: {
		[imported: string]: string[];
	};
	imports: string[];
	modules: {
		[id: string]: RenderedModule;
	};
	referencedFiles: string[];
}

export interface OutputChunk extends RenderedChunk {
	code: string;
	map: SourceMap | null;
	sourcemapFileName: string | null;
	preliminaryFileName: string;
}

export interface SerializablePluginCache {
	[key: string]: [number, any];
}

export interface RollupCache {
	modules: ModuleJSON[];
	plugins?: Record<string, SerializablePluginCache>;
}

export interface RollupOutput {
	output: [OutputChunk, ...(OutputChunk | OutputAsset)[]];
}

export interface RollupBuild {
	cache: RollupCache | undefined;
	close: () => Promise<void>;
	closed: boolean;
	generate: (outputOptions: OutputOptions) => Promise<RollupOutput>;
	getTimings?: () => SerializedTimings;
	watchFiles: string[];
	write: (options: OutputOptions) => Promise<RollupOutput>;
}

export interface RollupOptions extends InputOptions {
	// This is included for compatibility with config files but ignored by rollup.rollup
	output?: OutputOptions | OutputOptions[];
}

export interface MergedRollupOptions extends InputOptionsWithPlugins {
	output: OutputOptions[];
}

export function rollup(options: RollupOptions): Promise<RollupBuild>;

export interface ChokidarOptions {
	alwaysStat?: boolean;
	atomic?: boolean | number;
	awaitWriteFinish?:
		| {
				pollInterval?: number;
				stabilityThreshold?: number;
		  }
		| boolean;
	binaryInterval?: number;
	cwd?: string;
	depth?: number;
	disableGlobbing?: boolean;
	followSymlinks?: boolean;
	ignoreInitial?: boolean;
	ignorePermissionErrors?: boolean;
	ignored?: any;
	interval?: number;
	persistent?: boolean;
	useFsEvents?: boolean;
	usePolling?: boolean;
}

export type RollupWatchHooks = 'onError' | 'onStart' | 'onBundleStart' | 'onBundleEnd' | 'onEnd';

export interface WatcherOptions {
	buildDelay?: number;
	chokidar?: ChokidarOptions;
	clearScreen?: boolean;
	exclude?: string | RegExp | (string | RegExp)[];
	include?: string | RegExp | (string | RegExp)[];
	skipWrite?: boolean;
}

export interface RollupWatchOptions extends InputOptions {
	output?: OutputOptions | OutputOptions[];
	watch?: WatcherOptions | false;
}

export type AwaitedEventListener<
	T extends { [event: string]: (...parameters: any) => any },
	K extends keyof T
> = (...parameters: Parameters<T[K]>) => void | Promise<void>;

export interface AwaitingEventEmitter<T extends { [event: string]: (...parameters: any) => any }> {
	close(): Promise<void>;
	emit<K extends keyof T>(event: K, ...parameters: Parameters<T[K]>): Promise<unknown>;
	/**
	 * Removes an event listener.
	 */
	off<K extends keyof T>(event: K, listener: AwaitedEventListener<T, K>): this;
	/**
	 * Registers an event listener that will be awaited before Rollup continues.
	 * All listeners will be awaited in parallel while rejections are tracked via
	 * Promise.all.
	 */
	on<K extends keyof T>(event: K, listener: AwaitedEventListener<T, K>): this;
	/**
	 * Registers an event listener that will be awaited before Rollup continues.
	 * All listeners will be awaited in parallel while rejections are tracked via
	 * Promise.all.
	 * Listeners are removed automatically when removeListenersForCurrentRun is
	 * called, which happens automatically after each run.
	 */
	onCurrentRun<K extends keyof T>(
		event: K,
		listener: (...parameters: Parameters<T[K]>) => Promise<ReturnType<T[K]>>
	): this;
	removeAllListeners(): this;
	removeListenersForCurrentRun(): this;
}

export type RollupWatcherEvent =
	| { code: 'START' }
	| { code: 'BUNDLE_START'; input?: InputOption; output: readonly string[] }
	| {
			code: 'BUNDLE_END';
			duration: number;
			input?: InputOption;
			output: readonly string[];
			result: RollupBuild;
	  }
	| { code: 'END' }
	| { code: 'ERROR'; error: RollupError; result: RollupBuild | null };

export type RollupWatcher = AwaitingEventEmitter<{
	change: (id: string, change: { event: ChangeEvent }) => void;
	close: () => void;
	event: (event: RollupWatcherEvent) => void;
	restart: () => void;
}>;

export function watch(config: RollupWatchOptions | RollupWatchOptions[]): RollupWatcher;

interface AcornNode {
	end: number;
	start: number;
	type: string;
}

export function defineConfig(options: RollupOptions): RollupOptions;
export function defineConfig(options: RollupOptions[]): RollupOptions[];
export function defineConfig(optionsFunction: RollupOptionsFunction): RollupOptionsFunction;

export type RollupOptionsFunction = (
	commandLineArguments: Record<string, any>
) => MaybePromise<RollupOptions | RollupOptions[]>;
