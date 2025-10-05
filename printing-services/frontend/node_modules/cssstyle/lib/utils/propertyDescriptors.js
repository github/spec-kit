"use strict";

const parsers = require("../parsers");

exports.getPropertyDescriptor = function getPropertyDescriptor(property) {
  return {
    set(v) {
      v = parsers.parsePropertyValue(property, v, {
        globalObject: this._global
      });
      this._setProperty(property, v);
    },
    get() {
      return this.getPropertyValue(property);
    },
    enumerable: true,
    configurable: true
  };
};
