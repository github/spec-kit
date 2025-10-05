"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = contains;
var _assertString = _interopRequireDefault(require("./util/assertString"));
var _toString = _interopRequireDefault(require("./util/toString"));
var _merge = _interopRequireDefault(require("./util/merge"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
var defaulContainsOptions = {
  ignoreCase: false,
  minOccurrences: 1
};
function contains(str, elem, options) {
  (0, _assertString.default)(str);
  options = (0, _merge.default)(options, defaulContainsOptions);
  if (options.ignoreCase) {
    return str.toLowerCase().split((0, _toString.default)(elem).toLowerCase()).length > options.minOccurrences;
  }
  return str.split((0, _toString.default)(elem)).length > options.minOccurrences;
}
module.exports = exports.default;
module.exports.default = exports.default;