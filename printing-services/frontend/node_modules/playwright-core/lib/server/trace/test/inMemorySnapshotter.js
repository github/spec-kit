"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
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
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);
var inMemorySnapshotter_exports = {};
__export(inMemorySnapshotter_exports, {
  InMemorySnapshotter: () => InMemorySnapshotter
});
module.exports = __toCommonJS(inMemorySnapshotter_exports);
var import_snapshotStorage = require("../../../../../trace-viewer/src/sw/snapshotStorage");
var import_utils = require("../../../utils");
var import_harTracer = require("../../har/harTracer");
var import_snapshotter = require("../recorder/snapshotter");
class InMemorySnapshotter {
  constructor(context) {
    this._blobs = /* @__PURE__ */ new Map();
    this._snapshotReadyPromises = /* @__PURE__ */ new Map();
    this._snapshotCount = 0;
    this._snapshotter = new import_snapshotter.Snapshotter(context, this);
    this._harTracer = new import_harTracer.HarTracer(context, null, this, { content: "attach", includeTraceInfo: true, recordRequestOverrides: false, waitForContentOnStop: false });
    this._storage = new import_snapshotStorage.SnapshotStorage();
  }
  async initialize() {
    await this._snapshotter.start();
    this._harTracer.start({ omitScripts: true });
  }
  async reset() {
    await this._snapshotter.reset();
    await this._harTracer.flush();
    this._harTracer.stop();
    this._harTracer.start({ omitScripts: true });
  }
  async dispose() {
    this._snapshotter.dispose();
    await this._harTracer.flush();
    this._harTracer.stop();
  }
  async captureSnapshot(page, callId, snapshotName) {
    if (this._snapshotReadyPromises.has(snapshotName))
      throw new Error("Duplicate snapshot name: " + snapshotName);
    this._snapshotter.captureSnapshot(page, callId, snapshotName).catch(() => {
    });
    const promise = new import_utils.ManualPromise();
    this._snapshotReadyPromises.set(snapshotName, promise);
    return promise;
  }
  onEntryStarted(entry) {
  }
  onEntryFinished(entry) {
    this._storage.addResource("", entry);
  }
  onContentBlob(sha1, buffer) {
    this._blobs.set(sha1, buffer);
  }
  onSnapshotterBlob(blob) {
    this._blobs.set(blob.sha1, blob.buffer);
  }
  onFrameSnapshot(snapshot) {
    ++this._snapshotCount;
    const renderer = this._storage.addFrameSnapshot("", snapshot, []);
    this._snapshotReadyPromises.get(snapshot.snapshotName || "")?.resolve(renderer);
  }
  async resourceContentForTest(sha1) {
    return this._blobs.get(sha1);
  }
  snapshotCount() {
    return this._snapshotCount;
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  InMemorySnapshotter
});
