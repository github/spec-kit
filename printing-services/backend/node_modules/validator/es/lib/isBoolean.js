import assertString from './util/assertString';
var defaultOptions = {
  loose: false
};
var strictBooleans = ['true', 'false', '1', '0'];
var looseBooleans = [].concat(strictBooleans, ['yes', 'no']);
export default function isBoolean(str) {
  var options = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : defaultOptions;
  assertString(str);
  if (options.loose) {
    return looseBooleans.includes(str.toLowerCase());
  }
  return strictBooleans.includes(str);
}