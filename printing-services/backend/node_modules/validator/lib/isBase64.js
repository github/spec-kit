"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = isBase64;
var _assertString = _interopRequireDefault(require("./util/assertString"));
var _merge = _interopRequireDefault(require("./util/merge"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
var notBase64 = /[^A-Z0-9+\/=]/i;
var urlSafeBase64 = /^[A-Z0-9_\-]*$/i;
var defaultBase64Options = {
  urlSafe: false
};
function isBase64(str, options) {
  (0, _assertString.default)(str);
  options = (0, _merge.default)(options, defaultBase64Options);
  var len = str.length;
  if (options.urlSafe) {
    return urlSafeBase64.test(str);
  }
  if (len % 4 !== 0 || notBase64.test(str)) {
    return false;
  }
  var firstPaddingChar = str.indexOf('=');
  return firstPaddingChar === -1 || firstPaddingChar === len - 1 || firstPaddingChar === len - 2 && str[len - 1] === '=';
}
module.exports = exports.default;
module.exports.default = exports.default;