"use strict";

const parsers = require("../parsers");

const property = "border-right-color";
const lineShorthand = "border-color";
const positionShorthand = "border-right";
const shorthand = "border";

module.exports.parse = function parse(v, opt = {}) {
  const { globalObject } = opt;
  if (v === "") {
    return v;
  }
  const value = parsers.parsePropertyValue(property, v, {
    globalObject,
    inArray: true
  });
  if (Array.isArray(value) && value.length === 1) {
    const [{ name, type }] = value;
    switch (type) {
      case "GlobalKeyword": {
        return name;
      }
      default: {
        return parsers.parseColor(value);
      }
    }
  } else if (typeof value === "string") {
    return value;
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
      if (typeof val === "string") {
        const shorthandPriority = this._priorities.get(shorthand);
        const linePriority = this._priorities.get(lineShorthand);
        const positionPriority = this._priorities.get(positionShorthand);
        let priority = this._priorities.get(property) ?? "";
        if ((shorthandPriority || linePriority || positionPriority) && priority) {
          priority = "";
        }
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
