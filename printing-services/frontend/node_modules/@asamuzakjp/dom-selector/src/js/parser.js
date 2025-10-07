/**
 * parser.js
 */

/* import */
import { findAll, parse, toPlainObject, walk } from 'css-tree';
import { getType } from './utility.js';

/* constants */
import {
  ATTR_SELECTOR, BIT_01, BIT_02, BIT_04, BIT_08, BIT_16, BIT_32, BIT_FFFF,
  CLASS_SELECTOR, DUO, HEX, ID_SELECTOR, KEY_LOGICAL, KEY_PS_STATE,
  KEY_SHADOW_HOST, NTH, PS_CLASS_SELECTOR, PS_ELEMENT_SELECTOR, SELECTOR,
  SYNTAX_ERR, TYPE_SELECTOR
} from './constant.js';
const REG_EMPTY_PS_FUNC = /(?<=:(?:dir|has|host(?:-context)?|is|lang|not|nth-(?:last-)?(?:child|of-type)|where))\(\s+\)/g;
const REG_SHADOW_PS_ELEMENT = /^part|slotted$/;
const U_FFFD = '\uFFFD';

/**
 * unescape selector
 * @param {string} selector - CSS selector
 * @returns {?string} - unescaped selector
 */
export const unescapeSelector = (selector = '') => {
  if (typeof selector === 'string' && selector.indexOf('\\', 0) >= 0) {
    const arr = selector.split('\\');
    const l = arr.length;
    for (let i = 1; i < l; i++) {
      let item = arr[i];
      if (item === '' && i === l - 1) {
        item = U_FFFD;
      } else {
        const hexExists = /^([\da-f]{1,6}\s?)/i.exec(item);
        if (hexExists) {
          const [, hex] = hexExists;
          let str;
          try {
            const low = parseInt('D800', HEX);
            const high = parseInt('DFFF', HEX);
            const deci = parseInt(hex, HEX);
            if (deci === 0 || (deci >= low && deci <= high)) {
              str = U_FFFD;
            } else {
              str = String.fromCodePoint(deci);
            }
          } catch (e) {
            str = U_FFFD;
          }
          let postStr = '';
          if (item.length > hex.length) {
            postStr = item.substring(hex.length);
          }
          item = `${str}${postStr}`;
        // whitespace
        } else if (/^[\n\r\f]/.test(item)) {
          item = '\\' + item;
        }
      }
      arr[i] = item;
    }
    selector = arr.join('');
  }
  return selector;
};

/**
 * preprocess
 * @see https://drafts.csswg.org/css-syntax-3/#input-preprocessing
 * @param {string} selector - string
 * @returns {string} - filtered selector string
 */
