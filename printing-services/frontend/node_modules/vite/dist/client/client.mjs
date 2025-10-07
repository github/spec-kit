import '@vite/env';

const base$1 = __BASE__ || '/';
// set :host styles to make playwright detect the element as visible
const template = /*html*/ `
<style>
:host {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 99999;
  --monospace: 'SFMono-Regular', Consolas,
  'Liberation Mono', Menlo, Courier, monospace;
  --red: #ff5555;
  --yellow: #e2aa53;
  --purple: #cfa4ff;
  --cyan: #2dd9da;
  --dim: #c9c9c9;

  --window-background: #181818;
  --window-color: #d8d8d8;
}

.backdrop {
  position: fixed;
  z-index: 99999;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow-y: scroll;
  margin: 0;
  background: rgba(0, 0, 0, 0.66);
}

.window {
  font-family: var(--monospace);
  line-height: 1.5;
  width: 800px;
  color: var(--window-color);
  margin: 30px auto;
  padding: 25px 40px;
  position: relative;
  background: var(--window-background);
  border-radius: 6px 6px 8px 8px;
  box-shadow: 0 19px 38px rgba(0,0,0,0.30), 0 15px 12px rgba(0,0,0,0.22);
  overflow: hidden;
  border-top: 8px solid var(--red);
  direction: ltr;
  text-align: left;
}

pre {
  font-family: var(--monospace);
  font-size: 16px;
  margin-top: 0;
  margin-bottom: 1em;
  overflow-x: scroll;
  scrollbar-width: none;
}

pre::-webkit-scrollbar {
  display: none;
}

.message {
  line-height: 1.3;
  font-weight: 600;
  white-space: pre-wrap;
}

.message-body {
  color: var(--red);
}

.plugin {
  color: var(--purple);
}

.file {
  color: var(--cyan);
  margin-bottom: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.frame {
  color: var(--yellow);
}

.stack {
  font-size: 13px;
  color: var(--dim);
}

.tip {
  font-size: 13px;
  color: #999;
  border-top: 1px dotted #999;
  padding-top: 13px;
  line-height: 1.8;
}

code {
  font-size: 13px;
  font-family: var(--monospace);
  color: var(--yellow);
}

.file-link {
  text-decoration: underline;
  cursor: pointer;
}

kbd {
  line-height: 1.5;
  font-family: ui-monospace, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.75rem;
  font-weight: 700;
  background-color: rgb(38, 40, 44);
  color: rgb(166, 167, 171);
  padding: 0.15rem 0.3rem;
  border-radius: 0.25rem;
  border-width: 0.0625rem 0.0625rem 0.1875rem;
  border-style: solid;
  border-color: rgb(54, 57, 64);
  border-image: initial;
}
</style>
<div class="backdrop" part="backdrop">
  <div class="window" part="window">
    <pre class="message" part="message"><span class="plugin" part="plugin"></span><span class="message-body" part="message-body"></span></pre>
    <pre class="file" part="file"></pre>
    <pre class="frame" part="frame"></pre>
    <pre class="stack" part="stack"></pre>
    <div class="tip" part="tip">
      Click outside, press <kbd>Esc</kbd> key, or fix the code to dismiss.<br>
      You can also disable this overlay by setting
      <code part="config-option-name">server.hmr.overlay</code> to <code part="config-option-value">false</code> in <code part="config-file-name">vite.config.js.</code>
    </div>
  </div>
</div>
`;
const fileRE = /(?:[a-zA-Z]:\\|\/).*?:\d+:\d+/g;
const codeframeRE = /^(?:>?\s+\d+\s+\|.*|\s+\|\s*\^.*)\r?\n/gm;
// Allow `ErrorOverlay` to extend `HTMLElement` even in environments where
// `HTMLElement` was not originally defined.
const { HTMLElement = class {
} } = globalThis;
class ErrorOverlay extends HTMLElement {
    constructor(err, links = true) {
        var _a;
        super();
        this.root = this.attachShadow({ mode: 'open' });
        this.root.innerHTML = template;
        codeframeRE.lastIndex = 0;
        const hasFrame = err.frame && codeframeRE.test(err.frame);
        const message = hasFrame
            ? err.message.replace(codeframeRE, '')
            : err.message;
        if (err.plugin) {
            this.text('.plugin', `[plugin:${err.plugin}] `);
        }
        this.text('.message-body', message.trim());
        const [file] = (((_a = err.loc) === null || _a === void 0 ? void 0 : _a.file) || err.id || 'unknown file').split(`?`);
        if (err.loc) {
            this.text('.file', `${file}:${err.loc.line}:${err.loc.column}`, links);
        }
        else if (err.id) {
            this.text('.file', file);
        }
        if (hasFrame) {
            this.text('.frame', err.frame.trim());
        }
        this.text('.stack', err.stack, links);
        this.root.querySelector('.window').addEventListener('click', (e) => {
            e.stopPropagation();
        });
        this.addEventListener('click', () => {
            this.close();
        });
        this.closeOnEsc = (e) => {
            if (e.key === 'Escape' || e.code === 'Escape') {
                this.close();
            }
        };
        document.addEventListener('keydown', this.closeOnEsc);
    }
    text(selector, text, linkFiles = false) {
        const el = this.root.querySelector(selector);
        if (!linkFiles) {
            el.textContent = text;
        }
        else {
            let curIndex = 0;
            let match;
            fileRE.lastIndex = 0;
            while ((match = fileRE.exec(text))) {
                const { 0: file, index } = match;
                if (index != null) {
                    const frag = text.slice(curIndex, index);
                    el.appendChild(document.createTextNode(frag));
                    const link = document.createElement('a');
                    link.textContent = file;
                    link.className = 'file-link';
                    link.onclick = () => {
                        fetch(`${base$1}__open-in-editor?file=` + encodeURIComponent(file));
                    };
                    el.appendChild(link);
                    curIndex += frag.length + file.length;
                }
            }
        }
    }
    close() {
        var _a;
        (_a = this.parentNode) === null || _a === void 0 ? void 0 : _a.removeChild(this);
        document.removeEventListener('keydown', this.closeOnEsc);
    }
}
const overlayId = 'vite-error-overlay';
const { customElements } = globalThis; // Ensure `customElements` is defined before the next line.
if (customElements && !customElements.get(overlayId)) {
    customElements.define(overlayId, ErrorOverlay);
}

