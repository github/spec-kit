"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = toFloat;
var _isFloat = _interopRequireDefault(require("./isFloat"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
function toFloat(str) {
  if (!(0, _isFloat.default)(str)) return NaN;
  return parseFloat(str);
}
module.exports = exports.default;
module.exports.default = exports.default;