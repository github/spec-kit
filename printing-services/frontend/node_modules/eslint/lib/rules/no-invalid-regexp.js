/**
 * @fileoverview Validate strings passed to the RegExp constructor
 * @author Michael Ficarra
 */
"use strict";

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

const RegExpValidator = require("@eslint-community/regexpp").RegExpValidator;
const validator = new RegExpValidator();
const validFlags = /[dgimsuvy]/gu;
const undefined1 = void 0;

//------------------------------------------------------------------------------
// Rule Definition
//------------------------------------------------------------------------------

/** @type {import('../shared/types').Rule} */
module.exports = {
    meta: {
        type: "problem",

        docs: {
            description: "Disallow invalid regular expression strings in `RegExp` constructors",
            recommended: true,
            url: "https://eslint.org/docs/latest/rules/no-invalid-regexp"
        },

        schema: [{
            type: "object",
            properties: {
                allowConstructorFlags: {
                    type: "array",
                    items: {
                        type: "string"
                    }
                }
            },
            additionalProperties: false
        }],

        messages: {
            regexMessage: "{{message}}."
        }
    },

    create(context) {

        const options = context.options[0];
        let allowedFlags = null;

        if (options && options.allowConstructorFlags) {
            const temp = options.allowConstructorFlags.join("").replace(validFlags, "");

            if (temp) {
                allowedFlags = new RegExp(`[${temp}]`, "giu");
            }
        }

        /**
         * Reports error with the provided message.
         * @param {ASTNode} node The node holding the invalid RegExp
         * @param {string} message The message to report.
         * @returns {void}
         */
        function report(node, message) {
            context.report({
                node,
                messageId: "regexMessage",
                data: { message }
            });
        }

        /**
         * Check if node is a string
         * @param {ASTNode} node node to evaluate
         * @returns {boolean} True if its a string
         * @private
         */
        function isString(node) {
            return node && node.type === "Literal" && typeof node.value === "string";
        }

        /**
         * Gets flags of a regular expression created by the given `RegExp()` or `new RegExp()` call
         * Examples:
         *     new RegExp(".")         // => ""
         *     new RegExp(".", "gu")   // => "gu"
         *     new RegExp(".", flags)  // => null
         * @param {ASTNode} node `CallExpression` or `NewExpression` node
         * @returns {string|null} flags if they can be determined, `null` otherwise
         * @private
         */
        function getFlags(node) {
            if (node.arguments.length < 2) {
                return "";
            }

            if (isString(node.arguments[1])) {
                return node.arguments[1].value;
            }

            return null;
        }

        /**
         * Check syntax error in a given pattern.
         * @param {string} pattern The RegExp pattern to validate.
         * @param {Object} flags The RegExp flags to validate.
         * @param {boolean} [flags.unicode] The Unicode flag.
         * @param {boolean} [flags.unicodeSets] The UnicodeSets flag.
         * @returns {string|null} The syntax error.
         */
        function validateRegExpPattern(pattern, flags) {
            try {
                validator.validatePattern(pattern, undefined1, undefined1, flags);
                return null;
            } catch (err) {
                return err.message;
            }
        }

        /**
         * Check syntax error in a given flags.
         * @param {string|null} flags The RegExp flags to validate.
         * @returns {string|null} The syntax error.
         */
        function validateRegExpFlags(flags) {
            if (!flags) {
                return null;
            }
            try {
                validator.validateFlags(flags);
            } catch {
                return `Invalid flags supplied to RegExp constructor '${flags}'`;
            }

            /*
             * `regexpp` checks the combination of `u` and `v` flags when parsing `Pattern` according to `ecma262`,
             * but this rule may check only the flag when the pattern is unidentifiable, so check it here.
             * https://tc39.es/ecma262/multipage/text-processing.html#sec-parsepattern
             */
            if (flags.includes("u") && flags.includes("v")) {
                return "Regex 'u' and 'v' flags cannot be used together";
            }
            return null;
        }

        return {
            "CallExpression, NewExpression"(node) {
                if (node.callee.type !== "Identifier" || node.callee.name !== "RegExp") {
                    return;
                }

                let flags = getFlags(node);

                if (flags && allowedFlags) {
                    flags = flags.replace(allowedFlags, "");
                }

                let message = validateRegExpFlags(flags);

                if (message) {
                    report(node, message);
                    return;
                }

                if (!isString(node.arguments[0])) {
                    return;
                }

                const pattern = node.arguments[0].value;

                message = (

                    // If flags are unknown, report the regex only if its pattern is invalid both with and without the "u" flag
                    flags === null
                        ? (
                            validateRegExpPattern(pattern, { unicode: true, unicodeSets: false }) &&
                            validateRegExpPattern(pattern, { unicode: false, unicodeSets: true }) &&
                            validateRegExpPattern(pattern, { unicode: false, unicodeSets: false })
                        )
                        : validateRegExpPattern(pattern, { unicode: flags.includes("u"), unicodeSets: flags.includes("v") })
                );

                if (message) {
                    report(node, message);
                }
            }
        };
    }
};
