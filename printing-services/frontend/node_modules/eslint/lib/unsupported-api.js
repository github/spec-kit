/**
 * @fileoverview APIs that are not officially supported by ESLint.
 *      These APIs may change or be removed at any time. Use at your
 *      own risk.
 * @author Nicholas C. Zakas
 */

"use strict";

//-----------------------------------------------------------------------------
// Requirements
//-----------------------------------------------------------------------------

const { FileEnumerator } = require("./cli-engine/file-enumerator");
const { FlatESLint, shouldUseFlatConfig } = require("./eslint/flat-eslint");
const FlatRuleTester = require("./rule-tester/flat-rule-tester");
const { ESLint } = require("./eslint/eslint");

//-----------------------------------------------------------------------------
// Exports
//-----------------------------------------------------------------------------

module.exports = {
    builtinRules: require("./rules"),
    FlatESLint,
    shouldUseFlatConfig,
    FlatRuleTester,
    FileEnumerator,
    LegacyESLint: ESLint
};
