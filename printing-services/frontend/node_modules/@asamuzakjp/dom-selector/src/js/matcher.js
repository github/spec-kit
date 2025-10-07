/**
 * matcher.js
 */

/* import */
import { generateCSS, parseAstName, unescapeSelector } from './parser.js';
import { getDirectionality, getType, isNamespaceDeclared } from './utility.js';

/* constants */
import {
  ALPHA_NUM, ELEMENT_NODE, IDENT, LANG_PART, NOT_SUPPORTED_ERR,
  PS_ELEMENT_SELECTOR, STRING, SYNTAX_ERR
} from './constant.js';

/**
 * match pseudo-element selector
 * @param {string} astName - AST name
 * @param {string} astType - AST type
 * @param {object} [opt] - options
 * @param {boolean} [opt.forgive] - forgive unknown pseudo-element
 * @param {boolean} [opt.warn] - warn unsupported pseudo-element
 * @throws {DOMException}
 * @returns {void}
 */
export const matchPseudoElementSelector = (astName, astType, opt = {}) => {
  const { forgive, warn } = opt;
  if (astType === PS_ELEMENT_SELECTOR) {
    switch (astName) {
      case 'after':
      case 'backdrop':
      case 'before':
      case 'cue':
      case 'cue-region':
      case 'first-letter':
      case 'first-line':
      case 'file-selector-button':
      case 'marker':
      case 'placeholder':
      case 'selection':
      case 'target-text': {
        if (warn) {
          throw new DOMException(`Unsupported pseudo-element ::${astName}`,
            NOT_SUPPORTED_ERR);
        }
        break;
      }
      case 'part':
      case 'slotted': {
        if (warn) {
          throw new DOMException(`Unsupported pseudo-element ::${astName}()`,
            NOT_SUPPORTED_ERR);
        }
        break;
      }
      default: {
        if (astName.startsWith('-webkit-')) {
          if (warn) {
            throw new DOMException(`Unsupported pseudo-element ::${astName}`,
              NOT_SUPPORTED_ERR);
          }
        } else if (!forgive) {
          throw new DOMException(`Unknown pseudo-element ::${astName}`,
            SYNTAX_ERR);
        }
      }
    }
  } else {
    throw new TypeError(`Unexpected ast type ${getType(astType)}`);
  }
};

/**
 * match directionality pseudo-class - :dir()
 * @param {object} ast - AST
 * @param {object} node - Element node
 * @returns {boolean} - result
 */
export const matchDirectionPseudoClass = (ast, node) => {
  const { name } = ast;
  if (!name) {
    let type;
    if (name === '') {
      type = '(empty String)';
    } else {
      type = getType(name);
    }
    throw new TypeError(`Unexpected ast type ${type}`);
  }
  const dir = getDirectionality(node);
  return name === dir;
};

/**
 * match language pseudo-class - :lang()
 * @see https://datatracker.ietf.org/doc/html/rfc4647#section-3.3.1
 * @param {object} ast - AST
 * @param {object} node - Element node
 * @returns {boolean} - result
 */
