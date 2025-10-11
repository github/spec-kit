import assertString from './util/assertString';
import toDate from './toDate';
export default function isBefore(str) {
  var date = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : String(new Date());
  assertString(str);
  var comparison = toDate(date);
  var original = toDate(str);
  return !!(original && comparison && original < comparison);
}