export const preprocess = selector => {
  if (typeof selector === 'string') {
    let index = 0;
    while (index >= 0) {
      // @see https://drafts.csswg.org/selectors/#id-selectors
      index = selector.indexOf('#', index);
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
    selector = selector.replace(/\f|\r\n?/g, '\n')
      .replace(/[\0\uD800-\uDFFF]|\\$/g, U_FFFD);
  } else if (selector === undefined || selector === null) {
    selector = getType(selector).toLowerCase();
  } else if (Array.isArray(selector)) {
    selector = selector.join(',');
  } else if (Object.hasOwn(selector, 'toString')) {
    selector = selector.toString();
  } else {
    throw new DOMException(`Invalid selector ${selector}`, SYNTAX_ERR);
  }
  return selector.replace(/\x26/g, ':scope');
};

/**
 * create AST from CSS selector
 * @param {string} selector - CSS selector
 * @returns {object} - AST
 */
export const parseSelector = selector => {
  selector = preprocess(selector);
  // invalid selectors
  if (/^$|^\s*>|,\s*$/.test(selector)) {
    throw new DOMException(`Invalid selector ${selector}`, SYNTAX_ERR);
  }
  let res;
  try {
    const ast = parse(selector, {
      context: 'selectorList',
      parseCustomProperty: true
    });
    res = toPlainObject(ast);
  } catch (e) {
    const { message } = e;
    if (/^(?:"\]"|Attribute selector [()\s,=~^$*|]+) is expected$/.test(message) &&
        !selector.endsWith(']')) {
      const index = selector.lastIndexOf('[');
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
      // workaround for https://github.com/csstree/csstree/issues/283
      if (REG_EMPTY_PS_FUNC.test(selector)) {
        res = parseSelector(`${selector.replaceAll(REG_EMPTY_PS_FUNC, '()')}`);
      } else if (!selector.endsWith(')')) {
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

/**
 * walk AST
 * @param {object} ast - AST
 * @returns {object} - AST branches and info
 */
export const walkAST = (ast = {}) => {
  const branches = new Set();
  const info = new Map();
  const opt = {
    enter: node => {
      switch (node.type) {
        case CLASS_SELECTOR: {
          if (/^-?\d/.test(node.name)) {
            throw new DOMException(`Invalid selector .${node.name}`,
              SYNTAX_ERR);
          }
          break;
        }
        case ID_SELECTOR: {
          if (/^-?\d/.test(node.name)) {
            throw new DOMException(`Invalid selector #${node.name}`,
              SYNTAX_ERR);
          }
          break;
        }
        case PS_CLASS_SELECTOR: {
          if (KEY_LOGICAL.includes(node.name)) {
            info.set('hasNestedSelector', true);
            info.set('hasLogicalPseudoFunc', true);
            if (node.name === 'has') {
              info.set('hasHasPseudoFunc', true);
            }
          } else if (KEY_PS_STATE.includes(node.name)) {
            info.set('hasStatePseudoClass', true);
          } else if (KEY_SHADOW_HOST.includes(node.name) &&
                     Array.isArray(node.children) && node.children.length) {
            info.set('hasNestedSelector', true);
          }
          break;
        }
        case PS_ELEMENT_SELECTOR: {
          if (REG_SHADOW_PS_ELEMENT.test(node.name)) {
            info.set('hasNestedSelector', true);
          }
          break;
        }
        case NTH: {
          if (node.selector) {
            info.set('hasNestedSelector', true);
            info.set('hasNthChildOfSelector', true);
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
  walk(ast, opt);
  if (info.get('hasNestedSelector')) {
    findAll(ast, (node, item, list) => {
      if (list) {
        if (node.type === PS_CLASS_SELECTOR &&
            KEY_LOGICAL.includes(node.name)) {
          const itemList = list.filter(i => {
            const { name, type } = i;
            return type === PS_CLASS_SELECTOR && KEY_LOGICAL.includes(name);
          });
          for (const { children } of itemList) {
            // SelectorList
            for (const { children: grandChildren } of children) {
              // Selector
              for (const { children: greatGrandChildren } of grandChildren) {
                if (branches.has(greatGrandChildren)) {
                  branches.delete(greatGrandChildren);
                }
              }
            }
          }
        } else if (node.type === PS_CLASS_SELECTOR &&
                   KEY_SHADOW_HOST.includes(node.name) &&
                   Array.isArray(node.children) && node.children.length) {
          const itemList = list.filter(i => {
            const { children, name, type } = i;
            const res =
              type === PS_CLASS_SELECTOR && KEY_SHADOW_HOST.includes(name) &&
              Array.isArray(children) && children.length;
            return res;
          });
          for (const { children } of itemList) {
            // Selector
            for (const { children: grandChildren } of children) {
              if (branches.has(grandChildren)) {
                branches.delete(grandChildren);
              }
            }
          }
        } else if (node.type === PS_ELEMENT_SELECTOR &&
                   REG_SHADOW_PS_ELEMENT.test(node.name)) {
          const itemList = list.filter(i => {
            const { name, type } = i;
            const res =
              type === PS_ELEMENT_SELECTOR && REG_SHADOW_PS_ELEMENT.test(name);
            return res;
          });
          for (const { children } of itemList) {
            // Selector
            for (const { children: grandChildren } of children) {
              if (branches.has(grandChildren)) {
                branches.delete(grandChildren);
              }
            }
          }
        } else if (node.type === NTH && node.selector) {
          const itemList = list.filter(i => {
            const { selector, type } = i;
            const res = type === NTH && selector;
            return res;
          });
          for (const { selector } of itemList) {
            const { children } = selector;
            // Selector
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

/**
 * sort AST
 * @param {Array.<object>} asts - collection of AST
 * @returns {Array.<object>} - collection of sorted AST
 */
export const sortAST = asts => {
  const arr = [...asts];
  if (arr.length > 1) {
    const order = new Map([
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

/**
 * parse AST name - e.g. ns|E -> { prefix: ns, localName: E }
 * @param {string} selector - type selector
 * @returns {object} - node properties
 */
export const parseAstName = selector => {
  let prefix;
  let localName;
  if (selector && typeof selector === 'string') {
    if (selector.indexOf('|') > -1) {
      [prefix, localName] = selector.split('|');
    } else {
      prefix = '*';
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

/* export */
export { find as findAST, generate as generateCSS } from 'css-tree';
