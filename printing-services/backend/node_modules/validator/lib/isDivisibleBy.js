"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = isDivisibleBy;
var _assertString = _interopRequireDefault(require("./util/assertString"));
var _toFloat = _interopRequireDefault(require("./toFloat"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
function isDivisibleBy(str, num) {
  (0, _assertString.default)(str);
  return (0, _toFloat.default)(str) % parseInt(num, 10) === 0;
}
module.exports = exports.default;
module.exports.default = exports.default;