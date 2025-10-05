"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = isPort;
var _isInt = _interopRequireDefault(require("./isInt"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
function isPort(str) {
  return (0, _isInt.default)(str, {
    allow_leading_zeroes: false,
    min: 0,
    max: 65535
  });
}
module.exports = exports.default;
module.exports.default = exports.default;