console.debug('[vite] connecting...');
const importMetaUrl = new URL(import.meta.url);
// use server configuration, then fallback to inference
const serverHost = __SERVER_HOST__;
const socketProtocol = __HMR_PROTOCOL__ || (importMetaUrl.protocol === 'https:' ? 'wss' : 'ws');
const hmrPort = __HMR_PORT__;
const socketHost = `${__HMR_HOSTNAME__ || importMetaUrl.hostname}:${hmrPort || importMetaUrl.port}${__HMR_BASE__}`;
const directSocketHost = __HMR_DIRECT_TARGET__;
const base = __BASE__ || '/';
const wsToken = __WS_TOKEN__;
const messageBuffer = [];
let socket;
try {
    let fallback;
    // only use fallback when port is inferred to prevent confusion
    if (!hmrPort) {
        fallback = () => {
            // fallback to connecting directly to the hmr server
            // for servers which does not support proxying websocket
            socket = setupWebSocket(socketProtocol, directSocketHost, () => {
                const currentScriptHostURL = new URL(import.meta.url);
                const currentScriptHost = currentScriptHostURL.host +
                    currentScriptHostURL.pathname.replace(/@vite\/client$/, '');
                console.error('[vite] failed to connect to websocket.\n' +
                    'your current setup:\n' +
                    `  (browser) ${currentScriptHost} <--[HTTP]--> ${serverHost} (server)\n` +
                    `  (browser) ${socketHost} <--[WebSocket (failing)]--> ${directSocketHost} (server)\n` +
                    'Check out your Vite / network configuration and https://vitejs.dev/config/server-options.html#server-hmr .');
            });
            socket.addEventListener('open', () => {
                console.info('[vite] Direct websocket connection fallback. Check out https://vitejs.dev/config/server-options.html#server-hmr to remove the previous connection error.');
            }, { once: true });
        };
    }
    socket = setupWebSocket(socketProtocol, socketHost, fallback);
}
catch (error) {
    console.error(`[vite] failed to connect to websocket (${error}). `);
}
function setupWebSocket(protocol, hostAndPath, onCloseWithoutOpen) {
    const socket = new WebSocket(`${protocol}://${hostAndPath}?token=${wsToken}`, 'vite-hmr');
    let isOpened = false;
    socket.addEventListener('open', () => {
        isOpened = true;
        notifyListeners('vite:ws:connect', { webSocket: socket });
    }, { once: true });
    // Listen for messages
    socket.addEventListener('message', async ({ data }) => {
        handleMessage(JSON.parse(data));
    });
    // ping server
    socket.addEventListener('close', async ({ wasClean }) => {
        if (wasClean)
            return;
        if (!isOpened && onCloseWithoutOpen) {
            onCloseWithoutOpen();
            return;
        }
        notifyListeners('vite:ws:disconnect', { webSocket: socket });
        console.log(`[vite] server connection lost. polling for restart...`);
        await waitForSuccessfulPing(protocol, hostAndPath);
        location.reload();
    });
    return socket;
}
function warnFailedFetch(err, path) {
    if (!err.message.match('fetch')) {
        console.error(err);
    }
    console.error(`[hmr] Failed to reload ${path}. ` +
        `This could be due to syntax errors or importing non-existent ` +
        `modules. (see errors above)`);
}
function cleanUrl(pathname) {
    const url = new URL(pathname, location.toString());
    url.searchParams.delete('direct');
    return url.pathname + url.search;
}
let isFirstUpdate = true;
const outdatedLinkTags = new WeakSet();
const debounceReload = (time) => {
    let timer;
    return () => {
        if (timer) {
            clearTimeout(timer);
            timer = null;
        }
        timer = setTimeout(() => {
            location.reload();
        }, time);
    };
};
const pageReload = debounceReload(50);
async function handleMessage(payload) {
    switch (payload.type) {
        case 'connected':
            console.debug(`[vite] connected.`);
            sendMessageBuffer();
            // proxy(nginx, docker) hmr ws maybe caused timeout,
            // so send ping package let ws keep alive.
            setInterval(() => {
                if (socket.readyState === socket.OPEN) {
                    socket.send('{"type":"ping"}');
                }
            }, __HMR_TIMEOUT__);
            break;
        case 'update':
            notifyListeners('vite:beforeUpdate', payload);
            // if this is the first update and there's already an error overlay, it
            // means the page opened with existing server compile error and the whole
            // module script failed to load (since one of the nested imports is 500).
            // in this case a normal update won't work and a full reload is needed.
            if (isFirstUpdate && hasErrorOverlay()) {
                window.location.reload();
                return;
            }
            else {
                clearErrorOverlay();
                isFirstUpdate = false;
            }
            await Promise.all(payload.updates.map(async (update) => {
                if (update.type === 'js-update') {
                    return queueUpdate(fetchUpdate(update));
                }
                // css-update
                // this is only sent when a css file referenced with <link> is updated
                const { path, timestamp } = update;
                const searchUrl = cleanUrl(path);
                // can't use querySelector with `[href*=]` here since the link may be
                // using relative paths so we need to use link.href to grab the full
                // URL for the include check.
                const el = Array.from(document.querySelectorAll('link')).find((e) => !outdatedLinkTags.has(e) && cleanUrl(e.href).includes(searchUrl));
                if (!el) {
                    return;
                }
                const newPath = `${base}${searchUrl.slice(1)}${searchUrl.includes('?') ? '&' : '?'}t=${timestamp}`;
                // rather than swapping the href on the existing tag, we will
                // create a new link tag. Once the new stylesheet has loaded we
                // will remove the existing link tag. This removes a Flash Of
                // Unstyled Content that can occur when swapping out the tag href
                // directly, as the new stylesheet has not yet been loaded.
                return new Promise((resolve) => {
                    const newLinkTag = el.cloneNode();
                    newLinkTag.href = new URL(newPath, el.href).href;
                    const removeOldEl = () => {
                        el.remove();
                        console.debug(`[vite] css hot updated: ${searchUrl}`);
                        resolve();
                    };
                    newLinkTag.addEventListener('load', removeOldEl);
                    newLinkTag.addEventListener('error', removeOldEl);
                    outdatedLinkTags.add(el);
                    el.after(newLinkTag);
                });
            }));
            notifyListeners('vite:afterUpdate', payload);
            break;
        case 'custom': {
            notifyListeners(payload.event, payload.data);
            break;
        }
        case 'full-reload':
            notifyListeners('vite:beforeFullReload', payload);
            if (payload.path && payload.path.endsWith('.html')) {
                // if html file is edited, only reload the page if the browser is
                // currently on that page.
                const pagePath = decodeURI(location.pathname);
                const payloadPath = base + payload.path.slice(1);
                if (pagePath === payloadPath ||
                    payload.path === '/index.html' ||
                    (pagePath.endsWith('/') && pagePath + 'index.html' === payloadPath)) {
                    pageReload();
                }
                return;
            }
            else {
                pageReload();
            }
            break;
        case 'prune':
            notifyListeners('vite:beforePrune', payload);
            // After an HMR update, some modules are no longer imported on the page
            // but they may have left behind side effects that need to be cleaned up
            // (.e.g style injections)
            // TODO Trigger their dispose callbacks.
            payload.paths.forEach((path) => {
                const fn = pruneMap.get(path);
                if (fn) {
                    fn(dataMap.get(path));
                }
            });
            break;
        case 'error': {
            notifyListeners('vite:error', payload);
            const err = payload.err;
            if (enableOverlay) {
                createErrorOverlay(err);
            }
            else {
                console.error(`[vite] Internal Server Error\n${err.message}\n${err.stack}`);
            }
            break;
        }
        default: {
            const check = payload;
            return check;
        }
    }
}
function notifyListeners(event, data) {
    const cbs = customListenersMap.get(event);
    if (cbs) {
        cbs.forEach((cb) => cb(data));
    }
}
const enableOverlay = __HMR_ENABLE_OVERLAY__;
function createErrorOverlay(err) {
    if (!enableOverlay)
        return;
    clearErrorOverlay();
    document.body.appendChild(new ErrorOverlay(err));
}
function clearErrorOverlay() {
    document
        .querySelectorAll(overlayId)
        .forEach((n) => n.close());
}
function hasErrorOverlay() {
    return document.querySelectorAll(overlayId).length;
}
let pending = false;
let queued = [];
/**
 * buffer multiple hot updates triggered by the same src change
 * so that they are invoked in the same order they were sent.
 * (otherwise the order may be inconsistent because of the http request round trip)
 */
