"use strict";

const parsers = require("../parsers");

const property = "border-spacing";

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
    switch (value.length) {
      case 1: {
        const [part1] = value;
        const val1 = parsers.parseLength([part1]);
        if (val1) {
          return val1;
        }
        break;
      }
      case 2: {
        const [part1, part2] = value;
        const val1 = parsers.parseLength([part1]);
        const val2 = parsers.parseLength([part2]);
        if (val1 && val2) {
          return `${val1} ${val2}`;
        }
        break;
      }
      default:
    }
  } else if (typeof value === "string") {
    return value;
  }
};

module.exports.definition = {
  set(v) {
    v = parsers.prepareValue(v, this._global);
    if (parsers.hasVarFunc(v)) {
      this._setProperty(property, v);
    } else {
      const val = module.exports.parse(v, {
        globalObject: this._global
      });
      if (typeof val === "string") {
        const priority = this._priorities.get(property) ?? "";
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
