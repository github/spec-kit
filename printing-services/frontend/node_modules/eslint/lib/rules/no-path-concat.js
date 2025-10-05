/**
 * @fileoverview Disallow string concatenation when using __dirname and __filename
 * @author Nicholas C. Zakas
 * @deprecated in ESLint v7.0.0
 */
"use strict";

//------------------------------------------------------------------------------
// Rule Definition
//------------------------------------------------------------------------------

/** @type {import('../shared/types').Rule} */
module.exports = {
    meta: {
        deprecated: true,

        replacedBy: [],

        type: "suggestion",

        docs: {
            description: "Disallow string concatenation with `__dirname` and `__filename`",
            recommended: false,
            url: "https://eslint.org/docs/latest/rules/no-path-concat"
        },

        schema: [],

        messages: {
            usePathFunctions: "Use path.join() or path.resolve() instead of + to create paths."
        }
    },

    create(context) {

        const MATCHER = /^__(?:dir|file)name$/u;

        //--------------------------------------------------------------------------
        // Public
        //--------------------------------------------------------------------------

        return {

            BinaryExpression(node) {

                const left = node.left,
                    right = node.right;

                if (node.operator === "+" &&
                        ((left.type === "Identifier" && MATCHER.test(left.name)) ||
                        (right.type === "Identifier" && MATCHER.test(right.name)))
                ) {

                    context.report({
                        node,
                        messageId: "usePathFunctions"
                    });
                }
            }

        };

    }
};
