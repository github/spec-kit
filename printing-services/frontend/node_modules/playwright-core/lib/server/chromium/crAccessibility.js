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
var crAccessibility_exports = {};
__export(crAccessibility_exports, {
  getAccessibilityTree: () => getAccessibilityTree
});
module.exports = __toCommonJS(crAccessibility_exports);
async function getAccessibilityTree(client, needle) {
  const { nodes } = await client.send("Accessibility.getFullAXTree");
  const tree = CRAXNode.createTree(client, nodes);
  return {
    tree,
    needle: needle ? await tree._findElement(needle) : null
  };
}
class CRAXNode {
  constructor(client, payload) {
    this._children = [];
    this._richlyEditable = false;
    this._editable = false;
    this._focusable = false;
    this._expanded = false;
    this._hidden = false;
    this._client = client;
    this._payload = payload;
    this._name = this._payload.name ? this._payload.name.value : "";
    this._role = this._payload.role ? this._payload.role.value : "Unknown";
    for (const property of this._payload.properties || []) {
      if (property.name === "editable") {
        this._richlyEditable = property.value.value === "richtext";
        this._editable = true;
      }
      if (property.name === "focusable")
        this._focusable = property.value.value;
      if (property.name === "expanded")
        this._expanded = property.value.value;
      if (property.name === "hidden")
        this._hidden = property.value.value;
    }
  }
  _isPlainTextField() {
    if (this._richlyEditable)
      return false;
    if (this._editable)
      return true;
    return this._role === "textbox" || this._role === "ComboBox" || this._role === "searchbox";
  }
  _isTextOnlyObject() {
    const role = this._role;
    return role === "LineBreak" || role === "text" || role === "InlineTextBox" || role === "StaticText";
  }
  _hasFocusableChild() {
    if (this._cachedHasFocusableChild === void 0) {
      this._cachedHasFocusableChild = false;
      for (const child of this._children) {
        if (child._focusable || child._hasFocusableChild()) {
          this._cachedHasFocusableChild = true;
          break;
        }
      }
    }
    return this._cachedHasFocusableChild;
  }
  children() {
    return this._children;
  }
  async _findElement(element) {
    const objectId = element._objectId;
    const { node: { backendNodeId } } = await this._client.send("DOM.describeNode", { objectId });
    const needle = this.find((node) => node._payload.backendDOMNodeId === backendNodeId);
    return needle || null;
  }
  find(predicate) {
    if (predicate(this))
      return this;
    for (const child of this._children) {
      const result = child.find(predicate);
      if (result)
        return result;
    }
    return null;
  }
  isLeafNode() {
    if (!this._children.length)
      return true;
    if (this._isPlainTextField() || this._isTextOnlyObject())
      return true;
    switch (this._role) {
      case "doc-cover":
      case "graphics-symbol":
      case "img":
      case "Meter":
      case "scrollbar":
      case "slider":
      case "separator":
      case "progressbar":
        return true;
      default:
        break;
    }
    if (this._hasFocusableChild())
      return false;
    if (this._focusable && this._role !== "WebArea" && this._role !== "RootWebArea" && this._name)
      return true;
    if (this._role === "heading" && this._name)
      return true;
    return false;
  }
  isControl() {
    switch (this._role) {
      case "button":
      case "checkbox":
      case "ColorWell":
      case "combobox":
      case "DisclosureTriangle":
      case "listbox":
      case "menu":
      case "menubar":
      case "menuitem":
      case "menuitemcheckbox":
      case "menuitemradio":
      case "radio":
      case "scrollbar":
      case "searchbox":
      case "slider":
      case "spinbutton":
      case "switch":
      case "tab":
      case "textbox":
      case "tree":
        return true;
      default:
        return false;
    }
  }
  isInteresting(insideControl) {
    const role = this._role;
    if (role === "Ignored" || this._hidden)
      return false;
    if (this._focusable || this._richlyEditable)
      return true;
    if (this.isControl())
      return true;
    if (insideControl)
      return false;
    return this.isLeafNode() && !!this._name;
  }
  normalizedRole() {
    switch (this._role) {
      case "RootWebArea":
        return "WebArea";
      case "StaticText":
        return "text";
      default:
        return this._role;
    }
  }
  serialize() {
    const properties = /* @__PURE__ */ new Map();
    for (const property of this._payload.properties || [])
      properties.set(property.name.toLowerCase(), property.value.value);
    if (this._payload.description)
      properties.set("description", this._payload.description.value);
    const node = {
      role: this.normalizedRole(),
      name: this._payload.name ? this._payload.name.value || "" : ""
    };
    const userStringProperties = [
      "description",
      "keyshortcuts",
      "roledescription",
      "valuetext"
    ];
    for (const userStringProperty of userStringProperties) {
      if (!properties.has(userStringProperty))
        continue;
      node[userStringProperty] = properties.get(userStringProperty);
    }
    const booleanProperties = [
      "disabled",
      "expanded",
      "focused",
      "modal",
      "multiline",
      "multiselectable",
      "readonly",
      "required",
      "selected"
    ];
    for (const booleanProperty of booleanProperties) {
      if (booleanProperty === "focused" && (this._role === "WebArea" || this._role === "RootWebArea"))
        continue;
      const value = properties.get(booleanProperty);
      if (!value)
        continue;
      node[booleanProperty] = value;
    }
    const numericalProperties = [
      "level",
      "valuemax",
      "valuemin"
    ];
    for (const numericalProperty of numericalProperties) {
      if (!properties.has(numericalProperty))
        continue;
      node[numericalProperty] = properties.get(numericalProperty);
    }
    const tokenProperties = [
      "autocomplete",
      "haspopup",
      "invalid",
      "orientation"
    ];
    for (const tokenProperty of tokenProperties) {
      const value = properties.get(tokenProperty);
      if (!value || value === "false")
        continue;
      node[tokenProperty] = value;
    }
    const axNode = node;
    if (this._payload.value) {
      if (typeof this._payload.value.value === "string")
        axNode.valueString = this._payload.value.value;
      if (typeof this._payload.value.value === "number")
        axNode.valueNumber = this._payload.value.value;
    }
    if (properties.has("checked"))
      axNode.checked = properties.get("checked") === "true" ? "checked" : properties.get("checked") === "false" ? "unchecked" : "mixed";
    if (properties.has("pressed"))
      axNode.pressed = properties.get("pressed") === "true" ? "pressed" : properties.get("pressed") === "false" ? "released" : "mixed";
    return axNode;
  }
  static createTree(client, payloads) {
    const nodeById = /* @__PURE__ */ new Map();
    for (const payload of payloads)
      nodeById.set(payload.nodeId, new CRAXNode(client, payload));
    for (const node of nodeById.values()) {
      for (const childId of node._payload.childIds || [])
        node._children.push(nodeById.get(childId));
    }
    return nodeById.values().next().value;
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  getAccessibilityTree
});
