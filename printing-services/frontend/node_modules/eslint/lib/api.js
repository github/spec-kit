/**
 * @fileoverview Expose out ESLint and CLI to require.
 * @author Ian Christian Myers
 */

"use strict";

//-----------------------------------------------------------------------------
// Requirements
//-----------------------------------------------------------------------------

const { ESLint, FlatESLint } = require("./eslint");
const { shouldUseFlatConfig } = require("./eslint/flat-eslint");
const { Linter } = require("./linter");
const { RuleTester } = require("./rule-tester");
const { SourceCode } = require("./source-code");

//-----------------------------------------------------------------------------
// Functions
//-----------------------------------------------------------------------------

/**
 * Loads the correct ESLint constructor given the options.
 * @param {Object} [options] The options object
 * @param {boolean} [options.useFlatConfig] Whether or not to use a flat config
 * @param {string} [options.cwd] The current working directory
 * @returns {Promise<ESLint|LegacyESLint>} The ESLint constructor
 */
async function loadESLint({ useFlatConfig, cwd = process.cwd() } = {}) {

    /*
     * Note: The v9.x version of this function doesn't have a cwd option
     * because it's not used. It's only used in the v8.x version of this
     * function.
     */

    const shouldESLintUseFlatConfig = typeof useFlatConfig === "boolean"
        ? useFlatConfig
        : await shouldUseFlatConfig({ cwd });

    return shouldESLintUseFlatConfig ? FlatESLint : ESLint;
}

//-----------------------------------------------------------------------------
// Exports
//-----------------------------------------------------------------------------

module.exports = {
    Linter,
    loadESLint,
    ESLint,
    RuleTester,
    SourceCode
};
