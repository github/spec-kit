/**
 * @fileoverview A rule to disallow negated left operands of the `in` operator
 * @author Michael Ficarra
 * @deprecated in ESLint v3.3.0
 */

"use strict";

//------------------------------------------------------------------------------
// Rule Definition
//------------------------------------------------------------------------------

/** @type {import('../shared/types').Rule} */
module.exports = {
    meta: {
        type: "problem",

        docs: {
            description: "Disallow negating the left operand in `in` expressions",
            recommended: false,
            url: "https://eslint.org/docs/latest/rules/no-negated-in-lhs"
        },

        replacedBy: ["no-unsafe-negation"],

        deprecated: true,
        schema: [],

        messages: {
            negatedLHS: "The 'in' expression's left operand is negated."
        }
    },

    create(context) {

        return {

            BinaryExpression(node) {
                if (node.operator === "in" && node.left.type === "UnaryExpression" && node.left.operator === "!") {
                    context.report({ node, messageId: "negatedLHS" });
                }
            }
        };

    }
};
