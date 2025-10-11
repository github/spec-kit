"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = toDate;
var _assertString = _interopRequireDefault(require("./util/assertString"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
function toDate(date) {
  (0, _assertString.default)(date);
  date = Date.parse(date);
  return !isNaN(date) ? new Date(date) : null;
}
module.exports = exports.default;
module.exports.default = exports.default;