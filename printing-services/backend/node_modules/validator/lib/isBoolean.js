"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = isBoolean;
var _assertString = _interopRequireDefault(require("./util/assertString"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
var defaultOptions = {
  loose: false
};
var strictBooleans = ['true', 'false', '1', '0'];
var looseBooleans = [].concat(strictBooleans, ['yes', 'no']);
function isBoolean(str) {
  var options = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : defaultOptions;
  (0, _assertString.default)(str);
  if (options.loose) {
    return looseBooleans.includes(str.toLowerCase());
  }
  return strictBooleans.includes(str);
}
module.exports = exports.default;
module.exports.default = exports.default;