"use strict";

const parsers = require("../parsers");

const property = "background-size";
const shorthand = "background";

module.exports.parse = function parse(v, opt = {}) {
  const { globalObject } = opt;
  if (v === "") {
    return v;
  }
  const values = parsers.splitValue(v, {
    delimiter: ","
  });
  const parsedValues = [];
  for (const val of values) {
    const value = parsers.parsePropertyValue(property, val, {
      globalObject,
      inArray: true
    });
    if (Array.isArray(value) && value.length) {
      if (value.length === 1) {
        const [{ isNumber, name, type, value: itemValue }] = value;
        switch (type) {
          case "Calc": {
            if (isNumber) {
              return;
            }
            parsedValues.push(`${name}(${itemValue})`);
            break;
          }
          case "GlobalKeyword":
          case "Identifier": {
            parsedValues.push(name);
            break;
          }
          default: {
            const parsedValue = parsers.parseLengthPercentage(value);
            if (!parsedValue) {
              return;
            }
            parsedValues.push(parsedValue);
          }
        }
      } else {
        const [val1, val2] = value;
        const parts = [];
        if (val1.type === "Calc" && !val1.isNumber) {
          parts.push(`${val1.name}(${val1.value})`);
        } else if (val1.type === "Identifier") {
          parts.push(val1.name);
        } else if (val1.type === "Dimension") {
          parts.push(`${val1.value}${val1.unit}`);
        } else if (val1.type === "Percentage") {
          parts.push(`${val1.value}%`);
        } else {
          return;
        }
        switch (val2.type) {
          case "Calc": {
            if (val2.isNumber) {
              return;
            }
            parts.push(`${val2.name}(${val2.value})`);
            break;
          }
          case "Dimension": {
            parts.push(`${val2.value}${val2.unit}`);
            break;
          }
          case "Identifier": {
            if (val2.name !== "auto") {
              parts.push(val2.name);
            }
            break;
          }
          case "Percentage": {
            parts.push(`${val2.value}%`);
            break;
          }
          default: {
            return;
          }
        }
        parsedValues.push(parts.join(" "));
      }
    } else if (typeof value === "string") {
      parsedValues.push(value);
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
