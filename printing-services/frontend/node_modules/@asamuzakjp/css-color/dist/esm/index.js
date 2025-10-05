import { cssCalc } from "./js/css-calc.js";
import { resolveGradient, isGradient } from "./js/css-gradient.js";
import { cssVar } from "./js/css-var.js";
import { splitValue, isColor, extractDashedIdent } from "./js/util.js";
import { convert } from "./js/convert.js";
import { resolve } from "./js/resolve.js";
/*!
 * CSS color - Resolve, parse, convert CSS color.
 * @license MIT
 * @copyright asamuzaK (Kazz)
 * @see {@link https://github.com/asamuzaK/cssColor/blob/main/LICENSE}
 */
const utils = {
  cssCalc,
  cssVar,
  extractDashedIdent,
  isColor,
  isGradient,
  resolveGradient,
  splitValue
};
export {
  convert,
  resolve,
  utils
};
//# sourceMappingURL=index.js.map
