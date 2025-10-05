"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.parseEther = exports.formatEther = exports.parseUnits = exports.formatUnits = void 0;
/**
 *  Most interactions with Ethereum requires integer values, which use
 *  the smallest magnitude unit.
 *
 *  For example, imagine dealing with dollars and cents. Since dollars
 *  are divisible, non-integer values are possible, such as ``$10.77``.
 *  By using the smallest indivisible unit (i.e. cents), the value can
 *  be kept as the integer ``1077``.
 *
 *  When receiving decimal input from the user (as a decimal string),
 *  the value should be converted to an integer and when showing a user
 *  a value, the integer value should be converted to a decimal string.
 *
 *  This creates a clear distinction, between values to be used by code
 *  (integers) and values used for display logic to users (decimals).
 *
 *  The native unit in Ethereum, //ether// is divisible to 18 decimal places,
 *  where each individual unit is called a //wei//.
 *
 *  @_subsection api/utils:Unit Conversion  [about-units]
 */
const errors_js_1 = require("./errors.js");
const fixednumber_js_1 = require("./fixednumber.js");
const maths_js_1 = require("./maths.js");
const names = [
    "wei",
    "kwei",
    "mwei",
    "gwei",
    "szabo",
    "finney",
    "ether",
];
/**
 *  Converts %%value%% into a //decimal string//, assuming %%unit%% decimal
 *  places. The %%unit%% may be the number of decimal places or the name of
 *  a unit (e.g. ``"gwei"`` for 9 decimal places).
 *
 */
function formatUnits(value, unit) {
    let decimals = 18;
    if (typeof (unit) === "string") {
        const index = names.indexOf(unit);
        (0, errors_js_1.assertArgument)(index >= 0, "invalid unit", "unit", unit);
        decimals = 3 * index;
    }
    else if (unit != null) {
        decimals = (0, maths_js_1.getNumber)(unit, "unit");
    }
    return fixednumber_js_1.FixedNumber.fromValue(value, decimals, { decimals, width: 512 }).toString();
}
exports.formatUnits = formatUnits;
/**
 *  Converts the //decimal string// %%value%% to a BigInt, assuming
 *  %%unit%% decimal places. The %%unit%% may the number of decimal places
 *  or the name of a unit (e.g. ``"gwei"`` for 9 decimal places).
 */
function parseUnits(value, unit) {
    (0, errors_js_1.assertArgument)(typeof (value) === "string", "value must be a string", "value", value);
    let decimals = 18;
    if (typeof (unit) === "string") {
        const index = names.indexOf(unit);
        (0, errors_js_1.assertArgument)(index >= 0, "invalid unit", "unit", unit);
        decimals = 3 * index;
    }
    else if (unit != null) {
        decimals = (0, maths_js_1.getNumber)(unit, "unit");
    }
    return fixednumber_js_1.FixedNumber.fromString(value, { decimals, width: 512 }).value;
}
exports.parseUnits = parseUnits;
/**
 *  Converts %%value%% into a //decimal string// using 18 decimal places.
 */
function formatEther(wei) {
    return formatUnits(wei, 18);
}
exports.formatEther = formatEther;
/**
 *  Converts the //decimal string// %%ether%% to a BigInt, using 18
 *  decimal places.
 */
function parseEther(ether) {
    return parseUnits(ether, 18);
}
exports.parseEther = parseEther;
//# sourceMappingURL=units.js.map