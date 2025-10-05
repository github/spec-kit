"use strict";

const {
  resolve: resolveColor,
  utils: { cssCalc, resolveGradient, splitValue }
} = require("@asamuzakjp/css-color");
const { next: syntaxes } = require("@csstools/css-syntax-patches-for-csstree");
const csstree = require("css-tree");
const { asciiLowercase } = require("./utils/strings");

// CSS global keywords
// @see https://drafts.csswg.org/css-cascade-5/#defaulting-keywords
const GLOBAL_KEY = Object.freeze(["initial", "inherit", "unset", "revert", "revert-layer"]);

// System colors
// @see https://drafts.csswg.org/css-color/#css-system-colors
// @see https://drafts.csswg.org/css-color/#deprecated-system-colors
const SYS_COLOR = Object.freeze([
  "accentcolor",
  "accentcolortext",
  "activeborder",
  "activecaption",
  "activetext",
  "appworkspace",
  "background",
  "buttonborder",
  "buttonface",
  "buttonhighlight",
  "buttonshadow",
  "buttontext",
  "canvas",
  "canvastext",
  "captiontext",
  "field",
  "fieldtext",
  "graytext",
  "highlight",
  "highlighttext",
  "inactiveborder",
  "inactivecaption",
  "inactivecaptiontext",
  "infobackground",
  "infotext",
  "linktext",
  "mark",
  "marktext",
  "menu",
  "menutext",
  "scrollbar",
  "selecteditem",
  "selecteditemtext",
  "threeddarkshadow",
  "threedface",
  "threedhighlight",
  "threedlightshadow",
  "threedshadow",
  "visitedtext",
  "window",
  "windowframe",
  "windowtext"
]);

// Regular expressions
const CALC_FUNC_NAMES =
  "(?:a?(?:cos|sin|tan)|abs|atan2|calc|clamp|exp|hypot|log|max|min|mod|pow|rem|round|sign|sqrt)";
