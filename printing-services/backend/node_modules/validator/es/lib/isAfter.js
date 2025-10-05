import toDate from './toDate';
export default function isAfter(date, options) {
  // For backwards compatibility:
  // isAfter(str [, date]), i.e. `options` could be used as argument for the legacy `date`
  var comparisonDate = (options === null || options === void 0 ? void 0 : options.comparisonDate) || options || Date().toString();
  var comparison = toDate(comparisonDate);
  var original = toDate(date);
  return !!(original && comparison && original > comparison);
}