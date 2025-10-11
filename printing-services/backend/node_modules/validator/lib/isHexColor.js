"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = isHexColor;
var _assertString = _interopRequireDefault(require("./util/assertString"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
var hexcolor = /^#?([0-9A-F]{3}|[0-9A-F]{4}|[0-9A-F]{6}|[0-9A-F]{8})$/i;
function isHexColor(str) {
  (0, _assertString.default)(str);
  return hexcolor.test(str);
}
module.exports = exports.default;
module.exports.default = exports.default;