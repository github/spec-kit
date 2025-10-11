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
var wkAccessibility_exports = {};
__export(wkAccessibility_exports, {
  getAccessibilityTree: () => getAccessibilityTree
});
module.exports = __toCommonJS(wkAccessibility_exports);
async function getAccessibilityTree(session, needle) {
  const objectId = needle ? needle._objectId : void 0;
  const { axNode } = await session.send("Page.accessibilitySnapshot", { objectId });
  const tree = new WKAXNode(axNode);
  return {
    tree,
    needle: needle ? tree._findNeedle() : null
  };
}
const WKRoleToARIARole = new Map(Object.entries({
  "TextField": "textbox"
}));
const WKUnhelpfulRoleDescriptions = new Map(Object.entries({
  "WebArea": "HTML content",
  "Summary": "summary",
  "DescriptionList": "description list",
  "ImageMap": "image map",
  "ListMarker": "list marker",
  "Video": "video playback",
  "Mark": "highlighted",
  "contentinfo": "content information",
  "Details": "details",
  "DescriptionListDetail": "description",
  "DescriptionListTerm": "term",
  "alertdialog": "web alert dialog",
  "dialog": "web dialog",
  "status": "application status",
  "tabpanel": "tab panel",
  "application": "web application"
}));
class WKAXNode {
  constructor(payload) {
    this._payload = payload;
    this._children = [];
    for (const payload2 of this._payload.children || [])
      this._children.push(new WKAXNode(payload2));
  }
  children() {
    return this._children;
  }
  _findNeedle() {
    if (this._payload.found)
      return this;
    for (const child of this._children) {
      const found = child._findNeedle();
      if (found)
        return found;
    }
    return null;
  }
  isControl() {
    switch (this._payload.role) {
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
      case "TextField":
      case "tree":
        return true;
      default:
        return false;
    }
  }
  _isTextControl() {
    switch (this._payload.role) {
      case "combobox":
      case "searchfield":
      case "textbox":
      case "TextField":
        return true;
    }
    return false;
  }
  _name() {
    if (this._payload.role === "text")
      return this._payload.value || "";
    return this._payload.name || "";
  }
  isInteresting(insideControl) {
    const { role, focusable } = this._payload;
    const name = this._name();
    if (role === "ScrollArea")
      return false;
    if (role === "WebArea")
      return true;
    if (focusable || role === "MenuListOption")
      return true;
    if (this.isControl())
      return true;
    if (insideControl)
      return false;
    return this.isLeafNode() && !!name;
  }
  _hasRedundantTextChild() {
    if (this._children.length !== 1)
      return false;
    const child = this._children[0];
    return child._payload.role === "text" && this._payload.name === child._payload.value;
  }
  isLeafNode() {
    if (!this._children.length)
      return true;
    if (this._isTextControl())
      return true;
    if (this._hasRedundantTextChild())
      return true;
    return false;
  }
  serialize() {
    const node = {
      role: WKRoleToARIARole.get(this._payload.role) || this._payload.role,
      name: this._name()
    };
    if ("description" in this._payload && this._payload.description !== node.name)
      node.description = this._payload.description;
    if ("roledescription" in this._payload) {
      const roledescription = this._payload.roledescription;
      if (roledescription !== this._payload.role && WKUnhelpfulRoleDescriptions.get(this._payload.role) !== roledescription)
        node.roledescription = roledescription;
    }
    if ("value" in this._payload && this._payload.role !== "text") {
      if (typeof this._payload.value === "string")
        node.valueString = this._payload.value;
      else if (typeof this._payload.value === "number")
        node.valueNumber = this._payload.value;
    }
    if ("checked" in this._payload)
      node.checked = this._payload.checked === "true" ? "checked" : this._payload.checked === "false" ? "unchecked" : "mixed";
    if ("pressed" in this._payload)
      node.pressed = this._payload.pressed === "true" ? "pressed" : this._payload.pressed === "false" ? "released" : "mixed";
    const userStringProperties = [
      "keyshortcuts",
      "valuetext"
    ];
    for (const userStringProperty of userStringProperties) {
      if (!(userStringProperty in this._payload))
        continue;
      node[userStringProperty] = this._payload[userStringProperty];
    }
    const booleanProperties = [
      "disabled",
      "expanded",
      "focused",
      "modal",
      "multiselectable",
      "readonly",
      "required",
      "selected"
    ];
    for (const booleanProperty of booleanProperties) {
      if (booleanProperty === "focused" && (this._payload.role === "WebArea" || this._payload.role === "ScrollArea"))
        continue;
      const value = this._payload[booleanProperty];
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
      if (!(numericalProperty in this._payload))
        continue;
      node[numericalProperty] = this._payload[numericalProperty];
    }
    const tokenProperties = [
      "autocomplete",
      "haspopup",
      "invalid"
    ];
    for (const tokenProperty of tokenProperties) {
      const value = this._payload[tokenProperty];
      if (!value || value === "false")
        continue;
      node[tokenProperty] = value;
    }
    const orientationIsApplicable = /* @__PURE__ */ new Set([
      "ScrollArea",
      "scrollbar",
      "listbox",
      "combobox",
      "menu",
      "tree",
      "separator",
      "slider",
      "tablist",
      "toolbar"
    ]);
    if (this._payload.orientation && orientationIsApplicable.has(this._payload.role))
      node.orientation = this._payload.orientation;
    return node;
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  getAccessibilityTree
});
