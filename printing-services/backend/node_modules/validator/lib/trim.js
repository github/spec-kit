"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = trim;
var _rtrim = _interopRequireDefault(require("./rtrim"));
var _ltrim = _interopRequireDefault(require("./ltrim"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
function trim(str, chars) {
  return (0, _rtrim.default)((0, _ltrim.default)(str, chars), chars);
}
module.exports = exports.default;
module.exports.default = exports.default;