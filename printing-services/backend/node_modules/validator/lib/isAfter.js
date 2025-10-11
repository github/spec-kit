"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = isAfter;
var _toDate = _interopRequireDefault(require("./toDate"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
function isAfter(date, options) {
  // For backwards compatibility:
  // isAfter(str [, date]), i.e. `options` could be used as argument for the legacy `date`
  var comparisonDate = (options === null || options === void 0 ? void 0 : options.comparisonDate) || options || Date().toString();
  var comparison = (0, _toDate.default)(comparisonDate);
  var original = (0, _toDate.default)(date);
  return !!(original && comparison && original > comparison);
}
module.exports = exports.default;
module.exports.default = exports.default;