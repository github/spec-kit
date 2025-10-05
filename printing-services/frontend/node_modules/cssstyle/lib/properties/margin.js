"use strict";

const parsers = require("../parsers");
const marginTop = require("./marginTop");
const marginRight = require("./marginRight");
const marginBottom = require("./marginBottom");
const marginLeft = require("./marginLeft");

const property = "margin";

module.exports.position = "edges";

module.exports.shorthandFor = new Map([
  ["margin-top", marginTop],
  ["margin-right", marginRight],
  ["margin-bottom", marginBottom],
  ["margin-left", marginLeft]
]);

module.exports.parse = function parse(v, opt = {}) {
  const { globalObject } = opt;
  if (v === "") {
    return v;
  }
  const values = parsers.parsePropertyValue(property, v, {
    globalObject,
    inArray: true
  });
  const parsedValues = [];
  if (Array.isArray(values) && values.length) {
    if (values.length > 4) {
      return;
    }
    for (const value of values) {
      const { isNumber, name, type, value: itemValue } = value;
      switch (type) {
        case "Calc": {
          if (isNumber) {
            return;
          }
          parsedValues.push(`${name}(${itemValue})`);
          break;
        }
        case "GlobalKeyword": {
          if (values.length !== 1) {
            return;
          }
          parsedValues.push(name);
          break;
        }
        case "Identifier": {
          parsedValues.push(name);
          break;
        }
        default: {
          const parsedValue = parsers.parseLengthPercentage([value]);
          if (!parsedValue) {
            return;
          }
          parsedValues.push(parsedValue);
        }
      }
    }
  } else if (typeof values === "string") {
    parsedValues.push(values);
  }
  if (parsedValues.length) {
    return parsedValues;
  }
};

module.exports.definition = {
  set(v) {
    v = parsers.prepareValue(v, this._global);
    if (parsers.hasVarFunc(v)) {
      for (const [longhand] of module.exports.shorthandFor) {
        this._setProperty(longhand, "");
      }
      this._setProperty(property, v);
    } else {
      const val = module.exports.parse(v, {
        globalObject: this._global
      });
      if (Array.isArray(val) || typeof val === "string") {
        const priority = this._priorities.get(property) ?? "";
        this._positionShorthandSetter(property, val, priority);
      }
    }
  },
  get() {
    return this.getPropertyValue(property);
  },
  enumerable: true,
  configurable: true
};
