/**
 * Forked and modified from nwsapi@2.2.2
 * - Export to cjs only
 * - Remove ./modules directory
 * - Remove unused exported properties
 * - Remove unused pseudo-classes
 * - Remove Snapshot.root and resolve document.documentElement on runtime
 * - Use `let` and `const` as much as possible
 * - Use `===` and `!==`
 * - Fix `:nth-of-type()`
 * - Fix function source for :root, :target and :indeterminate pseudo-classes
 * - Fix <ident-token>
 * - Support complex selectors within `:is()` and `:not()`
 * - Add ::slotted() and ::part() to pseudo-elements list
 * - Add isContentEditable() function
 * - Add createMatchingParensRegex() function from upstream
 * - Invalidate cache for :has() pseudo class
 * - Optimize some regular expressions
 */
/*
 * Copyright (C) 2007-2019 Diego Perini
 * All rights reserved.
 *
 * nwsapi.js - Fast CSS Selectors API Engine
 *
 * Author: Diego Perini <diego.perini at gmail com>
 * Version: 2.2.0
 * Created: 20070722
 * Release: 20220901
 *
 * License:
 *  http://javascript.nwbox.com/nwsapi/MIT-LICENSE
 * Download:
 *  http://javascript.nwbox.com/nwsapi/nwsapi.js
 */