const calcRegEx = new RegExp(`^${CALC_FUNC_NAMES}\\(`);
const calcContainedRegEx = new RegExp(`(?<=[*/\\s(])${CALC_FUNC_NAMES}\\(`);
const calcNameRegEx = new RegExp(`^${CALC_FUNC_NAMES}$`);
const varRegEx = /^var\(/;
const varContainedRegEx = /(?<=[*/\s(])var\(/;

// Patched css-tree
const cssTree = csstree.fork(syntaxes);

// Prepare stringified value.
exports.prepareValue = (value, globalObject = globalThis) => {
  // `null` is converted to an empty string.
  // @see https://webidl.spec.whatwg.org/#LegacyNullToEmptyString
  if (value === null) {
    return "";
  }
  const type = typeof value;
  switch (type) {
    case "string":
      return value.trim();
    case "number":
      return value.toString();
    case "undefined":
      return "undefined";
    case "symbol":
      throw new globalObject.TypeError("Can not convert symbol to string.");
    default: {
      const str = value.toString();
      if (typeof str === "string") {
        return str.trim();
      }
      throw new globalObject.TypeError(`Can not convert ${type} to string.`);
    }
  }
};

// Value is a global keyword.
exports.isGlobalKeyword = (val) => {
  return GLOBAL_KEY.includes(asciiLowercase(val));
};

// Value starts with and/or contains CSS var() function.
exports.hasVarFunc = (val) => {
  return varRegEx.test(val) || varContainedRegEx.test(val);
};

// Value starts with and/or contains CSS calc() related functions.
exports.hasCalcFunc = (val) => {
  return calcRegEx.test(val) || calcContainedRegEx.test(val);
};

// Splits value into an array.
// @see https://github.com/asamuzaK/cssColor/blob/main/src/js/util.ts
exports.splitValue = splitValue;

// Parse CSS to AST.
exports.parseCSS = (val, opt, toObject = false) => {
  if (typeof val !== "string") {
    val = exports.prepareValue(val);
  }
  const ast = cssTree.parse(val, opt);
  if (toObject) {
    return cssTree.toPlainObject(ast);
  }
  return ast;
};

// Value is a valid property value.
// Returns `false` for custom property and/or var().
exports.isValidPropertyValue = (prop, val) => {
  if (typeof val !== "string") {
    val = exports.prepareValue(val);
  }
  if (val === "") {
    return true;
  }
  // cssTree.lexer does not support deprecated system colors
  // @see https://github.com/w3c/webref/issues/1519#issuecomment-3120290261
  // @see https://github.com/w3c/webref/issues/1647
  if (SYS_COLOR.includes(asciiLowercase(val))) {
    if (/^(?:-webkit-)?(?:[a-z][a-z\d]*-)*color$/i.test(prop)) {
      return true;
    }
    return false;
  }
  let ast;
  try {
    ast = exports.parseCSS(val, {
      context: "value"
    });
  } catch {
    return false;
  }
  const { error, matched } = cssTree.lexer.matchProperty(prop, ast);
  return error === null && matched !== null;
};

// Simplify / resolve math functions.
exports.resolveCalc = (val, opt = { format: "specifiedValue" }) => {
  if (typeof val !== "string") {
    val = exports.prepareValue(val);
  }
  if (val === "" || exports.hasVarFunc(val) || !exports.hasCalcFunc(val)) {
    return val;
  }
  const obj = exports.parseCSS(val, { context: "value" }, true);
  if (!obj?.children) {
    return;
  }
  const { children: items } = obj;
  const values = [];
  for (const item of items) {
    const { type: itemType, name: itemName, value: itemValue } = item;
    if (itemType === "Function") {
      const value = cssTree
        .generate(item)
        .replace(/\)(?!\)|\s|,)/g, ") ")
        .trim();
      if (calcNameRegEx.test(itemName)) {
        const newValue = cssCalc(value, opt);
        values.push(newValue);
      } else {
        values.push(value);
      }
    } else if (itemType === "String") {
      values.push(`"${itemValue}"`);
    } else {
      values.push(itemName ?? itemValue);
    }
  }
  return values.join(" ");
};

// Parse property value. Returns string or array of parsed object.
exports.parsePropertyValue = (prop, val, opt = {}) => {
  const { caseSensitive, globalObject, inArray } = opt;
  val = exports.prepareValue(val, globalObject);
  if (val === "" || exports.hasVarFunc(val)) {
    return val;
  } else if (exports.hasCalcFunc(val)) {
    const calculatedValue = exports.resolveCalc(val, {
      format: "specifiedValue"
    });
    if (typeof calculatedValue !== "string") {
      return;
    }
    val = calculatedValue;
  }
  const lowerCasedValue = asciiLowercase(val);
  if (GLOBAL_KEY.includes(lowerCasedValue)) {
    if (inArray) {
      return [
        {
          type: "GlobalKeyword",
          name: lowerCasedValue
        }
      ];
    }
    return lowerCasedValue;
  } else if (SYS_COLOR.includes(lowerCasedValue)) {
    if (/^(?:(?:-webkit-)?(?:[a-z][a-z\d]*-)*color|border)$/i.test(prop)) {
      if (inArray) {
        return [
          {
            type: "Identifier",
            name: lowerCasedValue
          }
        ];
      }
      return lowerCasedValue;
    }
    return;
  }
  try {
    const ast = exports.parseCSS(val, {
      context: "value"
    });
    const { error, matched } = cssTree.lexer.matchProperty(prop, ast);
    if (error || !matched) {
      return;
    }
    if (inArray) {
      const obj = cssTree.toPlainObject(ast);
      const items = obj.children;
      const parsedValues = [];
      for (const item of items) {
        const { children, name, type, value, unit } = item;
        switch (type) {
          case "Dimension": {
            parsedValues.push({
              type,
              value,
              unit: asciiLowercase(unit)
            });
            break;
          }
          case "Function": {
            const css = cssTree
              .generate(item)
              .replace(/\)(?!\)|\s|,)/g, ") ")
              .trim();
            const raw = items.length === 1 ? val : css;
            const itemValue = raw
              .replace(new RegExp(`^${name}\\(`), "")
              .replace(/\)$/, "")
              .trim();
            if (name === "calc") {
              if (children.length === 1) {
                const [child] = children;
                if (child.type === "Number") {
                  parsedValues.push({
                    type: "Calc",
                    name: "calc",
                    isNumber: true,
                    value: `${parseFloat(child.value)}`,
                    raw
                  });
                } else {
                  parsedValues.push({
                    type: "Calc",
                    name: "calc",
                    isNumber: false,
                    value: `${asciiLowercase(itemValue)}`,
                    raw
                  });
                }
              } else {
                parsedValues.push({
                  type: "Calc",
                  name: "calc",
                  isNumber: false,
                  value: asciiLowercase(itemValue),
                  raw
                });
              }
            } else {
              parsedValues.push({
                type,
                name,
                value: asciiLowercase(itemValue),
                raw
              });
            }
            break;
          }
          case "Identifier": {
            if (caseSensitive) {
              parsedValues.push(item);
            } else {
              parsedValues.push({
                type,
                name: asciiLowercase(name)
              });
            }
            break;
          }
          default: {
            parsedValues.push(item);
          }
        }
      }
      return parsedValues;
    }
  } catch {
    return;
  }
  return val;
};

