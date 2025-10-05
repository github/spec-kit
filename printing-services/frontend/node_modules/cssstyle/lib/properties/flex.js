"use strict";

const parsers = require("../parsers");
const flexGrow = require("./flexGrow");
const flexShrink = require("./flexShrink");
const flexBasis = require("./flexBasis");

const property = "flex";

module.exports.initialValues = new Map([
  ["flex-grow", "0"],
  ["flex-shrink", "1"],
  ["flex-basis", "auto"]
]);

module.exports.shorthandFor = new Map([
  ["flex-grow", flexGrow],
  ["flex-shrink", flexShrink],
  ["flex-basis", flexBasis]
]);

module.exports.parse = function parse(v, opt = {}) {
  const { globalObject } = opt;
  if (v === "") {
    return v;
  }
  const value = parsers.parsePropertyValue(property, v, {
    globalObject,
    inArray: true
  });
  if (Array.isArray(value) && value.length) {
    const flex = {
      "flex-grow": "1",
      "flex-shrink": "1",
      "flex-basis": "0%"
    };
    if (value.length === 1) {
      const [{ isNumber, name, type, unit, value: itemValue }] = value;
      switch (type) {
        case "Calc": {
          if (isNumber) {
            flex["flex-grow"] = `${name}(${itemValue})`;
            return flex;
          }
          flex["flex-basis"] = `${name}(${itemValue})`;
          return flex;
        }
        case "Dimension": {
          flex["flex-basis"] = `${itemValue}${unit}`;
          return flex;
        }
        case "GlobalKeyword": {
          return name;
        }
        case "Identifier": {
          if (name === "none") {
            return {
              "flex-grow": "0",
              "flex-shrink": "0",
              "flex-basis": "auto"
            };
          }
          flex["flex-basis"] = name;
          return flex;
        }
        case "Number": {
          flex["flex-grow"] = itemValue;
          return flex;
        }
        case "Percentage": {
          flex["flex-basis"] = `${itemValue}%`;
          return flex;
        }
        default:
      }
    } else {
      const [val1, val2, val3] = value;
      if (val1.type === "Calc" && val1.isNumber) {
        flex["flex-grow"] = `${val1.name}(${val1.value})`;
      } else if (val1.type === "Number") {
        flex["flex-grow"] = val1.value;
      } else {
        return;
      }
      if (val3) {
        if (val2.type === "Calc" && val2.isNumber) {
          flex["flex-shrink"] = `${val2.name}(${val2.value})`;
        } else if (val2.type === "Number") {
          flex["flex-shrink"] = val2.value;
        } else {
          return;
        }
        if (val3.type === "GlobalKeyword" || val3.type === "Identifier") {
          flex["flex-basis"] = val3.name;
        } else if (val3.type === "Calc" && !val3.isNumber) {
          flex["flex-basis"] = `${val3.name}(${val3.value})`;
        } else if (val3.type === "Dimension") {
          flex["flex-basis"] = `${val3.value}${val3.unit}`;
        } else if (val3.type === "Percentage") {
          flex["flex-basis"] = `${val3.value}%`;
        } else {
          return;
        }
      } else {
        switch (val2.type) {
          case "Calc": {
            if (val2.isNumber) {
              flex["flex-shrink"] = `${val2.name}(${val2.value})`;
            } else {
              flex["flex-basis"] = `${val2.name}(${val2.value})`;
            }
            break;
          }
          case "Dimension": {
            flex["flex-basis"] = `${val2.value}${val2.unit}`;
            break;
          }
          case "Number": {
            flex["flex-shrink"] = val2.value;
            break;
          }
          case "Percentage": {
            flex["flex-basis"] = `${val2.value}%`;
            break;
          }
          case "Identifier": {
            flex["flex-basis"] = val2.name;
            break;
          }
          default: {
            return;
          }
        }
      }
      return flex;
      // return [...Object.values(flex)].join(" ");
    }
  } else if (typeof value === "string") {
    return value;
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
      const priority = this._priorities.get(property) ?? "";
      if (typeof val === "string") {
        for (const [longhand] of module.exports.shorthandFor) {
          this._setProperty(longhand, val, priority);
        }
        this._setProperty(property, val, priority);
      } else if (val) {
        const values = [];
        for (const [longhand, value] of Object.entries(val)) {
          values.push(value);
          this._setProperty(longhand, value, priority);
        }
        this._setProperty(property, values.join(" "), priority);
      }
    }
  },
  get() {
    return this.getPropertyValue(property);
  },
  enumerable: true,
  configurable: true
};
