"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);
var bidiBrowser_exports = {};
__export(bidiBrowser_exports, {
  BidiBrowser: () => BidiBrowser,
  BidiBrowserContext: () => BidiBrowserContext,
  Network: () => Network
});
module.exports = __toCommonJS(bidiBrowser_exports);
var import_eventsHelper = require("../utils/eventsHelper");
var import_browser = require("../browser");
var import_browserContext = require("../browserContext");
var network = __toESM(require("../network"));
var import_bidiConnection = require("./bidiConnection");
var import_bidiNetworkManager = require("./bidiNetworkManager");
var import_bidiPage = require("./bidiPage");
var import_page = require("../page");
var bidi = __toESM(require("./third_party/bidiProtocol"));
class BidiBrowser extends import_browser.Browser {
  constructor(parent, transport, options) {
    super(parent, options);
    this._contexts = /* @__PURE__ */ new Map();
    this._bidiPages = /* @__PURE__ */ new Map();
    this._connection = new import_bidiConnection.BidiConnection(transport, this._onDisconnect.bind(this), options.protocolLogger, options.browserLogsCollector);
    this._browserSession = this._connection.browserSession;
    this._eventListeners = [
      import_eventsHelper.eventsHelper.addEventListener(this._browserSession, "browsingContext.contextCreated", this._onBrowsingContextCreated.bind(this)),
      import_eventsHelper.eventsHelper.addEventListener(this._browserSession, "script.realmDestroyed", this._onScriptRealmDestroyed.bind(this))
    ];
  }
  static async connect(parent, transport, options) {
    const browser = new BidiBrowser(parent, transport, options);
    if (options.__testHookOnConnectToBrowser)
      await options.__testHookOnConnectToBrowser();
    browser._bidiSessionInfo = await browser._browserSession.send("session.new", {
      capabilities: {
        alwaysMatch: {
          acceptInsecureCerts: options.persistent?.internalIgnoreHTTPSErrors || options.persistent?.ignoreHTTPSErrors,
          proxy: getProxyConfiguration(options.originalLaunchOptions.proxyOverride ?? options.proxy),
          unhandledPromptBehavior: {
            default: bidi.Session.UserPromptHandlerType.Ignore
          },
          webSocketUrl: true
        }
      }
    });
    await browser._browserSession.send("session.subscribe", {
      events: [
        "browsingContext",
        "network",
        "log",
        "script"
      ]
    });
    if (options.persistent) {
      const context = new BidiBrowserContext(browser, void 0, options.persistent);
      browser._defaultContext = context;
      await context._initialize();
      const page = await browser._defaultContext.doCreateNewPage();
      await page.waitForInitializedOrError();
    }
    return browser;
  }
  _onDisconnect() {
    this._didClose();
  }
  async doCreateNewContext(options) {
    const proxy = options.proxyOverride || options.proxy;
    const { userContext } = await this._browserSession.send("browser.createUserContext", {
      acceptInsecureCerts: options.internalIgnoreHTTPSErrors || options.ignoreHTTPSErrors,
      proxy: getProxyConfiguration(proxy)
    });
    const context = new BidiBrowserContext(this, userContext, options);
    await context._initialize();
    this._contexts.set(userContext, context);
    return context;
  }
  contexts() {
    return Array.from(this._contexts.values());
  }
  version() {
    return this._bidiSessionInfo.capabilities.browserVersion;
  }
  userAgent() {
    return this._bidiSessionInfo.capabilities.userAgent;
  }
  isConnected() {
    return !this._connection.isClosed();
  }
  _onBrowsingContextCreated(event) {
    if (event.parent) {
      const parentFrameId = event.parent;
      for (const page2 of this._bidiPages.values()) {
        const parentFrame = page2._page.frameManager.frame(parentFrameId);
        if (!parentFrame)
          continue;
        page2._session.addFrameBrowsingContext(event.context);
        page2._page.frameManager.frameAttached(event.context, parentFrameId);
        const frame = page2._page.frameManager.frame(event.context);
        if (frame)
          frame._url = event.url;
        return;
      }
      return;
    }
    let context = this._contexts.get(event.userContext);
    if (!context)
      context = this._defaultContext;
    if (!context)
      return;
    const session = this._connection.createMainFrameBrowsingContextSession(event.context);
    const opener = event.originalOpener && this._bidiPages.get(event.originalOpener);
    const page = new import_bidiPage.BidiPage(context, session, opener || null);
    page._page.mainFrame()._url = event.url;
    this._bidiPages.set(event.context, page);
  }
  _onBrowsingContextDestroyed(event) {
    if (event.parent) {
      this._browserSession.removeFrameBrowsingContext(event.context);
      const parentFrameId = event.parent;
      for (const page of this._bidiPages.values()) {
        const parentFrame = page._page.frameManager.frame(parentFrameId);
        if (!parentFrame)
          continue;
        page._page.frameManager.frameDetached(event.context);
        return;
      }
      return;
    }
    const bidiPage = this._bidiPages.get(event.context);
    if (!bidiPage)
      return;
    bidiPage.didClose();
    this._bidiPages.delete(event.context);
  }
  _onScriptRealmDestroyed(event) {
    for (const page of this._bidiPages.values()) {
      if (page._onRealmDestroyed(event))
        return;
    }
  }
}
class BidiBrowserContext extends import_browserContext.BrowserContext {
  constructor(browser, browserContextId, options) {
    super(browser, options, browserContextId);
    this._originToPermissions = /* @__PURE__ */ new Map();
    this._initScriptIds = /* @__PURE__ */ new Map();
    this._authenticateProxyViaHeader();
  }
  _bidiPages() {
    return [...this._browser._bidiPages.values()].filter((bidiPage) => bidiPage._browserContext === this);
  }
  async _initialize() {
    const promises = [
      super._initialize()
    ];
    promises.push(this.doUpdateDefaultViewport());
    if (this._options.geolocation)
      promises.push(this.setGeolocation(this._options.geolocation));
    if (this._options.locale) {
      promises.push(this._browser._browserSession.send("emulation.setLocaleOverride", {
        locale: this._options.locale,
        userContexts: [this._userContextId()]
      }));
    }
    await Promise.all(promises);
  }
  possiblyUninitializedPages() {
    return this._bidiPages().map((bidiPage) => bidiPage._page);
  }
  async doCreateNewPage() {
    const { context } = await this._browser._browserSession.send("browsingContext.create", {
      type: bidi.BrowsingContext.CreateType.Window,
      userContext: this._browserContextId
    });
    return this._browser._bidiPages.get(context)._page;
  }
  async doGetCookies(urls) {
    const { cookies } = await this._browser._browserSession.send(
      "storage.getCookies",
      { partition: { type: "storageKey", userContext: this._browserContextId } }
    );
    return network.filterCookies(cookies.map((c) => {
      const copy = {
        name: c.name,
        value: (0, import_bidiNetworkManager.bidiBytesValueToString)(c.value),
        domain: c.domain,
        path: c.path,
        httpOnly: c.httpOnly,
        secure: c.secure,
        expires: c.expiry ?? -1,
        sameSite: c.sameSite ? fromBidiSameSite(c.sameSite) : "None"
      };
      return copy;
    }), urls);
  }
  async addCookies(cookies) {
    cookies = network.rewriteCookies(cookies);
    const promises = cookies.map((c) => {
      const cookie = {
        name: c.name,
        value: { type: "string", value: c.value },
        domain: c.domain,
        path: c.path,
        httpOnly: c.httpOnly,
        secure: c.secure,
        sameSite: c.sameSite && toBidiSameSite(c.sameSite),
        expiry: c.expires === -1 || c.expires === void 0 ? void 0 : Math.round(c.expires)
      };
      return this._browser._browserSession.send(
        "storage.setCookie",
        { cookie, partition: { type: "storageKey", userContext: this._browserContextId } }
      );
    });
    await Promise.all(promises);
  }
  async doClearCookies() {
    await this._browser._browserSession.send(
      "storage.deleteCookies",
      { partition: { type: "storageKey", userContext: this._browserContextId } }
    );
  }
  async doGrantPermissions(origin, permissions) {
    const currentPermissions = this._originToPermissions.get(origin) || [];
    const toGrant = permissions.filter((permission) => !currentPermissions.includes(permission));
    this._originToPermissions.set(origin, [...currentPermissions, ...toGrant]);
    await Promise.all(toGrant.map((permission) => this._setPermission(origin, permission, bidi.Permissions.PermissionState.Granted)));
  }
  async doClearPermissions() {
    const currentPermissions = [...this._originToPermissions.entries()];
    this._originToPermissions = /* @__PURE__ */ new Map();
    await Promise.all(currentPermissions.map(([origin, permissions]) => permissions.map(
      (p) => this._setPermission(origin, p, bidi.Permissions.PermissionState.Prompt)
    )));
  }
  async _setPermission(origin, permission, state) {
    await this._browser._browserSession.send("permissions.setPermission", {
      descriptor: {
        name: permission
      },
      state,
      origin,
      userContext: this._userContextId()
    });
  }
  async setGeolocation(geolocation) {
    (0, import_browserContext.verifyGeolocation)(geolocation);
    this._options.geolocation = geolocation;
    await this._browser._browserSession.send("emulation.setGeolocationOverride", {
      coordinates: geolocation ? {
        latitude: geolocation.latitude,
        longitude: geolocation.longitude,
        accuracy: geolocation.accuracy
      } : null,
      userContexts: [this._userContextId()]
    });
  }
  async doUpdateExtraHTTPHeaders() {
  }
  async setUserAgent(userAgent) {
  }
  async doUpdateOffline() {
  }
  async doSetHTTPCredentials(httpCredentials) {
    this._options.httpCredentials = httpCredentials;
    for (const page of this.pages())
      await page.delegate.updateHttpCredentials();
  }
  async doAddInitScript(initScript) {
    const { script } = await this._browser._browserSession.send("script.addPreloadScript", {
      // TODO: remove function call from the source.
      functionDeclaration: `() => { return ${initScript.source} }`,
      userContexts: [this._userContextId()]
    });
    this._initScriptIds.set(initScript, script);
  }
  async doRemoveInitScripts(initScripts) {
    const ids = [];
    for (const script of initScripts) {
      const id = this._initScriptIds.get(script);
      if (id)
        ids.push(id);
      this._initScriptIds.delete(script);
    }
    await Promise.all(ids.map((script) => this._browser._browserSession.send("script.removePreloadScript", { script })));
  }
  async doUpdateRequestInterception() {
  }
  async doUpdateDefaultViewport() {
    if (!this._options.viewport)
      return;
    await this._browser._browserSession.send("browsingContext.setViewport", {
      viewport: {
        width: this._options.viewport.width,
        height: this._options.viewport.height
      },
      devicePixelRatio: this._options.deviceScaleFactor || 1,
      userContexts: [this._userContextId()]
    });
  }
  async doUpdateDefaultEmulatedMedia() {
  }
  async doExposePlaywrightBinding() {
    const args = [{
      type: "channel",
      value: {
        channel: import_bidiPage.kPlaywrightBindingChannel,
        ownership: bidi.Script.ResultOwnership.Root
      }
    }];
    const functionDeclaration = `function addMainBinding(callback) { globalThis['${import_page.PageBinding.kBindingName}'] = callback; }`;
    const promises = [];
    promises.push(this._browser._browserSession.send("script.addPreloadScript", {
      functionDeclaration,
      arguments: args,
      userContexts: [this._userContextId()]
    }));
    promises.push(...this._bidiPages().map((page) => {
      const realms = [...page._realmToContext].filter(([realm, context]) => context.world === "main").map(([realm, context]) => realm);
      return Promise.all(realms.map((realm) => {
        return page._session.send("script.callFunction", {
          functionDeclaration,
          arguments: args,
          target: { realm },
          awaitPromise: false,
          userActivation: false
        });
      }));
    }));
    await Promise.all(promises);
  }
  onClosePersistent() {
  }
  async clearCache() {
  }
  async doClose(reason) {
    if (!this._browserContextId) {
      await this._browser.close({ reason });
      return;
    }
    await this._browser._browserSession.send("browser.removeUserContext", {
      userContext: this._browserContextId
    });
    this._browser._contexts.delete(this._browserContextId);
  }
  async cancelDownload(uuid) {
  }
  _userContextId() {
    if (this._browserContextId)
      return this._browserContextId;
    return "default";
  }
}
function fromBidiSameSite(sameSite) {
  switch (sameSite) {
    case "strict":
      return "Strict";
    case "lax":
      return "Lax";
    case "none":
      return "None";
  }
  return "None";
}
function toBidiSameSite(sameSite) {
  switch (sameSite) {
    case "Strict":
      return bidi.Network.SameSite.Strict;
    case "Lax":
      return bidi.Network.SameSite.Lax;
    case "None":
      return bidi.Network.SameSite.None;
  }
  return bidi.Network.SameSite.None;
}
function getProxyConfiguration(proxySettings) {
  if (!proxySettings)
    return void 0;
  const proxy = {
    proxyType: "manual"
  };
  const url = new URL(proxySettings.server);
  switch (url.protocol) {
    case "http:":
      proxy.httpProxy = url.host;
      break;
    case "https:":
      proxy.sslProxy = url.host;
      break;
    case "socks4:":
      proxy.socksProxy = url.host;
      proxy.socksVersion = 4;
      break;
    case "socks5:":
      proxy.socksProxy = url.host;
      proxy.socksVersion = 5;
      break;
    default:
      throw new Error("Invalid proxy server protocol: " + proxySettings.server);
  }
  const bypass = proxySettings.bypass ?? process.env.PLAYWRIGHT_PROXY_BYPASS_FOR_TESTING;
  if (bypass)
    proxy.noProxy = bypass.split(",");
  return proxy;
}
var Network;
((Network2) => {
  let SameSite;
  ((SameSite2) => {
    SameSite2["Strict"] = "strict";
    SameSite2["Lax"] = "lax";
    SameSite2["None"] = "none";
  })(SameSite = Network2.SameSite || (Network2.SameSite = {}));
})(Network || (Network = {}));
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  BidiBrowser,
  BidiBrowserContext,
  Network
});