// Parse <number>.
exports.parseNumber = (val, opt = {}) => {
  const [item] = val;
  const { type, value } = item ?? {};
  if (type !== "Number") {
    return;
  }
  const { clamp } = opt;
  const max = opt.max ?? Number.INFINITY;
  const min = opt.min ?? Number.NEGATIVE_INFINITY;
  let num = parseFloat(value);
  if (clamp) {
    if (num > max) {
      num = max;
    } else if (num < min) {
      num = min;
    }
  } else if (num > max || num < min) {
    return;
  }
  return `${num}`;
};

// Parse <length>.
exports.parseLength = (val, opt = {}) => {
  const [item] = val;
  const { type, value, unit } = item ?? {};
  if (type !== "Dimension" && !(type === "Number" && value === "0")) {
    return;
  }
  const { clamp } = opt;
  const max = opt.max ?? Number.INFINITY;
  const min = opt.min ?? Number.NEGATIVE_INFINITY;
  let num = parseFloat(value);
  if (clamp) {
    if (num > max) {
      num = max;
    } else if (num < min) {
      num = min;
    }
  } else if (num > max || num < min) {
    return;
  }
  if (num === 0 && !unit) {
    return `${num}px`;
  } else if (unit) {
    return `${num}${asciiLowercase(unit)}`;
  }
};

// Parse <percentage>.
exports.parsePercentage = (val, opt = {}) => {
  const [item] = val;
  const { type, value } = item ?? {};
  if (type !== "Percentage" && !(type === "Number" && value === "0")) {
    return;
  }
  const { clamp } = opt;
  const max = opt.max ?? Number.INFINITY;
  const min = opt.min ?? Number.NEGATIVE_INFINITY;
  let num = parseFloat(value);
  if (clamp) {
    if (num > max) {
      num = max;
    } else if (num < min) {
      num = min;
    }
  } else if (num > max || num < min) {
    return;
  }
  if (num === 0) {
    return `${num}%`;
  }
  return `${num}%`;
};

// Parse <length-percentage>.
exports.parseLengthPercentage = (val, opt = {}) => {
  const [item] = val;
  const { type, value, unit } = item ?? {};
  if (type !== "Dimension" && type !== "Percentage" && !(type === "Number" && value === "0")) {
    return;
  }
  const { clamp } = opt;
  const max = opt.max ?? Number.INFINITY;
  const min = opt.min ?? Number.NEGATIVE_INFINITY;
  let num = parseFloat(value);
  if (clamp) {
    if (num > max) {
      num = max;
    } else if (num < min) {
      num = min;
    }
  } else if (num > max || num < min) {
    return;
  }
  if (unit) {
    if (/deg|g?rad|turn/i.test(unit)) {
      return;
    }
    return `${num}${asciiLowercase(unit)}`;
  } else if (type === "Percentage") {
    return `${num}%`;
  } else if (num === 0) {
    return `${num}px`;
  }
};

// Parse <angle>.
exports.parseAngle = (val) => {
  const [item] = val;
  const { type, value, unit } = item ?? {};
  if (type !== "Dimension" && !(type === "Number" && value === "0")) {
    return;
  }
  const num = parseFloat(value);
  if (unit) {
    if (!/^(?:deg|g?rad|turn)$/i.test(unit)) {
      return;
    }
    return `${num}${asciiLowercase(unit)}`;
  } else if (num === 0) {
    return `${num}deg`;
  }
};

// Parse <url>.
exports.parseUrl = (val) => {
  const [item] = val;
  const { type, value } = item ?? {};
  if (type !== "Url") {
    return;
  }
  const str = value.replace(/\\\\/g, "\\").replaceAll('"', '\\"');
  return `url("${str}")`;
};

// Parse <string>.
exports.parseString = (val) => {
  const [item] = val;
  const { type, value } = item ?? {};
  if (type !== "String") {
    return;
  }
  const str = value.replace(/\\\\/g, "\\").replaceAll('"', '\\"');
  return `"${str}"`;
};

// Parse <color>.
exports.parseColor = (val) => {
  const [item] = val;
  const { name, type, value } = item ?? {};
  switch (type) {
    case "Function": {
      const res = resolveColor(`${name}(${value})`, {
        format: "specifiedValue"
      });
      if (res) {
        return res;
      }
      break;
    }
    case "Hash": {
      const res = resolveColor(`#${value}`, {
        format: "specifiedValue"
      });
      if (res) {
        return res;
      }
      break;
    }
    case "Identifier": {
      if (SYS_COLOR.includes(name)) {
        return name;
      }
      const res = resolveColor(name, {
        format: "specifiedValue"
      });
      if (res) {
        return res;
      }
      break;
    }
    default:
  }
};

// Parse <gradient>.
exports.parseGradient = (val) => {
  const [item] = val;
  const { name, type, value } = item ?? {};
  if (type !== "Function") {
    return;
  }
  const res = resolveGradient(`${name}(${value})`, {
    format: "specifiedValue"
  });
  if (res) {
    return res;
  }
};
