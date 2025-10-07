/**
 * @fileoverview disallow use of the Buffer() constructor
 * @author Teddy Katz
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

        type: "problem",

        docs: {
            description: "Disallow use of the `Buffer()` constructor",
            recommended: false,
            url: "https://eslint.org/docs/latest/rules/no-buffer-constructor"
        },

        schema: [],

        messages: {
            deprecated: "{{expr}} is deprecated. Use Buffer.from(), Buffer.alloc(), or Buffer.allocUnsafe() instead."
        }
    },

    create(context) {

        //----------------------------------------------------------------------
        // Public
        //----------------------------------------------------------------------

        return {
            "CallExpression[callee.name='Buffer'], NewExpression[callee.name='Buffer']"(node) {
                context.report({
                    node,
                    messageId: "deprecated",
                    data: { expr: node.type === "CallExpression" ? "Buffer()" : "new Buffer()" }
                });
            }
        };
    }
};
