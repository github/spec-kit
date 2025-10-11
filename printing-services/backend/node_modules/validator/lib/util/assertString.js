"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = assertString;
function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
function assertString(input) {
  var isString = typeof input === 'string' || input instanceof String;
  if (!isString) {
    var invalidType = _typeof(input);
    if (input === null) invalidType = 'null';else if (invalidType === 'object') invalidType = input.constructor.name;
    throw new TypeError("Expected a string but received a ".concat(invalidType));
  }
}
module.exports = exports.default;
module.exports.default = exports.default;