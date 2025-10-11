"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = isSlug;
var _assertString = _interopRequireDefault(require("./util/assertString"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
var charsetRegex = /^[^\s-_](?!.*?[-_]{2,})[a-z0-9-\\][^\s]*[^-_\s]$/;
function isSlug(str) {
  (0, _assertString.default)(str);
  return charsetRegex.test(str);
}
module.exports = exports.default;
module.exports.default = exports.default;