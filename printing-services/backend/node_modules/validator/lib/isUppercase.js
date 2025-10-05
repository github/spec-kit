"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = isUppercase;
var _assertString = _interopRequireDefault(require("./util/assertString"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
function isUppercase(str) {
  (0, _assertString.default)(str);
  return str === str.toUpperCase();
}
module.exports = exports.default;
module.exports.default = exports.default;