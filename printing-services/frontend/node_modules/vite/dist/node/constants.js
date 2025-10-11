import path, { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readFileSync } from 'node:fs';

const { version } = JSON.parse(readFileSync(new URL('../../package.json', import.meta.url)).toString());
const VERSION = version;
const DEFAULT_MAIN_FIELDS = [
    'module',
    'jsnext:main',
    'jsnext',
];
// Baseline support browserslist
// "defaults and supports es6-module and supports es6-module-dynamic-import"
// Higher browser versions may be needed for extra features.
const ESBUILD_MODULES_TARGET = [
    'es2020',
    'edge88',
    'firefox78',
    'chrome87',
    'safari14',
];
const DEFAULT_EXTENSIONS = [
    '.mjs',
    '.js',
    '.mts',
    '.ts',
    '.jsx',
    '.tsx',
    '.json',
];
const DEFAULT_CONFIG_FILES = [
    'vite.config.js',
    'vite.config.mjs',
    'vite.config.ts',
    'vite.config.cjs',
    'vite.config.mts',
    'vite.config.cts',
];
const JS_TYPES_RE = /\.(?:j|t)sx?$|\.mjs$/;
const CSS_LANGS_RE = /\.(css|less|sass|scss|styl|stylus|pcss|postcss|sss)(?:$|\?)/;
const OPTIMIZABLE_ENTRY_RE = /\.[cm]?[jt]s$/;
const SPECIAL_QUERY_RE = /[?&](?:worker|sharedworker|raw|url)\b/;
/**
 * Prefix for resolved fs paths, since windows paths may not be valid as URLs.
 */
const FS_PREFIX = `/@fs/`;
/**
 * Prefix for resolved Ids that are not valid browser import specifiers
 */
const VALID_ID_PREFIX = `/@id/`;
/**
 * Plugins that use 'virtual modules' (e.g. for helper functions), prefix the
 * module ID with `\0`, a convention from the rollup ecosystem.
 * This prevents other plugins from trying to process the id (like node resolution),
 * and core features like sourcemaps can use this info to differentiate between
 * virtual modules and regular files.
 * `\0` is not a permitted char in import URLs so we have to replace them during
 * import analysis. The id will be decoded back before entering the plugins pipeline.
 * These encoded virtual ids are also prefixed by the VALID_ID_PREFIX, so virtual
 * modules in the browser end up encoded as `/@id/__x00__{id}`
 */
const NULL_BYTE_PLACEHOLDER = `__x00__`;
const CLIENT_PUBLIC_PATH = `/@vite/client`;
const ENV_PUBLIC_PATH = `/@vite/env`;
const VITE_PACKAGE_DIR = resolve(
// import.meta.url is `dist/node/constants.js` after bundle
fileURLToPath(import.meta.url), '../../..');
const CLIENT_ENTRY = resolve(VITE_PACKAGE_DIR, 'dist/client/client.mjs');
const ENV_ENTRY = resolve(VITE_PACKAGE_DIR, 'dist/client/env.mjs');
const CLIENT_DIR = path.dirname(CLIENT_ENTRY);
// ** READ THIS ** before editing `KNOWN_ASSET_TYPES`.
//   If you add an asset to `KNOWN_ASSET_TYPES`, make sure to also add it
//   to the TypeScript declaration file `packages/vite/client.d.ts` and
//   add a mime type to the `registerCustomMime` in
//   `packages/vite/src/node/plugin/assets.ts` if mime type cannot be
//   looked up by mrmime.
const KNOWN_ASSET_TYPES = [
    // images
    'apng',
    'png',
    'jpe?g',
    'jfif',
    'pjpeg',
    'pjp',
    'gif',
    'svg',
    'ico',
    'webp',
    'avif',
    // media
    'mp4',
    'webm',
    'ogg',
    'mp3',
    'wav',
    'flac',
    'aac',
    'opus',
    // fonts
    'woff2?',
    'eot',
    'ttf',
    'otf',
    // other
    'webmanifest',
    'pdf',
    'txt',
];
const DEFAULT_ASSETS_RE = new RegExp(`\\.(` + KNOWN_ASSET_TYPES.join('|') + `)(\\?.*)?$`);
const DEP_VERSION_RE = /[?&](v=[\w.-]+)\b/;
const loopbackHosts = new Set([
    'localhost',
    '127.0.0.1',
    '::1',
    '0000:0000:0000:0000:0000:0000:0000:0001',
]);
const wildcardHosts = new Set([
    '0.0.0.0',
    '::',
    '0000:0000:0000:0000:0000:0000:0000:0000',
]);
const DEFAULT_DEV_PORT = 5173;
const DEFAULT_PREVIEW_PORT = 4173;
// the regex to allow loopback address origins:
// - localhost domains (which will always resolve to the loopback address by RFC 6761 section 6.3)
// - 127.0.0.1
// - ::1
const defaultAllowedOrigins = /^https?:\/\/(?:(?:[^:]+\.)?localhost|127\.0\.0\.1|\[::1\])(?::\d+)?$/;

export { CLIENT_DIR, CLIENT_ENTRY, CLIENT_PUBLIC_PATH, CSS_LANGS_RE, DEFAULT_ASSETS_RE, DEFAULT_CONFIG_FILES, DEFAULT_DEV_PORT, DEFAULT_EXTENSIONS, DEFAULT_MAIN_FIELDS, DEFAULT_PREVIEW_PORT, DEP_VERSION_RE, ENV_ENTRY, ENV_PUBLIC_PATH, ESBUILD_MODULES_TARGET, FS_PREFIX, JS_TYPES_RE, KNOWN_ASSET_TYPES, NULL_BYTE_PLACEHOLDER, OPTIMIZABLE_ENTRY_RE, SPECIAL_QUERY_RE, VALID_ID_PREFIX, VERSION, VITE_PACKAGE_DIR, defaultAllowedOrigins, loopbackHosts, wildcardHosts };