async function queueUpdate(p) {
    queued.push(p);
    if (!pending) {
        pending = true;
        await Promise.resolve();
        pending = false;
        const loading = [...queued];
        queued = [];
        (await Promise.all(loading)).forEach((fn) => fn && fn());
    }
}
async function waitForSuccessfulPing(socketProtocol, hostAndPath, ms = 1000) {
    const pingHostProtocol = socketProtocol === 'wss' ? 'https' : 'http';
    const ping = async () => {
        // A fetch on a websocket URL will return a successful promise with status 400,
        // but will reject a networking error.
        // When running on middleware mode, it returns status 426, and an cors error happens if mode is not no-cors
        try {
            await fetch(`${pingHostProtocol}://${hostAndPath}`, {
                mode: 'no-cors',
                headers: {
                    // Custom headers won't be included in a request with no-cors so (ab)use one of the
                    // safelisted headers to identify the ping request
                    Accept: 'text/x-vite-ping',
                },
            });
            return true;
        }
        catch { }
        return false;
    };
    if (await ping()) {
        return;
    }
    await wait(ms);
    // eslint-disable-next-line no-constant-condition
    while (true) {
        if (document.visibilityState === 'visible') {
            if (await ping()) {
                break;
            }
            await wait(ms);
        }
        else {
            await waitForWindowShow();
        }
    }
}
function wait(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
function waitForWindowShow() {
    return new Promise((resolve) => {
        const onChange = async () => {
            if (document.visibilityState === 'visible') {
                resolve();
                document.removeEventListener('visibilitychange', onChange);
            }
        };
        document.addEventListener('visibilitychange', onChange);
    });
}
const sheetsMap = new Map();
// collect existing style elements that may have been inserted during SSR
// to avoid FOUC or duplicate styles
if ('document' in globalThis) {
    document.querySelectorAll('style[data-vite-dev-id]').forEach((el) => {
        sheetsMap.set(el.getAttribute('data-vite-dev-id'), el);
    });
}
// all css imports should be inserted at the same position
// because after build it will be a single css file
let lastInsertedStyle;
function updateStyle(id, content) {
    let style = sheetsMap.get(id);
    if (!style) {
        style = document.createElement('style');
        style.setAttribute('type', 'text/css');
        style.setAttribute('data-vite-dev-id', id);
        style.textContent = content;
        if (!lastInsertedStyle) {
            document.head.appendChild(style);
            // reset lastInsertedStyle after async
            // because dynamically imported css will be splitted into a different file
            setTimeout(() => {
                lastInsertedStyle = undefined;
            }, 0);
        }
        else {
            lastInsertedStyle.insertAdjacentElement('afterend', style);
        }
        lastInsertedStyle = style;
    }
    else {
        style.textContent = content;
    }
    sheetsMap.set(id, style);
}
function removeStyle(id) {
    const style = sheetsMap.get(id);
    if (style) {
        document.head.removeChild(style);
        sheetsMap.delete(id);
    }
}
async function fetchUpdate({ path, acceptedPath, timestamp, explicitImportRequired, }) {
    const mod = hotModulesMap.get(path);
    if (!mod) {
        // In a code-splitting project,
        // it is common that the hot-updating module is not loaded yet.
        // https://github.com/vitejs/vite/issues/721
        return;
    }
    let fetchedModule;
    const isSelfUpdate = path === acceptedPath;
    // determine the qualified callbacks before we re-import the modules
    const qualifiedCallbacks = mod.callbacks.filter(({ deps }) => deps.includes(acceptedPath));
    if (isSelfUpdate || qualifiedCallbacks.length > 0) {
        const disposer = disposeMap.get(acceptedPath);
        if (disposer)
            await disposer(dataMap.get(acceptedPath));
        const [acceptedPathWithoutQuery, query] = acceptedPath.split(`?`);
        try {
            fetchedModule = await import(
            /* @vite-ignore */
            base +
                acceptedPathWithoutQuery.slice(1) +
                `?${explicitImportRequired ? 'import&' : ''}t=${timestamp}${query ? `&${query}` : ''}`);
        }
        catch (e) {
            warnFailedFetch(e, acceptedPath);
        }
    }
    return () => {
        for (const { deps, fn } of qualifiedCallbacks) {
            fn(deps.map((dep) => (dep === acceptedPath ? fetchedModule : undefined)));
        }
        const loggedPath = isSelfUpdate ? path : `${acceptedPath} via ${path}`;
        console.debug(`[vite] hot updated: ${loggedPath}`);
    };
}
function sendMessageBuffer() {
    if (socket.readyState === 1) {
        messageBuffer.forEach((msg) => socket.send(msg));
        messageBuffer.length = 0;
    }
}
const hotModulesMap = new Map();
const disposeMap = new Map();
const pruneMap = new Map();
const dataMap = new Map();
const customListenersMap = new Map();
const ctxToListenersMap = new Map();
function createHotContext(ownerPath) {
    if (!dataMap.has(ownerPath)) {
        dataMap.set(ownerPath, {});
    }
    // when a file is hot updated, a new context is created
    // clear its stale callbacks
    const mod = hotModulesMap.get(ownerPath);
    if (mod) {
        mod.callbacks = [];
    }
    // clear stale custom event listeners
    const staleListeners = ctxToListenersMap.get(ownerPath);
    if (staleListeners) {
        for (const [event, staleFns] of staleListeners) {
            const listeners = customListenersMap.get(event);
            if (listeners) {
                customListenersMap.set(event, listeners.filter((l) => !staleFns.includes(l)));
            }
        }
    }
    const newListeners = new Map();
    ctxToListenersMap.set(ownerPath, newListeners);
    function acceptDeps(deps, callback = () => { }) {
        const mod = hotModulesMap.get(ownerPath) || {
            id: ownerPath,
            callbacks: [],
        };
        mod.callbacks.push({
            deps,
            fn: callback,
        });
        hotModulesMap.set(ownerPath, mod);
    }
    const hot = {
        get data() {
            return dataMap.get(ownerPath);
        },
        accept(deps, callback) {
            if (typeof deps === 'function' || !deps) {
                // self-accept: hot.accept(() => {})
                acceptDeps([ownerPath], ([mod]) => deps === null || deps === void 0 ? void 0 : deps(mod));
            }
            else if (typeof deps === 'string') {
                // explicit deps
                acceptDeps([deps], ([mod]) => callback === null || callback === void 0 ? void 0 : callback(mod));
            }
            else if (Array.isArray(deps)) {
                acceptDeps(deps, callback);
            }
            else {
                throw new Error(`invalid hot.accept() usage.`);
            }
        },
        // export names (first arg) are irrelevant on the client side, they're
        // extracted in the server for propagation
        acceptExports(_, callback) {
            acceptDeps([ownerPath], ([mod]) => callback === null || callback === void 0 ? void 0 : callback(mod));
        },
        dispose(cb) {
            disposeMap.set(ownerPath, cb);
        },
        prune(cb) {
            pruneMap.set(ownerPath, cb);
        },
        // Kept for backward compatibility (#11036)
        // @ts-expect-error untyped
        // eslint-disable-next-line @typescript-eslint/no-empty-function
        decline() { },
        // tell the server to re-perform hmr propagation from this module as root
        invalidate(message) {
            notifyListeners('vite:invalidate', { path: ownerPath, message });
            this.send('vite:invalidate', { path: ownerPath, message });
            console.debug(`[vite] invalidate ${ownerPath}${message ? `: ${message}` : ''}`);
        },
        // custom events
        on(event, cb) {
            const addToMap = (map) => {
                const existing = map.get(event) || [];
                existing.push(cb);
                map.set(event, existing);
            };
            addToMap(customListenersMap);
            addToMap(newListeners);
        },
        send(event, data) {
            messageBuffer.push(JSON.stringify({ type: 'custom', event, data }));
            sendMessageBuffer();
        },
    };
    return hot;
}
/**
 * urls here are dynamic import() urls that couldn't be statically analyzed
 */
function injectQuery(url, queryToInject) {
    // skip urls that won't be handled by vite
    if (url[0] !== '.' && url[0] !== '/') {
        return url;
    }
    // can't use pathname from URL since it may be relative like ../
    const pathname = url.replace(/#.*$/, '').replace(/\?.*$/, '');
    const { search, hash } = new URL(url, 'http://vitejs.dev');
    return `${pathname}?${queryToInject}${search ? `&` + search.slice(1) : ''}${hash || ''}`;
}

export { ErrorOverlay, createHotContext, injectQuery, removeStyle, updateStyle };
//# sourceMappingURL=client.mjs.map