export const matchLanguagePseudoClass = (ast, node) => {
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
  if (astName === '*') {
    if ((html && node.hasAttribute('lang')) ||
        (xml && node.hasAttribute('xml:lang'))) {
      if ((html && node.getAttribute('lang')) ||
        (xml && node.getAttribute('xml:lang'))) {
        return true;
      }
    } else {
      let parent = node.parentNode;
      let res;
      while (parent) {
        if (parent.nodeType === ELEMENT_NODE) {
          if ((html && parent.hasAttribute('lang')) ||
              (xml && parent.hasAttribute('xml:lang'))) {
            if ((html && parent.hasAttribute('lang')) ||
                (xml && parent.hasAttribute('xml:lang'))) {
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
    const reg = new RegExp(`^(?:\\*-)?${ALPHA_NUM}${LANG_PART}$`, 'i');
    if (reg.test(astName)) {
      let regExtendedLang;
      if (astName.indexOf('-') > -1) {
        const [langMain, langSub, ...langRest] = astName.split('-');
        let extendedMain;
        if (langMain === '*') {
          extendedMain = `${ALPHA_NUM}${LANG_PART}`;
        } else {
          extendedMain = `${langMain}${LANG_PART}`;
        }
        const extendedSub = `-${langSub}${LANG_PART}`;
        const len = langRest.length;
        let extendedRest = '';
        if (len) {
          for (let i = 0; i < len; i++) {
            extendedRest += `-${langRest[i]}${LANG_PART}`;
          }
        }
        regExtendedLang =
          new RegExp(`^${extendedMain}${extendedSub}${extendedRest}$`, 'i');
      } else {
        regExtendedLang = new RegExp(`^${astName}${LANG_PART}$`, 'i');
      }
      if ((html && node.hasAttribute('lang')) ||
          (xml && node.hasAttribute('xml:lang'))) {
        const attr = (html && node.getAttribute('lang')) ||
                     (xml && node.getAttribute('xml:lang')) || '';
        return regExtendedLang.test(attr);
      } else {
        let parent = node.parentNode;
        let res;
        while (parent) {
          if (parent.nodeType === ELEMENT_NODE) {
            if ((html && parent.hasAttribute('lang')) ||
                (xml && parent.hasAttribute('xml:lang'))) {
              const attr = (html && parent.getAttribute('lang')) ||
                           (xml && parent.getAttribute('xml:lang')) || '';
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

/**
 * match attribute selector
 * @param {object} ast - AST
 * @param {object} node - Element node
 * @param {object} [opt] - options
 * @param {boolean} [opt.check] - running in internal check()
 * @param {boolean} [opt.forgive] - forgive unknown pseudo-element
 * @returns {boolean} - result
 */
export const matchAttributeSelector = (ast, node, opt = {}) => {
  const {
    flags: astFlags, matcher: astMatcher, name: astName, value: astValue
  } = ast;
  const { check, forgive } = opt;
  if (typeof astFlags === 'string' && !/^[is]$/i.test(astFlags) && !forgive) {
    const css = generateCSS(ast);
    throw new DOMException(`Invalid selector ${css}`, SYNTAX_ERR);
  }
  const { attributes } = node;
  if (attributes?.length) {
    const contentType = node.ownerDocument.contentType;
    let caseInsensitive;
    if (contentType === 'text/html') {
      if (typeof astFlags === 'string' && /^s$/i.test(astFlags)) {
        caseInsensitive = false;
      } else {
        caseInsensitive = true;
      }
    } else if (typeof astFlags === 'string' && /^i$/i.test(astFlags)) {
      caseInsensitive = true;
    } else {
      caseInsensitive = false;
    }
    let astAttrName = unescapeSelector(astName.name);
    if (caseInsensitive) {
      astAttrName = astAttrName.toLowerCase();
    }
    const attrValues = new Set();
    // namespaced
    if (astAttrName.indexOf('|') > -1) {
      const {
        prefix: astPrefix, localName: astLocalName
      } = parseAstName(astAttrName);
      for (const item of attributes) {
        let { name: itemName, value: itemValue } = item;
        if (caseInsensitive) {
          itemName = itemName.toLowerCase();
          itemValue = itemValue.toLowerCase();
        }
        switch (astPrefix) {
          case '': {
            if (astLocalName === itemName) {
              attrValues.add(itemValue);
            }
            break;
          }
          case '*': {
            if (itemName.indexOf(':') > -1) {
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
              const css = generateCSS(ast);
              throw new DOMException(`Invalid selector ${css}`, SYNTAX_ERR);
            }
            if (itemName.indexOf(':') > -1) {
              const [itemPrefix, itemLocalName] = itemName.split(':');
              // ignore xml:lang
              if (itemPrefix === 'xml' && itemLocalName === 'lang') {
                continue;
              } else if (astPrefix === itemPrefix &&
                           astLocalName === itemLocalName) {
                const namespaceDeclared =
                    isNamespaceDeclared(astPrefix, node);
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
        if (itemName.indexOf(':') > -1) {
          const [itemPrefix, itemLocalName] = itemName.split(':');
          // ignore xml:lang
          if (itemPrefix === 'xml' && itemLocalName === 'lang') {
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
      } else if (astStringValue === '') {
        attrValue = astStringValue;
      }
      switch (astMatcher) {
        case '=': {
          return typeof attrValue === 'string' && attrValues.has(attrValue);
        }
        case '~=': {
          if (attrValue && typeof attrValue === 'string') {
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
        case '|=': {
          if (attrValue && typeof attrValue === 'string') {
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
        case '^=': {
          if (attrValue && typeof attrValue === 'string') {
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
        case '$=': {
          if (attrValue && typeof attrValue === 'string') {
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
        case '*=': {
          if (attrValue && typeof attrValue === 'string') {
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

/**
 * match type selector
 * @param {object} ast - AST
 * @param {object} node - Element node
 * @param {object} [opt] - options
 * @param {boolean} [opt.check] - running in internal check()
 * @param {boolean} [opt.forgive] - forgive undeclared namespace
 * @returns {boolean} - result
 */
export const matchTypeSelector = (ast, node, opt = {}) => {
  const astName = unescapeSelector(ast.name);
  const { localName, namespaceURI, prefix } = node;
  const { check, forgive } = opt;
  let {
    prefix: astPrefix, localName: astLocalName
  } = parseAstName(astName, node);
  if (node.ownerDocument.contentType === 'text/html' &&
      (!namespaceURI || namespaceURI === 'http://www.w3.org/1999/xhtml') &&
      /[A-Z][\\w-]*/i.test(localName)) {
    astPrefix = astPrefix.toLowerCase();
    astLocalName = astLocalName.toLowerCase();
  }
  let nodePrefix;
  let nodeLocalName;
  // just in case that the namespaced content is parsed as text/html
  if (localName.indexOf(':') > -1) {
    [nodePrefix, nodeLocalName] = localName.split(':');
  } else {
    nodePrefix = prefix || '';
    nodeLocalName = localName;
  }
  switch (astPrefix) {
    case '': {
      if (!nodePrefix && !namespaceURI &&
          (astLocalName === '*' || astLocalName === nodeLocalName)) {
        return true;
      }
      return false;
    }
    case '*': {
      if (astLocalName === '*' || astLocalName === nodeLocalName) {
        return true;
      }
      return false;
    }
    default: {
      if (!check) {
        if (forgive) {
          return false;
        }
        const css = generateCSS(ast);
        throw new DOMException(`Invalid selector ${css}`, SYNTAX_ERR);
      }
      const astNS = node.lookupNamespaceURI(astPrefix);
      const nodeNS = node.lookupNamespaceURI(nodePrefix);
      if (astNS === nodeNS && astPrefix === nodePrefix) {
        if (astLocalName === '*' || astLocalName === nodeLocalName) {
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
