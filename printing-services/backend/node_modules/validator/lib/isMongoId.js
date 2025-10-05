"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = isMongoId;
var _assertString = _interopRequireDefault(require("./util/assertString"));
var _isHexadecimal = _interopRequireDefault(require("./isHexadecimal"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
function isMongoId(str) {
  (0, _assertString.default)(str);
  return (0, _isHexadecimal.default)(str) && str.length === 24;
}
module.exports = exports.default;
module.exports.default = exports.default;