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

// src/index.js
var index_exports = {};
__export(index_exports, {
  DOMSelector: () => DOMSelector
});
module.exports = __toCommonJS(index_exports);
var import_lru_cache = require("lru-cache");

// src/js/parser.js
var import_css_tree2 = require("css-tree");

// src/js/utility.js
var import_nwsapi = __toESM(require("@asamuzakjp/nwsapi"), 1);
var import_bidi_js = __toESM(require("bidi-js"), 1);
var import_css_tree = require("css-tree");
var import_is_potential_custom_element_name = __toESM(require("is-potential-custom-element-name"), 1);

// src/js/constant.js
var ATTR_SELECTOR = "AttributeSelector";
var CLASS_SELECTOR = "ClassSelector";
var COMBINATOR = "Combinator";
var IDENT = "Identifier";
var ID_SELECTOR = "IdSelector";
var NOT_SUPPORTED_ERR = "NotSupportedError";
var NTH = "Nth";
var PS_CLASS_SELECTOR = "PseudoClassSelector";
var PS_ELEMENT_SELECTOR = "PseudoElementSelector";
var SELECTOR = "Selector";
var STRING = "String";
var SYNTAX_ERR = "SyntaxError";
var TARGET_ALL = "all";
var TARGET_FIRST = "first";
var TARGET_LINEAL = "lineal";
var TARGET_SELF = "self";
var TYPE_SELECTOR = "TypeSelector";
var BIT_01 = 1;
var BIT_02 = 2;
var BIT_04 = 4;
var BIT_08 = 8;
var BIT_16 = 16;
var BIT_32 = 32;
var BIT_FFFF = 65535;
var DUO = 2;
var HEX = 16;
var TYPE_FROM = 8;
var TYPE_TO = -1;
var ELEMENT_NODE = 1;
var TEXT_NODE = 3;
var DOCUMENT_NODE = 9;
var DOCUMENT_FRAGMENT_NODE = 11;
var DOCUMENT_POSITION_PRECEDING = 2;
var DOCUMENT_POSITION_CONTAINS = 8;
var SHOW_ALL = 4294967295;
var SHOW_CONTAINER = 1281;
var ALPHA_NUM = "[A-Z\\d]+";
var CHILD_IDX = "(?:first|last|only)-(?:child|of-type)";
var DIGIT = "(?:0|[1-9]\\d*)";
var LANG_PART = `(?:-${ALPHA_NUM})*`;
var PSEUDO_CLASS = `(?:any-)?link|${CHILD_IDX}|checked|empty|indeterminate|read-(?:only|write)|target`;
var ANB = `[+-]?(?:${DIGIT}n?|n)|(?:[+-]?${DIGIT})?n\\s*[+-]\\s*${DIGIT}`;
var N_TH = `nth-(?:last-)?(?:child|of-type)\\(\\s*(?:even|odd|${ANB})\\s*\\)`;
var SUB_TYPE = "\\[[^|\\]]+\\]|[#.:][\\w-]+";
var SUB_TYPE_WO_PSEUDO = "\\[[^|\\]]+\\]|[#.][\\w-]+";
var SUB_CLASS = "(?:\\.[\\w-]+)";
var TAG_TYPE = "\\*|[A-Za-z][\\w-]*";
var TAG_TYPE_I = "\\*|[A-Z][\\w-]*";
var COMPOUND = `(?:${TAG_TYPE}|(?:${TAG_TYPE})?(?:${SUB_TYPE})+)`;
var COMPOUND_WO_PSEUDO = `(?:${TAG_TYPE}|(?:${TAG_TYPE})?(?:${SUB_TYPE_WO_PSEUDO})+)`;
var COMBO = "\\s?[\\s>~+]\\s?";
var COMPLEX = `${COMPOUND}(?:${COMBO}${COMPOUND})*`;
var DESCEND = "\\s?[\\s>]\\s?";
var SIBLING = "\\s?[+~]\\s?";
var NESTED_LOGIC_A = `:is\\(\\s*${COMPOUND}(?:\\s*,\\s*${COMPOUND})*\\s*\\)`;
var NESTED_LOGIC_B = `:is\\(\\s*${COMPLEX}(?:\\s*,\\s*${COMPLEX})*\\s*\\)`;
var COMPOUND_A = `(?:${TAG_TYPE}|(?:${TAG_TYPE})?(?:${SUB_TYPE}|${NESTED_LOGIC_A})+)`;
var COMPOUND_B = `(?:${TAG_TYPE}|(?:${TAG_TYPE})?(?:${SUB_TYPE}|${NESTED_LOGIC_B})+)`;
var COMPOUND_I = `(?:${TAG_TYPE_I}|(?:${TAG_TYPE_I})?(?:${SUB_TYPE})+)`;
var COMPLEX_L = `${COMPOUND_B}(?:${COMBO}${COMPOUND_B})*`;
var LOGIC_COMPLEX = `(?:is|not)\\(\\s*${COMPLEX_L}(?:\\s*,\\s*${COMPLEX_L})*\\s*\\)`;
var LOGIC_COMPOUND = `(?:is|not)\\(\\s*${COMPOUND_A}(?:\\s*,\\s*${COMPOUND_A})*\\s*\\)`;
var HAS_COMPOUND = `has\\([\\s>]?\\s*${COMPOUND_WO_PSEUDO}\\s*\\)`;
var KEY_FORM_FOCUS = Object.freeze(["button", "input", "select", "textarea"]);
var KEY_INPUT_BUTTON = Object.freeze(["button", "reset", "submit"]);
var KEY_INPUT_DATE = Object.freeze(["date", "datetime-local", "month", "time", "week"]);
var KEY_INPUT_TEXT = Object.freeze(["email", "password", "search", "tel", "text", "url"]);
var KEY_INPUT_EDIT = Object.freeze([...KEY_INPUT_DATE, ...KEY_INPUT_TEXT, "number"]);
var KEY_INPUT_LTR = Object.freeze([
  "checkbox",
  "color",
  "date",
  "image",
  "number",
  "range",
  "radio",
  "time"
]);
var KEY_LOGICAL = Object.freeze(["has", "is", "not", "where"]);
var KEY_MODIFIER = Object.freeze([
  "Alt",
  "AltGraph",
  "CapsLock",
  "Control",
  "Fn",
  "FnLock",
  "Hyper",
  "Meta",
  "NumLock",
  "ScrollLock",
  "Shift",
  "Super",
  "Symbol",
  "SymbolLock"
]);
var KEY_PS_STATE = Object.freeze([
  "enabled",
  "disabled",
  "valid",
  "invalid",
  "in-range",
  "out-of-range",
  "checked",
  "indeterminate",
  "read-only",
  "read-write",
  "open",
  "closed",
  "placeholder-shown"
]);
var KEY_SHADOW_HOST = Object.freeze(["host", "host-context"]);

