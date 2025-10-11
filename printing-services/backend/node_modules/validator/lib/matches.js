"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = matches;
var _assertString = _interopRequireDefault(require("./util/assertString"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
function matches(str, pattern, modifiers) {
  (0, _assertString.default)(str);
  if (Object.prototype.toString.call(pattern) !== '[object RegExp]') {
    pattern = new RegExp(pattern, modifiers);
  }
  return !!str.match(pattern);
}
module.exports = exports.default;
module.exports.default = exports.default;