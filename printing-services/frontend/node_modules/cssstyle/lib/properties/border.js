"use strict";

const parsers = require("../parsers");
const borderWidth = require("./borderWidth");
const borderStyle = require("./borderStyle");
const borderColor = require("./borderColor");
const borderTop = require("./borderTop");
const borderRight = require("./borderRight");
const borderBottom = require("./borderBottom");
const borderLeft = require("./borderLeft");

const property = "border";

module.exports.initialValues = new Map([
  ["border-width", "medium"],
  ["border-style", "none"],
  ["border-color", "currentcolor"]
]);

module.exports.shorthandFor = new Map([
  ["border-width", borderWidth],
  ["border-style", borderStyle],
  ["border-color", borderColor]
]);

module.exports.positionShorthandFor = new Map([
  ["border-top", borderTop],
  ["border-right", borderRight],
  ["border-bottom", borderBottom],
  ["border-left", borderLeft]
]);

module.exports.parse = function parse(v, opt = {}) {
  const { globalObject } = opt;
  if (v === "" || parsers.hasVarFunc(v)) {
    return v;
  }
  const values = parsers.splitValue(v);
  const parsedValues = new Map();
  for (const val of values) {
    const value = parsers.parsePropertyValue(property, val, {
      globalObject,
      inArray: true
    });
    if (Array.isArray(value) && value.length === 1) {
      const [{ isNumber, name, type, value: itemValue }] = value;
      switch (type) {
        case "Calc": {
          if (isNumber || parsedValues.has("border-width")) {
            return;
          }
          parsedValues.set("border-width", `${name}(${itemValue})`);
          break;
        }
        case "Dimension":
        case "Number": {
          if (parsedValues.has("border-width")) {
            return;
          }
          const parsedValue = parsers.parseLength(value, {
            min: 0
          });
          if (!parsedValue) {
            return;
          }
          parsedValues.set("border-width", parsedValue);
          break;
        }
        case "Function": {
          if (parsedValues.has("border-color")) {
            return;
          }
          const parsedValue = parsers.parseColor(value);
          if (!parsedValue) {
            return;
          }
          parsedValues.set("border-color", parsedValue);
          break;
        }
        case "GlobalKeyword": {
          return name;
        }
        case "Hash": {
          if (parsedValues.has("border-color")) {
            return;
          }
          const parsedValue = parsers.parseColor(`#${itemValue}`);
          if (!parsedValue) {
            return;
          }
          parsedValues.set("border-color", parsedValue);
          break;
        }
        case "Identifier": {
          if (parsers.isValidPropertyValue("border-width", name)) {
            if (parsedValues.has("border-width")) {
              return;
            }
            parsedValues.set("border-width", name);
            break;
          } else if (parsers.isValidPropertyValue("border-style", name)) {
            if (parsedValues.has("border-style")) {
              return;
            }
            parsedValues.set("border-style", name);
            break;
          } else if (parsers.isValidPropertyValue("border-color", name)) {
            if (parsedValues.has("border-color")) {
              return;
            }
            parsedValues.set("border-color", name);
            break;
          }
          return;
        }
        default: {
          return;
        }
      }
    } else {
      return;
    }
  }
  if (parsedValues.size) {
    const keys = module.exports.shorthandFor.keys();
    const obj = {
      "border-width": "medium"
    };
    for (const key of keys) {
      if (parsedValues.has(key)) {
        const parsedValue = parsedValues.get(key);
        if (parsedValue !== module.exports.initialValues.get(key)) {
          obj[key] = parsedValues.get(key);
          if (obj["border-width"] && obj["border-width"] === "medium") {
            delete obj["border-width"];
          }
        }
      }
    }
    return obj;
  }
};

module.exports.definition = {
  set(v) {
    v = parsers.prepareValue(v, this._global);
    if (parsers.hasVarFunc(v)) {
      this._borderSetter(property, v, "");
    } else {
      const val = module.exports.parse(v, {
        globalObject: this._global
      });
      if (val || typeof val === "string") {
        const priority = this._priorities.get(property) ?? "";
        this._borderSetter(property, val, priority);
      }
    }
  },
  get() {
    return this.getPropertyValue(property);
  },
  enumerable: true,
  configurable: true
};
