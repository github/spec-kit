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
var bidiPage_exports = {};
__export(bidiPage_exports, {
  BidiPage: () => BidiPage,
  kPlaywrightBindingChannel: () => kPlaywrightBindingChannel
});
module.exports = __toCommonJS(bidiPage_exports);
var import_eventsHelper = require("../utils/eventsHelper");
var dialog = __toESM(require("../dialog"));
var dom = __toESM(require("../dom"));
var import_page = require("../page");
var import_bidiExecutionContext = require("./bidiExecutionContext");
var import_bidiInput = require("./bidiInput");
var import_bidiNetworkManager = require("./bidiNetworkManager");
var import_bidiPdf = require("./bidiPdf");
var bidi = __toESM(require("./third_party/bidiProtocol"));
const UTILITY_WORLD_NAME = "__playwright_utility_world__";
const kPlaywrightBindingChannel = "playwrightChannel";
class BidiPage {
  constructor(browserContext, bidiSession, opener) {
    this._sessionListeners = [];
    this._initScriptIds = /* @__PURE__ */ new Map();
    this._session = bidiSession;
    this._opener = opener;
    this.rawKeyboard = new import_bidiInput.RawKeyboardImpl(bidiSession);
    this.rawMouse = new import_bidiInput.RawMouseImpl(bidiSession);
    this.rawTouchscreen = new import_bidiInput.RawTouchscreenImpl(bidiSession);
    this._realmToContext = /* @__PURE__ */ new Map();
    this._page = new import_page.Page(this, browserContext);
    this._browserContext = browserContext;
    this._networkManager = new import_bidiNetworkManager.BidiNetworkManager(this._session, this._page);
    this._pdf = new import_bidiPdf.BidiPDF(this._session);
    this._page.on(import_page.Page.Events.FrameDetached, (frame) => this._removeContextsForFrame(frame, false));
    this._sessionListeners = [
      import_eventsHelper.eventsHelper.addEventListener(bidiSession, "script.realmCreated", this._onRealmCreated.bind(this)),
      import_eventsHelper.eventsHelper.addEventListener(bidiSession, "script.message", this._onScriptMessage.bind(this)),
      import_eventsHelper.eventsHelper.addEventListener(bidiSession, "browsingContext.contextDestroyed", this._onBrowsingContextDestroyed.bind(this)),
      import_eventsHelper.eventsHelper.addEventListener(bidiSession, "browsingContext.navigationStarted", this._onNavigationStarted.bind(this)),
      import_eventsHelper.eventsHelper.addEventListener(bidiSession, "browsingContext.navigationCommitted", this._onNavigationCommitted.bind(this)),
      import_eventsHelper.eventsHelper.addEventListener(bidiSession, "browsingContext.navigationAborted", this._onNavigationAborted.bind(this)),
      import_eventsHelper.eventsHelper.addEventListener(bidiSession, "browsingContext.navigationFailed", this._onNavigationFailed.bind(this)),
      import_eventsHelper.eventsHelper.addEventListener(bidiSession, "browsingContext.fragmentNavigated", this._onFragmentNavigated.bind(this)),
      import_eventsHelper.eventsHelper.addEventListener(bidiSession, "browsingContext.historyUpdated", this._onHistoryUpdated.bind(this)),
      import_eventsHelper.eventsHelper.addEventListener(bidiSession, "browsingContext.domContentLoaded", this._onDomContentLoaded.bind(this)),
      import_eventsHelper.eventsHelper.addEventListener(bidiSession, "browsingContext.load", this._onLoad.bind(this)),
      import_eventsHelper.eventsHelper.addEventListener(bidiSession, "browsingContext.userPromptOpened", this._onUserPromptOpened.bind(this)),
      import_eventsHelper.eventsHelper.addEventListener(bidiSession, "log.entryAdded", this._onLogEntryAdded.bind(this))
    ];
    this._initialize().then(
      () => this._page.reportAsNew(this._opener?._page),
      (error) => this._page.reportAsNew(this._opener?._page, error)
    );
  }
  async _initialize() {
    this._onFrameAttached(this._session.sessionId, null);
    await Promise.all([
      this.updateHttpCredentials(),
      this.updateRequestInterception()
      // If the page is created by the Playwright client's call, some initialization
      // may be pending. Wait for it to complete before reporting the page as new.
    ]);
  }
  didClose() {
    this._session.dispose();
    import_eventsHelper.eventsHelper.removeEventListeners(this._sessionListeners);
    this._page._didClose();
  }
  _onFrameAttached(frameId, parentFrameId) {
    return this._page.frameManager.frameAttached(frameId, parentFrameId);
  }
  _removeContextsForFrame(frame, notifyFrame) {
    for (const [contextId, context] of this._realmToContext) {
      if (context.frame === frame) {
        this._realmToContext.delete(contextId);
        if (notifyFrame)
          frame._contextDestroyed(context);
      }
    }
  }
  _onRealmCreated(realmInfo) {
    if (this._realmToContext.has(realmInfo.realm))
      return;
    if (realmInfo.type !== "window")
      return;
    const frame = this._page.frameManager.frame(realmInfo.context);
    if (!frame)
      return;
    let worldName;
    if (!realmInfo.sandbox) {
      worldName = "main";
      this._touchUtilityWorld(realmInfo.context);
    } else if (realmInfo.sandbox === UTILITY_WORLD_NAME) {
      worldName = "utility";
    } else {
      return;
    }
    const delegate = new import_bidiExecutionContext.BidiExecutionContext(this._session, realmInfo);
    const context = new dom.FrameExecutionContext(delegate, frame, worldName);
    frame._contextCreated(worldName, context);
    this._realmToContext.set(realmInfo.realm, context);
  }
  async _touchUtilityWorld(context) {
    await this._session.sendMayFail("script.evaluate", {
      expression: "1 + 1",
      target: {
        context,
        sandbox: UTILITY_WORLD_NAME
      },
      serializationOptions: {
        maxObjectDepth: 10,
        maxDomDepth: 10
      },
      awaitPromise: true,
      userActivation: true
    });
  }
  _onRealmDestroyed(params) {
    const context = this._realmToContext.get(params.realm);
    if (!context)
      return false;
    this._realmToContext.delete(params.realm);
    context.frame._contextDestroyed(context);
    return true;
  }
  // TODO: route the message directly to the browser
  _onBrowsingContextDestroyed(params) {
    this._browserContext._browser._onBrowsingContextDestroyed(params);
  }
  _onNavigationStarted(params) {
    const frameId = params.context;
    this._page.frameManager.frameRequestedNavigation(frameId, params.navigation);
  }
  _onNavigationCommitted(params) {
    const frameId = params.context;
    this._page.frameManager.frameCommittedNewDocumentNavigation(
      frameId,
      params.url,
      "",
      params.navigation,
      /* initial */
      false
    );
  }
  _onDomContentLoaded(params) {
    const frameId = params.context;
    this._page.frameManager.frameLifecycleEvent(frameId, "domcontentloaded");
  }
  _onLoad(params) {
    this._page.frameManager.frameLifecycleEvent(params.context, "load");
  }
  _onNavigationAborted(params) {
    this._page.frameManager.frameAbortedNavigation(params.context, "Navigation aborted", params.navigation || void 0);
  }
  _onNavigationFailed(params) {
    this._page.frameManager.frameAbortedNavigation(params.context, "Navigation failed", params.navigation || void 0);
  }
  _onFragmentNavigated(params) {
    this._page.frameManager.frameCommittedSameDocumentNavigation(params.context, params.url);
  }
  _onHistoryUpdated(params) {
    this._page.frameManager.frameCommittedSameDocumentNavigation(params.context, params.url);
  }
  _onUserPromptOpened(event) {
    this._page.browserContext.dialogManager.dialogDidOpen(new dialog.Dialog(
      this._page,
      event.type,
      event.message,
      async (accept, userText) => {
        await this._session.send("browsingContext.handleUserPrompt", { context: event.context, accept, userText });
      },
      event.defaultValue
    ));
  }
  _onLogEntryAdded(params) {
    if (params.type !== "console")
      return;
    const entry = params;
    const context = this._realmToContext.get(params.source.realm);
    if (!context)
      return;
    const callFrame = params.stackTrace?.callFrames[0];
    const location = callFrame ?? { url: "", lineNumber: 1, columnNumber: 1 };
    this._page.addConsoleMessage(entry.method, entry.args.map((arg) => (0, import_bidiExecutionContext.createHandle)(context, arg)), location, params.text || void 0);
  }
  async navigateFrame(frame, url, referrer) {
    const { navigation } = await this._session.send("browsingContext.navigate", {
      context: frame._id,
      url
    });
    return { newDocumentId: navigation || void 0 };
  }
  async updateExtraHTTPHeaders() {
  }
  async updateEmulateMedia() {
  }
  async updateUserAgent() {
  }
  async bringToFront() {
    await this._session.send("browsingContext.activate", {
      context: this._session.sessionId
    });
  }
  async updateEmulatedViewportSize() {
    const options = this._browserContext._options;
    const emulatedSize = this._page.emulatedSize();
    if (!emulatedSize)
      return;
    const viewportSize = emulatedSize.viewport;
    await this._session.send("browsingContext.setViewport", {
      context: this._session.sessionId,
      viewport: {
        width: viewportSize.width,
        height: viewportSize.height
      },
      devicePixelRatio: options.deviceScaleFactor || 1
    });
  }
  async updateRequestInterception() {
    await this._networkManager.setRequestInterception(this._page.needsRequestInterception());
  }
  async updateOffline() {
  }
  async updateHttpCredentials() {
    await this._networkManager.setCredentials(this._browserContext._options.httpCredentials);
  }
  async updateFileChooserInterception() {
  }
  async reload() {
    await this._session.send("browsingContext.reload", {
      context: this._session.sessionId,
      // ignoreCache: true,
      wait: bidi.BrowsingContext.ReadinessState.Interactive
    });
  }
  async goBack() {
    return await this._session.send("browsingContext.traverseHistory", {
      context: this._session.sessionId,
      delta: -1
    }).then(() => true).catch(() => false);
  }
  async goForward() {
    return await this._session.send("browsingContext.traverseHistory", {
      context: this._session.sessionId,
      delta: 1
    }).then(() => true).catch(() => false);
  }
  async requestGC() {
    throw new Error("Method not implemented.");
  }
  async _onScriptMessage(event) {
    if (event.channel !== kPlaywrightBindingChannel)
      return;
    const pageOrError = await this._page.waitForInitializedOrError();
    if (pageOrError instanceof Error)
      return;
    const context = this._realmToContext.get(event.source.realm);
    if (!context)
      return;
    if (event.data.type !== "string")
      return;
    await this._page.onBindingCalled(event.data.value, context);
  }
  async addInitScript(initScript) {
    const { script } = await this._session.send("script.addPreloadScript", {
      // TODO: remove function call from the source.
      functionDeclaration: `() => { return ${initScript.source} }`,
      // TODO: push to iframes?
      contexts: [this._session.sessionId]
    });
    this._initScriptIds.set(initScript, script);
  }
  async removeInitScripts(initScripts) {
    const ids = [];
    for (const script of initScripts) {
      const id = this._initScriptIds.get(script);
      if (id)
        ids.push(id);
      this._initScriptIds.delete(script);
    }
    await Promise.all(ids.map((script) => this._session.send("script.removePreloadScript", { script })));
  }
  async closePage(runBeforeUnload) {
    await this._session.send("browsingContext.close", {
      context: this._session.sessionId,
      promptUnload: runBeforeUnload
    });
  }
  async setBackgroundColor(color) {
  }
  async takeScreenshot(progress, format, documentRect, viewportRect, quality, fitsViewport, scale) {
    const rect = documentRect || viewportRect;
    const { data } = await progress.race(this._session.send("browsingContext.captureScreenshot", {
      context: this._session.sessionId,
      format: {
        type: `image/${format === "png" ? "png" : "jpeg"}`,
        quality: quality ? quality / 100 : 0.8
      },
      origin: documentRect ? "document" : "viewport",
      clip: {
        type: "box",
        ...rect
      }
    }));
    return Buffer.from(data, "base64");
  }
  async getContentFrame(handle) {
    const executionContext = toBidiExecutionContext(handle._context);
    const frameId = await executionContext.contentFrameIdForFrame(handle);
    if (!frameId)
      return null;
    return this._page.frameManager.frame(frameId);
  }
  async getOwnerFrame(handle) {
    const windowHandle = await handle.evaluateHandle((node) => {
      const doc = node.ownerDocument ?? node;
      return doc.defaultView;
    });
    if (!windowHandle)
      return null;
    const executionContext = toBidiExecutionContext(handle._context);
    return executionContext.frameIdForWindowHandle(windowHandle);
  }
  async getBoundingBox(handle) {
    const box = await handle.evaluate((element) => {
      if (!(element instanceof Element))
        return null;
      const rect = element.getBoundingClientRect();
      return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
    });
    if (!box)
      return null;
    const position = await this._framePosition(handle._frame);
    if (!position)
      return null;
    box.x += position.x;
    box.y += position.y;
    return box;
  }
  // TODO: move to Frame.
  async _framePosition(frame) {
    if (frame === this._page.mainFrame())
      return { x: 0, y: 0 };
    const element = await frame.frameElement();
    const box = await element.boundingBox();
    if (!box)
      return null;
    const style = await element.evaluateInUtility(([injected, iframe]) => injected.describeIFrameStyle(iframe), {}).catch((e) => "error:notconnected");
    if (style === "error:notconnected" || style === "transformed")
      return null;
    box.x += style.left;
    box.y += style.top;
    return box;
  }
  async scrollRectIntoViewIfNeeded(handle, rect) {
    return await handle.evaluateInUtility(([injected, node]) => {
      node.scrollIntoView({
        block: "center",
        inline: "center",
        behavior: "instant"
      });
    }, null).then(() => "done").catch((e) => {
      if (e instanceof Error && e.message.includes("Node is detached from document"))
        return "error:notconnected";
      if (e instanceof Error && e.message.includes("Node does not have a layout object"))
        return "error:notvisible";
      throw e;
    });
  }
  async setScreencastOptions(options) {
  }
  rafCountForStablePosition() {
    return 1;
  }
  async getContentQuads(handle) {
    const quads = await handle.evaluateInUtility(([injected, node]) => {
      if (!node.isConnected)
        return "error:notconnected";
      const rects = node.getClientRects();
      if (!rects)
        return null;
      return [...rects].map((rect) => [
        { x: rect.left, y: rect.top },
        { x: rect.right, y: rect.top },
        { x: rect.right, y: rect.bottom },
        { x: rect.left, y: rect.bottom }
      ]);
    }, null);
    if (!quads || quads === "error:notconnected")
      return quads;
    const position = await this._framePosition(handle._frame);
    if (!position)
      return null;
    quads.forEach((quad) => quad.forEach((point) => {
      point.x += position.x;
      point.y += position.y;
    }));
    return quads;
  }
  async setInputFilePaths(handle, paths) {
    const fromContext = toBidiExecutionContext(handle._context);
    await this._session.send("input.setFiles", {
      context: this._session.sessionId,
      element: await fromContext.nodeIdForElementHandle(handle),
      files: paths
    });
  }
  async adoptElementHandle(handle, to) {
    const fromContext = toBidiExecutionContext(handle._context);
    const nodeId = await fromContext.nodeIdForElementHandle(handle);
    const executionContext = toBidiExecutionContext(to);
    return await executionContext.remoteObjectForNodeId(to, nodeId);
  }
  async getAccessibilityTree(needle) {
    throw new Error("Method not implemented.");
  }
  async inputActionEpilogue() {
  }
  async resetForReuse(progress) {
  }
  async pdf(options) {
    return this._pdf.generate(options);
  }
  async getFrameElement(frame) {
    const parent = frame.parentFrame();
    if (!parent)
      throw new Error("Frame has been detached.");
    const parentContext = await parent._mainContext();
    const list = await parentContext.evaluateHandle(() => {
      return [...document.querySelectorAll("iframe,frame")];
    });
    const length = await list.evaluate((list2) => list2.length);
    let foundElement = null;
    for (let i = 0; i < length; i++) {
      const element = await list.evaluateHandle((list2, i2) => list2[i2], i);
      const candidate = await element.contentFrame();
      if (frame === candidate) {
        foundElement = element;
        break;
      } else {
        element.dispose();
      }
    }
    list.dispose();
    if (!foundElement)
      throw new Error("Frame has been detached.");
    return foundElement;
  }
  shouldToggleStyleSheetToSyncAnimations() {
    return true;
  }
}
function toBidiExecutionContext(executionContext) {
  return executionContext.delegate;
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  BidiPage,
  kPlaywrightBindingChannel
});
