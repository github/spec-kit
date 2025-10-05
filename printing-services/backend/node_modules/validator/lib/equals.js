"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = equals;
var _assertString = _interopRequireDefault(require("./util/assertString"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
function equals(str, comparison) {
  (0, _assertString.default)(str);
  return str === comparison;
}
module.exports = exports.default;
module.exports.default = exports.default;