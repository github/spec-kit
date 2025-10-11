/**
 * @fileoverview Utilities to operate on strings.
 * @author Stephen Wade
 */

"use strict";

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

const Graphemer = require("graphemer").default;

//------------------------------------------------------------------------------
// Helpers
//------------------------------------------------------------------------------

// eslint-disable-next-line no-control-regex -- intentionally including control characters
const ASCII_REGEX = /^[\u0000-\u007f]*$/u;

/** @type {Graphemer | undefined} */
let splitter;

//------------------------------------------------------------------------------
// Public Interface
//------------------------------------------------------------------------------

/**
 * Converts the first letter of a string to uppercase.
 * @param {string} string The string to operate on
 * @returns {string} The converted string
 */
function upperCaseFirst(string) {
    if (string.length <= 1) {
        return string.toUpperCase();
    }
    return string[0].toUpperCase() + string.slice(1);
}

/**
 * Counts graphemes in a given string.
 * @param {string} value A string to count graphemes.
 * @returns {number} The number of graphemes in `value`.
 */
function getGraphemeCount(value) {
    if (ASCII_REGEX.test(value)) {
        return value.length;
    }

    if (!splitter) {
        splitter = new Graphemer();
    }

    return splitter.countGraphemes(value);
}

module.exports = {
    upperCaseFirst,
    getGraphemeCount
};
