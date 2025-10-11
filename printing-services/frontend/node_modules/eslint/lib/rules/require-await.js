/**
 * @fileoverview Rule to disallow async functions which have no `await` expression.
 * @author Toru Nagashima
 */

"use strict";

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

const astUtils = require("./utils/ast-utils");

//------------------------------------------------------------------------------
// Helpers
//------------------------------------------------------------------------------

/**
 * Capitalize the 1st letter of the given text.
 * @param {string} text The text to capitalize.
 * @returns {string} The text that the 1st letter was capitalized.
 */
function capitalizeFirstLetter(text) {
    return text[0].toUpperCase() + text.slice(1);
}

//------------------------------------------------------------------------------
// Rule Definition
//------------------------------------------------------------------------------

/** @type {import('../shared/types').Rule} */
module.exports = {
    meta: {
        type: "suggestion",

        docs: {
            description: "Disallow async functions which have no `await` expression",
            recommended: false,
            url: "https://eslint.org/docs/latest/rules/require-await"
        },

        schema: [],

        messages: {
            missingAwait: "{{name}} has no 'await' expression."
        }
    },

    create(context) {
        const sourceCode = context.sourceCode;
        let scopeInfo = null;

        /**
         * Push the scope info object to the stack.
         * @returns {void}
         */
        function enterFunction() {
            scopeInfo = {
                upper: scopeInfo,
                hasAwait: false
            };
        }

        /**
         * Pop the top scope info object from the stack.
         * Also, it reports the function if needed.
         * @param {ASTNode} node The node to report.
         * @returns {void}
         */
        function exitFunction(node) {
            if (!node.generator && node.async && !scopeInfo.hasAwait && !astUtils.isEmptyFunction(node)) {
                context.report({
                    node,
                    loc: astUtils.getFunctionHeadLoc(node, sourceCode),
                    messageId: "missingAwait",
                    data: {
                        name: capitalizeFirstLetter(
                            astUtils.getFunctionNameWithKind(node)
                        )
                    }
                });
            }

            scopeInfo = scopeInfo.upper;
        }

        return {
            FunctionDeclaration: enterFunction,
            FunctionExpression: enterFunction,
            ArrowFunctionExpression: enterFunction,
            "FunctionDeclaration:exit": exitFunction,
            "FunctionExpression:exit": exitFunction,
            "ArrowFunctionExpression:exit": exitFunction,

            AwaitExpression() {
                if (!scopeInfo) {
                    return;
                }

                scopeInfo.hasAwait = true;
            },
            ForOfStatement(node) {
                if (!scopeInfo) {
                    return;
                }

                if (node.await) {
                    scopeInfo.hasAwait = true;
                }
            }
        };
    }
};
