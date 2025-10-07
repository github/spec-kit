"use strict";

const parsers = require("../parsers");

const property = "font-variant";
const shorthand = "font";

module.exports.parse = function parse(v, opt = {}) {
  const { globalObject } = opt;
  if (v === "") {
    return v;
  }
  const values = parsers.splitValue(v);
  const parsedValues = [];
  for (const val of values) {
    const value = parsers.parsePropertyValue(property, val, {
      globalObject,
      inArray: true
    });
    if (Array.isArray(value) && value.length === 1) {
      const [{ name, type, value: itemValue }] = value;
      switch (type) {
        case "Function": {
          parsedValues.push(`${name}(${itemValue})`);
          break;
        }
        case "GlobalKeyword":
        case "Identifier": {
          parsedValues.push(name);
          break;
        }
        default: {
          return;
        }
      }
    } else if (typeof value === "string") {
      parsedValues.push(value);
    }
  }
  if (parsedValues.length) {
    if (parsedValues.length > 1) {
      if (parsedValues.includes("normal") || parsedValues.includes("none")) {
        return;
      }
    }
    return parsedValues.join(" ");
  }
};

module.exports.definition = {
  set(v) {
    v = parsers.prepareValue(v, this._global);
    if (parsers.hasVarFunc(v)) {
      this._setProperty(shorthand, "");
      this._setProperty(property, v);
    } else {
      const val = module.exports.parse(v, {
        globalObject: this._global
      });
      if (typeof val === "string") {
        const shorthandPriority = this._priorities.get(shorthand);
        const prior = this._priorities.get(property) ?? "";
        const priority = shorthandPriority && prior ? "" : prior;
        this._setProperty(property, val, priority);
      }
    }
  },
  get() {
    return this.getPropertyValue(property);
  },
  enumerable: true,
  configurable: true
};
