import assertString from './util/assertString';
var hexcolor = /^#?([0-9A-F]{3}|[0-9A-F]{4}|[0-9A-F]{6}|[0-9A-F]{8})$/i;
export default function isHexColor(str) {
  assertString(str);
  return hexcolor.test(str);
}