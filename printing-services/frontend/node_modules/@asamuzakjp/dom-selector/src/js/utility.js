/**
 * utility.js
 */

/* import */
import nwsapi from '@asamuzakjp/nwsapi';
import bidiFactory from 'bidi-js';
import { generate, parse, walk } from 'css-tree';
import isCustomElementName from 'is-potential-custom-element-name';

/* constants */
import {
  ATRULE, COMBO, COMPOUND_I, DESCEND, DOCUMENT_FRAGMENT_NODE, DOCUMENT_NODE,
  DOCUMENT_POSITION_CONTAINS, DOCUMENT_POSITION_PRECEDING, ELEMENT_NODE,
  HAS_COMPOUND, KEY_INPUT_BUTTON, KEY_INPUT_EDIT, KEY_INPUT_TEXT,
  LOGIC_COMPLEX, LOGIC_COMPOUND, N_TH, PSEUDO_CLASS, RULE, SCOPE, SELECTOR_LIST,
  SIBLING, SUB_CLASS, TARGET_ALL, TARGET_FIRST, TEXT_NODE, TYPE_FROM, TYPE_TO
} from './constant.js';
const REG_EXCLUDE_FILTER = /[|\\]|::|[^\u0021-\u007F\s]|\[\s*[\w$*=^|~-]+(?:(?:"[\w$*=^|~\s'-]+"|'[\w$*=^|~\s"-]+')?(?:\s+[\w$*=^|~-]+)+|"[^"\]]{1,255}|'[^'\]]{1,255})\s*\]|:(?:is|where)\(\s*\)/;
const REG_SIMPLE_CLASS = new RegExp(`^${SUB_CLASS}$`);
const REG_COMPLEX = new RegExp(`${COMPOUND_I}${COMBO}${COMPOUND_I}`, 'i');
const REG_DESCEND = new RegExp(`${COMPOUND_I}${DESCEND}${COMPOUND_I}`, 'i');
const REG_SIBLING = new RegExp(`${COMPOUND_I}${SIBLING}${COMPOUND_I}`, 'i');
const REG_LOGIC_COMPLEX =
  new RegExp(`:(?!${PSEUDO_CLASS}|${N_TH}|${LOGIC_COMPLEX})`);
const REG_LOGIC_COMPOUND =
  new RegExp(`:(?!${PSEUDO_CLASS}|${N_TH}|${LOGIC_COMPOUND})`);
const REG_LOGIC_HAS_COMPOUND =
  new RegExp(`:(?!${PSEUDO_CLASS}|${N_TH}|${LOGIC_COMPOUND}|${HAS_COMPOUND})`);
const REG_END_WITH_HAS = new RegExp(`:${HAS_COMPOUND}$`);
const REG_WO_LOGICAL = new RegExp(`:(?!${PSEUDO_CLASS}|${N_TH})`);

/**
 * get type
 * @param {object} o - object to check
 * @returns {string} - type of object
 */
export const getType = o =>
  Object.prototype.toString.call(o).slice(TYPE_FROM, TYPE_TO);

/**
 * verify array contents
 * @param {Array} arr - array
 * @param {string} type - expected type, e.g. 'String'
 * @throws {TypeError} - TypeError
 * @returns {Array} - verified array
 */
export const verifyArray = (arr, type) => {
  if (!Array.isArray(arr)) {
    throw new TypeError(`Unexpected type ${getType(arr)}`);
  }
  if (typeof type !== 'string') {
    throw new TypeError(`Unexpected type ${getType(type)}`);
  }
  for (const item of arr) {
    if (getType(item) !== type) {
      throw new TypeError(`Unexpected type ${getType(item)}`);
    }
  }
  return arr;
};

/**
 * resolve content document, root node and tree walker, is in shadow
 * @param {object} node - Document, DocumentFragment, Element node
 * @returns {Array.<object|boolean>}
 *   - array of document, root node , tree walker, node is in shadow
 */
