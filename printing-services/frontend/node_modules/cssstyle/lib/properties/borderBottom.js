"use strict";

const parsers = require("../parsers");
const borderBottomWidth = require("./borderBottomWidth");
const borderBottomStyle = require("./borderBottomStyle");
const borderBottomColor = require("./borderBottomColor");

const property = "border-bottom";
const shorthand = "border";

module.exports.initialValues = new Map([
  ["border-bottom-width", "medium"],
  ["border-bottom-style", "none"],
  ["border-bottom-color", "currentcolor"]
]);

module.exports.shorthandFor = new Map([
  ["border-bottom-width", borderBottomWidth],
  ["border-bottom-style", borderBottomStyle],
  ["border-bottom-color", borderBottomColor]
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
          if (isNumber || parsedValues.has("border-bottom-width")) {
            return;
          }
          parsedValues.set("border-bottom-width", `${name}(${itemValue})`);
          break;
        }
        case "Dimension":
        case "Number": {
          if (parsedValues.has("border-bottom-width")) {
            return;
          }
          const parsedValue = parsers.parseLength(value, {
            min: 0
          });
          if (!parsedValue) {
            return;
          }
          parsedValues.set("border-bottom-width", parsedValue);
          break;
        }
        case "Function": {
          if (parsedValues.has("border-bottom-color")) {
            return;
          }
          const parsedValue = parsers.parseColor(value);
          if (!parsedValue) {
            return;
          }
          parsedValues.set("border-bottom-color", parsedValue);
          break;
        }
        case "GlobalKeyword": {
          return name;
        }
        case "Hash": {
          if (parsedValues.has("border-bottom-color")) {
            return;
          }
          const parsedValue = parsers.parseColor(`#${itemValue}`);
          if (!parsedValue) {
            return;
          }
          parsedValues.set("border-bottom-color", parsedValue);
          break;
        }
        case "Identifier": {
          if (parsers.isValidPropertyValue("border-bottom-width", name)) {
            if (parsedValues.has("border-bottom-width")) {
              return;
            }
            parsedValues.set("border-bottom-width", name);
            break;
          } else if (parsers.isValidPropertyValue("border-bottom-style", name)) {
            if (parsedValues.has("border-bottom-style")) {
              return;
            }
            parsedValues.set("border-bottom-style", name);
            break;
          } else if (parsers.isValidPropertyValue("border-bottom-color", name)) {
            if (parsedValues.has("border-bottom-color")) {
              return;
            }
            parsedValues.set("border-bottom-color", name);
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
      "border-bottom-width": "medium"
    };
    for (const key of keys) {
      if (parsedValues.has(key)) {
        const parsedValue = parsedValues.get(key);
        if (parsedValue !== module.exports.initialValues.get(key)) {
          obj[key] = parsedValues.get(key);
          if (obj["border-bottom-width"] && obj["border-bottom-width"] === "medium") {
            delete obj["border-bottom-width"];
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
