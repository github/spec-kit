/*!
 * DOM Selector - A CSS selector engine.
 * @license MIT
 * @copyright asamuzaK (Kazz)
 * @see {@link https://github.com/asamuzaK/domSelector/blob/main/LICENSE}
 */

/* import */
import { LRUCache } from 'lru-cache';
import { Finder } from './js/finder.js';
import { filterSelector, getType, initNwsapi } from './js/utility.js';

/* constants */
import {
  DOCUMENT_NODE, ELEMENT_NODE, TARGET_ALL, TARGET_FIRST, TARGET_LINEAL,
  TARGET_SELF
} from './js/constant.js';
const MAX_CACHE = 4096;

/* DOMSelector */
export class DOMSelector {
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
    this.#cache = new LRUCache({
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
    const document = this.#domSymbolTree
      ? node._ownerDocument
      : node.ownerDocument;
    if (document === this.#document && document.contentType === 'text/html' &&
        document.documentElement && node.parentNode) {
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
          // fall through
        }
      }
    }
    let res;
    try {
      // FIXME: remove later
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
    const document = this.#domSymbolTree
      ? node._ownerDocument
      : node.ownerDocument;
    if (document === this.#document && document.contentType === 'text/html' &&
        document.documentElement && node.parentNode) {
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
          const res = this.#nwsapi.match(selector, n);
          return res;
        } catch (e) {
          // fall through
        }
      }
    }
    let res;
    try {
      // FIXME: remove later
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
    const document = this.#domSymbolTree
      ? node._ownerDocument
      : node.ownerDocument;
    if (document === this.#document && document.contentType === 'text/html' &&
        document.documentElement && node.parentNode) {
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
          const res = this.#nwsapi.closest(selector, n);
          return res;
        } catch (e) {
          // fall through
        }
      }
    }
    let res;
    try {
      // FIXME: remove later
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
      // FIXME: remove later
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
    if (document === this.#document && document.contentType === 'text/html' &&
        document.documentElement) {
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
          const res = this.#nwsapi.select(selector, n);
          return res;
        } catch (e) {
          // fall through
        }
      }
    }
    let res;
    try {
      // FIXME: remove later
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
}
