import assertString from './util/assertString';
import { decimal } from './alpha';
export default function isFloat(str, options) {
  assertString(str);
  options = options || {};
  var _float = new RegExp("^(?:[-+])?(?:[0-9]+)?(?:\\".concat(options.locale ? decimal[options.locale] : '.', "[0-9]*)?(?:[eE][\\+\\-]?(?:[0-9]+))?$"));
  if (str === '' || str === '.' || str === ',' || str === '-' || str === '+') {
    return false;
  }
  var value = parseFloat(str.replace(',', '.'));
  return _float.test(str) && (!options.hasOwnProperty('min') || value >= options.min) && (!options.hasOwnProperty('max') || value <= options.max) && (!options.hasOwnProperty('lt') || value < options.lt) && (!options.hasOwnProperty('gt') || value > options.gt);
}
export var locales = Object.keys(decimal);