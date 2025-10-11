"use strict";

const parsers = require("../parsers");

const property = "background-image";
const shorthand = "background";

module.exports.parse = function parse(v, opt = {}) {
  const { globalObject } = opt;
  if (v === "") {
    return v;
  }
  const values = parsers.splitValue(v, { delimiter: "," });
  const parsedValues = [];
  for (const val of values) {
    const value = parsers.parsePropertyValue(property, val, {
      globalObject,
      inArray: true
    });
    if (Array.isArray(value) && value.length === 1) {
      const [{ name, type }] = value;
      switch (type) {
        case "GlobalKeyword":
        case "Identifier": {
          parsedValues.push(name);
          break;
        }
        case "Url": {
          const parsedValue = parsers.parseUrl(value);
          if (!parsedValue) {
            return;
          }
          parsedValues.push(parsedValue);
          break;
        }
        default: {
          const parsedValue = parsers.parseGradient(value);
          if (!parsedValue) {
            return;
          }
          parsedValues.push(parsedValue);
        }
      }
    } else if (typeof value === "string") {
      parsedValues.push(value);
    } else {
      return;
    }
  }
  if (parsedValues.length) {
    return parsedValues.join(", ");
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
