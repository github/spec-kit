"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = whitelist;
var _assertString = _interopRequireDefault(require("./util/assertString"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
function whitelist(str, chars) {
  (0, _assertString.default)(str);
  return str.replace(new RegExp("[^".concat(chars, "]+"), 'g'), '');
}
module.exports = exports.default;
module.exports.default = exports.default;