export const resolveContent = node => {
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
      shadow = host && (mode === 'close' || mode === 'open');
      break;
    }
    case ELEMENT_NODE: {
      document = node.ownerDocument;
      let refNode = node;
      while (refNode) {
        const { host, mode, nodeType, parentNode } = refNode;
        if (nodeType === DOCUMENT_FRAGMENT_NODE) {
          shadow = host && (mode === 'close' || mode === 'open');
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
    default : {
      throw new TypeError(`Unexpected node ${node.nodeName}`);
    }
  }
  return [
    document,
    root,
    !!shadow
  ];
};

/**
 * traverse node tree
 * @param {object} node - node
 * @param {object} walker - tree walker
 * @param {boolean} [force] - traverse only to next node
 * @returns {?object} - current node
 */
export const traverseNode = (node, walker, force = false) => {
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

/**
 * is custom element
 * @param {object} node - Element node
 * @param {object} [opt] - options
 * @returns {boolean} - result
 */
export const isCustomElement = (node, opt = {}) => {
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
  const attr = node.getAttribute('is');
  if (attr) {
    elmConstructor =
      isCustomElementName(attr) && window.customElements.get(attr);
  } else {
    elmConstructor =
      isCustomElementName(localName) && window.customElements.get(localName);
  }
  if (elmConstructor) {
    if (formAssociated) {
      return !!elmConstructor.formAssociated;
    }
    return true;
  }
  return false;
};

/**
 * get slotted text content
 * @param {object} node - Element node
 * @returns {?string} - text content
 */
export const getSlottedTextContent = node => {
  if (!node?.nodeType) {
    throw new TypeError(`Unexpected type ${getType(node)}`);
  }
  if (typeof node.assignedNodes !== 'function') {
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

/**
 * get directionality of node
 * @see https://html.spec.whatwg.org/multipage/dom.html#the-dir-attribute
 * @param {object} node - Element node
 * @returns {?string} - 'ltr' / 'rtl'
 */
export const getDirectionality = node => {
  if (!node?.nodeType) {
    throw new TypeError(`Unexpected type ${getType(node)}`);
  }
  if (node.nodeType !== ELEMENT_NODE) {
    return null;
  }
  const { dir: dirAttr, localName, parentNode } = node;
  const { getEmbeddingLevels } = bidiFactory();
  if (dirAttr === 'ltr' || dirAttr === 'rtl') {
    return dirAttr;
  } else if (dirAttr === 'auto') {
    let text;
    switch (localName) {
      case 'input': {
        const valueKeys = [...KEY_INPUT_BUTTON, ...KEY_INPUT_TEXT, 'hidden'];
        if (!node.type || valueKeys.includes(node.type)) {
          text = node.value;
        } else {
          const ltrKeys = [
            'checkbox', 'color', 'date', 'image', 'number', 'range', 'radio',
            'time'
          ];
          if (ltrKeys.includes(node.type)) {
            return 'ltr';
          }
        }
        break;
      }
      case 'slot': {
        text = getSlottedTextContent(node);
        break;
      }
      case 'textarea': {
        text = node.value;
        break;
      }
      default: {
        const items = [].slice.call(node.childNodes);
        for (const item of items) {
          const {
            dir: itemDir, localName: itemLocalName, nodeType: itemNodeType,
            textContent: itemTextContent
          } = item;
          if (itemNodeType === TEXT_NODE) {
            text = itemTextContent.trim();
          } else if (itemNodeType === ELEMENT_NODE) {
            const keys = ['bdi', 'script', 'style', 'textarea'];
            if (!keys.includes(itemLocalName) &&
                (!itemDir || (itemDir !== 'ltr' && itemDir !== 'rtl'))) {
              if (itemLocalName === 'slot') {
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
        return 'rtl';
      }
    } else if (parentNode) {
      const { nodeType: parentNodeType } = parentNode;
      if (parentNodeType === ELEMENT_NODE) {
        return getDirectionality(parentNode);
      }
    }
  } else if (localName === 'input' && node.type === 'tel') {
    return 'ltr';
  } else if (localName === 'bdi') {
    const text = node.textContent.trim();
    if (text) {
      const { paragraphs: [{ level }] } = getEmbeddingLevels(text);
      if (level % 2 === 1) {
        return 'rtl';
      }
    }
  } else if (parentNode) {
    if (localName === 'slot') {
      const text = getSlottedTextContent(node);
      if (text) {
        const { paragraphs: [{ level }] } = getEmbeddingLevels(text);
        if (level % 2 === 1) {
          return 'rtl';
        }
        return 'ltr';
      }
    }
    const { nodeType: parentNodeType } = parentNode;
    if (parentNodeType === ELEMENT_NODE) {
      return getDirectionality(parentNode);
    }
  }
  return 'ltr';
};

/**
 * is content editable
 * NOTE: not implemented in jsdom https://github.com/jsdom/jsdom/issues/1670
 * @param {object} node - Element node
 * @returns {boolean} - result
 */
export const isContentEditable = node => {
  if (!node?.nodeType) {
    throw new TypeError(`Unexpected type ${getType(node)}`);
  }
  if (node.nodeType !== ELEMENT_NODE) {
    return false;
  }
  if (typeof node.isContentEditable === 'boolean') {
    return node.isContentEditable;
  } else if (node.ownerDocument.designMode === 'on') {
    return true;
  } else {
    let attr;
    if (node.hasAttribute('contenteditable')) {
      attr = node.getAttribute('contenteditable');
    } else {
      attr = 'inherit';
    }
    switch (attr) {
      case '':
      case 'true': {
        return true;
      }
      case 'plaintext-only': {
        // FIXME:
        // @see https://github.com/w3c/editing/issues/470
        // @see https://github.com/whatwg/html/issues/10651
        return true;
      }
      case 'false': {
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

/**
 * is node visible
 * @param {object} node - Element node
 * @returns {boolean} - result
 */
export const isVisible = node => {
  if (node?.nodeType !== ELEMENT_NODE) {
    return false;
  }
  const window = node.ownerDocument.defaultView;
  const { display, visibility } = window.getComputedStyle(node);
  if (display !== 'none' && visibility === 'visible') {
    return true;
  }
  return false;
};

/**
 * is focus visible
 * @param {object} node - Element node
 * @returns {boolean} - result
 */
export const isFocusVisible = node => {
  if (node?.nodeType !== ELEMENT_NODE) {
    return false;
  }
  const { localName, type } = node;
  switch (localName) {
    case 'input': {
      if (!type || KEY_INPUT_EDIT.includes(type)) {
        return true;
      }
      return false;
    }
    case 'textarea': {
      return true;
    }
    default: {
      return isContentEditable(node);
    }
  }
};

/**
 * is focusable area
 * @param {object} node - Element node
 * @returns {boolean} - result
 */
export const isFocusableArea = node => {
  if (node?.nodeType !== ELEMENT_NODE) {
    return false;
  }
  if (!node.isConnected) {
    return false;
  }
  const window = node.ownerDocument.defaultView;
  if (node instanceof window.HTMLElement) {
    if (Number.isInteger(parseInt(node.getAttribute('tabindex')))) {
      return true;
    }
    if (isContentEditable(node)) {
      return true;
    }
    const { localName, parentNode } = node;
    switch (localName) {
      case 'a': {
        if (node.href || node.hasAttribute('href')) {
          return true;
        }
        return false;
      }
      case 'iframe': {
        return true;
      }
      case 'input': {
        if (node.disabled || node.hasAttribute('disabled') ||
            node.hidden || node.hasAttribute('hidden')) {
          return false;
        }
        return true;
      }
      case 'summary': {
        if (parentNode.localName === 'details') {
          let child = parentNode.firstElementChild;
          let bool = false;
          while (child) {
            if (child.localName === 'summary') {
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
        const keys = ['button', 'select', 'textarea'];
        if (keys.includes(localName) &&
            !(node.disabled || node.hasAttribute('disabled'))) {
          return true;
        }
      }
    }
  } else if (node instanceof window.SVGElement) {
    if (Number.isInteger(parseInt(node.getAttributeNS(null, 'tabindex')))) {
      const keys = [
        'clipPath', 'defs', 'desc', 'linearGradient', 'marker', 'mask',
        'metadata', 'pattern', 'radialGradient', 'script', 'style', 'symbol',
        'title'
      ];
      const ns = 'http://www.w3.org/2000/svg';
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
    if (node.localName === 'a' &&
        (node.href || node.hasAttributeNS(null, 'href'))) {
      return true;
    }
  }
  return false;
};

/**
 * is focusable
 * NOTE: not applied, need fix in jsdom itself
 * @see https://github.com/whatwg/html/pull/8392
 * @see https://phabricator.services.mozilla.com/D156219
 * @see https://github.com/jsdom/jsdom/issues/3029
 * @see https://github.com/jsdom/jsdom/issues/3464
 * @param {object} node - Element node
 * @returns {boolean} - result
 */
export const isFocusable = node => {
  if (node?.nodeType !== ELEMENT_NODE) {
    return false;
  }
  const window = node.ownerDocument.defaultView;
  let refNode = node;
  let res = true;
  while (refNode) {
    if (refNode.disabled || refNode.hasAttribute('disabled')) {
      res = false;
      break;
    }
    if (refNode.hidden || refNode.hasAttribute('hidden')) {
      res = false;
    }
    const {
      contentVisibility, display, visibility
    } = window.getComputedStyle(refNode);
    if (display === 'none' || visibility !== 'visible' ||
        (contentVisibility === 'hidden' && refNode !== node)) {
      res = false;
    } else {
      res = true;
    }
    if (res && refNode?.parentNode?.nodeType === ELEMENT_NODE) {
      refNode = refNode.parentNode;
    } else {
      break;
    }
  }
  return res;
};

/**
 * get namespace URI
 * @param {string} ns - namespace prefix
 * @param {Array} node - Element node
 * @returns {?string} - namespace URI
 */
export const getNamespaceURI = (ns, node) => {
  if (typeof ns !== 'string') {
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

/**
 * is namespace declared
 * @param {string} ns - namespace
 * @param {object} node - Element node
 * @returns {boolean} - result
 */
export const isNamespaceDeclared = (ns = '', node = {}) => {
  if (!ns || typeof ns !== 'string' || node?.nodeType !== ELEMENT_NODE) {
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

/**
 * is preceding - nodeA precedes and/or contains nodeB
 * @param {object} nodeA - Element node
 * @param {object} nodeB - Element node
 * @returns {boolean} - result
 */
export const isPreceding = (nodeA, nodeB) => {
  if (!nodeA?.nodeType) {
    throw new TypeError(`Unexpected type ${getType(nodeA)}`);
  } else if (!nodeB?.nodeType) {
    throw new TypeError(`Unexpected type ${getType(nodeB)}`);
  }
  if (nodeA.nodeType !== ELEMENT_NODE || nodeB.nodeType !== ELEMENT_NODE) {
    return false;
  }
  const posBit = nodeB.compareDocumentPosition(nodeA);
  const res = posBit & DOCUMENT_POSITION_PRECEDING ||
              posBit & DOCUMENT_POSITION_CONTAINS;
  return !!res;
};

/**
 * sort nodes
 * @param {Array.<object>|Set.<object>} nodes - collection of nodes
 * @returns {Array.<object>} - collection of sorted nodes
 */
export const sortNodes = (nodes = []) => {
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

/**
 * concat array of nested selectors into equivalent selector
 * @param {Array.<Array.<string>>} selectors - [parents, children, ...]
 * @returns {string} - selector
 */
export const concatNestedSelectors = selectors => {
  if (!Array.isArray(selectors)) {
    throw new TypeError(`Unexpected type ${getType(selectors)}`);
  }
  let selector = '';
  if (selectors.length) {
    const revSelectors = selectors.toReversed();
    let child = verifyArray(revSelectors.shift(), 'String');
    if (child.length === 1) {
      [child] = child;
    }
    while (revSelectors.length) {
      const parentArr = verifyArray(revSelectors.shift(), 'String');
      if (!parentArr.length) {
        continue;
      }
      let parent;
      if (parentArr.length === 1) {
        [parent] = parentArr;
        if (!/^[>~+]/.test(parent) && /[\s>~+]/.test(parent)) {
          parent = `:is(${parent})`;
        }
      } else {
        parent = `:is(${parentArr.join(', ')})`;
      }
      if (selector.includes('\x26')) {
        selector = selector.replace(/\x26/g, parent);
      }
      if (Array.isArray(child)) {
        const items = [];
        for (let item of child) {
          if (item.includes('\x26')) {
            if (/^[>~+]/.test(item)) {
              item = `${parent} ${item.replace(/\x26/g, parent)} ${selector}`;
            } else {
              item = `${item.replace(/\x26/g, parent)} ${selector}`;
            }
          } else {
            item = `${parent} ${item} ${selector}`;
          }
          items.push(item.trim());
        }
        selector = items.join(', ');
      } else if (revSelectors.length) {
        selector = `${child} ${selector}`;
      } else {
        if (child.includes('\x26')) {
          if (/^[>~+]/.test(child)) {
            selector =
              `${parent} ${child.replace(/\x26/g, parent)} ${selector}`;
          } else {
            selector = `${child.replace(/\x26/g, parent)} ${selector}`;
          }
        } else {
          selector = `${parent} ${child} ${selector}`;
        }
      }
      selector = selector.trim();
      if (revSelectors.length) {
        child = parentArr.length > 1 ? parentArr : parent;
      } else {
        break;
      }
    }
    selector = selector.replace(/\x26/g, ':scope').trim();
  }
  return selector;
};

/**
 * extract nested selectors from CSSRule.cssText
 * @param {string} css - CSSRule.cssText
 * @returns {Array.<Array.<string>>} - array of nested selectors
 */
export const extractNestedSelectors = css => {
  const ast = parse(css, {
    context: 'rule'
  });
  const selectors = [];
  let isScoped = false;
  walk(ast, {
    enter: node => {
      switch (node.type) {
        case ATRULE: {
          if (node.name === 'scope') {
            isScoped = true;
          }
          break;
        }
        case SCOPE: {
          const { children, type } = node.root;
          const arr = [];
          if (type === SELECTOR_LIST) {
            for (const child of children) {
              const selector = generate(child);
              arr.push(selector);
            }
            selectors.push(arr);
          }
          break;
        }
        case RULE: {
          const { children, type } = node.prelude;
          const arr = [];
          if (type === SELECTOR_LIST) {
            let hasAmp = false;
            for (const child of children) {
              const selector = generate(child);
              if (isScoped && !hasAmp) {
                hasAmp = /\x26/.test(selector);
              }
              arr.push(selector);
            }
            if (isScoped) {
              if (hasAmp) {
                selectors.push(arr);
              /* FIXME:
              } else {
                selectors = arr;
                isScoped = false;
              */
              }
            } else {
              selectors.push(arr);
            }
          }
        }
      }
    },
    leave: node => {
      if (node.type === ATRULE) {
        if (node.name === 'scope') {
          isScoped = false;
        }
      }
    }
  });
  return selectors;
};

/**
 * init nwsapi
 * @param {object} window - Window
 * @param {object} document - Document
 * @returns {object} - nwsapi
 */
export const initNwsapi = (window, document) => {
  if (!window?.DOMException) {
    throw new TypeError(`Unexpected global object ${getType(window)}`);
  }
  if (document?.nodeType !== DOCUMENT_NODE) {
    document = window.document;
  }
  const nw = nwsapi({
    document,
    DOMException: window.DOMException
  });
  nw.configure({
    LOGERRORS: false
  });
  return nw;
};

/**
 * filter selector (for nwsapi)
 * @param {string} selector - selector
 * @param {string} target - target type
 * @returns {boolean} - result
 */
export const filterSelector = (selector, target) => {
  if (!selector || typeof selector !== 'string' || /null|undefined/.test(selector) || target === TARGET_FIRST) {
    return false;
  }
  // exclude simple class selector
  if (target === TARGET_ALL && REG_SIMPLE_CLASS.test(selector)) {
    return false;
  }
  // exclude missing close square bracket
  if (selector.includes('[')) {
    const index = selector.lastIndexOf('[');
    const sel = selector.substring(index);
    if (sel.indexOf(']') < 0) {
      return false;
    }
  }
  // exclude '/',
  // exclude namespaced selectors, escaped selectors, pseudo-element selectors,
  // selectors containing non-ASCII or control character other than whitespace,
  // attribute selectors with case flag, e.g. [attr i], or with unclosed quotes,
  // and empty :is() or :where()
  if (selector.includes('/') || REG_EXCLUDE_FILTER.test(selector)) {
    return false;
  }
  // include pseudo-classes that are known to work correctly
  if (selector.includes(':')) {
    let complex = false;
    if (target !== TARGET_ALL) {
      complex = REG_COMPLEX.test(selector);
    }
    if (target === TARGET_ALL && REG_DESCEND.test(selector) &&
        !REG_SIBLING.test(selector)) {
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