(function Export(global, factory) {
  'use strict';
  module.exports = factory;
})(this, function Factory(global, Export) {
  const version = 'nwsapi-2.2.2';

  let doc = global.document;

  /**
   * Generate a regex that matches a balanced set of parentheses.
   * Outermost parentheses are excluded so any amount of children can be handled.
   * See https://stackoverflow.com/a/35271017 for reference
   *
   * @param {number} depth
   * @return {string}
   */
  function createMatchingParensRegex(depth = 1) {
    const out = '\\([^)(]*?(?:'.repeat(depth) + '\\([^)(]*?\\)' + '[^)(]*?)*?\\)'.repeat(depth);
    // remove outermost escaped parens
    return out.slice(2, out.length - 2);
  }

  const CFG = {
    // extensions
    operators: '[~*^$|]=|=',
    combinators: '[\\s>+~](?=[^>+~])'
  };

  const NOT = {
    // not enclosed in double/single/parens/square
    doubleEnc: '(?=(?:[^"]*"[^"]*")*[^"]*$)',
    singleEnc: "(?=(?:[^']*'[^']*')*[^']*$)",
    parensEnc: '(?![^\\x28]*\\x29)',
    squareEnc: '(?![^\\x5b]*\\x5d)'
  };

  const REX = {
    // regular expressions
    hasEscapes: /\\/,
    hexNumbers: /^[0-9a-f]/i,
    escOrQuote: /^\\|[\x22\x27]/,
    regExpChar: /(?:(?!\\)[\\^$.*+?()[\]{}|/])/g,
    trimSpaces: /[\r\n\f]|^\s+|\s+$/g,
    commaGroup: RegExp('(\\s{0,255},\\s{0,255})' + NOT.squareEnc + NOT.parensEnc, 'g'),
    splitGroup: /((?:\x28[^\x29]{0,255}\x29|\[[^\]]{0,255}\]|\\.|[^,])+)/g,
    fixEscapes: /\\([0-9a-f]{1,6}\s?|.)|([\x22\x27])/gi,
    combineWSP: RegExp('\\s{1,255}' + NOT.singleEnc + NOT.doubleEnc, 'g'),
    tabCharWSP: RegExp('(\\s?\\t{1,255}\\s?)' + NOT.singleEnc + NOT.doubleEnc, 'g'),
    pseudosWSP: RegExp('\\s{1,255}([-+])\\s{1,255}' + NOT.squareEnc, 'g')
  };

  const STD = {
    combinator: /\s?([>+~])\s?/g,
    apimethods: /^(?:[a-z]+|\*)\|/i,
    namespaces: /(\*|[a-z]+)\|[-a-z]+/i
  };

  const GROUPS = {
    // pseudo-classes requiring parameters
    logicalsel: '(is|where|matches|not|has)(?:\\x28\\s?(' + createMatchingParensRegex(3) + ')\\s?\\x29)',
    treestruct: '(nth(?:-last)?(?:-child|-of-type))(?:\\x28\\s?(even|odd|(?:[-+]?\\d*)(?:n\\s?[-+]?\\s?\\d*)?)\\s?(?:\\x29|$))',
    // pseudo-classes not requiring parameters
    locationpc: '(any-link|link|visited|target)\\b',
    structural: '(root|empty|(?:(?:first|last|only)(?:-child|-of-type)))\\b',
    inputstate: '(enabled|disabled|read-(?:only|write)|placeholder-shown|default)\\b',
    inputvalue: '(checked|indeterminate)\\b',
    // pseudo-classes for parsing only selectors
    pseudoNop: '(autofill|-webkit-autofill)\\b',
    // pseudo-elements starting with single colon (:)
    pseudoSng: '(after|before|first-letter|first-line)\\b',
    // pseudo-elements starting with double colon (::)
    pseudoDbl: ':(after|before|first-letter|first-line|selection|part|placeholder|slotted|-webkit-[-a-z0-9]{2,})\\b'
  };

  const Patterns = {
    // pseudo-classes
    treestruct: RegExp('^:(?:' + GROUPS.treestruct + ')(.*)', 'i'),
    structural: RegExp('^:(?:' + GROUPS.structural + ')(.*)', 'i'),
    inputstate: RegExp('^:(?:' + GROUPS.inputstate + ')(.*)', 'i'),
    inputvalue: RegExp('^:(?:' + GROUPS.inputvalue + ')(.*)', 'i'),
    locationpc: RegExp('^:(?:' + GROUPS.locationpc + ')(.*)', 'i'),
    logicalsel: RegExp('^:(?:' + GROUPS.logicalsel + ')(.*)', 'i'),
    pseudoNop: RegExp('^:(?:' + GROUPS.pseudoNop + ')(.*)', 'i'),
    pseudoSng: RegExp('^:(?:' + GROUPS.pseudoSng + ')(.*)', 'i'),
    pseudoDbl: RegExp('^:(?:' + GROUPS.pseudoDbl + ')(.*)', 'i'),
    // combinator symbols
    children: /^\s?>\s?(.*)/,
    adjacent: /^\s?\+\s?(.*)/,
    relative: /^\s?~\s?(.*)/,
    ancestor: /^\s+(.*)/,
    // universal & namespace
    universal: /^\*(.*)/,
    namespace: /^(\w+|\*)?\|(.*)/
  };

  // emulate firefox error strings
  const qsNotArgs = 'Not enough arguments';
  const qsInvalid = ' is not a valid selector';

  // detect structural pseudo-classes in selectors
  const reNthElem = /(:nth(?:-last)?-child)/i;
  const reNthType = /(:nth(?:-last)?-of-type)/i;

  // placeholder for global regexp
  let reOptimizer;
  let reValidator;

  // special handling configuration flags
  const Config = {
    IDS_DUPES: true,
    MIXEDCASE: true,
    LOGERRORS: true,
    VERBOSITY: true
  };

  let NAMESPACE;
  let QUIRKS_MODE;
  let HTML_DOCUMENT;

  const ATTR_STD_OPS = {
    '=': 1,
    '^=': 1,
    '$=': 1,
    '|=': 1,
    '*=': 1,
    '~=': 1
  };

  const HTML_TABLE = {
    accept: 1,
    'accept-charset': 1,
    align: 1,
    alink: 1,
    axis: 1,
    bgcolor: 1,
    charset: 1,
    checked: 1,
    clear: 1,
    codetype: 1,
    color: 1,
    compact: 1,
    declare: 1,
    defer: 1,
    dir: 1,
    direction: 1,
    disabled: 1,
    enctype: 1,
    face: 1,
    frame: 1,
    hreflang: 1,
    'http-equiv': 1,
    lang: 1,
    language: 1,
    link: 1,
    media: 1,
    method: 1,
    multiple: 1,
    nohref: 1,
    noresize: 1,
    noshade: 1,
    nowrap: 1,
    readonly: 1,
    rel: 1,
    rev: 1,
    rules: 1,
    scope: 1,
    scrolling: 1,
    selected: 1,
    shape: 1,
    target: 1,
    text: 1,
    type: 1,
    valign: 1,
    valuetype: 1,
    vlink: 1
  };

  const Combinators = {};

  const Selectors = {};

  const Operators = {
    '=': {
      p1: '^',
      p2: '$',
      p3: 'true'
    },
    '^=': {
      p1: '^',
      p2: '',
      p3: 'true'
    },
    '$=': {
      p1: '',
      p2: '$',
      p3: 'true'
    },
    '*=': {
      p1: '',
      p2: '',
      p3: 'true'
    },
    '|=': {
      p1: '^',
      p2: '(-|$)',
      p3: 'true'
    },
    '~=': {
      p1: '(^|\\s)',
      p2: '(\\s|$)',
      p3: 'true'
    }
  };

  const concatCall = function (nodes, callback) {
    let i = 0;
    const l = nodes.length;
    const list = Array(l);
    while (l > i) {
      if (callback(list[i] = nodes[i]) === false) {
        break;
      }
      ++i;
    }
    return list;
  };

  const concatList = function (list, nodes) {
    let i = -1;
    let l = nodes.length;
    while (l--) {
      list[list.length] = nodes[++i];
    }
    return list;
  };

  let hasDupes = false;

  const documentOrder = function (a, b) {
    if (!hasDupes && a === b) {
      hasDupes = true;
      return 0;
    }
    return a.compareDocumentPosition(b) & 4 ? -1 : 1;
  };

  const unique = function (nodes) {
    let i = 0;
    let j = -1;
    let l = nodes.length + 1;
    const list = [];
    while (--l) {
      if (nodes[i++] === nodes[i]) {
        continue;
      }
      list[++j] = nodes[i - 1];
    }
    hasDupes = false;
    return list;
  };

  // check context for mixed content
  const hasMixedCaseTagNames = function (context) {
    const api = 'getElementsByTagNameNS';

    // current host context (ownerDocument)
    context = context.ownerDocument || context;

    // documentElement (root) element namespace or default html/xhtml namespace
    const ns = context.documentElement && context.documentElement.namespaceURI
       ? context.documentElement.namespaceURI
       : 'http://www.w3.org/1999/xhtml';

    // checking the number of non HTML nodes in the document
    return (context[api]('*', '*').length - context[api](ns, '*').length) > 0;
  };

  // check if the document type is HTML
  const isHTML = function (node) {
    const doc = node.ownerDocument || node;
    return doc.nodeType === 9 && doc.contentType === 'text/html';
  };

  // convert single codepoint to UTF-16 encoding
  const codePointToUTF16 = function (codePoint) {
    // out of range, use replacement character
    if (codePoint < 1 || codePoint > 0x10ffff ||
        (codePoint > 0xd7ff && codePoint < 0xe000)) {
      return '\\ufffd';
    }
    // javascript strings are UTF-16 encoded
    if (codePoint < 0x10000) {
      const lowHex = '000' + codePoint.toString(16);
      return '\\u' + lowHex.substr(lowHex.length - 4);
    }
    // supplementary high + low surrogates
    return '\\u' + (((codePoint - 0x10000) >> 0x0a) + 0xd800).toString(16) +
           '\\u' + (((codePoint - 0x10000) % 0x400) + 0xdc00).toString(16);
  };

  // convert single codepoint to string
  const stringFromCodePoint = function (codePoint) {
    // out of range, use replacement character
    if (codePoint < 1 || codePoint > 0x10ffff ||
        (codePoint > 0xd7ff && codePoint < 0xe000)) {
      return '\ufffd';
    }
    if (codePoint < 0x10000) {
      return String.fromCharCode(codePoint);
    }
    return String.fromCodePoint(codePoint);
  };

  // convert escape sequence in a CSS string or identifier
  // to javascript string with javascript escape sequences
  const convertEscapes = function (str) {
    return REX.hasEscapes.test(str)
      ? str.replace(REX.fixEscapes, function (substring, p1, p2) {
        // unescaped " or '
        return p2
          ? '\\' + p2
          // javascript strings are UTF-16 encoded
          : REX.hexNumbers.test(p1)
            ? codePointToUTF16(parseInt(p1, 16))
            // \' \"
            : REX.escOrQuote.test(p1)
              ? substring
              // \g \h \. \# etc
              : p1;
      })
      : str;
  };

  // convert escape sequence in a CSS string or identifier
  // to javascript string with characters representations
  const unescapeIdentifier = function (str) {
    return REX.hasEscapes.test(str)
      ? str.replace(REX.fixEscapes, function (substring, p1, p2) {
        // unescaped " or '
        return p2 || (REX.hexNumbers.test(p1)
          ? stringFromCodePoint(parseInt(p1, 16))
          // \' \"
          : REX.escOrQuote.test(p1)
            ? substring
            // \g \h \. \# etc
            : p1);
      })
      : str;
  };

  // empty set
  const none = [];

  // cached lambdas
  const matchLambdas = {};
  const selectLambdas = {};

  // cached resolvers
  let matchResolvers = {};
  let selectResolvers = {};

  const method = {
    '#': 'getElementById',
    '*': 'getElementsByTagName',
    '|': 'getElementsByTagNameNS',
    '.': 'getElementsByClassName'
  };

  // find duplicate ids using iterative walk
  const byIdRaw = function (id, context) {
    let node = context;
    const nodes = [];
    let next = node.firstElementChild;
    while ((node = next)) {
      node.id === id && nodes.push(node);
      if ((next = node.firstElementChild || node.nextElementSibling)) {
        continue;
      }
      while (!next && (node = node.parentElement) && node !== context) {
        next = node.nextElementSibling;
      }
    }
    return nodes;
  };

  // context agnostic getElementById
  const byId = function (id, context) {
    let e;
    const api = method['#'];

    // duplicates id allowed
    if (Config.IDS_DUPES === false) {
      if (api in context) {
        e = context[api](id);
        return e ? [e] : none;
      }
    } else if ('all' in context) {
      if ((e = context.all[id])) {
        if (e.nodeType === 1) {
          return e.getAttribute('id') !== id ? [] : [e];
        } else if (id === 'length') {
          e = context[api](id);
          return e ? [e] : none;
        }
        const nodes = [];
        for (let i = 0, l = e.length; l > i; ++i) {
          if (e[i].id === id) {
            nodes.push(e[i]);
          }
        }
        return nodes.length ? nodes : none;
      } else {
        return none;
      }
    }

    return byIdRaw(id, context);
  };

  // context agnostic getElementsByTagName
  const byTag = function (tag, context) {
    let e;
    let nodes;
    const api = method['*'];

    // DOCUMENT_NODE (9) & ELEMENT_NODE (1)
    if (api in context) {
      return Array.prototype.slice.call(context[api](tag));
    } else {
      tag = tag.toLowerCase();
      // DOCUMENT_FRAGMENT_NODE (11)
      if ((e = context.firstElementChild)) {
        if (!(e.nextElementSibling || tag === '*' || e.localName === tag)) {
          return Array.prototype.slice.call(e[api](tag));
        } else {
          nodes = [];
          do {
            if (tag === '*' || e.localName === tag) {
              nodes.push(e);
            }
            concatList(nodes, e[api](tag));
          } while ((e = e.nextElementSibling));
        }
      } else {
        nodes = none;
      }
    }
    return nodes;
  };

  // context agnostic getElementsByClassName
  const byClass = function (cls, context) {
    let e;
    let nodes;
    const api = method['.'];
    let reCls;
    // DOCUMENT_NODE (9) & ELEMENT_NODE (1)
    if (api in context) {
      return Array.prototype.slice.call(context[api](cls));
    } else {
      // DOCUMENT_FRAGMENT_NODE (11)
      if ((e = context.firstElementChild)) {
        reCls = RegExp('(^|\\s)' + cls + '(\\s|$)', QUIRKS_MODE ? 'i' : '');
        if (!(e.nextElementSibling || reCls.test(e.className))) {
          return Array.prototype.slice.call(e[api](cls));
        } else {
          nodes = [];
          do {
            if (reCls.test(e.className)) {
              nodes.push(e);
            }
            concatList(nodes, e[api](cls));
          } while ((e = e.nextElementSibling));
        }
      } else nodes = none;
    }
    return nodes;
  };

  const compat = {
    '#': function (c, n) {
      REX.hasEscapes.test(n) && (n = unescapeIdentifier(n));
      return function (e, f) {
        return byId(n, c);
      };
    },
    '*': function (c, n) {
      REX.hasEscapes.test(n) && (n = unescapeIdentifier(n));
      return function (e, f) {
        return byTag(n, c);
      };
    },
    '|': function (c, n) {
      REX.hasEscapes.test(n) && (n = unescapeIdentifier(n));
      return function (e, f) {
        return byTag(n, c);
      };
    },
    '.': function (c, n) {
      REX.hasEscapes.test(n) && (n = unescapeIdentifier(n));
      return function (e, f) {
        return byClass(n, c);
      };
    }
  };

  // namespace aware hasAttribute
  // helper for XML/XHTML documents
  const hasAttributeNS = function (e, name) {
    let i;
    let l;
    const attr = e.getAttributeNames();
    name = RegExp(':?' + name + '$', HTML_DOCUMENT ? 'i' : '');
    for (i = 0, l = attr.length; l > i; ++i) {
      if (name.test(attr[i])) {
        return true;
      }
    }
    return false;
  };

  // fast resolver for the :nth-child() and :nth-last-child() pseudo-classes
  const nthElement = (function () {
    let idx = 0;
    let len = 0;
    let set = 0;
    let parent;
    let parents = [];
    let nodes = [];
    return function (element, dir) {
      // ensure caches are emptied after each run, invoking with dir = 2
      if (dir === 2) {
        idx = 0; len = 0; set = 0; nodes = []; parents = []; parent = undefined;
        return -1;
      }
      let e, i, j, k, l;
      if (parent === element.parentElement) {
        i = set; j = idx; l = len;
      } else {
        l = parents.length;
        parent = element.parentElement;
        for (i = -1, j = 0, k = l - 1; l > j; ++j, --k) {
          if (parents[j] === parent) {
            i = j;
            break;
          }
          if (parents[k] === parent) {
            i = k;
            break;
          }
        }
        if (i < 0) {
          parents[i = l] = parent;
          l = 0; nodes[i] = [];
          e = (parent && parent.firstElementChild) || element;
          while (e) {
            nodes[i][l] = e;
            if (e === element) {
              j = l;
            }
            e = e.nextElementSibling;
            ++l;
          }
          set = i; idx = 0; len = l;
          if (l < 2) {
            return l;
          }
        } else {
          l = nodes[i].length;
          set = i;
        }
      }
      if (element !== nodes[i][j] && element !== nodes[i][j = 0]) {
        for (j = 0, e = nodes[i], k = l - 1; l > j; ++j, --k) {
          if (e[j] === element) {
            break;
          }
          if (e[k] === element) {
            j = k;
            break;
          }
        }
      }
      idx = j + 1; len = l;
      return dir ? l - j : idx;
    };
  })();

  // fast resolver for the :nth-of-type() and :nth-last-of-type() pseudo-classes
  const nthOfType = (function () {
    let idx = 0;
    let len = 0;
    let set = 0;
    let parent;
    let parents = [];
    let nodes = [];
    return function (element, dir) {
      // ensure caches are emptied after each run, invoking with dir = 2
      if (dir === 2) {
        idx = 0; len = 0; set = 0; nodes = []; parents = []; parent = undefined;
        return -1;
      }
      const name = element.localName;
      const nsURI = element.namespaceURI;
      if (nsURI !== 'http://www.w3.org/1999/xhtml') {
        idx = 0; len = 0; set = 0; nodes = []; parents = []; parent = undefined;
      }
      let e;
      let i;
      let j;
      let k;
      let l;
      if (nodes[set] && nodes[set][name] && parent === element.parentElement) {
        i = set;
        j = idx;
        l = len;
      } else {
        l = parents.length;
        parent = element.parentElement;
        for (i = -1, j = 0, k = l - 1; l > j; ++j, --k) {
          if (parents[j] === parent) {
            i = j;
            break;
          }
          if (parents[k] === parent) {
            i = k;
            break;
          }
        }
        if (i < 0 || !nodes[i][name]) {
          parents[i = l] = parent;
          nodes[i] || (nodes[i] = Object());
          l = 0; nodes[i][name] = [];
          e = (parent && parent.firstElementChild) || element;
          while (e) {
            if (e === element) {
              j = l;
            }
            if (e.localName === name && e.namespaceURI === nsURI) {
              nodes[i][name][l] = e;
              ++l;
            }
            e = e.nextElementSibling;
          }
          set = i; idx = j; len = l;
          if (l < 2) {
            return l;
          }
        } else {
          l = nodes[i][name].length;
          set = i;
        }
      }
      if (element !== nodes[i][name][j] && element !== nodes[i][name][j = 0]) {
        for (j = 0, e = nodes[i][name], k = l - 1; l > j; ++j, --k) {
          if (e[j] === element) {
            break;
          }
          if (e[k] === element) {
            j = k;
            break;
          }
        }
      }
      idx = j + 1; len = l;
      return dir ? l - j : idx;
    };
  })();

  // check if the node is the target
  const isTarget = function (node) {
    const doc = node.ownerDocument || node;
    const { hash } = new URL(doc.URL);
    if (node.id && hash === `#${node.id}` && doc.contains(node)) {
      return true;
    }
    return false;
  };

  // check if node is indeterminate
  const isIndeterminate = function (node) {
    if ((node.indeterminate && node.localName === 'input' &&
         node.type === 'checkbox') ||
        (node.localName === 'progress' && !node.hasAttribute('value'))) {
      return true;
    }
    if (node.localName === 'input' && node.type === 'radio' &&
        !node.hasAttribute('checked')) {
      const nodeName = node.name;
      let parent = node.parentNode;
      while (parent) {
        if (parent.localName === 'form') {
          break;
        }
        parent = parent.parentNode;
      }
      if (!parent) {
        const doc = node.ownerDocument;
        parent = doc.documentElement;
      }
      const items = parent.getElementsByTagName('input');
      const l = items.length;
      let checked;
      for (let i = 0; i < l; i++) {
        const item = items[i];
        if (item.getAttribute('type') === 'radio') {
          if (nodeName) {
            if (item.getAttribute('name') === nodeName) {
              checked = !!item.checked;
            }
          } else if (!item.hasAttribute('name')) {
            checked = !!item.checked;
          }
          if (checked) {
            break;
          }
        }
      }
      if (!checked) {
        return true;
      }
    }
    return false;
  };

  // check if node content is editable
  const isContentEditable = function (node) {
    let attrValue = 'inherit';
    if (node.hasAttribute('contenteditable')) {
      attrValue = node.getAttribute('contenteditable');
    }
    switch (attrValue) {
      case '':
      case 'plaintext-only':
      case 'true':
        return true;
      case 'false':
        return false;
      default:
        if (node.parentNode && node.parentNode.nodeType === 1) {
          return isContentEditable(node.parentNode);
        }
        return false;
    }
  };

  // build validation regexps used by the engine
  const setIdentifierSyntax = function () {
    //
    // NOTE: SPECIAL CASES IN CSS SYNTAX PARSING RULES
    //
    // The <EOF-token> https://drafts.csswg.org/css-syntax/#typedef-eof-token
    // allow mangled|unclosed selector syntax at the end of selectors strings
    //
    // Literal equivalent hex representations of the characters: " ' ` ] )
    //
    //     \\x22 = " - double quotes    \\x5b = [ - open square bracket
    //     \\x27 = ' - single quote     \\x5d = ] - closed square bracket
    //     \\x60 = ` - back tick        \\x28 = ( - open round parens
    //     \\x5c = \ - back slash       \\x29 = ) - closed round parens
    //
    // using hex format prevents false matches of opened/closed instances
    // pairs, coloring breakage and other editors highlightning problems.
    //

    // @see https://drafts.csswg.org/css-syntax-3/#ident-token-diagram
    const nonascii = '[^\\x00-\\x9f]';
    const esctoken = '\\\\(?:[^\\r\\n\\f\\da-f]|[\\da-f]{1,6}\\s{0,255})';
    const identifier =
      '(?:--|-?(?:[a-z_]|' + nonascii + '|' + esctoken + '))' +
      '(?:[\\w-]|' + nonascii + '|' + esctoken + ')*';

    const pseudonames = '[-\\w]+';
    const pseudoparms = '(?:[-+]?\\d*)(?:n\\s?[-+]?\\s?\\d*)';
    const doublequote = '"[^"\\\\]*(?:\\\\.[^"\\\\]*)*(?:"|$)';
    const singlequote = "'[^'\\\\]*(?:\\\\.[^'\\\\]*)*(?:'|$)";

    const attrparser = identifier + '|' + doublequote + '|' + singlequote;

    const attrvalues = '([\\x22\\x27]?)((?!\\3)*|(?:\\\\?.)*?)(?:\\3|$)';

    const attributes =
      '\\[' +
        // attribute presence
        '(?:\\*\\|)?\\s?(' + identifier + '(?::' + identifier + ')?)\\s?' +
        '(?:(' + CFG.operators + ')\\s?(?:' + attrparser + '))?' +
        // attribute case sensitivity
        '(?:\\s?\\b(i))?\\s?' +
      '(?:\\]|$)';

    const attrmatcher = attributes.replace(attrparser, attrvalues);

    const pseudoclass =
      '(?:\\x28\\s*' +
        '(?:' + pseudoparms + '?)?|' +
        // universal * &
        // namespace *|*
        '[*|]|' +
        '(?:' +
          '(?::' + pseudonames + '(?:\\x28' + pseudoparms + '?(?:\\x29|$))?)|' +
          '(?:[.#]?' + identifier + ')|' +
          '(?:' + attributes + ')' +
        ')+|' +
        '\\s?[>+~]\\s?|' +
        '\\s?,\\s?|' +
        '\\s|' +
        '\\x29|$' +
      ')*';

    const standardValidator =
      '(?=\\s?[^>+~(){}<])' +
      '(?:' +
        // universal * &
        // namespace *|*
        '\\*|\\||' +
        '(?:[.#]?' + identifier + ')+|' +
        '(?:' + attributes + ')+|' +
        '(?:::?' + pseudonames + pseudoclass + ')|' +
        '(?:\\s?' + CFG.combinators + '\\s?)|' +
        '\\s?,\\s?|' +
        '\\s?' +
      ')+';

    // the following global RE is used to return the
    // deepest localName in selector strings and then
    // use it to retrieve all possible matching nodes
    // that will be filtered by compiled resolvers
    reOptimizer = RegExp(
      '(?:([.:#*]?)(' + identifier + ')' +
        '(?::[-\\w]+|\\[[^\\]]+(?:\\]|$)|\\x28[^\\x29]+(?:\\x29|$))*' +
      ')$', 'i');

    // global
    reValidator = RegExp(standardValidator, 'gi');

    Patterns.id = RegExp('^#(' + identifier + ')(.*)', 'i');
    Patterns.tagName = RegExp('^(' + identifier + ')(.*)', 'i');
    Patterns.className = RegExp('^\\.(' + identifier + ')(.*)', 'i');
    Patterns.attribute = RegExp('^(?:' + attrmatcher + ')(.*)');
  };

  // configure the engine to use special handling
  const configure = function (option, clear) {
    if (typeof option === 'string') {
      return !!Config[option];
    }
    if (typeof option !== 'object') {
      return Config;
    }
    for (const i in option) {
      Config[i] = !!option[i];
    }
    // clear lambda cache
    if (clear) {
      matchResolvers = {};
      selectResolvers = {};
    }
    setIdentifierSyntax();
    return true;
  };

  // centralized error and exceptions handling
  const emit = function (message, proto) {
    let err;
    if (Config.VERBOSITY) {
      if (global[proto]) {
        err = new global[proto](message);
      } else {
        err = new global.DOMException(message, 'SyntaxError');
      }
      throw err;
    }
    if (Config.LOGERRORS && console && console.log) {
      console.log(message);
    }
  };

  // passed to resolvers
  const Snapshot = {
    doc: null,
    from: null,
    byTag: null,
    first: null,
    match: null,
    ancestor: null,
    nthOfType: null,
    nthElement: null,
    hasAttributeNS: null,
    isTarget: null,
    isIndeterminate: null,
    isContentEditable: null
  };

  // context
  let lastContext;

  const switchContext = function (context, force) {
    const oldDoc = doc;
    doc = context.ownerDocument || context;
    if (force || oldDoc !== doc) {
      // force a new check for each document change
      // performed before the next select operation
      HTML_DOCUMENT = isHTML(doc);
      QUIRKS_MODE = HTML_DOCUMENT && doc.compatMode.indexOf('CSS') < 0;
      NAMESPACE = doc.documentElement && doc.documentElement.namespaceURI;
      Snapshot.doc = doc;
    }
    Snapshot.from = context;
    return context;
  };

  // selector
  let lastMatched;
  let lastSelected;

  const F_INIT = '"use strict";return function Resolver(c,f,x,r)';

  const S_HEAD = 'var e,n,o,j=r.length-1,k=-1';
  const M_HEAD = 'var e,n,o';

  const S_LOOP = 'main:while((e=c[++k]))';
  const N_LOOP = 'main:while((e=c.item(++k)))';
  const M_LOOP = 'e=c;';

  const S_BODY = 'r[++j]=c[k];';
  const N_BODY = 'r[++j]=c.item(k);';
  const M_BODY = '';

  const S_TAIL = 'continue main;';
  const M_TAIL = 'r=true;';

  const S_TEST = 'if(f(c[k])){break main;}';
  const N_TEST = 'if(f(c.item(k))){break main;}';
  const M_TEST = 'f(c);';

  let S_VARS = [];
  let M_VARS = [];

  // build conditional code to check components of selector strings
  const compileSelector = function (expression, source, mode, callback) {
    // N is the negation pseudo-class flag
    // D is the default inverted negation flag
    let a;
    let b;
    let n;
    let f;
    let name;
    let NS;
    const N = '';
    const D = '!';
    let compat;
    let expr;
    let match;
    let result;
    let status;
    let symbol;
    let test;
    let type;
    let selector = expression;
    let vars;

    // original 'select' or 'match' selector string before normalization
    const selectorString = mode ? lastSelected : lastMatched;

    // isolate selector combinators/components and normalize whitespace
    selector = selector.replace(STD.combinator, '$1'); // .replace(STD.whitespace, ' ');

    let selectorRecursion = true;
    while (selector) {
      // get namespace prefix if present or get first char of selector
      symbol = STD.apimethods.test(selector) ? '|' : selector[0];

      switch (symbol) {
        // universal resolver
        case '*':
          match = selector.match(Patterns.universal);
          if (N === '!') {
            source = 'if(' + N + 'true' + '){' + source + '}';
          }
          break;
        // id resolver
        case '#':
          match = selector.match(Patterns.id);
          source = 'if(' + N + '(/^' + match[1] + '$/.test(e.getAttribute("id"))' +
            ')){' + source + '}';
          break;
        // class name resolver
        case '.':
          match = selector.match(Patterns.className);
          compat = (QUIRKS_MODE ? 'i' : '') + '.test(e.getAttribute("class"))';
          source = 'if(' + N + '(/(^|\\s)' + match[1] + '(\\s|$)/' + compat +
            ')){' + source + '}';
          break;
        // tag name resolver
        case (/[_a-z]/i.test(symbol) ? symbol : undefined):
          match = selector.match(Patterns.tagName);
          source = 'if(' + N + '(e.localName' +
            (Config.MIXEDCASE || hasMixedCaseTagNames(doc)
              ? '=="' + match[1].toLowerCase() + '"'
              : '=="' + match[1].toUpperCase() + '"') +
            ')){' + source + '}';
          break;
        // namespace resolver
        case '|':
          match = selector.match(Patterns.namespace);
          if (match[1] === '*') {
            source = 'if(' + N + 'true){' + source + '}';
          } else if (!match[1]) {
            source = 'if(' + N + '(!e.namespaceURI)){' + source + '}';
          } else if (typeof match[1] === 'string' && doc.documentElement &&
                     doc.documentElement.prefix === match[1]) {
            source = 'if(' + N + '(e.namespaceURI=="' + NAMESPACE + '")){' + source + '}';
          } else {
            emit('\'' + selectorString + '\'' + qsInvalid);
          }
          break;
        // attributes resolver
        case '[':
          match = selector.match(Patterns.attribute);
          NS = match[0].match(STD.namespaces);
          name = match[1];
          expr = name.split(':');
          expr = expr.length === 2 ? expr[1] : expr[0];
          if (match[2] && !(test = Operators[match[2]])) {
            emit('\'' + selectorString + '\'' + qsInvalid);
            return '';
          }
          if (match[4] === '') {
            test = match[2] === '~='
              ? { p1: '^\\s', p2: '+$', p3: 'true' }
              : match[2] in ATTR_STD_OPS && match[2] !== '~='
                ? { p1: '^', p2: '$', p3: 'true' }
                : test;
          } else if (match[2] === '~=' && match[4].includes(' ')) {
            // whitespace separated list but value contains space
            source = 'if(' + N + 'false){' + source + '}';
            break;
          } else if (match[4]) {
            match[4] = convertEscapes(match[4]).replace(REX.regExpChar, '\\$&');
          }
          type = match[5] === 'i' || (HTML_DOCUMENT && HTML_TABLE[expr.toLowerCase()])
            ? 'i'
            : '';
          source =
            'if(' + N + '(' +
              (!match[2]
                ? (NS ? 's.hasAttributeNS(e,"' + name + '")' : 'e.hasAttribute&&e.hasAttribute("' + name + '")')
                : !match[4] && ATTR_STD_OPS[match[2]] && match[2] !== '~='
                  ? 'e.getAttribute&&e.getAttribute("' + name + '")==""'
                  : '(/' + test.p1 + match[4] + test.p2 + '/' + type + ').test(e.getAttribute&&e.getAttribute("' + name + '"))==' + test.p3) +
            ')){' + source + '}';
          break;
        // *** General sibling combinator
        // E ~ F (F relative sibling of E)
        case '~':
          match = selector.match(Patterns.relative);
          source = 'n=e;while((e=e.previousElementSibling)){' + source + '}e=n;';
          break;
        // *** Adjacent sibling combinator
        // E + F (F adiacent sibling of E)
        case '+':
          match = selector.match(Patterns.adjacent);
          source = 'n=e;if((e=e.previousElementSibling)){' + source + '}e=n;';
          break;
        // *** Descendant combinator
        // E F (E ancestor of F)
        case '\x09':
        case '\x20':
          match = selector.match(Patterns.ancestor);
          source = 'n=e;while((e=e.parentElement)){' + source + '}e=n;';
          break;
        // *** Child combinator
        // E > F (F children of E)
        case '>':
          match = selector.match(Patterns.children);
          source = 'n=e;if((e=e.parentElement)){' + source + '}e=n;';
          break;
        // *** user supplied combinators extensions
        case (symbol in Combinators ? symbol : undefined):
          // for other registered combinators extensions
          match[match.length - 1] = '*';
          source = Combinators[symbol](match) + source;
          break;
        // *** tree-structural pseudo-classes
        // :root, :empty, :first-child, :last-child, :only-child, :first-of-type, :last-of-type, :only-of-type
        case ':':
          if ((match = selector.match(Patterns.structural))) {
            match[1] = match[1].toLowerCase();
            switch (match[1]) {
              case 'root':
                // there can only be one :root element, so exit the loop once found
                source = 'if(' + N + '(e===s.doc.documentElement)){' + source + (mode ? 'break main;' : '') + '}';
                break;
              case 'empty':
                // matches elements that don't contain elements or text nodes
                source = 'n=e.firstChild;while(n&&!(/1|3/).test(n.nodeType)){n=n.nextSibling}if(' + D + 'n){' + source + '}';
                break;
              // *** child-indexed pseudo-classes
              // :first-child, :last-child, :only-child
              case 'only-child':
                source = 'if(' + N + '(!e.nextElementSibling&&!e.previousElementSibling)){' + source + '}';
                break;
              case 'last-child':
                source = 'if(' + N + '(!e.nextElementSibling)){' + source + '}';
                break;
              case 'first-child':
                source = 'if(' + N + '(!e.previousElementSibling)){' + source + '}';
                break;
              // *** typed child-indexed pseudo-classes
              // :only-of-type, :last-of-type, :first-of-type
              case 'only-of-type':
                source = 'o=e.localName;' +
                  'n=e;while((n=n.nextElementSibling)&&n.localName!=o);if(!n){' +
                  'n=e;while((n=n.previousElementSibling)&&n.localName!=o);}if(' + D + 'n){' + source + '}';
                break;
              case 'last-of-type':
                source = 'n=e;o=e.localName;while((n=n.nextElementSibling)&&n.localName!=o);if(' + D + 'n){' + source + '}';
                break;
              case 'first-of-type':
                source = 'n=e;o=e.localName;while((n=n.previousElementSibling)&&n.localName!=o);if(' + D + 'n){' + source + '}';
                break;
              default:
                emit('\'' + selectorString + '\'' + qsInvalid);
            }
          // *** child-indexed & typed child-indexed pseudo-classes
          // :nth-child, :nth-of-type, :nth-last-child, :nth-last-of-type
          } else if ((match = selector.match(Patterns.treestruct))) {
            match[1] = match[1].toLowerCase();
            switch (match[1]) {
              case 'nth-child':
              case 'nth-of-type':
              case 'nth-last-child':
              case 'nth-last-of-type':
                expr = /-of-type/i.test(match[1]);
                if (match[1] && match[2]) {
                  type = /last/i.test(match[1]);
                  if (match[2] === 'n') {
                    source = 'if(' + N + 'true){' + source + '}';
                    break;
                  } else if (match[2] === '1') {
                    test = type ? 'next' : 'previous';
                    source = expr
                      ? 'n=e;o=e.localName;' +
                          'while((n=n.' + test + 'ElementSibling)&&n.localName!=o);if(' + D + 'n){' + source + '}'
                      : 'if(' + N + '!e.' + test + 'ElementSibling){' + source + '}';
                    break;
                  } else if (match[2] === 'even' || match[2] === '2n0' || match[2] === '2n+0' || match[2] === '2n') {
                    test = 'n%2==0';
                  } else if (match[2] === 'odd' || match[2] === '2n1' || match[2] === '2n+1') {
                    test = 'n%2==1';
                  } else {
                    f = /n/i.test(match[2]);
                    n = match[2].split('n');
                    a = parseInt(n[0], 10) || 0;
                    b = parseInt(n[1], 10) || 0;
                    if (n[0] === '-') {
                      a = -1;
                    }
                    if (n[0] === '+') {
                      a = +1;
                    }
                    test = (b ? '(n' + (b > 0 ? '-' : '+') + Math.abs(b) + ')' : 'n') + '%' + a + '==0';
                    test = a >= +1
                      ? (f
                          ? 'n>' + (b - 1) + (Math.abs(a) !== 1
                            ? '&&' + test
                            : '')
                          : 'n==' + a)
                      : a <= -1
                        ? (f
                            ? 'n<' + (b + 1) + (Math.abs(a) !== 1
                              ? '&&' + test
                              : '')
                            : 'n==' + a)
                        : a === 0
                          ? (n[0]
                              ? 'n==' + b
                              : 'n>' + (b - 1))
                          : 'false';
                  }
                  expr = expr ? 'OfType' : 'Element';
                  type = type ? 'true' : 'false';
                  source = 'n=s.nth' + expr + '(e,' + type + ');if(' + N + '(' + test + ')){' + source + '}';
                } else {
                  emit('\'' + selectorString + '\'' + qsInvalid);
                }
                break;
              default:
                emit('\'' + selectorString + '\'' + qsInvalid);
            }
          // *** logical combination pseudo-classes
          // :is( s1, [ s2, ... ]), :not( s1, [ s2, ... ])
          } else if ((match = selector.match(Patterns.logicalsel))) {
            match[1] = match[1].toLowerCase();
            expr = match[2].replace(REX.CommaGroup, ',').replace(REX.TrimSpaces, '');
            switch (match[1]) {
              // FIXME:
              case 'is':
              case 'where':
              case 'matches':
                source = 'if(s.match("' + expr.replace(/\x22/g, '\\"') + '",e)){' + source + '}';
                break;
              // FIXME:
              case 'not':
                source = 'if(!s.match("' + expr.replace(/\x22/g, '\\"') + '",e)){' + source + '}';
                break;
              // FIXME:
              case 'has':
                // clear cache
                matchResolvers = {};
                source = 'if(e.querySelector(":scope ' + expr.replace(/\x22/g, '\\"') + '")){' + source + '}';
                break;
              default:
                emit('\'' + selectorString + '\'' + qsInvalid);
            }
          // *** location pseudo-classes
          // :any-link, :link, :visited, :target
          } else if ((match = selector.match(Patterns.locationpc))) {
            match[1] = match[1].toLowerCase();
            switch (match[1]) {
              case 'any-link':
                source = 'if(' + N + '(/^a|area$/i.test(e.localName)&&e.hasAttribute("href")||e.visited)){' + source + '}';
                break;
              case 'link':
                source = 'if(' + N + '(/^a|area$/i.test(e.localName)&&e.hasAttribute("href"))){' + source + '}';
                break;
              // FIXME:
              case 'visited':
                source = 'if(' + N + '(/^a|area$/i.test(e.localName)&&e.hasAttribute("href")&&e.visited)){' + source + '}';
                break;
              case 'target':
                source = 'if(s.isTarget(e)){' + source + '}';
                break;
              default:
                emit('\'' + selectorString + '\'' + qsInvalid);
            }
          // *** user interface and form pseudo-classes
          // :enabled, :disabled, :read-only, :read-write, :placeholder-shown, :default
          } else if ((match = selector.match(Patterns.inputstate))) {
            match[1] = match[1].toLowerCase();
            switch (match[1]) {
              // FIXME: lacks custom element support
              case 'enabled':
                source = 'if((("form" in e||/^optgroup$/i.test(e.localName))&&"disabled" in e &&e.disabled===false' +
                  ')){' + source + '}';
                break;
              // FIXME: lacks custom element support
              case 'disabled':
                // https://html.spec.whatwg.org/#enabling-and-disabling-form-controls:-the-disabled-attribute
                source = 'if((("form" in e||/^optgroup$/i.test(e.localName))&&"disabled" in e)){' +
                  // F is true if any of the fieldset elements in the ancestry chain has the disabled attribute specified
                  // L is true if the first legend element of the fieldset contains the element
                  'var x=0,N=[],F=false,L=false;' +
                  'if(!(/^(optgroup|option)$/i.test(e.localName))){' +
                    'n=e.parentElement;' +
                    'while(n){' +
                      'if(n.localName==="fieldset"){' +
                        'N[x++]=n;' +
                        'if(n.disabled===true){' +
                          'F=true;' +
                          'break;' +
                        '}' +
                      '}' +
                      'n=n.parentElement;' +
                    '}' +
                    'for(var x=0;x<N.length;x++){' +
                      'if((n=s.first("legend",N[x]))&&n.contains(e)){' +
                        'L=true;' +
                        'break;' +
                      '}' +
                    '}' +
                  '}' +
                  'if(e.disabled===true||(F&&!L)){' + source + '}}';
                break;
              case 'read-only':
                source =
                  'if(' +
                    '(/^textarea$/i.test(e.localName)&&(e.readOnly||e.disabled))||' +
                    '(/^input$/i.test(e.localName)&&("|date|datetime-local|email|month|number|password|search|tel|text|time|url|week|".includes("|"+e.type+"|")?(e.readOnly||e.disabled):true))||' +
                    '(!/^(?:input|textarea)$/i.test(e.localName) && !s.isContentEditable(e))' +
                  '){' + source + '}';
                break;
              case 'read-write':
                source =
                  'if(' +
                    '(/^textarea$/i.test(e.localName)&&!e.readOnly&&!e.disabled)||' +
                    '(/^input$/i.test(e.localName)&&"|date|datetime-local|email|month|number|password|search|tel|text|time|url|week|".includes("|"+e.type+"|")&&!e.readOnly&&!e.disabled)||' +
                    '(!/^(?:input|textarea)$/i.test(e.localName) && s.isContentEditable(e))' +
                  '){' + source + '}';
                break;
              // FIXME:
              case 'placeholder-shown':
                source =
                  'if((' +
                    '(/^input|textarea$/i.test(e.localName))&&e.hasAttribute("placeholder")&&' +
                    '("|textarea|password|number|search|email|text|tel|url|".includes("|"+e.type+"|"))&&' +
                    '(!s.match(":focus",e))' +
                  ')){' + source + '}';
                break;
              // FIXME:
              case 'default':
                source =
                  'if(("form" in e && e.form)){' +
                    'var x=0;n=[];' +
                    'if(e.type=="image")n=e.form.getElementsByTagName("input");' +
                    'if(e.type=="submit")n=e.form.elements;' +
                    'while(n[x]&&e!==n[x]){' +
                      'if(n[x].type=="image")break;' +
                      'if(n[x].type=="submit")break;' +
                      'x++;' +
                    '}' +
                  '}' +
                  'if((e.form&&(e===n[x]&&"|image|submit|".includes("|"+e.type+"|"))||' +
                    '((/^option$/i.test(e.localName))&&e.defaultSelected)||' +
                    '(("|radio|checkbox|".includes("|"+e.type+"|"))&&e.defaultChecked)' +
                  ')){' + source + '}';
                break;
              default:
                emit('\'' + selector_string + '\'' + qsInvalid);
                break;
            }
          // *** input pseudo-classes (for form validation)
          // :checked, :indeterminate, :valid, :invalid, :in-range, :out-of-range, :required, :optional
          } else if ((match = selector.match(Patterns.inputvalue))) {
            match[1] = match[1].toLowerCase();
            switch (match[1]) {
              case 'checked':
                source = 'if(' + N + '(/^input$/i.test(e.localName)&&' +
                  '("|radio|checkbox|".includes("|"+e.type+"|")&&e.checked)||' +
                  '(/^option$/i.test(e.localName)&&(e.selected||e.checked))' +
                  ')){' + source + '}';
                break;
              case 'indeterminate':
                source = 'if(s.isIndeterminate(e)){' + source + '}';
                break;
              // FIXME:
              case 'required':
                source =
                  'if(' + N +
                    '(/^input|select|textarea$/i.test(e.localName)&&e.required)' +
                  '){' + source + '}';
                break;
              // FIXME:
              case 'optional':
                source =
                  'if(' + N +
                    '(/^input|select|textarea$/i.test(e.localName)&&!e.required)' +
                  '){' + source + '}';
                break;
              // FIXME:
              case 'invalid':
                source =
                  'if(' + N + '((' +
                    '(/^form$/i.test(e.localName)&&!e.noValidate)||' +
                    '(e.willValidate&&!e.formNoValidate))&&!e.checkValidity())||' +
                    '(/^fieldset$/i.test(e.localName)&&s.first(":invalid",e))' +
                  '){' + source + '}';
                break;
              // FIXME:
              case 'valid':
                source =
                  'if(' + N + '((' +
                    '(/^form$/i.test(e.localName)&&!e.noValidate)||' +
                    '(e.willValidate&&!e.formNoValidate))&&e.checkValidity())||' +
                    '(/^fieldset$/i.test(e.localName)&&s.first(":valid",e))' +
                  '){' + source + '}';
                break;
              // FIXME:
              case 'in-range':
                source =
                  'if(' + N +
                    '(/^input$/i.test(e.localName))&&' +
                    '(e.willValidate&&!e.formNoValidate)&&' +
                    '(!e.validity.rangeUnderflow&&!e.validity.rangeOverflow)&&' +
                    '("|date|datetime-local|month|number|range|time|week|".includes("|"+e.type+"|"))&&' +
                    '("range"==e.type||e.getAttribute("min")||e.getAttribute("max"))' +
                  '){' + source + '}';
                break;
              // FIXME:
              case 'out-of-range':
                source =
                  'if(' + N +
                    '(/^input$/i.test(e.localName))&&' +
                    '(e.willValidate&&!e.formNoValidate)&&' +
                    '(e.validity.rangeUnderflow||e.validity.rangeOverflow)&&' +
                    '("|date|datetime-local|month|number|range|time|week|".includes("|"+e.type+"|"))&&' +
                    '("range"==e.type||e.getAttribute("min")||e.getAttribute("max"))' +
                  '){' + source + '}';
                break;
              default:
                emit('\'' + selectorString + '\'' + qsInvalid);
            }
          // allow pseudo-elements starting with single colon (:)
          // :after, :before, :first-letter, :first-line
          // assert: e.type is in double-colon format, like ::after
          } else if ((match = selector.match(Patterns.pseudoSng))) {
            source = 'if(e.element&&e.type.toLowerCase()=="' +
              ':' + match[0].toLowerCase() + '"){e=e.element;' + source + '}';
          // allow pseudo-elements starting with double colon (::)
          // ::after, ::before, ::marker, ::placeholder, ::inactive-selection, ::selection, ::-webkit-<foo-bar>
          // assert: e.type is in double-colon format, like ::after
          } else if ((match = selector.match(Patterns.pseudoDbl))) {
            source = 'if(e.element&&e.type.toLowerCase()=="' +
              match[0].toLowerCase() + '"){e=e.element;' + source + '}';
          // placeholder for parsed only no-op selectors
          } else if ((match = selector.match(Patterns.pseudoNop))) {
            source = 'if(' + N + 'false' + '){' + source + '}';
          } else {
            // reset
            expr = false;
            status = false;
            // process registered selector extensions
            for (expr in Selectors) {
              if ((match = selector.match(Selectors[expr].Expression))) {
                result = Selectors[expr].Callback(match, source, mode, callback);
                if ('match' in result) {
                  match = result.match;
                }
                vars = result.modvar;
                if (mode) {
                  // add extra select() vars
                  vars && !S_VARS.includes(vars) && S_VARS.push(vars);
                } else {
                  // add extra match() vars
                  vars && M_VARS.includes(vars) && M_VARS.push(vars);
                }
                // extension source code
                source = result.source;
                // extension status code
                status = result.status;
                // break on status error
                if (status) { break; }
              }
            }
            if (!status) {
              emit('unknown pseudo-class selector \'' + selector + '\'');
              return '';
            }
            if (!expr) {
              emit('unknown token in selector \'' + selector + '\'');
              return '';
            }
          }
          break;
        default:
          selectorRecursion = false;
          emit('\'' + selectorString + '\'' + qsInvalid);
      }
      // end of switch symbol
      if (!selectorRecursion) {
        break;
      }
      if (!match) {
        emit('\'' + selectorString + '\'' + qsInvalid);
        return '';
      }

      // pop last component
      selector = match.pop();
    }
    // end of while selector

    return source;
  };

  // compile groups or single selector strings into
  // executable functions for matching or selecting
  const compile = function (selector, mode, callback) {
    let head = ''; let loop = ''; let macro = ''; let source = ''; let vars = '';

    // 'mode' can be boolean or null
    // true = select / false = match
    // null to use collection.item()
    switch (mode) {
      case true:
        if (selectLambdas[selector]) {
          return selectLambdas[selector];
        }
        macro = S_BODY + (callback ? S_TEST : '') + S_TAIL;
        head = S_HEAD;
        loop = S_LOOP;
        break;
      case false:
        if (matchLambdas[selector]) {
          return matchLambdas[selector];
        }
        macro = M_BODY + (callback ? M_TEST : '') + M_TAIL;
        head = M_HEAD;
        loop = M_LOOP;
        break;
      case null:
        if (selectLambdas[selector]) {
          return selectLambdas[selector];
        }
        macro = N_BODY + (callback ? N_TEST : '') + S_TAIL;
        head = S_HEAD;
        loop = N_LOOP;
        break;
      default:
    }

    source = compileSelector(selector, macro, mode, callback);

    loop += (mode || mode === null) ? '{' + source + '}' : source;

    if ((mode || mode === null) && selector.includes(':nth')) {
      loop += reNthElem.test(selector) ? 's.nthElement(null, 2);' : '';
      loop += reNthType.test(selector) ? 's.nthOfType(null, 2);' : '';
    }

    if (S_VARS[0] || M_VARS[0]) {
      vars = ',' + (S_VARS.join(',') || M_VARS.join(','));
      S_VARS = [];
      M_VARS = [];
    }

    const factory = Function('s', F_INIT + '{' + head + vars + ';' + loop + 'return r;}')(Snapshot);

    return mode || mode === null ? (selectLambdas[selector] = factory) : (matchLambdas[selector] = factory);
  };

  // optimize selectors avoiding duplicated checks
  const optimize = function (selector, token) {
    const index = token.index;
    const length = token[1].length + token[2].length;
    return selector.slice(0, index) +
      (' >+~'.indexOf(selector.charAt(index - 1)) > -1
        ? (':['.indexOf(selector.charAt(index + length + 1)) > -1
            ? '*'
            : '')
        : '') + selector.slice(index + length - (token[1] === '*' ? 1 : 0));
  };

  // prepare factory resolvers and closure collections
  const collect = function (selectors, context, callback) {
    let i;
    let l;
    const seen = { };
    let token = ['', '*', '*'];
    const optimized = selectors;
    const factory = [];
    const htmlset = [];
    const nodeset = [];
    let results = [];
    let type;

    for (i = 0, l = selectors.length; l > i; ++i) {
      if (!seen[selectors[i]] && (seen[selectors[i]] = true)) {
        type = selectors[i].match(reOptimizer);
        if (type && type[1] !== ':' && (token = type)) {
          token[1] || (token[1] = '*');
          optimized[i] = optimize(optimized[i], token);
        } else {
          token = ['', '*', '*'];
        }
      }

      nodeset[i] = token[1] + token[2];
      htmlset[i] = compat[token[1]](context, token[2]);
      factory[i] = compile(optimized[i], true, null);

      factory[i]
        ? factory[i](htmlset[i](), callback, context, results)
        : results.concat(htmlset[i]());
    }

    if (l > 1) {
      results.sort(documentOrder);
      hasDupes && (results = unique(results));
    }

    return {
      callback,
      context,
      factory,
      htmlset,
      nodeset,
      results
    };
  };

  // replace ':scope' pseudo-class with element references
  const makeref = function (selectors, element) {
    // DOCUMENT_NODE (9)
    if (element.nodeType === 9) {
      element = element.documentElement;
    }

    return selectors.replace(/:scope/gi,
      element.localName +
        (element.id ? '#' + element.id : '') +
        (element.className ? '.' + element.classList[0] : ''));
  };

  const matchAssert = function (f, element, callback) {
    let r = false;
    for (let i = 0, l = f.length; l > i; ++i) {
      f[i](element, callback, null, false) && (r = true);
    }
    return r;
  };

  const matchCollect = function (selectors, callback) {
    const f = [];
    for (let i = 0, l = selectors.length; l > i; ++i) {
      f[i] = compile(selectors[i], false, callback);
    }
    return { factory: f };
  };

  // equivalent of w3c 'matches' method
  const match = function _matches(selectors, element, callback) {
    let expressions;

    if (element && !/:has\(/.test(selectors) && matchResolvers[selectors]) {
      return matchAssert(matchResolvers[selectors].factory, element, callback);
    }

    lastMatched = selectors;

    // arguments validation
    if (arguments.length === 0) {
      emit(qsNotArgs, 'TypeError');
      return Config.VERBOSITY ? undefined : false;
    } else if (arguments[0] === '') {
      emit('\'\'' + qsInvalid);
      return Config.VERBOSITY ? undefined : false;
    }

    // input NULL or UNDEFINED
    if (typeof selectors !== 'string') {
      selectors = '' + selectors;
    }

    if ((/:scope/i).test(selectors)) {
      selectors = makeref(selectors, element);
    }

    // normalize input string
    const parsed = selectors
      .replace(/\0|\\$/g, '\ufffd')
      .replace(REX.combineWSP, '\x20')
      .replace(REX.pseudosWSP, '$1')
      .replace(REX.tabCharWSP, '\t')
      .replace(REX.commaGroup, ',')
      .replace(REX.trimSpaces, '');

    // parse, validate and split possible compound selectors
    if ((expressions = parsed.match(reValidator)) && expressions.join('') === parsed) {
      expressions = parsed.match(REX.splitGroup);
      if (parsed[parsed.length - 1] === ',') {
        emit(qsInvalid);
        return Config.VERBOSITY ? undefined : false;
      }
    } else {
      emit('\'' + selectors + '\'' + qsInvalid);
      return Config.VERBOSITY ? undefined : false;
    }

    matchResolvers[selectors] = matchCollect(expressions, callback);

    return matchAssert(matchResolvers[selectors].factory, element, callback);
  };

  // equivalent of w3c 'closest' method
  const ancestor = function _closest(selectors, element, callback) {
    if ((/:scope/i).test(selectors)) {
      selectors = makeref(selectors, element);
    }

    while (element) {
      if (match(selectors, element, callback)) break;
      element = element.parentElement;
    }
    return element;
  };

  // equivalent of w3c 'querySelectorAll' method
  const select = function _querySelectorAll(selectors, context, callback) {
    let expressions; let nodes = []; let resolver;

    context || (context = doc);

    if (selectors) {
      if ((resolver = selectResolvers[selectors])) {
        if (resolver.context === context && resolver.callback === callback) {
          const f = resolver.factory;
          const h = resolver.htmlset;
          const n = resolver.nodeset;
          if (n.length > 1) {
            const l = n.length;
            for (let i = 0, l = n.length, list; l > i; ++i) {
              list = compat[n[i][0]](context, n[i].slice(1))();
              if (f[i] !== null) {
                f[i](list, callback, context, nodes);
              } else {
                nodes = nodes.concat(list);
              }
            }
            if (l > 1 && nodes.length > 1) {
              nodes.sort(documentOrder);
              hasDupes && (nodes = unique(nodes));
            }
          } else {
            if (f[0]) {
              nodes = f[0](h[0](), callback, context, nodes);
            } else {
              nodes = h[0]();
            }
          }
          return typeof callback === 'function'
            ? concatCall(nodes, callback)
            : nodes;
        }
      }
    }

    lastSelected = selectors;

    // arguments validation
    if (arguments.length === 0) {
      emit(qsNotArgs, 'TypeError');
      return Config.VERBOSITY ? undefined : none;
    } else if (arguments[0] === '') {
      emit('\'\'' + qsInvalid);
      return Config.VERBOSITY ? undefined : none;
    } else if (lastContext !== context) {
      lastContext = switchContext(context);
    }

    // input NULL or UNDEFINED
    if (typeof selectors !== 'string') {
      selectors = '' + selectors;
    }

    if ((/:scope/i).test(selectors)) {
      selectors = makeref(selectors, context);
    }

    // normalize input string
    const parsed = selectors
      .replace(/\0|\\$/g, '\ufffd')
      .replace(REX.combineWSP, '\x20')
      .replace(REX.pseudosWSP, '$1')
      .replace(REX.tabCharWSP, '\t')
      .replace(REX.commaGroup, ',')
      .replace(REX.trimSpaces, '');

    // parse, validate and split possible compound selectors
    if ((expressions = parsed.match(reValidator)) && expressions.join('') === parsed) {
      expressions = parsed.match(REX.splitGroup);
      if (parsed[parsed.length - 1] === ',') {
        emit(qsInvalid);
        return Config.VERBOSITY ? undefined : false;
      }
    } else {
      emit('\'' + selectors + '\'' + qsInvalid);
      return Config.VERBOSITY ? undefined : false;
    }

    // save/reuse factory and closure collection
    selectResolvers[selectors] = collect(expressions, context, callback);

    nodes = selectResolvers[selectors].results;

    return typeof callback === 'function'
      ? concatCall(nodes, callback)
      : nodes;
  };

  // equivalent of w3c 'querySelector' method
  const first = function _querySelector(selectors, context, callback) {
    if (arguments.length === 0) {
      emit(qsNotArgs, 'TypeError');
    }
    return select(selectors, context, typeof callback === 'function'
      ? function firstMatch(element) {
        callback(element);
        return false;
      }
      : function firstMatch() {
        return false;
      }
    )[0] || null;
  };

  // execute the engine initialization code
  const initialize = function (d) {
    setIdentifierSyntax();
    lastContext = switchContext(d, true);
    Snapshot.doc = doc;
    Snapshot.from = doc;
    Snapshot.byTag = byTag;
    Snapshot.first = first;
    Snapshot.match = match;
    Snapshot.ancestor = ancestor;
    Snapshot.nthOfType = nthOfType;
    Snapshot.nthElement = nthElement;
    Snapshot.hasAttributeNS = hasAttributeNS;
    Snapshot.isTarget = isTarget;
    Snapshot.isIndeterminate = isIndeterminate;
    Snapshot.isContentEditable = isContentEditable;
  };

  initialize(doc);

  // public exported methods/objects
  const Dom = {
    // exported engine methods
    Version: version,
    configure,
    match,
    closest: ancestor,
    first,
    select
  };

  return Dom;
});