// src/js/utility.js
var REG_EXCLUDE_FILTER = /[|\\]|::|[^\u0021-\u007F\s]|\[\s*[\w$*=^|~-]+(?:(?:"[\w$*=^|~\s'-]+"|'[\w$*=^|~\s"-]+')?(?:\s+[\w$*=^|~-]+)+|"[^"\]]{1,255}|'[^'\]]{1,255})\s*\]|:(?:is|where)\(\s*\)/;
var REG_SIMPLE_CLASS = new RegExp(`^${SUB_CLASS}$`);
var REG_COMPLEX = new RegExp(`${COMPOUND_I}${COMBO}${COMPOUND_I}`, "i");
var REG_DESCEND = new RegExp(`${COMPOUND_I}${DESCEND}${COMPOUND_I}`, "i");
var REG_SIBLING = new RegExp(`${COMPOUND_I}${SIBLING}${COMPOUND_I}`, "i");
var REG_LOGIC_COMPLEX = new RegExp(`:(?!${PSEUDO_CLASS}|${N_TH}|${LOGIC_COMPLEX})`);
var REG_LOGIC_COMPOUND = new RegExp(`:(?!${PSEUDO_CLASS}|${N_TH}|${LOGIC_COMPOUND})`);
var REG_LOGIC_HAS_COMPOUND = new RegExp(`:(?!${PSEUDO_CLASS}|${N_TH}|${LOGIC_COMPOUND}|${HAS_COMPOUND})`);
var REG_END_WITH_HAS = new RegExp(`:${HAS_COMPOUND}$`);
var REG_WO_LOGICAL = new RegExp(`:(?!${PSEUDO_CLASS}|${N_TH})`);
var getType = (o) => Object.prototype.toString.call(o).slice(TYPE_FROM, TYPE_TO);
var resolveContent = (node) => {
  if (!node?.nodeType) {
    throw new TypeError(`Unexpected type ${getType(node)}`);
  }
  let document;
  let root;
  let shadow;
  switch (node.nodeType) {
    case DOCUMENT_NODE: {
      document = node;
      root = node;
      break;
    }
    case DOCUMENT_FRAGMENT_NODE: {
      const { host, mode, ownerDocument } = node;
      document = ownerDocument;
      root = node;
      shadow = host && (mode === "close" || mode === "open");
      break;
    }
    case ELEMENT_NODE: {
      document = node.ownerDocument;
      let refNode = node;
      while (refNode) {
        const { host, mode, nodeType, parentNode } = refNode;
        if (nodeType === DOCUMENT_FRAGMENT_NODE) {
          shadow = host && (mode === "close" || mode === "open");
          break;
        } else if (parentNode) {
          refNode = parentNode;
        } else {
          break;
        }
      }
      root = refNode;
      break;
    }
    default: {
      throw new TypeError(`Unexpected node ${node.nodeName}`);
    }
  }
  return [
    document,
    root,
    !!shadow
  ];
};
var traverseNode = (node, walker, force = false) => {
  if (!node?.nodeType) {
    throw new TypeError(`Unexpected type ${getType(node)}`);
  }
  if (!walker) {
    return null;
  }
  let refNode = walker.currentNode;
  if (refNode === node) {
    return refNode;
  } else if (force || refNode.contains(node)) {
    refNode = walker.nextNode();
    while (refNode) {
      if (refNode === node) {
        break;
      }
      refNode = walker.nextNode();
    }
    return refNode;
  } else {
    if (refNode !== walker.root) {
      let bool;
      while (refNode) {
        if (refNode === node) {
          bool = true;
          break;
        } else if (refNode === walker.root || refNode.contains(node)) {
          break;
        }
        refNode = walker.parentNode();
      }
      if (bool) {
        return refNode;
      }
    }
    if (node.nodeType === ELEMENT_NODE) {
      let bool;
      while (refNode) {
        if (refNode === node) {
          bool = true;
          break;
        }
        refNode = walker.nextNode();
      }
      if (bool) {
        return refNode;
      }
    }
  }
  return null;
};
var isCustomElement = (node, opt = {}) => {
  if (!node?.nodeType) {
    throw new TypeError(`Unexpected type ${getType(node)}`);
  }
  if (node.nodeType !== ELEMENT_NODE) {
    return false;
  }
  const { localName, ownerDocument } = node;
  const { formAssociated } = opt;
  const window = ownerDocument.defaultView;
  let elmConstructor;
  const attr = node.getAttribute("is");
  if (attr) {
    elmConstructor = (0, import_is_potential_custom_element_name.default)(attr) && window.customElements.get(attr);
  } else {
    elmConstructor = (0, import_is_potential_custom_element_name.default)(localName) && window.customElements.get(localName);
  }
  if (elmConstructor) {
    if (formAssociated) {
      return !!elmConstructor.formAssociated;
    }
    return true;
  }
  return false;
};
var getSlottedTextContent = (node) => {
  if (!node?.nodeType) {
    throw new TypeError(`Unexpected type ${getType(node)}`);
  }
  if (typeof node.assignedNodes !== "function") {
    return null;
  }
  const nodes = node.assignedNodes();
  if (nodes.length) {
    let text;
    for (const item of nodes) {
      text = item.textContent.trim();
      if (text) {
        break;
      }
    }
    return text;
  }
  return node.textContent.trim();
};
var getDirectionality = (node) => {
  if (!node?.nodeType) {
    throw new TypeError(`Unexpected type ${getType(node)}`);
  }
  if (node.nodeType !== ELEMENT_NODE) {
    return null;
  }
  const { dir: dirAttr, localName, parentNode } = node;
  const { getEmbeddingLevels } = (0, import_bidi_js.default)();
  if (dirAttr === "ltr" || dirAttr === "rtl") {
    return dirAttr;
  } else if (dirAttr === "auto") {
    let text;
    switch (localName) {
      case "input": {
        const valueKeys = [...KEY_INPUT_BUTTON, ...KEY_INPUT_TEXT, "hidden"];
        if (!node.type || valueKeys.includes(node.type)) {
          text = node.value;
        } else {
          const ltrKeys = [
            "checkbox",
            "color",
            "date",
            "image",
            "number",
            "range",
            "radio",
            "time"
          ];
          if (ltrKeys.includes(node.type)) {
            return "ltr";
          }
        }
        break;
      }
      case "slot": {
        text = getSlottedTextContent(node);
        break;
      }
      case "textarea": {
        text = node.value;
        break;
      }
      default: {
        const items = [].slice.call(node.childNodes);
        for (const item of items) {
          const {
            dir: itemDir,
            localName: itemLocalName,
            nodeType: itemNodeType,
            textContent: itemTextContent
          } = item;
          if (itemNodeType === TEXT_NODE) {
            text = itemTextContent.trim();
          } else if (itemNodeType === ELEMENT_NODE) {
            const keys = ["bdi", "script", "style", "textarea"];
            if (!keys.includes(itemLocalName) && (!itemDir || itemDir !== "ltr" && itemDir !== "rtl")) {
              if (itemLocalName === "slot") {
                text = getSlottedTextContent(item);
              } else {
                text = itemTextContent.trim();
              }
            }
          }
          if (text) {
            break;
          }
        }
      }
    }
    if (text) {
      const { paragraphs: [{ level }] } = getEmbeddingLevels(text);
      if (level % 2 === 1) {
        return "rtl";
      }
    } else if (parentNode) {
      const { nodeType: parentNodeType } = parentNode;
      if (parentNodeType === ELEMENT_NODE) {
        return getDirectionality(parentNode);
      }
    }
  } else if (localName === "input" && node.type === "tel") {
    return "ltr";
  } else if (localName === "bdi") {
    const text = node.textContent.trim();
    if (text) {
      const { paragraphs: [{ level }] } = getEmbeddingLevels(text);
      if (level % 2 === 1) {
        return "rtl";
      }
    }
  } else if (parentNode) {
    if (localName === "slot") {
      const text = getSlottedTextContent(node);
      if (text) {
        const { paragraphs: [{ level }] } = getEmbeddingLevels(text);
        if (level % 2 === 1) {
          return "rtl";
        }
        return "ltr";
      }
    }
    const { nodeType: parentNodeType } = parentNode;
    if (parentNodeType === ELEMENT_NODE) {
      return getDirectionality(parentNode);
    }
  }
  return "ltr";
};
var isContentEditable = (node) => {
  if (!node?.nodeType) {
    throw new TypeError(`Unexpected type ${getType(node)}`);
  }
  if (node.nodeType !== ELEMENT_NODE) {
    return false;
  }
  if (typeof node.isContentEditable === "boolean") {
    return node.isContentEditable;
  } else if (node.ownerDocument.designMode === "on") {
    return true;
  } else {
    let attr;
    if (node.hasAttribute("contenteditable")) {
      attr = node.getAttribute("contenteditable");
    } else {
      attr = "inherit";
    }
    switch (attr) {
      case "":
      case "true": {
        return true;
      }
      case "plaintext-only": {
        return true;
      }
      case "false": {
        return false;
      }
      default: {
        if (node?.parentNode?.nodeType === ELEMENT_NODE) {
          return isContentEditable(node.parentNode);
        }
        return false;
      }
    }
  }
};
var isVisible = (node) => {
  if (node?.nodeType !== ELEMENT_NODE) {
    return false;
  }
  const window = node.ownerDocument.defaultView;
  const { display, visibility } = window.getComputedStyle(node);
  if (display !== "none" && visibility === "visible") {
    return true;
  }
  return false;
};
var isFocusVisible = (node) => {
  if (node?.nodeType !== ELEMENT_NODE) {
    return false;
  }
  const { localName, type } = node;
  switch (localName) {
    case "input": {
      if (!type || KEY_INPUT_EDIT.includes(type)) {
        return true;
      }
      return false;
    }
    case "textarea": {
      return true;
    }
    default: {
      return isContentEditable(node);
    }
  }
};
var isFocusableArea = (node) => {
  if (node?.nodeType !== ELEMENT_NODE) {
    return false;
  }
  if (!node.isConnected) {
    return false;
  }
  const window = node.ownerDocument.defaultView;
  if (node instanceof window.HTMLElement) {
    if (Number.isInteger(parseInt(node.getAttribute("tabindex")))) {
      return true;
    }
    if (isContentEditable(node)) {
      return true;
    }
    const { localName, parentNode } = node;
    switch (localName) {
      case "a": {
        if (node.href || node.hasAttribute("href")) {
          return true;
        }
        return false;
      }
      case "iframe": {
        return true;
      }
      case "input": {
        if (node.disabled || node.hasAttribute("disabled") || node.hidden || node.hasAttribute("hidden")) {
          return false;
        }
        return true;
      }
      case "summary": {
        if (parentNode.localName === "details") {
          let child = parentNode.firstElementChild;
          let bool = false;
          while (child) {
            if (child.localName === "summary") {
              bool = child === node;
              break;
            }
            child = child.nextElementSibling;
          }
          return bool;
        }
        return false;
      }
      default: {
        const keys = ["button", "select", "textarea"];
        if (keys.includes(localName) && !(node.disabled || node.hasAttribute("disabled"))) {
          return true;
        }
      }
    }
  } else if (node instanceof window.SVGElement) {
    if (Number.isInteger(parseInt(node.getAttributeNS(null, "tabindex")))) {
      const keys = [
        "clipPath",
        "defs",
        "desc",
        "linearGradient",
        "marker",
        "mask",
        "metadata",
        "pattern",
        "radialGradient",
        "script",
        "style",
        "symbol",
        "title"
      ];
      const ns = "http://www.w3.org/2000/svg";
      let bool;
      let refNode = node;
      while (refNode.namespaceURI === ns) {
        bool = keys.includes(refNode.localName);
        if (bool) {
          break;
        }
        if (refNode?.parentNode?.namespaceURI === ns) {
          refNode = refNode.parentNode;
        } else {
          break;
        }
      }
      if (bool) {
        return false;
      }
      return true;
    }
    if (node.localName === "a" && (node.href || node.hasAttributeNS(null, "href"))) {
      return true;
    }
  }
  return false;
};
var getNamespaceURI = (ns, node) => {
  if (typeof ns !== "string") {
    throw new TypeError(`Unexpected type ${getType(ns)}`);
  } else if (!node?.nodeType) {
    throw new TypeError(`Unexpected type ${getType(node)}`);
  }
  if (!ns || node.nodeType !== ELEMENT_NODE) {
    return null;
  }
  const { attributes } = node;
  let res;
  for (const attr of attributes) {
    const { name, namespaceURI, prefix, value } = attr;
    if (name === `xmlns:${ns}`) {
      res = value;
    } else if (prefix === ns) {
      res = namespaceURI;
    }
    if (res) {
      break;
    }
  }
  return res ?? null;
};
var isNamespaceDeclared = (ns = "", node = {}) => {
  if (!ns || typeof ns !== "string" || node?.nodeType !== ELEMENT_NODE) {
    return false;
  }
  if (node.lookupNamespaceURI(ns)) {
    return true;
  }
  const root = node.ownerDocument.documentElement;
  let parent = node;
  let res;
  while (parent) {
    res = getNamespaceURI(ns, parent);
    if (res || parent === root) {
      break;
    }
    parent = parent.parentNode;
  }
  return !!res;
};
var isPreceding = (nodeA, nodeB) => {
  if (!nodeA?.nodeType) {
    throw new TypeError(`Unexpected type ${getType(nodeA)}`);
  } else if (!nodeB?.nodeType) {
    throw new TypeError(`Unexpected type ${getType(nodeB)}`);
  }
  if (nodeA.nodeType !== ELEMENT_NODE || nodeB.nodeType !== ELEMENT_NODE) {
    return false;
  }
  const posBit = nodeB.compareDocumentPosition(nodeA);
  const res = posBit & DOCUMENT_POSITION_PRECEDING || posBit & DOCUMENT_POSITION_CONTAINS;
  return !!res;
};
var sortNodes = (nodes = []) => {
  const arr = [...nodes];
  if (arr.length > 1) {
    arr.sort((a, b) => {
      let res;
      if (isPreceding(b, a)) {
        res = 1;
      } else {
        res = -1;
      }
      return res;
    });
  }
  return arr;
};
var initNwsapi = (window, document) => {
  if (!window?.DOMException) {
    throw new TypeError(`Unexpected global object ${getType(window)}`);
  }
  if (document?.nodeType !== DOCUMENT_NODE) {
    document = window.document;
  }
  const nw = (0, import_nwsapi.default)({
    document,
    DOMException: window.DOMException
  });
  nw.configure({
    LOGERRORS: false
  });
  return nw;
};
var filterSelector = (selector, target) => {
  if (!selector || typeof selector !== "string" || /null|undefined/.test(selector) || target === TARGET_FIRST) {
    return false;
  }
  if (target === TARGET_ALL && REG_SIMPLE_CLASS.test(selector)) {
    return false;
  }
  if (selector.includes("[")) {
    const index = selector.lastIndexOf("[");
    const sel = selector.substring(index);
    if (sel.indexOf("]") < 0) {
      return false;
    }
  }
  if (selector.includes("/") || REG_EXCLUDE_FILTER.test(selector)) {
    return false;
  }
  if (selector.includes(":")) {
    let complex = false;
    if (target !== TARGET_ALL) {
      complex = REG_COMPLEX.test(selector);
    }
    if (target === TARGET_ALL && REG_DESCEND.test(selector) && !REG_SIBLING.test(selector)) {
      return false;
    } else if (target !== TARGET_ALL && /:has\(/.test(selector)) {
      if (!complex || REG_LOGIC_HAS_COMPOUND.test(selector)) {
        return false;
      }
      return REG_END_WITH_HAS.test(selector);
    } else if (/:(?:is|not)\(/.test(selector)) {
      if (complex) {
        return !REG_LOGIC_COMPLEX.test(selector);
      } else {
        return !REG_LOGIC_COMPOUND.test(selector);
      }
    } else {
      return !REG_WO_LOGICAL.test(selector);
    }
  }
  return true;
};

// src/js/parser.js
var import_css_tree3 = require("css-tree");
var REG_EMPTY_PS_FUNC = /(?<=:(?:dir|has|host(?:-context)?|is|lang|not|nth-(?:last-)?(?:child|of-type)|where))\(\s+\)/g;
var REG_SHADOW_PS_ELEMENT = /^part|slotted$/;
var U_FFFD = "\uFFFD";
var unescapeSelector = (selector = "") => {
  if (typeof selector === "string" && selector.indexOf("\\", 0) >= 0) {
    const arr = selector.split("\\");
    const l = arr.length;
    for (let i = 1; i < l; i++) {
      let item = arr[i];
      if (item === "" && i === l - 1) {
        item = U_FFFD;
      } else {
        const hexExists = /^([\da-f]{1,6}\s?)/i.exec(item);
        if (hexExists) {
          const [, hex] = hexExists;
          let str;
          try {
            const low = parseInt("D800", HEX);
            const high = parseInt("DFFF", HEX);
            const deci = parseInt(hex, HEX);
            if (deci === 0 || deci >= low && deci <= high) {
              str = U_FFFD;
            } else {
              str = String.fromCodePoint(deci);
            }
          } catch (e) {
            str = U_FFFD;
          }
          let postStr = "";
          if (item.length > hex.length) {
            postStr = item.substring(hex.length);
          }
          item = `${str}${postStr}`;
        } else if (/^[\n\r\f]/.test(item)) {
          item = "\\" + item;
        }
      }
      arr[i] = item;
    }
    selector = arr.join("");
  }
  return selector;
};
var preprocess = (selector) => {
  if (typeof selector === "string") {
    let index = 0;
    while (index >= 0) {
      index = selector.indexOf("#", index);
      if (index < 0) {
        break;
      }
      const preHash = selector.substring(0, index + 1);
      let postHash = selector.substring(index + 1);
      const codePoint = postHash.codePointAt(0);
      if (codePoint > BIT_FFFF) {
        const str = `\\${codePoint.toString(HEX)} `;
        if (postHash.length === DUO) {
          postHash = str;
        } else {
          postHash = `${str}${postHash.substring(DUO)}`;
        }
      }
      selector = `${preHash}${postHash}`;
      index++;
    }
    selector = selector.replace(/\f|\r\n?/g, "\n").replace(/[\0\uD800-\uDFFF]|\\$/g, U_FFFD);
  } else if (selector === void 0 || selector === null) {
    selector = getType(selector).toLowerCase();
  } else if (Array.isArray(selector)) {
    selector = selector.join(",");
  } else if (Object.hasOwn(selector, "toString")) {
    selector = selector.toString();
  } else {
    throw new DOMException(`Invalid selector ${selector}`, SYNTAX_ERR);
  }
  return selector.replace(/\x26/g, ":scope");
};
var parseSelector = (selector) => {
  selector = preprocess(selector);
  if (/^$|^\s*>|,\s*$/.test(selector)) {
    throw new DOMException(`Invalid selector ${selector}`, SYNTAX_ERR);
  }
  let res;
  try {
    const ast = (0, import_css_tree2.parse)(selector, {
      context: "selectorList",
      parseCustomProperty: true
    });
    res = (0, import_css_tree2.toPlainObject)(ast);
  } catch (e) {
    const { message } = e;
    if (/^(?:"\]"|Attribute selector [()\s,=~^$*|]+) is expected$/.test(message) && !selector.endsWith("]")) {
      const index = selector.lastIndexOf("[");
      const sel = selector.substring(index);
      if (sel.includes('"')) {
        const quotes = sel.match(/"/g).length;
        if (quotes % 2) {
          res = parseSelector(`${selector}"]`);
        } else {
          res = parseSelector(`${selector}]`);
        }
      } else {
        res = parseSelector(`${selector}]`);
      }
    } else if (message === '")" is expected') {
      if (REG_EMPTY_PS_FUNC.test(selector)) {
        res = parseSelector(`${selector.replaceAll(REG_EMPTY_PS_FUNC, "()")}`);
      } else if (!selector.endsWith(")")) {
        res = parseSelector(`${selector})`);
      } else {
        throw new DOMException(`Invalid selector ${selector}`, SYNTAX_ERR);
      }
    } else {
      throw new DOMException(`Invalid selector ${selector}`, SYNTAX_ERR);
    }
  }
  return res;
};
var walkAST = (ast = {}) => {
  const branches = /* @__PURE__ */ new Set();
  const info = /* @__PURE__ */ new Map();
  const opt = {
    enter: (node) => {
      switch (node.type) {
        case CLASS_SELECTOR: {
          if (/^-?\d/.test(node.name)) {
            throw new DOMException(
              `Invalid selector .${node.name}`,
              SYNTAX_ERR
            );
          }
          break;
        }
        case ID_SELECTOR: {
          if (/^-?\d/.test(node.name)) {
            throw new DOMException(
              `Invalid selector #${node.name}`,
              SYNTAX_ERR
            );
          }
          break;
        }
        case PS_CLASS_SELECTOR: {
          if (KEY_LOGICAL.includes(node.name)) {
            info.set("hasNestedSelector", true);
            info.set("hasLogicalPseudoFunc", true);
            if (node.name === "has") {
              info.set("hasHasPseudoFunc", true);
            }
          } else if (KEY_PS_STATE.includes(node.name)) {
            info.set("hasStatePseudoClass", true);
          } else if (KEY_SHADOW_HOST.includes(node.name) && Array.isArray(node.children) && node.children.length) {
            info.set("hasNestedSelector", true);
          }
          break;
        }
        case PS_ELEMENT_SELECTOR: {
          if (REG_SHADOW_PS_ELEMENT.test(node.name)) {
            info.set("hasNestedSelector", true);
          }
          break;
        }
        case NTH: {
          if (node.selector) {
            info.set("hasNestedSelector", true);
            info.set("hasNthChildOfSelector", true);
          }
          break;
        }
        case SELECTOR: {
          branches.add(node.children);
          break;
        }
        default:
      }
    }
  };
  (0, import_css_tree2.walk)(ast, opt);
  if (info.get("hasNestedSelector")) {
    (0, import_css_tree2.findAll)(ast, (node, item, list) => {
      if (list) {
        if (node.type === PS_CLASS_SELECTOR && KEY_LOGICAL.includes(node.name)) {
          const itemList = list.filter((i) => {
            const { name, type } = i;
            return type === PS_CLASS_SELECTOR && KEY_LOGICAL.includes(name);
          });
          for (const { children } of itemList) {
            for (const { children: grandChildren } of children) {
              for (const { children: greatGrandChildren } of grandChildren) {
                if (branches.has(greatGrandChildren)) {
                  branches.delete(greatGrandChildren);
                }
              }
            }
          }
        } else if (node.type === PS_CLASS_SELECTOR && KEY_SHADOW_HOST.includes(node.name) && Array.isArray(node.children) && node.children.length) {
          const itemList = list.filter((i) => {
            const { children, name, type } = i;
            const res = type === PS_CLASS_SELECTOR && KEY_SHADOW_HOST.includes(name) && Array.isArray(children) && children.length;
            return res;
          });
          for (const { children } of itemList) {
            for (const { children: grandChildren } of children) {
              if (branches.has(grandChildren)) {
                branches.delete(grandChildren);
              }
            }
          }
        } else if (node.type === PS_ELEMENT_SELECTOR && REG_SHADOW_PS_ELEMENT.test(node.name)) {
          const itemList = list.filter((i) => {
            const { name, type } = i;
            const res = type === PS_ELEMENT_SELECTOR && REG_SHADOW_PS_ELEMENT.test(name);
            return res;
          });
          for (const { children } of itemList) {
            for (const { children: grandChildren } of children) {
              if (branches.has(grandChildren)) {
                branches.delete(grandChildren);
              }
            }
          }
        } else if (node.type === NTH && node.selector) {
          const itemList = list.filter((i) => {
            const { selector, type } = i;
            const res = type === NTH && selector;
            return res;
          });
          for (const { selector } of itemList) {
            const { children } = selector;
            for (const { children: grandChildren } of children) {
              if (branches.has(grandChildren)) {
                branches.delete(grandChildren);
              }
            }
          }
        }
      }
    });
  }
  return {
    branches: [...branches],
    info: Object.fromEntries(info)
  };
};
var sortAST = (asts) => {
  const arr = [...asts];
  if (arr.length > 1) {
    const order = /* @__PURE__ */ new Map([
      [PS_ELEMENT_SELECTOR, BIT_01],
      [ID_SELECTOR, BIT_02],
      [CLASS_SELECTOR, BIT_04],
      [TYPE_SELECTOR, BIT_08],
      [ATTR_SELECTOR, BIT_16],
      [PS_CLASS_SELECTOR, BIT_32]
    ]);
    arr.sort((a, b) => {
      const { type: typeA } = a;
      const { type: typeB } = b;
      const bitA = order.get(typeA);
      const bitB = order.get(typeB);
      let res;
      if (bitA === bitB) {
        res = 0;
      } else if (bitA > bitB) {
        res = 1;
      } else {
        res = -1;
      }
      return res;
    });
  }
  return arr;
};
var parseAstName = (selector) => {
  let prefix;
  let localName;
  if (selector && typeof selector === "string") {
    if (selector.indexOf("|") > -1) {
      [prefix, localName] = selector.split("|");
    } else {
      prefix = "*";
      localName = selector;
    }
  } else {
    throw new DOMException(`Invalid selector ${selector}`, SYNTAX_ERR);
  }
  return {
    prefix,
    localName
  };
};

// src/js/matcher.js
var matchPseudoElementSelector = (astName, astType, opt = {}) => {
  const { forgive, warn } = opt;
  if (astType === PS_ELEMENT_SELECTOR) {
    switch (astName) {
      case "after":
      case "backdrop":
      case "before":
      case "cue":
      case "cue-region":
      case "first-letter":
      case "first-line":
      case "file-selector-button":
      case "marker":
      case "placeholder":
      case "selection":
      case "target-text": {
        if (warn) {
          throw new DOMException(
            `Unsupported pseudo-element ::${astName}`,
            NOT_SUPPORTED_ERR
          );
        }
        break;
      }
      case "part":
      case "slotted": {
        if (warn) {
          throw new DOMException(
            `Unsupported pseudo-element ::${astName}()`,
            NOT_SUPPORTED_ERR
          );
        }
        break;
      }
      default: {
        if (astName.startsWith("-webkit-")) {
          if (warn) {
            throw new DOMException(
              `Unsupported pseudo-element ::${astName}`,
              NOT_SUPPORTED_ERR
            );
          }
        } else if (!forgive) {
          throw new DOMException(
            `Unknown pseudo-element ::${astName}`,
            SYNTAX_ERR
          );
        }
      }
    }
  } else {
    throw new TypeError(`Unexpected ast type ${getType(astType)}`);
  }
};
var matchDirectionPseudoClass = (ast, node) => {
  const { name } = ast;
  if (!name) {
    let type;
    if (name === "") {
      type = "(empty String)";
    } else {
      type = getType(name);
    }
    throw new TypeError(`Unexpected ast type ${type}`);
  }
  const dir = getDirectionality(node);
  return name === dir;
};
var matchLanguagePseudoClass = (ast, node) => {
  const { name, type, value } = ast;
  let astName;
  if (type === STRING && value) {
    astName = value;
  } else if (type === IDENT && name) {
    astName = unescapeSelector(name);
  }
  const { contentType } = node.ownerDocument;
  const html = /^(?:application\/xhtml\+x|text\/ht)ml$/.test(contentType);
  const xml = /^(?:application\/(?:[\w\-.]+\+)?|image\/[\w\-.]+\+|text\/)xml$/.test(contentType);
  if (astName === "*") {
    if (html && node.hasAttribute("lang") || xml && node.hasAttribute("xml:lang")) {
      if (html && node.getAttribute("lang") || xml && node.getAttribute("xml:lang")) {
        return true;
      }
    } else {
      let parent = node.parentNode;
      let res;
      while (parent) {
        if (parent.nodeType === ELEMENT_NODE) {
          if (html && parent.hasAttribute("lang") || xml && parent.hasAttribute("xml:lang")) {
            if (html && parent.hasAttribute("lang") || xml && parent.hasAttribute("xml:lang")) {
              res = true;
            }
            break;
          }
          parent = parent.parentNode;
        } else {
          break;
        }
      }
      return !!res;
    }
  } else if (astName) {
    const reg = new RegExp(`^(?:\\*-)?${ALPHA_NUM}${LANG_PART}$`, "i");
    if (reg.test(astName)) {
      let regExtendedLang;
      if (astName.indexOf("-") > -1) {
        const [langMain, langSub, ...langRest] = astName.split("-");
        let extendedMain;
        if (langMain === "*") {
          extendedMain = `${ALPHA_NUM}${LANG_PART}`;
        } else {
          extendedMain = `${langMain}${LANG_PART}`;
        }
        const extendedSub = `-${langSub}${LANG_PART}`;
        const len = langRest.length;
        let extendedRest = "";
        if (len) {
          for (let i = 0; i < len; i++) {
            extendedRest += `-${langRest[i]}${LANG_PART}`;
          }
        }
        regExtendedLang = new RegExp(`^${extendedMain}${extendedSub}${extendedRest}$`, "i");
      } else {
        regExtendedLang = new RegExp(`^${astName}${LANG_PART}$`, "i");
      }
      if (html && node.hasAttribute("lang") || xml && node.hasAttribute("xml:lang")) {
        const attr = html && node.getAttribute("lang") || xml && node.getAttribute("xml:lang") || "";
        return regExtendedLang.test(attr);
      } else {
        let parent = node.parentNode;
        let res;
        while (parent) {
          if (parent.nodeType === ELEMENT_NODE) {
            if (html && parent.hasAttribute("lang") || xml && parent.hasAttribute("xml:lang")) {
              const attr = html && parent.getAttribute("lang") || xml && parent.getAttribute("xml:lang") || "";
              res = regExtendedLang.test(attr);
              break;
            }
            parent = parent.parentNode;
          } else {
            break;
          }
        }
        return !!res;
      }
    }
  }
  return false;
};
var matchAttributeSelector = (ast, node, opt = {}) => {
  const {
    flags: astFlags,
    matcher: astMatcher,
    name: astName,
    value: astValue
  } = ast;
  const { check, forgive } = opt;
  if (typeof astFlags === "string" && !/^[is]$/i.test(astFlags) && !forgive) {
    const css = (0, import_css_tree3.generate)(ast);
    throw new DOMException(`Invalid selector ${css}`, SYNTAX_ERR);
  }
  const { attributes } = node;
  if (attributes?.length) {
    const contentType = node.ownerDocument.contentType;
    let caseInsensitive;
    if (contentType === "text/html") {
      if (typeof astFlags === "string" && /^s$/i.test(astFlags)) {
        caseInsensitive = false;
      } else {
        caseInsensitive = true;
      }
    } else if (typeof astFlags === "string" && /^i$/i.test(astFlags)) {
      caseInsensitive = true;
    } else {
      caseInsensitive = false;
    }
    let astAttrName = unescapeSelector(astName.name);
    if (caseInsensitive) {
      astAttrName = astAttrName.toLowerCase();
    }
    const attrValues = /* @__PURE__ */ new Set();
    if (astAttrName.indexOf("|") > -1) {
      const {
        prefix: astPrefix,
        localName: astLocalName
      } = parseAstName(astAttrName);
      for (const item of attributes) {
        let { name: itemName, value: itemValue } = item;
        if (caseInsensitive) {
          itemName = itemName.toLowerCase();
          itemValue = itemValue.toLowerCase();
        }
        switch (astPrefix) {
          case "": {
            if (astLocalName === itemName) {
              attrValues.add(itemValue);
            }
            break;
          }
          case "*": {
            if (itemName.indexOf(":") > -1) {
              if (itemName.endsWith(`:${astLocalName}`)) {
                attrValues.add(itemValue);
              }
            } else if (astLocalName === itemName) {
              attrValues.add(itemValue);
            }
            break;
          }
          default: {
            if (!check) {
              if (forgive) {
                return false;
              }
              const css = (0, import_css_tree3.generate)(ast);
              throw new DOMException(`Invalid selector ${css}`, SYNTAX_ERR);
            }
            if (itemName.indexOf(":") > -1) {
              const [itemPrefix, itemLocalName] = itemName.split(":");
              if (itemPrefix === "xml" && itemLocalName === "lang") {
                continue;
              } else if (astPrefix === itemPrefix && astLocalName === itemLocalName) {
                const namespaceDeclared = isNamespaceDeclared(astPrefix, node);
                if (namespaceDeclared) {
                  attrValues.add(itemValue);
                }
              }
            }
          }
        }
      }
    } else {
      for (let { name: itemName, value: itemValue } of attributes) {
        if (caseInsensitive) {
          itemName = itemName.toLowerCase();
          itemValue = itemValue.toLowerCase();
        }
        if (itemName.indexOf(":") > -1) {
          const [itemPrefix, itemLocalName] = itemName.split(":");
          if (itemPrefix === "xml" && itemLocalName === "lang") {
            continue;
          } else if (astAttrName === itemLocalName) {
            attrValues.add(itemValue);
          }
        } else if (astAttrName === itemName) {
          attrValues.add(itemValue);
        }
      }
    }
    if (attrValues.size) {
      const { name: astIdentValue, value: astStringValue } = astValue ?? {};
      let attrValue;
      if (astIdentValue) {
        if (caseInsensitive) {
          attrValue = astIdentValue.toLowerCase();
        } else {
          attrValue = astIdentValue;
        }
      } else if (astStringValue) {
        if (caseInsensitive) {
          attrValue = astStringValue.toLowerCase();
        } else {
          attrValue = astStringValue;
        }
      } else if (astStringValue === "") {
        attrValue = astStringValue;
      }
      switch (astMatcher) {
        case "=": {
          return typeof attrValue === "string" && attrValues.has(attrValue);
        }
        case "~=": {
          if (attrValue && typeof attrValue === "string") {
            let res;
            for (const value of attrValues) {
              const item = new Set(value.split(/\s+/));
              if (item.has(attrValue)) {
                res = true;
                break;
              }
            }
            return !!res;
          }
          return false;
        }
        case "|=": {
          if (attrValue && typeof attrValue === "string") {
            let item;
            for (const value of attrValues) {
              if (value === attrValue || value.startsWith(`${attrValue}-`)) {
                item = value;
                break;
              }
            }
            if (item) {
              return true;
            }
            return false;
          }
          return false;
        }
        case "^=": {
          if (attrValue && typeof attrValue === "string") {
            let item;
            for (const value of attrValues) {
              if (value.startsWith(`${attrValue}`)) {
                item = value;
                break;
              }
            }
            if (item) {
              return true;
            }
            return false;
          }
          return false;
        }
        case "$=": {
          if (attrValue && typeof attrValue === "string") {
            let item;
            for (const value of attrValues) {
              if (value.endsWith(`${attrValue}`)) {
                item = value;
                break;
              }
            }
            if (item) {
              return true;
            }
            return false;
          }
          return false;
        }
        case "*=": {
          if (attrValue && typeof attrValue === "string") {
            let item;
            for (const value of attrValues) {
              if (value.includes(`${attrValue}`)) {
                item = value;
                break;
              }
            }
            if (item) {
              return true;
            }
            return false;
          }
          return false;
        }
        case null:
        default: {
          return true;
        }
      }
    }
  }
  return false;
};
var matchTypeSelector = (ast, node, opt = {}) => {
  const astName = unescapeSelector(ast.name);
  const { localName, namespaceURI, prefix } = node;
  const { check, forgive } = opt;
  let {
    prefix: astPrefix,
    localName: astLocalName
  } = parseAstName(astName, node);
  if (node.ownerDocument.contentType === "text/html" && (!namespaceURI || namespaceURI === "http://www.w3.org/1999/xhtml") && /[A-Z][\\w-]*/i.test(localName)) {
    astPrefix = astPrefix.toLowerCase();
    astLocalName = astLocalName.toLowerCase();
  }
  let nodePrefix;
  let nodeLocalName;
  if (localName.indexOf(":") > -1) {
    [nodePrefix, nodeLocalName] = localName.split(":");
  } else {
    nodePrefix = prefix || "";
    nodeLocalName = localName;
  }
  switch (astPrefix) {
    case "": {
      if (!nodePrefix && !namespaceURI && (astLocalName === "*" || astLocalName === nodeLocalName)) {
        return true;
      }
      return false;
    }
    case "*": {
      if (astLocalName === "*" || astLocalName === nodeLocalName) {
        return true;
      }
      return false;
    }
    default: {
      if (!check) {
        if (forgive) {
          return false;
        }
        const css = (0, import_css_tree3.generate)(ast);
        throw new DOMException(`Invalid selector ${css}`, SYNTAX_ERR);
      }
      const astNS = node.lookupNamespaceURI(astPrefix);
      const nodeNS = node.lookupNamespaceURI(nodePrefix);
      if (astNS === nodeNS && astPrefix === nodePrefix) {
        if (astLocalName === "*" || astLocalName === nodeLocalName) {
          return true;
        }
        return false;
      } else if (!forgive && !astNS) {
        throw new DOMException(`Undeclared namespace ${astPrefix}`, SYNTAX_ERR);
      }
      return false;
    }
  }
};

// src/js/finder.js
var DIR_NEXT = "next";
var DIR_PREV = "prev";
var Finder = class {
  /* private fields */
  #ast;
  #astCache;
  #check;
  #descendant;
  #document;
  #documentCache;
  #domSymbolTree;
  #event;
  #focus;
  #invalidate;
  #invalidateResults;
  #lastFocusVisible;
  #node;
  #nodeWalker;
  #nodes;
  #noexcept;
  #pseudoElement;
  #results;
  #root;
  #rootWalker;
  #selector;
  #shadow;
  #verifyShadowHost;
  #walkers;
  #warn;
  #window;
  /**
   * construct
   * @param {object} window - window
   */
  constructor(window) {
    this.#window = window;
    this.#astCache = /* @__PURE__ */ new WeakMap();
    this.#documentCache = /* @__PURE__ */ new WeakMap();
    this.#invalidateResults = /* @__PURE__ */ new WeakMap();
    this.#results = /* @__PURE__ */ new WeakMap();
    this.#event = null;
    this.#focus = null;
    this.#lastFocusVisible = null;
    this._registerEventListeners();
  }
  /**
   * handle error
   * @param {Error} e - Error
   * @param {object} [opt] - options
   * @param {boolean} [opt.noexcept] - no exception
   * @throws {Error} - Error
   * @returns {void}
   */
  onError(e, opt = {}) {
    const noexcept = opt.noexcept ?? this.#noexcept;
    if (!noexcept) {
      if (e instanceof DOMException || e instanceof this.#window.DOMException) {
        if (e.name === NOT_SUPPORTED_ERR) {
          if (this.#warn) {
            console.warn(e.message);
          }
        } else {
          throw new this.#window.DOMException(e.message, e.name);
        }
      } else if (e.name in this.#window) {
        throw new this.#window[e.name](e.message, { cause: e });
      } else {
        throw e;
      }
    }
  }
  /**
   * setup finder
   * @param {string} selector - CSS selector
   * @param {object} node - Document, DocumentFragment, Element node
   * @param {object} [opt] - options
   * @param {boolean} [opt.check] - running in internal check()
   * @param {object} [opt.domSymbolTree] - domSymbolTree
   * @param {boolean} [opt.noexcept] - no exception
   * @param {boolean} [opt.warn] - console warn
   * @returns {object} - finder
   */
  setup(selector, node, opt = {}) {
    const { check, domSymbolTree, noexcept, warn } = opt;
    this.#check = !!check;
    this.#domSymbolTree = domSymbolTree;
    this.#noexcept = !!noexcept;
    this.#warn = !!warn;
    [
      this.#document,
      this.#root,
      this.#shadow
    ] = resolveContent(node);
    this.#node = node;
    this.#selector = selector;
    [
      this.#ast,
      this.#nodes
    ] = this._correspond(selector);
    this.#invalidateResults = /* @__PURE__ */ new WeakMap();
    this.#pseudoElement = [];
    this.#walkers = /* @__PURE__ */ new WeakMap();
    this.#verifyShadowHost = null;
    return this;
  }
  /**
   * register event listeners
   * @private
   * @returns {Array.<void>} - results
   */
  _registerEventListeners() {
    const opt = {
      capture: true,
      passive: true
    };
    const func = [];
    const focusKeys = ["focus", "focusin"];
    for (const key of focusKeys) {
      func.push(this.#window.addEventListener(key, (evt) => {
        this.#focus = evt;
      }, opt));
    }
    const keyboardKeys = ["keydown", "keyup"];
    for (const key of keyboardKeys) {
      func.push(this.#window.addEventListener(key, (evt) => {
        const { key: key2 } = evt;
        if (!KEY_MODIFIER.includes(key2)) {
          this.#event = evt;
        }
      }, opt));
    }
    const mouseKeys = [
      "mouseover",
      "mousedown",
      "mouseup",
      "mouseout"
    ];
    for (const key of mouseKeys) {
      func.push(this.#window.addEventListener(key, (evt) => {
        this.#event = evt;
      }, opt));
    }
    func.push(this.#window.addEventListener("click", (evt) => {
      this.#event = evt;
      this.#invalidateResults = /* @__PURE__ */ new WeakMap();
      this.#results = /* @__PURE__ */ new WeakMap();
    }, opt));
    return func;
  }
  /**
   * correspond ast and nodes
   * @private
   * @param {string} selector - CSS selector
   * @returns {Array.<Array.<object>>} - array of ast and nodes
   */
  _correspond(selector) {
    const nodes = [];
    this.#descendant = false;
    this.#invalidate = false;
    let ast;
    if (this.#documentCache.has(this.#document)) {
      const cachedItem = this.#documentCache.get(this.#document);
      if (cachedItem && cachedItem.has(`${selector}`)) {
        const item = cachedItem.get(`${selector}`);
        ast = item.ast;
        this.#descendant = item.descendant;
        this.#invalidate = item.invalidate;
      }
    }
    if (ast) {
      const l = ast.length;
      for (let i = 0; i < l; i++) {
        ast[i].dir = null;
        ast[i].filtered = false;
        ast[i].find = false;
        nodes[i] = [];
      }
    } else {
      let cssAst;
      try {
        cssAst = parseSelector(selector);
      } catch (e) {
        return this.onError(e);
      }
      const { branches, info } = walkAST(cssAst);
      const {
        hasHasPseudoFunc,
        hasLogicalPseudoFunc,
        hasNthChildOfSelector,
        hasStatePseudoClass
      } = info;
      let invalidate = hasHasPseudoFunc || hasStatePseudoClass || !!(hasLogicalPseudoFunc && hasNthChildOfSelector);
      let descendant = false;
      let i = 0;
      ast = [];
      for (const [...items] of branches) {
        const branch = [];
        let item = items.shift();
        if (item && item.type !== COMBINATOR) {
          const leaves = /* @__PURE__ */ new Set();
          while (item) {
            let itemName = item.name;
            if (item.type === COMBINATOR) {
              const [nextItem] = items;
              if (nextItem.type === COMBINATOR) {
                return this.onError(new this.#window.DOMException(
                  `Invalid selector ${selector}`,
                  SYNTAX_ERR
                ));
              }
              if (itemName === "+" || itemName === "~") {
                invalidate = true;
              } else {
                descendant = true;
              }
              branch.push({
                combo: item,
                leaves: sortAST(leaves)
              });
              leaves.clear();
            } else if (item) {
              if (itemName && typeof itemName === "string") {
                itemName = unescapeSelector(itemName);
                if (typeof itemName === "string" && itemName !== item.name) {
                  item.name = itemName;
                }
                if (/[|:]/.test(itemName)) {
                  item.namespace = true;
                }
              }
              leaves.add(item);
            }
            if (items.length) {
              item = items.shift();
            } else {
              branch.push({
                combo: null,
                leaves: sortAST(leaves)
              });
              leaves.clear();
              break;
            }
          }
        }
        ast.push({
          branch,
          dir: null,
          filtered: false,
          find: false
        });
        nodes[i] = [];
        i++;
      }
      let cachedItem;
      if (this.#documentCache.has(this.#document)) {
        cachedItem = this.#documentCache.get(this.#document);
      } else {
        cachedItem = /* @__PURE__ */ new Map();
      }
      cachedItem.set(`${selector}`, {
        ast,
        descendant,
        invalidate
      });
      this.#documentCache.set(this.#document, cachedItem);
      this.#descendant = descendant;
      this.#invalidate = invalidate;
    }
    return [
      ast,
      nodes
    ];
  }
  /**
   * create tree walker
   * @private
   * @param {object} node - Document, DocumentFragment, Element node
   * @param {object} [opt] - options
   * @param {boolean} [opt.force] - force new tree walker
   * @param {number} [opt.whatToShow] - NodeFilter whatToShow
   * @returns {object} - tree walker
   */
  _createTreeWalker(node, opt = {}) {
    const { force = false, whatToShow = SHOW_CONTAINER } = opt;
    let walker;
    if (force) {
      walker = this.#document.createTreeWalker(node, whatToShow);
    } else if (this.#walkers.has(node)) {
      walker = this.#walkers.get(node);
    } else {
      walker = this.#document.createTreeWalker(node, whatToShow);
      this.#walkers.set(node, walker);
    }
    return walker;
  }
  /**
   * prepare querySelector walker
   * @private
   * @returns {object} - tree walker
   */
  _prepareQuerySelectorWalker() {
    this.#nodeWalker = this._createTreeWalker(this.#node);
    this.#rootWalker = null;
    return this.#nodeWalker;
  }
  /**
   * collect nth child
   * @private
   * @param {object} anb - An+B options
   * @param {number} anb.a - a
   * @param {number} anb.b - b
   * @param {boolean} [anb.reverse] - reverse order
   * @param {object} [anb.selector] - AST
   * @param {object} node - Element node
   * @param {object} [opt] - options
   * @returns {Set.<object>} - collection of matched nodes
   */
  _collectNthChild(anb, node, opt = {}) {
    const { a, b, reverse, selector } = anb;
    const { parentNode } = node;
    const matched = /* @__PURE__ */ new Set();
    let selectorBranches;
    if (selector) {
      if (this.#astCache.has(selector)) {
        selectorBranches = this.#astCache.get(selector);
      } else {
        const { branches: branches2 } = walkAST(selector);
        selectorBranches = branches2;
        this.#astCache.set(selector, selectorBranches);
      }
      const { branches } = walkAST(selector);
      selectorBranches = branches;
    }
    if (parentNode) {
      const walker = this._createTreeWalker(parentNode, {
        force: true
      });
      let refNode = walker.firstChild();
      const selectorNodes = /* @__PURE__ */ new Set();
      let l = 0;
      if (selectorBranches) {
        while (refNode) {
          if (isVisible(refNode)) {
            let bool;
            for (const leaves of selectorBranches) {
              bool = this._matchLeaves(leaves, refNode, opt);
              if (!bool) {
                break;
              }
            }
            if (bool) {
              selectorNodes.add(refNode);
            }
          }
          l++;
          refNode = walker.nextSibling();
        }
      } else {
        while (refNode) {
          l++;
          refNode = walker.nextSibling();
        }
      }
      if (a === 0) {
        if (b > 0 && b <= l) {
          if (selectorNodes.size) {
            refNode = traverseNode(parentNode, walker);
            if (reverse) {
              refNode = walker.lastChild();
            } else {
              refNode = walker.firstChild();
            }
            let i = 0;
            while (refNode) {
              if (selectorNodes.has(refNode)) {
                if (i === b - 1) {
                  matched.add(refNode);
                  break;
                }
                i++;
              }
              if (reverse) {
                refNode = walker.previousSibling();
              } else {
                refNode = walker.nextSibling();
              }
            }
          } else if (!selector) {
            refNode = traverseNode(parentNode, walker);
            if (reverse) {
              refNode = walker.lastChild();
            } else {
              refNode = walker.firstChild();
            }
            let i = 0;
            while (refNode) {
              if (i === b - 1) {
                matched.add(refNode);
                break;
              }
              if (reverse) {
                refNode = walker.previousSibling();
              } else {
                refNode = walker.nextSibling();
              }
              i++;
            }
          }
        }
      } else {
        let nth = b - 1;
        if (a > 0) {
          while (nth < 0) {
            nth += a;
          }
        }
        if (nth >= 0 && nth < l) {
          refNode = traverseNode(parentNode, walker);
          if (reverse) {
            refNode = walker.lastChild();
          } else {
            refNode = walker.firstChild();
          }
          let i = 0;
          let j = a > 0 ? 0 : b - 1;
          while (refNode) {
            if (refNode && nth >= 0 && nth < l) {
              if (selectorNodes.size) {
                if (selectorNodes.has(refNode)) {
                  if (j === nth) {
                    matched.add(refNode);
                    nth += a;
                  }
                  if (a > 0) {
                    j++;
                  } else {
                    j--;
                  }
                }
              } else if (i === nth) {
                if (!selector) {
                  matched.add(refNode);
                }
                nth += a;
              }
              if (reverse) {
                refNode = walker.previousSibling();
              } else {
                refNode = walker.nextSibling();
              }
              i++;
            } else {
              break;
            }
          }
        }
      }
      if (reverse && matched.size > 1) {
        return new Set([...matched].toReversed());
      }
    } else if (node === this.#root && a + b === 1) {
      if (selectorBranches) {
        let bool;
        for (const leaves of selectorBranches) {
          bool = this._matchLeaves(leaves, node, opt);
          if (bool) {
            break;
          }
        }
        if (bool) {
          matched.add(node);
        }
      } else {
        matched.add(node);
      }
    }
    return matched;
  }
  /**
   * collect nth of type
   * @private
   * @param {object} anb - An+B options
   * @param {number} anb.a - a
   * @param {number} anb.b - b
   * @param {boolean} [anb.reverse] - reverse order
   * @param {object} node - Element node
   * @returns {Set.<object>} - collection of matched nodes
   */
  _collectNthOfType(anb, node) {
    const { a, b, reverse } = anb;
    const { localName, namespaceURI, parentNode, prefix } = node;
    const matched = /* @__PURE__ */ new Set();
    if (parentNode) {
      const walker = this._createTreeWalker(parentNode, {
        force: true
      });
      let refNode = traverseNode(parentNode, walker);
      refNode = walker.firstChild();
      let l = 0;
      while (refNode) {
        l++;
        refNode = walker.nextSibling();
      }
      if (a === 0) {
        if (b > 0 && b <= l) {
          refNode = traverseNode(parentNode, walker);
          if (reverse) {
            refNode = walker.lastChild();
          } else {
            refNode = walker.firstChild();
          }
          let j = 0;
          while (refNode) {
            const {
              localName: itemLocalName,
              namespaceURI: itemNamespaceURI,
              prefix: itemPrefix
            } = refNode;
            if (itemLocalName === localName && itemPrefix === prefix && itemNamespaceURI === namespaceURI) {
              if (j === b - 1) {
                matched.add(refNode);
                break;
              }
              j++;
            }
            if (reverse) {
              refNode = walker.previousSibling();
            } else {
              refNode = walker.nextSibling();
            }
          }
        }
      } else {
        let nth = b - 1;
        if (a > 0) {
          while (nth < 0) {
            nth += a;
          }
        }
        if (nth >= 0 && nth < l) {
          refNode = traverseNode(parentNode, walker);
          if (reverse) {
            refNode = walker.lastChild();
          } else {
            refNode = walker.firstChild();
          }
          let j = a > 0 ? 0 : b - 1;
          while (refNode) {
            const {
              localName: itemLocalName,
              namespaceURI: itemNamespaceURI,
              prefix: itemPrefix
            } = refNode;
            if (itemLocalName === localName && itemPrefix === prefix && itemNamespaceURI === namespaceURI) {
              if (j === nth) {
                matched.add(refNode);
                nth += a;
              }
              if (nth < 0 || nth >= l) {
                break;
              } else if (a > 0) {
                j++;
              } else {
                j--;
              }
            }
            if (reverse) {
              refNode = walker.previousSibling();
            } else {
              refNode = walker.nextSibling();
            }
          }
        }
      }
      if (reverse && matched.size > 1) {
        return new Set([...matched].toReversed());
      }
    } else if (node === this.#root && a + b === 1) {
      matched.add(node);
    }
    return matched;
  }
  /**
   * match An+B
   * @private
   * @param {object} ast - AST
   * @param {object} node - Element node
   * @param {string} nthName - nth pseudo-class name
   * @param {object} [opt] - options
   * @returns {Set.<object>} - collection of matched nodes
   */
  _matchAnPlusB(ast, node, nthName, opt = {}) {
    const {
      nth: {
        a,
        b,
        name: nthIdentName
      },
      selector
    } = ast;
    const anbMap = /* @__PURE__ */ new Map();
    if (nthIdentName) {
      if (nthIdentName === "even") {
        anbMap.set("a", 2);
        anbMap.set("b", 0);
      } else if (nthIdentName === "odd") {
        anbMap.set("a", 2);
        anbMap.set("b", 1);
      }
      if (nthName.indexOf("last") > -1) {
        anbMap.set("reverse", true);
      }
    } else {
      if (typeof a === "string" && /-?\d+/.test(a)) {
        anbMap.set("a", a * 1);
      } else {
        anbMap.set("a", 0);
      }
      if (typeof b === "string" && /-?\d+/.test(b)) {
        anbMap.set("b", b * 1);
      } else {
        anbMap.set("b", 0);
      }
      if (nthName.indexOf("last") > -1) {
        anbMap.set("reverse", true);
      }
    }
    if (nthName === "nth-child" || nthName === "nth-last-child") {
      if (selector) {
        anbMap.set("selector", selector);
      }
      const anb = Object.fromEntries(anbMap);
      const nodes = this._collectNthChild(anb, node, opt);
      return nodes;
    } else if (nthName === "nth-of-type" || nthName === "nth-last-of-type") {
      const anb = Object.fromEntries(anbMap);
      const nodes = this._collectNthOfType(anb, node);
      return nodes;
    }
    return /* @__PURE__ */ new Set();
  }
  /**
   * match :has() pseudo-class function
   * @private
   * @param {Array.<object>} astLeaves - AST leaves
   * @param {object} node - Element node
   * @param {object} [opt] - options
   * @returns {boolean} - result
   */
  _matchHasPseudoFunc(astLeaves, node, opt = {}) {
    if (Array.isArray(astLeaves) && astLeaves.length) {
      const leaves = [...astLeaves];
      const [leaf] = leaves;
      const { type: leafType } = leaf;
      let combo;
      if (leafType === COMBINATOR) {
        combo = leaves.shift();
      } else {
        combo = {
          name: " ",
          type: COMBINATOR
        };
      }
      const twigLeaves = [];
      while (leaves.length) {
        const [item] = leaves;
        const { type: itemType } = item;
        if (itemType === COMBINATOR) {
          break;
        } else {
          twigLeaves.push(leaves.shift());
        }
      }
      const twig = {
        combo,
        leaves: twigLeaves
      };
      opt.dir = DIR_NEXT;
      const nodes = this._matchCombinator(twig, node, opt);
      if (nodes.size) {
        if (leaves.length) {
          let bool = false;
          for (const nextNode of nodes) {
            bool = this._matchHasPseudoFunc(leaves, nextNode, opt);
            if (bool) {
              break;
            }
          }
          return bool;
        }
        return true;
      }
    }
    return false;
  }
  /**
   * match logical pseudo-class functions - :has(), :is(), :not(), :where()
   * @private
   * @param {object} astData - AST data
   * @param {object} node - Element node
   * @param {object} [opt] - options
   * @returns {?object} - matched node
   */
  _matchLogicalPseudoFunc(astData, node, opt = {}) {
    const { astName, branches, twigBranches } = astData;
    const isShadowRoot = (opt.isShadowRoot || this.#shadow) && node.nodeType === DOCUMENT_FRAGMENT_NODE;
    if (astName === "has") {
      let bool;
      for (const leaves of branches) {
        bool = this._matchHasPseudoFunc(leaves, node, opt);
        if (bool) {
          break;
        }
      }
      if (bool) {
        if (isShadowRoot) {
          if (this.#verifyShadowHost) {
            return node;
          }
        } else {
          return node;
        }
      }
    } else {
      if (isShadowRoot) {
        let invalid;
        for (const branch of branches) {
          if (branch.length > 1) {
            invalid = true;
            break;
          } else if (astName === "not") {
            const [{ type: childAstType }] = branch;
            if (childAstType !== PS_CLASS_SELECTOR) {
              invalid = true;
              break;
            }
          }
        }
        if (invalid) {
          return null;
        }
      }
      opt.forgive = astName === "is" || astName === "where";
      const l = twigBranches.length;
      let bool;
      for (let i = 0; i < l; i++) {
        const branch = twigBranches[i];
        const lastIndex = branch.length - 1;
        const { leaves } = branch[lastIndex];
        bool = this._matchLeaves(leaves, node, opt);
        if (bool && lastIndex > 0) {
          let nextNodes = /* @__PURE__ */ new Set([node]);
          for (let j = lastIndex - 1; j >= 0; j--) {
            const twig = branch[j];
            const arr = [];
            opt.dir = DIR_PREV;
            for (const nextNode of nextNodes) {
              const m = this._matchCombinator(twig, nextNode, opt);
              if (m.size) {
                arr.push(...m);
              }
            }
            if (arr.length) {
              if (j === 0) {
                bool = true;
              } else {
                nextNodes = new Set(arr);
              }
            } else {
              bool = false;
              break;
            }
          }
        }
        if (bool) {
          break;
        }
      }
      if (astName === "not") {
        if (bool) {
          return null;
        }
        return node;
      } else if (bool) {
        return node;
      }
    }
    return null;
  }
  /**
   * match pseudo-class selector
   * @private
   * @see https://html.spec.whatwg.org/#pseudo-classes
   * @param {object} ast - AST
   * @param {object} node - Element node
   * @param {object} [opt] - options
   * @returns {Set.<object>} - collection of matched nodes
   */
  _matchPseudoClassSelector(ast, node, opt = {}) {
    const { children: astChildren, name: astName } = ast;
    const { localName, parentNode } = node;
    const {
      forgive,
      warn = this.#warn
    } = opt;
    const matched = /* @__PURE__ */ new Set();
    if (Array.isArray(astChildren) && KEY_LOGICAL.includes(astName)) {
      if (!astChildren.length && astName !== "is" && astName !== "where") {
        const css = (0, import_css_tree3.generate)(ast);
        return this.onError(new this.#window.DOMException(
          `Invalid selector ${css}`,
          SYNTAX_ERR
        ));
      }
      let astData;
      if (this.#astCache.has(ast)) {
        astData = this.#astCache.get(ast);
      } else {
        const { branches } = walkAST(ast);
        if (astName === "has") {
          let forgiven;
          for (const child of astChildren) {
            const item = (0, import_css_tree3.find)(child, (leaf) => {
              if (KEY_LOGICAL.includes(leaf.name) && (0, import_css_tree3.find)(leaf, (nestedLeaf) => nestedLeaf.name === "has")) {
                return leaf;
              }
              return null;
            });
            if (item) {
              const itemName = item.name;
              if (itemName === "is" || itemName === "where") {
                forgiven = true;
                break;
              } else {
                const css = (0, import_css_tree3.generate)(ast);
                return this.onError(new this.#window.DOMException(
                  `Invalid selector ${css}`,
                  SYNTAX_ERR
                ));
              }
            }
          }
          if (forgiven) {
            return matched;
          }
          astData = {
            astName,
            branches
          };
        } else {
          const twigBranches = [];
          for (const [...leaves] of branches) {
            const branch = [];
            const leavesSet = /* @__PURE__ */ new Set();
            let item = leaves.shift();
            while (item) {
              if (item.type === COMBINATOR) {
                branch.push({
                  combo: item,
                  leaves: [...leavesSet]
                });
                leavesSet.clear();
              } else if (item) {
                leavesSet.add(item);
              }
              if (leaves.length) {
                item = leaves.shift();
              } else {
                branch.push({
                  combo: null,
                  leaves: [...leavesSet]
                });
                leavesSet.clear();
                break;
              }
            }
            twigBranches.push(branch);
          }
          astData = {
            astName,
            branches,
            twigBranches
          };
          this.#astCache.set(ast, astData);
        }
      }
      const res = this._matchLogicalPseudoFunc(astData, node, opt);
      if (res) {
        matched.add(res);
      }
    } else if (Array.isArray(astChildren)) {
      if (/^nth-(?:last-)?(?:child|of-type)$/.test(astName)) {
        if (astChildren.length !== 1) {
          const css = (0, import_css_tree3.generate)(ast);
          return this.onError(new this.#window.DOMException(
            `Invalid selector ${css}`,
            SYNTAX_ERR
          ));
        }
        const [branch] = astChildren;
        const nodes = this._matchAnPlusB(branch, node, astName, opt);
        return nodes;
      } else {
        switch (astName) {
          // :dir()
          case "dir": {
            if (astChildren.length !== 1) {
              const css = (0, import_css_tree3.generate)(ast);
              return this.onError(new this.#window.DOMException(
                `Invalid selector ${css}`,
                SYNTAX_ERR
              ));
            }
            const [astChild] = astChildren;
            const res = matchDirectionPseudoClass(astChild, node);
            if (res) {
              matched.add(node);
            }
            break;
          }
          // :lang()
          case "lang": {
            if (!astChildren.length) {
              const css = (0, import_css_tree3.generate)(ast);
              return this.onError(new this.#window.DOMException(
                `Invalid selector ${css}`,
                SYNTAX_ERR
              ));
            }
            let bool;
            for (const astChild of astChildren) {
              bool = matchLanguagePseudoClass(astChild, node);
              if (bool) {
                break;
              }
            }
            if (bool) {
              matched.add(node);
            }
            break;
          }
          // :state()
          case "state": {
            if (isCustomElement(node)) {
              const [{ value: stateValue }] = astChildren;
              if (stateValue) {
                if (node[stateValue]) {
                  matched.add(node);
                } else {
                  for (const i in node) {
                    const prop = node[i];
                    if (prop instanceof this.#window.ElementInternals) {
                      if (prop?.states?.has(stateValue)) {
                        matched.add(node);
                      }
                      break;
                    }
                  }
                }
              }
            }
            break;
          }
          case "current":
          case "nth-col":
          case "nth-last-col": {
            if (warn) {
              this.onError(new this.#window.DOMException(
                `Unsupported pseudo-class :${astName}()`,
                NOT_SUPPORTED_ERR
              ));
            }
            break;
          }
          case "host":
          case "host-context": {
            break;
          }
          // dropped from CSS Selectors 3
          case "contains": {
            if (warn) {
              this.onError(new this.#window.DOMException(
                `Unknown pseudo-class :${astName}()`,
                NOT_SUPPORTED_ERR
              ));
            }
            break;
          }
          default: {
            if (!forgive) {
              this.onError(new this.#window.DOMException(
                `Unknown pseudo-class :${astName}()`,
                SYNTAX_ERR
              ));
            }
          }
        }
      }
    } else {
      switch (astName) {
        case "any-link":
        case "link": {
          if ((localName === "a" || localName === "area") && node.hasAttribute("href")) {
            matched.add(node);
          }
          break;
        }
        case "local-link": {
          if ((localName === "a" || localName === "area") && node.hasAttribute("href")) {
            const { href, origin, pathname } = new URL(this.#document.URL);
            const attrURL = new URL(node.getAttribute("href"), href);
            if (attrURL.origin === origin && attrURL.pathname === pathname) {
              matched.add(node);
            }
          }
          break;
        }
        case "visited": {
          break;
        }
        case "hover": {
          const { target, type } = this.#event ?? {};
          if (/^(?:click|mouse(?:down|over|up))$/.test(type) && node.contains(target)) {
            matched.add(node);
          }
          break;
        }
        case "active": {
          const { buttons, target, type } = this.#event ?? {};
          if (type === "mousedown" && buttons & BIT_01 && node.contains(target)) {
            matched.add(node);
          }
          break;
        }
        case "target": {
          const { hash } = new URL(this.#document.URL);
          if (node.id && hash === `#${node.id}` && this.#document.contains(node)) {
            matched.add(node);
          }
          break;
        }
        case "target-within": {
          const { hash } = new URL(this.#document.URL);
          if (hash) {
            const id = hash.replace(/^#/, "");
            let current = this.#document.getElementById(id);
            while (current) {
              if (current === node) {
                matched.add(node);
                break;
              }
              current = current.parentNode;
            }
          }
          break;
        }
        case "scope": {
          if (this.#node.nodeType === ELEMENT_NODE) {
            if (!this.#shadow && node === this.#node) {
              matched.add(node);
            }
          } else if (node === this.#document.documentElement) {
            matched.add(node);
          }
          break;
        }
        case "focus": {
          if (node === this.#document.activeElement && isFocusableArea(node)) {
            matched.add(node);
          }
          break;
        }
        case "focus-visible": {
          if (node === this.#document.activeElement && isFocusableArea(node)) {
            let bool;
            if (isFocusVisible(node)) {
              bool = true;
            } else if (this.#focus) {
              const { relatedTarget, target: focusTarget } = this.#focus;
              if (focusTarget === node) {
                if (isFocusVisible(relatedTarget)) {
                  bool = true;
                } else if (this.#event) {
                  const {
                    key: eventKey,
                    target: eventTarget,
                    type: eventType
                  } = this.#event;
                  if (eventTarget === relatedTarget) {
                    if (this.#lastFocusVisible === null) {
                      bool = true;
                    } else if (focusTarget === this.#lastFocusVisible) {
                      bool = true;
                    }
                  } else if (eventKey === "Tab") {
                    if (eventType === "keydown" && eventTarget !== node || eventType === "keyup" && eventTarget === node) {
                      if (eventTarget === focusTarget) {
                        if (this.#lastFocusVisible === null) {
                          bool = true;
                        } else if (eventTarget === this.#lastFocusVisible && relatedTarget === null) {
                          bool = true;
                        }
                      } else {
                        bool = true;
                      }
                    }
                  } else if (eventKey) {
                    if ((eventType === "keydown" || eventType === "keyup") && eventTarget === node) {
                      bool = true;
                    }
                  }
                } else if (relatedTarget === null || relatedTarget === this.#lastFocusVisible) {
                  bool = true;
                }
              }
            }
            if (bool) {
              this.#lastFocusVisible = node;
              matched.add(node);
            } else if (this.#lastFocusVisible === node) {
              this.#lastFocusVisible = null;
            }
          }
          break;
        }
        case "focus-within": {
          let bool;
          let current = this.#document.activeElement;
          if (isFocusableArea(current)) {
            while (current) {
              if (current === node) {
                bool = true;
                break;
              }
              current = current.parentNode;
            }
          }
          if (bool) {
            matched.add(node);
          }
          break;
        }
        case "open":
        case "closed": {
          if (localName === "details" || localName === "dialog") {
            if (node.hasAttribute("open")) {
              if (astName === "open") {
                matched.add(node);
              }
            } else if (astName === "closed") {
              matched.add(node);
            }
          }
          break;
        }
        case "disabled":
        case "enabled": {
          const keys = [...KEY_FORM_FOCUS, "fieldset", "optgroup", "option"];
          if (keys.includes(localName) || isCustomElement(node, { formAssociated: true })) {
            let disabled;
            if (node.disabled || node.hasAttribute("disabled")) {
              disabled = true;
            } else if (node.localName === "option") {
              if (parentNode.localName === "optgroup" && (parentNode.disabled || parentNode.hasAttribute("disabled"))) {
                disabled = true;
              }
            } else if (node.localName !== "optgroup") {
              let parent = parentNode;
              while (parent) {
                if (parent.localName === "fieldset" && (parent.disabled || parent.hasAttribute("disabled"))) {
                  let refNode = parent.firstElementChild;
                  while (refNode) {
                    if (refNode.localName === "legend") {
                      break;
                    }
                    refNode = refNode.nextElementSibling;
                  }
                  if (refNode) {
                    if (!refNode.contains(node)) {
                      disabled = true;
                    }
                  } else {
                    disabled = true;
                  }
                  break;
                } else if (parent.localName === "form") {
                  break;
                } else if (parent.parentNode?.nodeType === ELEMENT_NODE) {
                  if (parent.parentNode.localName === "form") {
                    break;
                  } else {
                    parent = parent.parentNode;
                  }
                } else {
                  break;
                }
              }
            }
            if (disabled) {
              if (astName === "disabled") {
                matched.add(node);
              }
            } else if (astName === "enabled") {
              matched.add(node);
            }
          }
          break;
        }
        case "read-only":
        case "read-write": {
          let readonly;
          let writable;
          switch (localName) {
            case "textarea": {
              if (node.readOnly || node.hasAttribute("readonly") || node.disabled || node.hasAttribute("disabled")) {
                readonly = true;
              } else {
                writable = true;
              }
              break;
            }
            case "input": {
              if (!node.type || KEY_INPUT_EDIT.includes(node.type)) {
                if (node.readOnly || node.hasAttribute("readonly") || node.disabled || node.hasAttribute("disabled")) {
                  readonly = true;
                } else {
                  writable = true;
                }
              } else {
                readonly = true;
              }
              break;
            }
            default: {
              if (isContentEditable(node)) {
                writable = true;
              } else {
                readonly = true;
              }
            }
          }
          if (readonly) {
            if (astName === "read-only") {
              matched.add(node);
            }
          } else if (astName === "read-write" && writable) {
            matched.add(node);
          }
          break;
        }
        case "placeholder-shown": {
          let placeholder;
          if (node.placeholder) {
            placeholder = node.placeholder;
          } else if (node.hasAttribute("placeholder")) {
            placeholder = node.getAttribute("placeholder");
          }
          if (typeof placeholder === "string" && !/[\r\n]/.test(placeholder)) {
            let targetNode;
            if (localName === "textarea") {
              targetNode = node;
            } else if (localName === "input") {
              if (node.hasAttribute("type")) {
                const keys = [...KEY_INPUT_TEXT, "number"];
                if (keys.includes(node.getAttribute("type"))) {
                  targetNode = node;
                }
              } else {
                targetNode = node;
              }
            }
            if (targetNode && node.value === "") {
              matched.add(node);
            }
          }
          break;
        }
        case "checked": {
          const attrType = node.getAttribute("type");
          if (node.checked && localName === "input" && (attrType === "checkbox" || attrType === "radio") || node.selected && localName === "option") {
            matched.add(node);
          }
          break;
        }
        case "indeterminate": {
          if (node.indeterminate && localName === "input" && node.type === "checkbox" || localName === "progress" && !node.hasAttribute("value")) {
            matched.add(node);
          } else if (localName === "input" && node.type === "radio" && !node.hasAttribute("checked")) {
            const nodeName = node.name;
            let parent = node.parentNode;
            while (parent) {
              if (parent.localName === "form") {
                break;
              }
              parent = parent.parentNode;
            }
            if (!parent) {
              parent = this.#document.documentElement;
            }
            const walker = this._createTreeWalker(parent);
            let refNode = traverseNode(parent, walker);
            refNode = walker.firstChild();
            let checked;
            while (refNode) {
              if (refNode.localName === "input" && refNode.getAttribute("type") === "radio") {
                if (refNode.hasAttribute("name")) {
                  if (refNode.getAttribute("name") === nodeName) {
                    checked = !!refNode.checked;
                  }
                } else {
                  checked = !!refNode.checked;
                }
                if (checked) {
                  break;
                }
              }
              refNode = walker.nextNode();
            }
            if (!checked) {
              matched.add(node);
            }
          }
          break;
        }
        case "default": {
          const chekcKeys = ["checkbox", "radio"];
          const resetKeys = ["button", "reset"];
          const submitKeys = ["image", "submit"];
          const attrType = node.getAttribute("type");
          if (localName === "button" && !(node.hasAttribute("type") && resetKeys.includes(attrType)) || localName === "input" && node.hasAttribute("type") && submitKeys.includes(attrType)) {
            let form = node.parentNode;
            while (form) {
              if (form.localName === "form") {
                break;
              }
              form = form.parentNode;
            }
            if (form) {
              const walker = this._createTreeWalker(form);
              let refNode = traverseNode(form, walker);
              refNode = walker.firstChild();
              while (refNode) {
                const nodeName = refNode.localName;
                const nodeAttrType = refNode.getAttribute("type");
                let m;
                if (nodeName === "button") {
                  m = !(refNode.hasAttribute("type") && resetKeys.includes(nodeAttrType));
                } else if (nodeName === "input") {
                  m = refNode.hasAttribute("type") && submitKeys.includes(nodeAttrType);
                }
                if (m) {
                  if (refNode === node) {
                    matched.add(node);
                  }
                  break;
                }
                refNode = walker.nextNode();
              }
            }
          } else if (localName === "input" && node.hasAttribute("type") && chekcKeys.includes(attrType) && node.hasAttribute("checked")) {
            matched.add(node);
          } else if (localName === "option" && node.hasAttribute("selected")) {
            matched.add(node);
          }
          break;
        }
        case "valid":
        case "invalid": {
          const keys = [...KEY_FORM_FOCUS, "form"];
          if (keys.includes(localName)) {
            let valid;
            if (node.checkValidity()) {
              if (node.maxLength >= 0) {
                if (node.maxLength >= node.value.length) {
                  valid = true;
                }
              } else {
                valid = true;
              }
            }
            if (valid) {
              if (astName === "valid") {
                matched.add(node);
              }
            } else if (astName === "invalid") {
              matched.add(node);
            }
          } else if (localName === "fieldset") {
            const walker = this._createTreeWalker(node);
            let refNode = traverseNode(node, walker);
            refNode = walker.firstChild();
            let valid;
            if (!refNode) {
              valid = true;
            } else {
              while (refNode) {
                if (keys.includes(refNode.localName)) {
                  if (refNode.checkValidity()) {
                    if (refNode.maxLength >= 0) {
                      valid = refNode.maxLength >= refNode.value.length;
                    } else {
                      valid = true;
                    }
                  } else {
                    valid = false;
                  }
                  if (!valid) {
                    break;
                  }
                }
                refNode = walker.nextNode();
              }
            }
            if (valid) {
              if (astName === "valid") {
                matched.add(node);
              }
            } else if (astName === "invalid") {
              matched.add(node);
            }
          }
          break;
        }
        case "in-range":
        case "out-of-range": {
          const keys = [...KEY_INPUT_DATE, "number", "range"];
          const attrType = node.getAttribute("type");
          if (localName === "input" && !(node.readonly || node.hasAttribute("readonly")) && !(node.disabled || node.hasAttribute("disabled")) && keys.includes(attrType)) {
            const flowed = node.validity.rangeUnderflow || node.validity.rangeOverflow;
            if (astName === "out-of-range" && flowed) {
              matched.add(node);
            } else if (astName === "in-range" && !flowed && (node.hasAttribute("min") || node.hasAttribute("max") || attrType === "range")) {
              matched.add(node);
            }
          }
          break;
        }
        case "required":
        case "optional": {
          let required;
          let optional;
          if (localName === "select" || localName === "textarea") {
            if (node.required || node.hasAttribute("required")) {
              required = true;
            } else {
              optional = true;
            }
          } else if (localName === "input") {
            if (node.hasAttribute("type")) {
              const keys = [...KEY_INPUT_EDIT, "checkbox", "file", "radio"];
              const attrType = node.getAttribute("type");
              if (keys.includes(attrType)) {
                if (node.required || node.hasAttribute("required")) {
                  required = true;
                } else {
                  optional = true;
                }
              } else {
                optional = true;
              }
            } else if (node.required || node.hasAttribute("required")) {
              required = true;
            } else {
              optional = true;
            }
          }
          if (astName === "required" && required) {
            matched.add(node);
          } else if (astName === "optional" && optional) {
            matched.add(node);
          }
          break;
        }
        case "root": {
          if (node === this.#document.documentElement) {
            matched.add(node);
          }
          break;
        }
        case "empty": {
          if (node.hasChildNodes()) {
            const walker = this._createTreeWalker(node, {
              force: true,
              whatToShow: SHOW_ALL
            });
            let refNode = walker.firstChild();
            let bool;
            while (refNode) {
              bool = refNode.nodeType !== ELEMENT_NODE && refNode.nodeType !== TEXT_NODE;
              if (!bool) {
                break;
              }
              refNode = walker.nextSibling();
            }
            if (bool) {
              matched.add(node);
            }
          } else {
            matched.add(node);
          }
          break;
        }
        case "first-child": {
          if (parentNode && node === parentNode.firstElementChild || node === this.#root) {
            matched.add(node);
          }
          break;
        }
        case "last-child": {
          if (parentNode && node === parentNode.lastElementChild || node === this.#root) {
            matched.add(node);
          }
          break;
        }
        case "only-child": {
          if (parentNode && node === parentNode.firstElementChild && node === parentNode.lastElementChild || node === this.#root) {
            matched.add(node);
          }
          break;
        }
        case "first-of-type": {
          if (parentNode) {
            const [node1] = this._collectNthOfType({
              a: 0,
              b: 1
            }, node);
            if (node1) {
              matched.add(node1);
            }
          } else if (node === this.#root) {
            matched.add(node);
          }
          break;
        }
        case "last-of-type": {
          if (parentNode) {
            const [node1] = this._collectNthOfType({
              a: 0,
              b: 1,
              reverse: true
            }, node);
            if (node1) {
              matched.add(node1);
            }
          } else if (node === this.#root) {
            matched.add(node);
          }
          break;
        }
        case "only-of-type": {
          if (parentNode) {
            const [node1] = this._collectNthOfType({
              a: 0,
              b: 1
            }, node);
            if (node1 === node) {
              const [node2] = this._collectNthOfType({
                a: 0,
                b: 1,
                reverse: true
              }, node);
              if (node2 === node) {
                matched.add(node);
              }
            }
          } else if (node === this.#root) {
            matched.add(node);
          }
          break;
        }
        case "defined": {
          if (node.hasAttribute("is") || localName.includes("-")) {
            if (isCustomElement(node)) {
              matched.add(node);
            }
          } else if (node instanceof this.#window.HTMLElement || node instanceof this.#window.SVGElement) {
            matched.add(node);
          }
          break;
        }
        case "popover-open": {
          if (node.popover && isVisible(node)) {
            matched.add(node);
          }
          break;
        }
        case "host":
        case "host-context": {
          break;
        }
        // legacy pseudo-elements
        case "after":
        case "before":
        case "first-letter":
        case "first-line": {
          if (warn) {
            this.onError(new this.#window.DOMException(
              `Unsupported pseudo-element ::${astName}`,
              NOT_SUPPORTED_ERR
            ));
          }
          break;
        }
        // not supported
        case "autofill":
        case "blank":
        case "buffering":
        case "current":
        case "fullscreen":
        case "future":
        case "has-slotted":
        case "modal":
        case "muted":
        case "past":
        case "paused":
        case "picture-in-picture":
        case "playing":
        case "seeking":
        case "stalled":
        case "user-invalid":
        case "user-valid":
        case "volume-locked":
        case "-webkit-autofill": {
          if (warn) {
            this.onError(new this.#window.DOMException(
              `Unsupported pseudo-class :${astName}`,
              NOT_SUPPORTED_ERR
            ));
          }
          break;
        }
        default: {
          if (astName.startsWith("-webkit-")) {
            if (warn) {
              this.onError(new this.#window.DOMException(
                `Unsupported pseudo-class :${astName}`,
                NOT_SUPPORTED_ERR
              ));
            }
          } else if (!forgive) {
            this.onError(new this.#window.DOMException(
              `Unknown pseudo-class :${astName}`,
              SYNTAX_ERR
            ));
          }
        }
      }
    }
    return matched;
  }
  /**
   * match shadow host pseudo class
   * @private
   * @param {object} ast - AST
   * @param {object} node - DocumentFragment node
   * @returns {?object} - matched node
   */
  _matchShadowHostPseudoClass(ast, node) {
    const { children: astChildren, name: astName } = ast;
    if (Array.isArray(astChildren)) {
      if (astChildren.length !== 1) {
        const css = (0, import_css_tree3.generate)(ast);
        return this.onError(new this.#window.DOMException(
          `Invalid selector ${css}`,
          SYNTAX_ERR
        ));
      }
      const { branches } = walkAST(astChildren[0]);
      const [branch] = branches;
      const [...leaves] = branch;
      const { host } = node;
      if (astName === "host") {
        let bool;
        for (const leaf of leaves) {
          const { type: leafType } = leaf;
          if (leafType === COMBINATOR) {
            const css = (0, import_css_tree3.generate)(ast);
            return this.onError(new this.#window.DOMException(
              `Invalid selector ${css}`,
              SYNTAX_ERR
            ));
          }
          bool = this._matchSelector(leaf, host).has(host);
          if (!bool) {
            break;
          }
        }
        if (bool) {
          return node;
        }
        return null;
      } else if (astName === "host-context") {
        let parent = host;
        let bool;
        while (parent) {
          for (const leaf of leaves) {
            const { type: leafType } = leaf;
            if (leafType === COMBINATOR) {
              const css = (0, import_css_tree3.generate)(ast);
              return this.onError(new this.#window.DOMException(
                `Invalid selector ${css}`,
                SYNTAX_ERR
              ));
            }
            bool = this._matchSelector(leaf, parent).has(parent);
            if (!bool) {
              break;
            }
          }
          if (bool) {
            break;
          } else {
            parent = parent.parentNode;
          }
        }
        if (bool) {
          return node;
        }
        return null;
      }
    } else if (astName === "host") {
      return node;
    }
    return this.onError(new this.#window.DOMException(
      `Invalid selector :${astName}`,
      SYNTAX_ERR
    ));
  }
  /**
   * match selector
   * @private
   * @param {object} ast - AST
   * @param {object} node - Document, DocumentFragment, Element node
   * @param {object} [opt] - options
   * @returns {Set.<object>} - collection of matched nodes
   */
  _matchSelector(ast, node, opt = {}) {
    const { type: astType } = ast;
    const astName = unescapeSelector(ast.name);
    const matched = /* @__PURE__ */ new Set();
    if (node.nodeType === ELEMENT_NODE) {
      switch (astType) {
        case ATTR_SELECTOR: {
          const res = matchAttributeSelector(ast, node, opt);
          if (res) {
            matched.add(node);
          }
          break;
        }
        case ID_SELECTOR: {
          if (node.id === astName) {
            matched.add(node);
          }
          break;
        }
        case CLASS_SELECTOR: {
          if (node.classList.contains(astName)) {
            matched.add(node);
          }
          break;
        }
        case PS_CLASS_SELECTOR: {
          const nodes = this._matchPseudoClassSelector(ast, node, opt);
          return nodes;
        }
        case TYPE_SELECTOR: {
          const res = matchTypeSelector(ast, node, opt);
          if (res) {
            matched.add(node);
          }
          break;
        }
        case PS_ELEMENT_SELECTOR:
        default: {
          try {
            const { check } = opt;
            if (check) {
              const css = (0, import_css_tree3.generate)(ast);
              this.#pseudoElement.push(css);
              matched.add(node);
            } else {
              matchPseudoElementSelector(astName, astType, opt);
            }
          } catch (e) {
            this.onError(e);
          }
        }
      }
    } else if (this.#shadow && astType === PS_CLASS_SELECTOR && node.nodeType === DOCUMENT_FRAGMENT_NODE) {
      if (KEY_LOGICAL.includes(astName)) {
        opt.isShadowRoot = true;
        const nodes = this._matchPseudoClassSelector(ast, node, opt);
        return nodes;
      } else if (astName === "host" || astName === "host-context") {
        const res = this._matchShadowHostPseudoClass(ast, node, opt);
        if (res) {
          this.#verifyShadowHost = true;
          matched.add(res);
        }
      }
    }
    return matched;
  }
  /**
   * match leaves
   * @private
   * @param {Array.<object>} leaves - AST leaves
   * @param {object} node - node
   * @param {object} [opt] - options
   * @returns {boolean} - result
   */
  _matchLeaves(leaves, node, opt = {}) {
    let result;
    if (this.#invalidate) {
      result = this.#invalidateResults.get(leaves);
    } else {
      result = this.#results.get(leaves);
    }
    if (result && result.has(node)) {
      const { matched } = result.get(node);
      return matched;
    } else {
      let cacheable = true;
      const formKeys = [...KEY_FORM_FOCUS, "fieldset", "form"];
      const pseudoKeys = ["any-link", "defined", "dir", "link", "scope"];
      if (node.nodeType === ELEMENT_NODE && formKeys.includes(node.localName)) {
        cacheable = false;
      }
      let bool;
      for (const leaf of leaves) {
        switch (leaf.type) {
          case ATTR_SELECTOR:
          case ID_SELECTOR: {
            cacheable = false;
            break;
          }
          case PS_CLASS_SELECTOR: {
            if (pseudoKeys.includes(leaf.name)) {
              cacheable = false;
            }
            break;
          }
          default:
        }
        bool = this._matchSelector(leaf, node, opt).has(node);
        if (!bool) {
          break;
        }
      }
      if (cacheable) {
        if (!result) {
          result = /* @__PURE__ */ new WeakMap();
        }
        result.set(node, {
          matched: bool
        });
        if (this.#invalidate) {
          this.#invalidateResults.set(leaves, result);
        } else {
          this.#results.set(leaves, result);
        }
      }
      return bool;
    }
  }
  /**
   * find descendant nodes
   * @private
   * @param {Array.<object>} leaves - AST leaves
   * @param {object} baseNode - base Element node or Element.shadowRoot
   * @param {object} [opt] - options
   * @returns {Set.<object>} - collection of matched nodes
   */
  _findDescendantNodes(leaves, baseNode, opt = {}) {
    const [leaf, ...filterLeaves] = leaves;
    const compound = filterLeaves.length > 0;
    const { type: leafType } = leaf;
    const leafName = unescapeSelector(leaf.name);
    const nodes = /* @__PURE__ */ new Set();
    let pending = false;
    if (this.#shadow || baseNode.nodeType !== ELEMENT_NODE) {
      pending = true;
    } else {
      switch (leafType) {
        case PS_ELEMENT_SELECTOR: {
          matchPseudoElementSelector(leafName, leafType, opt);
          break;
        }
        case ID_SELECTOR: {
          if (this.#root.nodeType === ELEMENT_NODE) {
            pending = true;
          } else {
            const node = this.#root.getElementById(leafName);
            if (node && node !== baseNode && baseNode.contains(node)) {
              if (compound) {
                const bool = this._matchLeaves(filterLeaves, node, opt);
                if (bool) {
                  nodes.add(node);
                }
              } else {
                nodes.add(node);
              }
            }
          }
          break;
        }
        default: {
          pending = true;
        }
      }
    }
    if (pending) {
      const walker = this._createTreeWalker(baseNode);
      let refNode = traverseNode(baseNode, walker);
      refNode = walker.firstChild();
      while (refNode) {
        const bool = this._matchLeaves(leaves, refNode, opt);
        if (bool) {
          nodes.add(refNode);
        }
        refNode = walker.nextNode();
      }
    }
    return nodes;
  }
  /**
   * match combinator
   * @private
   * @param {object} twig - twig
   * @param {object} node - Element node
   * @param {object} [opt] - option
   * @returns {Set.<object>} - collection of matched nodes
   */
  _matchCombinator(twig, node, opt = {}) {
    const { combo, leaves } = twig;
    const { name: comboName } = combo;
    const { parentNode } = node;
    const { dir } = opt;
    const matched = /* @__PURE__ */ new Set();
    if (dir === DIR_NEXT) {
      switch (comboName) {
        case "+": {
          const refNode = node.nextElementSibling;
          if (refNode) {
            const bool = this._matchLeaves(leaves, refNode, opt);
            if (bool) {
              matched.add(refNode);
            }
          }
          break;
        }
        case "~": {
          if (parentNode) {
            let refNode = node.nextElementSibling;
            while (refNode) {
              const bool = this._matchLeaves(leaves, refNode, opt);
              if (bool) {
                matched.add(refNode);
              }
              refNode = refNode.nextElementSibling;
            }
          }
          break;
        }
        case ">": {
          let refNode = node.firstElementChild;
          while (refNode) {
            const bool = this._matchLeaves(leaves, refNode, opt);
            if (bool) {
              matched.add(refNode);
            }
            refNode = refNode.nextElementSibling;
          }
          break;
        }
        case " ":
        default: {
          const nodes = this._findDescendantNodes(leaves, node, opt);
          if (nodes.size) {
            return nodes;
          }
        }
      }
    } else {
      switch (comboName) {
        case "+": {
          const refNode = node.previousElementSibling;
          if (refNode) {
            const bool = this._matchLeaves(leaves, refNode, opt);
            if (bool) {
              matched.add(refNode);
            }
          }
          break;
        }
        case "~": {
          if (parentNode) {
            let refNode = parentNode.firstElementChild;
            while (refNode) {
              if (refNode === node) {
                break;
              } else {
                const bool = this._matchLeaves(leaves, refNode, opt);
                if (bool) {
                  matched.add(refNode);
                }
              }
              refNode = refNode.nextElementSibling;
            }
          }
          break;
        }
        case ">": {
          if (parentNode) {
            const bool = this._matchLeaves(leaves, parentNode, opt);
            if (bool) {
              matched.add(parentNode);
            }
          }
          break;
        }
        case " ":
        default: {
          const arr = [];
          let refNode = parentNode;
          while (refNode) {
            const bool = this._matchLeaves(leaves, refNode, opt);
            if (bool) {
              arr.push(refNode);
            }
            refNode = refNode.parentNode;
          }
          if (arr.length) {
            return new Set(arr.toReversed());
          }
        }
      }
    }
    return matched;
  }
  /**
   * find matched node(s) preceding this.#node
   * @private
   * @param {Array.<object>} leaves - AST leaves
   * @param {object} node - node to start from
   * @param {object} opt - options
   * @param {boolean} [opt.force] - traverse only to next node
   * @param {string} [opt.targetType] - target type
   * @returns {Array.<object>} - collection of matched nodes
   */
  _findPrecede(leaves, node, opt = {}) {
    const { force, targetType } = opt;
    if (!this.#rootWalker) {
      this.#rootWalker = this._createTreeWalker(this.#root);
    }
    const walker = this.#rootWalker;
    const nodes = [];
    let refNode = traverseNode(node, walker, !!force);
    if (refNode && refNode !== this.#node) {
      if (refNode.nodeType !== ELEMENT_NODE) {
        refNode = walker.nextNode();
      } else if (refNode === node) {
        if (refNode !== this.#root) {
          refNode = walker.nextNode();
        }
      }
      while (refNode) {
        if (refNode === this.#node) {
          break;
        }
        const matched = this._matchLeaves(leaves, refNode, {
          warn: this.#warn
        });
        if (matched) {
          nodes.push(refNode);
          if (targetType !== TARGET_ALL) {
            break;
          }
        }
        refNode = walker.nextNode();
      }
    }
    return nodes;
  }
  /**
   * find matched node(s) in #nodeWalker
   * @private
   * @param {Array.<object>} leaves - AST leaves
   * @param {object} node - node to start from
   * @param {object} opt - options
   * @param {boolean} [opt.precede] - find precede
   * @param {boolean} [opt.force] - traverse only to next node
   * @param {string} [opt.targetType] - target type
   * @returns {Array.<object>} - collection of matched nodes
   */
  _findNodeWalker(leaves, node, opt = {}) {
    const { force, precede, targetType } = opt;
    const walker = this.#nodeWalker;
    if (precede) {
      const precedeNodes = this._findPrecede(leaves, this.#root, opt);
      if (precedeNodes.length) {
        return precedeNodes;
      }
    }
    const nodes = [];
    let refNode = traverseNode(node, walker, !!force);
    if (refNode) {
      if (refNode.nodeType !== ELEMENT_NODE) {
        refNode = walker.nextNode();
      } else if (refNode === node) {
        if (refNode !== this.#root) {
          refNode = walker.nextNode();
        }
      }
      while (refNode) {
        const matched = this._matchLeaves(leaves, refNode, {
          warn: this.#warn
        });
        if (matched) {
          nodes.push(refNode);
          if (targetType !== TARGET_ALL) {
            break;
          }
        }
        refNode = walker.nextNode();
      }
    }
    return nodes;
  }
  /**
   * match self
   * @private
   * @param {Array} leaves - AST leaves
   * @param {boolean} check - running in internal check()
   * @returns {Array} - [nodes, filtered]
   */
  _matchSelf(leaves, check = false) {
    const nodes = [];
    let filtered = false;
    const bool = this._matchLeaves(leaves, this.#node, {
      check,
      warn: this.#warn
    });
    if (bool) {
      nodes.push(this.#node);
      filtered = true;
    }
    return [nodes, filtered, this.#pseudoElement];
  }
  /**
   * find lineal
   * @private
   * @param {Array} leaves - AST leaves
   * @param {object} opt - options
   * @returns {Array} - [nodes, filtered]
   */
  _findLineal(leaves, opt) {
    const { complex } = opt;
    const nodes = [];
    let filtered = false;
    let bool = this._matchLeaves(leaves, this.#node, {
      warn: this.#warn
    });
    if (bool) {
      nodes.push(this.#node);
      filtered = true;
    }
    if (!bool || complex) {
      let refNode = this.#node.parentNode;
      while (refNode) {
        bool = this._matchLeaves(leaves, refNode, {
          warn: this.#warn
        });
        if (bool) {
          nodes.push(refNode);
          filtered = true;
        }
        if (refNode.parentNode) {
          refNode = refNode.parentNode;
        } else {
          break;
        }
      }
    }
    return [nodes, filtered];
  }
  /**
   * find entry nodes
   * @private
   * @param {object} twig - twig
   * @param {string} targetType - target type
   * @param {object} [opt] - options
   * @param {boolean} [opt.complex] - complex selector
   * @param {string} [opt.dir] - find direction
   * @returns {object} - nodes and info about it's state.
   */
  _findEntryNodes(twig, targetType, opt = {}) {
    const { leaves } = twig;
    const [leaf, ...filterLeaves] = leaves;
    const compound = filterLeaves.length > 0;
    const { name: leafName, type: leafType } = leaf;
    const { complex = false, dir = DIR_PREV } = opt;
    const precede = dir === DIR_NEXT && this.#node.nodeType === ELEMENT_NODE && this.#node !== this.#root;
    let nodes = [];
    let filtered = false;
    let pending = false;
    switch (leafType) {
      case PS_ELEMENT_SELECTOR: {
        if (targetType === TARGET_SELF && this.#check) {
          const css = (0, import_css_tree3.generate)(leaf);
          this.#pseudoElement.push(css);
          if (filterLeaves.length) {
            [nodes, filtered] = this._matchSelf(filterLeaves, this.#check);
          } else {
            nodes.push(this.#node);
            filtered = true;
          }
        } else {
          matchPseudoElementSelector(leafName, leafType, {
            warn: this.#warn
          });
        }
        break;
      }
      case ID_SELECTOR: {
        if (targetType === TARGET_SELF) {
          [nodes, filtered] = this._matchSelf(leaves);
        } else if (targetType === TARGET_LINEAL) {
          [nodes, filtered] = this._findLineal(leaves, {
            complex
          });
        } else if (targetType === TARGET_FIRST && this.#root.nodeType !== ELEMENT_NODE) {
          const node = this.#root.getElementById(leafName);
          if (node) {
            if (compound) {
              const bool = this._matchLeaves(filterLeaves, node, {
                warn: this.#warn
              });
              if (bool) {
                nodes.push(node);
                filtered = true;
              }
            } else {
              nodes.push(node);
              filtered = true;
            }
          }
        } else {
          nodes = this._findNodeWalker(leaves, this.#node, {
            precede,
            targetType
          });
          if (nodes.length) {
            filtered = true;
          }
        }
        break;
      }
      case CLASS_SELECTOR: {
        if (targetType === TARGET_SELF) {
          [nodes, filtered] = this._matchSelf(leaves);
        } else if (targetType === TARGET_LINEAL) {
          [nodes, filtered] = this._findLineal(leaves, {
            complex
          });
        } else {
          nodes = this._findNodeWalker(leaves, this.#node, {
            precede,
            targetType
          });
          if (nodes.length) {
            filtered = true;
          }
        }
        break;
      }
      case TYPE_SELECTOR: {
        if (targetType === TARGET_SELF) {
          [nodes, filtered] = this._matchSelf(leaves);
        } else if (targetType === TARGET_LINEAL) {
          [nodes, filtered] = this._findLineal(leaves, {
            complex
          });
        } else {
          nodes = this._findNodeWalker(leaves, this.#node, {
            precede,
            targetType
          });
          if (nodes.length) {
            filtered = true;
          }
        }
        break;
      }
      default: {
        if (targetType !== TARGET_LINEAL && (leafName === "host" || leafName === "host-context")) {
          let shadowRoot;
          if (this.#shadow && this.#node.nodeType === DOCUMENT_FRAGMENT_NODE) {
            shadowRoot = this._matchShadowHostPseudoClass(leaf, this.#node);
          } else if (compound && this.#node.nodeType === ELEMENT_NODE) {
            shadowRoot = this._matchShadowHostPseudoClass(leaf, this.#node.shadowRoot);
          }
          if (shadowRoot) {
            let bool;
            if (compound) {
              for (const item of filterLeaves) {
                if (/^host(?:-context)?$/.test(item.name)) {
                  const node = this._matchShadowHostPseudoClass(item, shadowRoot);
                  bool = node === shadowRoot;
                } else if (item.name === "has") {
                  bool = this._matchPseudoClassSelector(item, shadowRoot, {}).has(shadowRoot);
                } else {
                  bool = false;
                }
                if (!bool) {
                  break;
                }
              }
            } else {
              bool = true;
            }
            if (bool) {
              nodes.push(shadowRoot);
              filtered = true;
            }
          }
        } else if (targetType === TARGET_SELF) {
          [nodes, filtered] = this._matchSelf(leaves);
        } else if (targetType === TARGET_LINEAL) {
          [nodes, filtered] = this._findLineal(leaves, {
            complex
          });
        } else if (targetType === TARGET_FIRST) {
          nodes = this._findNodeWalker(leaves, this.#node, {
            precede,
            targetType
          });
          if (nodes.length) {
            filtered = true;
          }
        } else {
          pending = true;
        }
      }
    }
    return {
      compound,
      filtered,
      nodes,
      pending
    };
  }
  /**
   * collect nodes
   * @private
   * @param {string} targetType - target type
   * @returns {Array.<Array.<object>>} - #ast and #nodes
   */
  _collectNodes(targetType) {
    const ast = this.#ast.values();
    if (targetType === TARGET_ALL || targetType === TARGET_FIRST) {
      const pendingItems = /* @__PURE__ */ new Set();
      let i = 0;
      for (const { branch } of ast) {
        const branchLen = branch.length;
        const complex = branchLen > 1;
        const firstTwig = branch[0];
        let dir;
        let twig;
        if (complex) {
          const {
            combo: firstCombo,
            leaves: [{
              name: firstName,
              type: firstType
            }]
          } = firstTwig;
          const lastTwig = branch[branchLen - 1];
          const {
            leaves: [{
              name: lastName,
              type: lastType
            }]
          } = lastTwig;
          dir = DIR_NEXT;
          twig = firstTwig;
          if (this.#selector.includes(":scope") || lastType === PS_ELEMENT_SELECTOR || lastType === ID_SELECTOR) {
            dir = DIR_PREV;
            twig = lastTwig;
          } else if (firstType === ID_SELECTOR) {
            dir = DIR_NEXT;
            twig = firstTwig;
          } else if (firstName === "*" && firstType === TYPE_SELECTOR) {
            dir = DIR_PREV;
            twig = lastTwig;
          } else if (lastName === "*" && lastType === TYPE_SELECTOR) {
            dir = DIR_NEXT;
            twig = firstTwig;
          } else if (branchLen === 2) {
            if (targetType === TARGET_FIRST) {
              dir = DIR_PREV;
              twig = lastTwig;
            } else {
              const { name: comboName } = firstCombo;
              if (comboName === "+" || comboName === "~") {
                dir = DIR_PREV;
                twig = lastTwig;
              }
            }
          }
        } else {
          dir = DIR_PREV;
          twig = firstTwig;
        }
        const {
          compound,
          filtered,
          nodes,
          pending
        } = this._findEntryNodes(twig, targetType, { complex, dir });
        if (nodes.length) {
          this.#ast[i].find = true;
          this.#nodes[i] = nodes;
        } else if (pending) {
          pendingItems.add(/* @__PURE__ */ new Map([
            ["index", i],
            ["twig", twig]
          ]));
        }
        this.#ast[i].dir = dir;
        this.#ast[i].filtered = filtered || !compound;
        i++;
      }
      if (pendingItems.size) {
        let node;
        let walker;
        if (this.#node !== this.#root && this.#node.nodeType === ELEMENT_NODE) {
          node = this.#node;
          walker = this.#nodeWalker;
        } else {
          if (!this.#rootWalker) {
            this.#rootWalker = this._createTreeWalker(this.#root);
          }
          node = this.#root;
          walker = this.#rootWalker;
        }
        let nextNode = traverseNode(node, walker);
        while (nextNode) {
          let bool = false;
          if (this.#node.nodeType === ELEMENT_NODE) {
            if (nextNode === this.#node) {
              bool = true;
            } else {
              bool = this.#node.contains(nextNode);
            }
          } else {
            bool = true;
          }
          if (bool) {
            for (const pendingItem of pendingItems) {
              const { leaves } = pendingItem.get("twig");
              const matched = this._matchLeaves(leaves, nextNode, {
                warn: this.#warn
              });
              if (matched) {
                const index = pendingItem.get("index");
                this.#ast[index].filtered = true;
                this.#ast[index].find = true;
                this.#nodes[index].push(nextNode);
              }
            }
          }
          if (nextNode !== walker.currentNode) {
            nextNode = traverseNode(nextNode, walker);
          }
          nextNode = walker.nextNode();
        }
      }
    } else {
      let i = 0;
      for (const { branch } of ast) {
        const twig = branch[branch.length - 1];
        const complex = branch.length > 1;
        const dir = DIR_PREV;
        const {
          compound,
          filtered,
          nodes
        } = this._findEntryNodes(twig, targetType, { complex, dir });
        if (nodes.length) {
          this.#ast[i].find = true;
          this.#nodes[i] = nodes;
        }
        this.#ast[i].dir = dir;
        this.#ast[i].filtered = filtered || !compound;
        i++;
      }
    }
    return [
      this.#ast,
      this.#nodes
    ];
  }
  /**
   * get combined nodes
   * @private
   * @param {object} twig - twig
   * @param {object} nodes - collection of nodes
   * @param {string} dir - direction
   * @returns {Set.<object>} - collection of matched nodes
   */
  _getCombinedNodes(twig, nodes, dir) {
    const arr = [];
    for (const node of nodes) {
      const matched = this._matchCombinator(twig, node, {
        dir,
        warn: this.#warn
      });
      if (matched.size) {
        arr.push(...matched);
      }
    }
    if (arr.length) {
      return new Set(arr);
    }
    return /* @__PURE__ */ new Set();
  }
  /**
   * match node to next direction
   * @private
   * @param {Array} branch - branch
   * @param {Set.<object>} nodes - collection of Element node
   * @param {object} opt - option
   * @param {object} opt.combo - combo
   * @param {number} opt.index - index
   * @returns {?object} - matched node
   */
  _matchNodeNext(branch, nodes, opt) {
    const { combo, index } = opt;
    const { combo: nextCombo, leaves } = branch[index];
    const twig = {
      combo,
      leaves
    };
    const nextNodes = this._getCombinedNodes(twig, nodes, DIR_NEXT);
    if (nextNodes.size) {
      if (index === branch.length - 1) {
        const [nextNode] = sortNodes(nextNodes);
        return nextNode;
      } else {
        return this._matchNodeNext(branch, nextNodes, {
          combo: nextCombo,
          index: index + 1
        });
      }
    }
    return null;
  }
  /**
   * match node to previous direction
   * @private
   * @param {Array} branch - branch
   * @param {object} node - Element node
   * @param {object} opt - option
   * @param {number} opt.index - index
   * @returns {?object} - node
   */
  _matchNodePrev(branch, node, opt) {
    const { index } = opt;
    const twig = branch[index];
    const nodes = /* @__PURE__ */ new Set([node]);
    const nextNodes = this._getCombinedNodes(twig, nodes, DIR_PREV);
    if (nextNodes.size) {
      if (index === 0) {
        return node;
      } else {
        let matched;
        for (const nextNode of nextNodes) {
          matched = this._matchNodePrev(branch, nextNode, {
            index: index - 1
          });
          if (matched) {
            break;
          }
        }
        if (matched) {
          return node;
        }
      }
    }
    return null;
  }
  /**
   * find matched nodes
   * @param {string} targetType - target type
   * @returns {Set.<object>} - collection of matched nodes
   */
  find(targetType) {
    if (targetType === TARGET_ALL || targetType === TARGET_FIRST) {
      this._prepareQuerySelectorWalker();
    }
    const [[...branches], collectedNodes] = this._collectNodes(targetType);
    const l = branches.length;
    let sort;
    let nodes = /* @__PURE__ */ new Set();
    for (let i = 0; i < l; i++) {
      const { branch, dir, find: find2 } = branches[i];
      const branchLen = branch.length;
      if (branchLen && find2) {
        const entryNodes = collectedNodes[i];
        const entryNodesLen = entryNodes.length;
        const lastIndex = branchLen - 1;
        if (lastIndex === 0) {
          if ((targetType === TARGET_ALL || targetType === TARGET_FIRST) && this.#node.nodeType === ELEMENT_NODE) {
            for (let j = 0; j < entryNodesLen; j++) {
              const node = entryNodes[j];
              if (node !== this.#node && this.#node.contains(node)) {
                nodes.add(node);
                if (targetType === TARGET_FIRST) {
                  break;
                }
              }
            }
          } else if (targetType === TARGET_ALL) {
            if (nodes.size) {
              nodes.add(...entryNodes);
              sort = true;
            } else {
              nodes = new Set(entryNodes);
            }
          } else {
            const [node] = entryNodes;
            nodes.add(node);
          }
        } else if (targetType === TARGET_ALL) {
          if (dir === DIR_NEXT) {
            const { combo: firstCombo } = branch[0];
            let combo = firstCombo;
            for (const node of entryNodes) {
              let nextNodes = /* @__PURE__ */ new Set([node]);
              for (let j = 1; j < branchLen; j++) {
                const { combo: nextCombo, leaves } = branch[j];
                const twig = {
                  combo,
                  leaves
                };
                nextNodes = this._getCombinedNodes(twig, nextNodes, dir);
                if (nextNodes.size) {
                  if (j === lastIndex) {
                    if (nodes.size) {
                      for (const nextNode of nextNodes) {
                        nodes.add(nextNode);
                      }
                      sort = true;
                      combo = firstCombo;
                    } else {
                      nodes = nextNodes;
                      combo = firstCombo;
                    }
                  } else {
                    combo = nextCombo;
                  }
                } else {
                  break;
                }
              }
            }
          } else {
            for (const node of entryNodes) {
              let nextNodes = /* @__PURE__ */ new Set([node]);
              for (let j = lastIndex - 1; j >= 0; j--) {
                const twig = branch[j];
                nextNodes = this._getCombinedNodes(twig, nextNodes, dir);
                if (nextNodes.size) {
                  if (j === 0) {
                    nodes.add(node);
                    if (branchLen > 1 && nodes.size > 1) {
                      sort = true;
                    }
                  }
                } else {
                  break;
                }
              }
            }
          }
        } else if (targetType === TARGET_FIRST && dir === DIR_NEXT) {
          const { combo: entryCombo } = branch[0];
          let matched;
          for (const node of entryNodes) {
            const matchedNode = this._matchNodeNext(branch, /* @__PURE__ */ new Set([node]), {
              combo: entryCombo,
              index: 1
            });
            if (matchedNode) {
              if (this.#node.nodeType === ELEMENT_NODE) {
                if (matchedNode !== this.#node && this.#node.contains(matchedNode)) {
                  nodes.add(matchedNode);
                  matched = true;
                  break;
                }
              } else {
                nodes.add(matchedNode);
                matched = true;
                break;
              }
            }
          }
          if (!matched) {
            const { leaves: entryLeaves } = branch[0];
            const [entryNode] = entryNodes;
            if (this.#node.contains(entryNode)) {
              let [refNode] = this._findNodeWalker(entryLeaves, entryNode, {
                targetType
              });
              while (refNode) {
                const matchedNode = this._matchNodeNext(branch, /* @__PURE__ */ new Set([refNode]), {
                  combo: entryCombo,
                  index: 1
                });
                if (matchedNode) {
                  if (this.#node.nodeType === ELEMENT_NODE) {
                    if (matchedNode !== this.#node && this.#node.contains(matchedNode)) {
                      nodes.add(matchedNode);
                      break;
                    }
                  } else {
                    nodes.add(matchedNode);
                    break;
                  }
                }
                [refNode] = this._findNodeWalker(entryLeaves, refNode, {
                  targetType,
                  force: true
                });
              }
            } else {
              const { combo: firstCombo } = branch[0];
              let combo = firstCombo;
              let nextNodes = /* @__PURE__ */ new Set([entryNode]);
              for (let j = 1; j < branchLen; j++) {
                const { combo: nextCombo, leaves } = branch[j];
                const twig = {
                  combo,
                  leaves
                };
                nextNodes = this._getCombinedNodes(twig, nextNodes, dir);
                if (nextNodes.size) {
                  if (j === lastIndex) {
                    for (const nextNode of nextNodes) {
                      if (this.#node.contains(nextNode)) {
                        nodes.add(nextNode);
                        break;
                      }
                    }
                  } else {
                    combo = nextCombo;
                  }
                } else {
                  break;
                }
              }
            }
          }
        } else {
          let matched;
          for (const node of entryNodes) {
            const matchedNode = this._matchNodePrev(branch, node, {
              index: lastIndex - 1
            });
            if (matchedNode) {
              nodes.add(node);
              matched = true;
              break;
            }
          }
          if (!matched && targetType === TARGET_FIRST) {
            const { leaves: entryLeaves } = branch[lastIndex];
            const [entryNode] = entryNodes;
            let [refNode] = this._findNodeWalker(entryLeaves, entryNode, {
              targetType
            });
            while (refNode) {
              const matchedNode = this._matchNodePrev(branch, refNode, {
                index: lastIndex - 1
              });
              if (matchedNode) {
                nodes.add(refNode);
                break;
              }
              [refNode] = this._findNodeWalker(entryLeaves, refNode, {
                targetType,
                force: true
              });
            }
          }
        }
      }
    }
    if (this.#check) {
      const match = !!nodes.size;
      let pseudoElement;
      if (this.#pseudoElement.length) {
        pseudoElement = this.#pseudoElement.join("");
      } else {
        pseudoElement = null;
      }
      return {
        match,
        pseudoElement
      };
    }
    if (targetType === TARGET_FIRST) {
      nodes.delete(this.#node);
      if (nodes.size > 1) {
        nodes = new Set(sortNodes(nodes));
      }
    } else if (targetType === TARGET_ALL) {
      nodes.delete(this.#node);
      if (sort && nodes.size > 1) {
        nodes = new Set(sortNodes(nodes));
      }
    }
    return nodes;
  }
};

// src/index.js
var MAX_CACHE = 4096;
var DOMSelector = class {
  /* private fields */
  #window;
  #document;
  #domSymbolTree;
  #finder;
  #idlUtils;
  #nwsapi;
  #cache;
  /**
   * construct
   * @param {object} window - window
   * @param {object} document - document
   * @param {object} [opt] - options
   */
  constructor(window, document, opt = {}) {
    const { domSymbolTree, idlUtils } = opt;
    this.#window = window;
    this.#document = document ?? window.document;
    this.#domSymbolTree = domSymbolTree;
    this.#finder = new Finder(window);
    this.#idlUtils = idlUtils;
    this.#nwsapi = initNwsapi(window, document);
    this.#cache = new import_lru_cache.LRUCache({
      max: MAX_CACHE
    });
  }
  /**
   * @typedef CheckResult
   * @type {object}
   * @property {boolean} match - match result excluding pseudo-element selector
   * @property {string?} pseudoElement - pseudo-element selector
   */
  /**
   * check
   * @param {string} selector - CSS selector
   * @param {object} node - Element node
   * @param {object} [opt] - options
   * @returns {CheckResult} - check result
   */
  check(selector, node, opt = {}) {
    if (!node?.nodeType) {
      const e = new this.#window.TypeError(`Unexpected type ${getType(node)}`);
      this.#finder.onError(e, opt);
    } else if (node.nodeType !== ELEMENT_NODE) {
      const e = new this.#window.TypeError(`Unexpected node ${node.nodeName}`);
      this.#finder.onError(e, opt);
    }
    const document = this.#domSymbolTree ? node._ownerDocument : node.ownerDocument;
    if (document === this.#document && document.contentType === "text/html" && document.documentElement && node.parentNode) {
      const cacheKey = `check_${selector}`;
      let filterMatches = false;
      if (this.#cache.has(cacheKey)) {
        filterMatches = this.#cache.get(cacheKey);
      } else {
        filterMatches = filterSelector(selector, TARGET_SELF);
        this.#cache.set(cacheKey, filterMatches);
      }
      if (filterMatches) {
        try {
          const n = this.#idlUtils ? this.#idlUtils.wrapperForImpl(node) : node;
          const match = this.#nwsapi.match(selector, n);
          return {
            match,
            pseudoElement: null
          };
        } catch (e) {
        }
      }
    }
    let res;
    try {
      if (this.#idlUtils) {
        node = this.#idlUtils.wrapperForImpl(node);
      }
      opt.domSymbolTree = this.#domSymbolTree;
      opt.check = true;
      opt.noexept = true;
      opt.warn = false;
      this.#finder.setup(selector, node, opt);
      res = this.#finder.find(TARGET_SELF);
    } catch (e) {
      this.#finder.onError(e, opt);
    }
    return res;
  }
  /**
   * matches
   * @param {string} selector - CSS selector
   * @param {object} node - Element node
   * @param {object} [opt] - options
   * @returns {boolean} - `true` if matched `false` otherwise
   */
  matches(selector, node, opt = {}) {
    if (!node?.nodeType) {
      const e = new this.#window.TypeError(`Unexpected type ${getType(node)}`);
      this.#finder.onError(e, opt);
    } else if (node.nodeType !== ELEMENT_NODE) {
      const e = new this.#window.TypeError(`Unexpected node ${node.nodeName}`);
      this.#finder.onError(e, opt);
    }
    const document = this.#domSymbolTree ? node._ownerDocument : node.ownerDocument;
    if (document === this.#document && document.contentType === "text/html" && document.documentElement && node.parentNode) {
      const cacheKey = `matches_${selector}`;
      let filterMatches = false;
      if (this.#cache.has(cacheKey)) {
        filterMatches = this.#cache.get(cacheKey);
      } else {
        filterMatches = filterSelector(selector, TARGET_SELF);
        this.#cache.set(cacheKey, filterMatches);
      }
      if (filterMatches) {
        try {
          const n = this.#idlUtils ? this.#idlUtils.wrapperForImpl(node) : node;
          const res2 = this.#nwsapi.match(selector, n);
          return res2;
        } catch (e) {
        }
      }
    }
    let res;
    try {
      if (this.#idlUtils) {
        node = this.#idlUtils.wrapperForImpl(node);
      }
      opt.domSymbolTree = this.#domSymbolTree;
      this.#finder.setup(selector, node, opt);
      const nodes = this.#finder.find(TARGET_SELF);
      res = nodes.size;
    } catch (e) {
      this.#finder.onError(e, opt);
    }
    return !!res;
  }
  /**
   * closest
   * @param {string} selector - CSS selector
   * @param {object} node - Element node
   * @param {object} [opt] - options
   * @returns {?object} - matched node
   */
  closest(selector, node, opt = {}) {
    if (!node?.nodeType) {
      const e = new this.#window.TypeError(`Unexpected type ${getType(node)}`);
      this.#finder.onError(e, opt);
    } else if (node.nodeType !== ELEMENT_NODE) {
      const e = new this.#window.TypeError(`Unexpected node ${node.nodeName}`);
      this.#finder.onError(e, opt);
    }
    const document = this.#domSymbolTree ? node._ownerDocument : node.ownerDocument;
    if (document === this.#document && document.contentType === "text/html" && document.documentElement && node.parentNode) {
      const cacheKey = `closest_${selector}`;
      let filterMatches = false;
      if (this.#cache.has(cacheKey)) {
        filterMatches = this.#cache.get(cacheKey);
      } else {
        filterMatches = filterSelector(selector, TARGET_LINEAL);
        this.#cache.set(cacheKey, filterMatches);
      }
      if (filterMatches) {
        try {
          const n = this.#idlUtils ? this.#idlUtils.wrapperForImpl(node) : node;
          const res2 = this.#nwsapi.closest(selector, n);
          return res2;
        } catch (e) {
        }
      }
    }
    let res;
    try {
      if (this.#idlUtils) {
        node = this.#idlUtils.wrapperForImpl(node);
      }
      opt.domSymbolTree = this.#domSymbolTree;
      this.#finder.setup(selector, node, opt);
      const nodes = this.#finder.find(TARGET_LINEAL);
      if (nodes.size) {
        let refNode = node;
        while (refNode) {
          if (nodes.has(refNode)) {
            res = refNode;
            break;
          }
          refNode = refNode.parentNode;
        }
      }
    } catch (e) {
      this.#finder.onError(e, opt);
    }
    return res ?? null;
  }
  /**
   * query selector
   * @param {string} selector - CSS selector
   * @param {object} node - Document, DocumentFragment, Element node
   * @param {object} [opt] - options
   * @returns {?object} - matched node
   */
  querySelector(selector, node, opt = {}) {
    if (!node?.nodeType) {
      const e = new this.#window.TypeError(`Unexpected type ${getType(node)}`);
      this.#finder.onError(e, opt);
    }
    let res;
    try {
      if (this.#idlUtils) {
        node = this.#idlUtils.wrapperForImpl(node);
      }
      opt.domSymbolTree = this.#domSymbolTree;
      this.#finder.setup(selector, node, opt);
      const nodes = this.#finder.find(TARGET_FIRST);
      if (nodes.size) {
        [res] = [...nodes];
      }
    } catch (e) {
      this.#finder.onError(e, opt);
    }
    return res ?? null;
  }
  /**
   * query selector all
   * NOTE: returns Array, not NodeList
   * @param {string} selector - CSS selector
   * @param {object} node - Document, DocumentFragment, Element node
   * @param {object} [opt] - options
   * @returns {Array.<object|undefined>} - collection of matched nodes
   */
  querySelectorAll(selector, node, opt = {}) {
    if (!node?.nodeType) {
      const e = new this.#window.TypeError(`Unexpected type ${getType(node)}`);
      this.#finder.onError(e, opt);
    }
    let document;
    if (this.#domSymbolTree) {
      document = node._ownerDocument;
    } else if (node.nodeType === DOCUMENT_NODE) {
      document = node;
    } else {
      document = node.ownerDocument;
    }
    if (document === this.#document && document.contentType === "text/html" && document.documentElement) {
      const cacheKey = `querySelectorAll_${selector}`;
      let filterMatches = false;
      if (this.#cache.has(cacheKey)) {
        filterMatches = this.#cache.get(cacheKey);
      } else {
        filterMatches = filterSelector(selector, TARGET_ALL);
        this.#cache.set(cacheKey, filterMatches);
      }
      if (filterMatches) {
        try {
          const n = this.#idlUtils ? this.#idlUtils.wrapperForImpl(node) : node;
          const res2 = this.#nwsapi.select(selector, n);
          return res2;
        } catch (e) {
        }
      }
    }
    let res;
    try {
      if (this.#idlUtils) {
        node = this.#idlUtils.wrapperForImpl(node);
      }
      opt.domSymbolTree = this.#domSymbolTree;
      this.#finder.setup(selector, node, opt);
      const nodes = this.#finder.find(TARGET_ALL);
      if (nodes.size) {
        res = [...nodes];
      }
    } catch (e) {
      this.#finder.onError(e, opt);
    }
    return res ?? [];
  }
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  DOMSelector
});
/*!
 * DOM Selector - A CSS selector engine.
 * @license MIT
 * @copyright asamuzaK (Kazz)
 * @see {@link https://github.com/asamuzaK/domSelector/blob/main/LICENSE}
 */
//# sourceMappingURL=index.cjs.map