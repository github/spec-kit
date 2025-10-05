"use strict";

const parsers = require("../parsers");
const borderTopWidth = require("./borderTopWidth");
const borderTopStyle = require("./borderTopStyle");
const borderTopColor = require("./borderTopColor");

const property = "border-top";
const shorthand = "border";

module.exports.initialValues = new Map([
  ["border-top-width", "medium"],
  ["border-top-style", "none"],
  ["border-top-color", "currentcolor"]
]);

module.exports.shorthandFor = new Map([
  ["border-top-width", borderTopWidth],
  ["border-top-style", borderTopStyle],
  ["border-top-color", borderTopColor]
]);

module.exports.parse = function parse(v, opt = {}) {
  const { globalObject } = opt;
  if (v === "") {
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
          if (isNumber || parsedValues.has("border-top-width")) {
            return;
          }
          parsedValues.set("border-top-width", `${name}(${itemValue})`);
          break;
        }
        case "Dimension":
        case "Number": {
          if (parsedValues.has("border-top-width")) {
            return;
          }
          const parsedValue = parsers.parseLength(value, {
            min: 0
          });
          if (!parsedValue) {
            return;
          }
          parsedValues.set("border-top-width", parsedValue);
          break;
        }
        case "Function": {
          if (parsedValues.has("border-top-color")) {
            return;
          }
          const parsedValue = parsers.parseColor(value);
          if (!parsedValue) {
            return;
          }
          parsedValues.set("border-top-color", parsedValue);
          break;
        }
        case "GlobalKeyword": {
          return name;
        }
        case "Hash": {
          if (parsedValues.has("border-top-color")) {
            return;
          }
          const parsedValue = parsers.parseColor(`#${itemValue}`);
          if (!parsedValue) {
            return;
          }
          parsedValues.set("border-top-color", parsedValue);
          break;
        }
        case "Identifier": {
          if (parsers.isValidPropertyValue("border-top-width", name)) {
            if (parsedValues.has("border-top-width")) {
              return;
            }
            parsedValues.set("border-top-width", name);
            break;
          } else if (parsers.isValidPropertyValue("border-top-style", name)) {
            if (parsedValues.has("border-top-style")) {
              return;
            }
            parsedValues.set("border-top-style", name);
            break;
          } else if (parsers.isValidPropertyValue("border-top-color", name)) {
            if (parsedValues.has("border-top-color")) {
              return;
            }
            parsedValues.set("border-top-color", name);
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
      "border-top-width": "medium"
    };
    for (const key of keys) {
      if (parsedValues.has(key)) {
        const parsedValue = parsedValues.get(key);
        if (parsedValue !== module.exports.initialValues.get(key)) {
          obj[key] = parsedValues.get(key);
          if (obj["border-top-width"] && obj["border-top-width"] === "medium") {
            delete obj["border-top-width"];
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
        const shorthandPriority = this._priorities.get(shorthand);
        const prior = this._priorities.get(property) ?? "";
        const priority = shorthandPriority && prior ? "" : prior;
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
