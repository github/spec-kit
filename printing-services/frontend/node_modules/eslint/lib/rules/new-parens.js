/**
 * @fileoverview Rule to flag when using constructor without parentheses
 * @author Ilya Volodin
 * @deprecated in ESLint v8.53.0
 */

"use strict";

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

const astUtils = require("./utils/ast-utils");

//------------------------------------------------------------------------------
// Helpers
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
// Rule Definition
//------------------------------------------------------------------------------

/** @type {import('../shared/types').Rule} */
module.exports = {
    meta: {
        deprecated: true,
        replacedBy: [],
        type: "layout",

        docs: {
            description: "Enforce or disallow parentheses when invoking a constructor with no arguments",
            recommended: false,
            url: "https://eslint.org/docs/latest/rules/new-parens"
        },

        fixable: "code",
        schema: [
            {
                enum: ["always", "never"]
            }
        ],
        messages: {
            missing: "Missing '()' invoking a constructor.",
            unnecessary: "Unnecessary '()' invoking a constructor with no arguments."
        }
    },

    create(context) {
        const options = context.options;
        const always = options[0] !== "never"; // Default is always

        const sourceCode = context.sourceCode;

        return {
            NewExpression(node) {
                if (node.arguments.length !== 0) {
                    return; // if there are arguments, there have to be parens
                }

                const lastToken = sourceCode.getLastToken(node);
                const hasLastParen = lastToken && astUtils.isClosingParenToken(lastToken);

                // `hasParens` is true only if the new expression ends with its own parens, e.g., new new foo() does not end with its own parens
                const hasParens = hasLastParen &&
                    astUtils.isOpeningParenToken(sourceCode.getTokenBefore(lastToken)) &&
                    node.callee.range[1] < node.range[1];

                if (always) {
                    if (!hasParens) {
                        context.report({
                            node,
                            messageId: "missing",
                            fix: fixer => fixer.insertTextAfter(node, "()")
                        });
                    }
                } else {
                    if (hasParens) {
                        context.report({
                            node,
                            messageId: "unnecessary",
                            fix: fixer => [
                                fixer.remove(sourceCode.getTokenBefore(lastToken)),
                                fixer.remove(lastToken),
                                fixer.insertTextBefore(node, "("),
                                fixer.insertTextAfter(node, ")")
                            ]
                        });
                    }
                }
            }
        };
    }
};
