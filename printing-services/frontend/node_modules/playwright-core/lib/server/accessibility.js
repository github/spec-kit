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
var accessibility_exports = {};
__export(accessibility_exports, {
  Accessibility: () => Accessibility
});
module.exports = __toCommonJS(accessibility_exports);
class Accessibility {
  constructor(getAXTree) {
    this._getAXTree = getAXTree;
  }
  async snapshot(options = {}) {
    const {
      interestingOnly = true,
      root = null
    } = options;
    const { tree, needle } = await this._getAXTree(root || void 0);
    if (!interestingOnly) {
      if (root)
        return needle && serializeTree(needle)[0];
      return serializeTree(tree)[0];
    }
    const interestingNodes = /* @__PURE__ */ new Set();
    collectInterestingNodes(interestingNodes, tree, false);
    if (root && (!needle || !interestingNodes.has(needle)))
      return null;
    return serializeTree(needle || tree, interestingNodes)[0];
  }
}
function collectInterestingNodes(collection, node, insideControl) {
  if (node.isInteresting(insideControl))
    collection.add(node);
  if (node.isLeafNode())
    return;
  insideControl = insideControl || node.isControl();
  for (const child of node.children())
    collectInterestingNodes(collection, child, insideControl);
}
function serializeTree(node, whitelistedNodes) {
  const children = [];
  for (const child of node.children())
    children.push(...serializeTree(child, whitelistedNodes));
  if (whitelistedNodes && !whitelistedNodes.has(node))
    return children;
  const serializedNode = node.serialize();
  if (children.length)
    serializedNode.children = children;
  return [serializedNode];
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  Accessibility
});
