/**
 * @fileoverview Rule to flag variable leak in CatchClauses in IE 8 and earlier
 * @author Ian Christian Myers
 * @deprecated in ESLint v5.1.0
 */

"use strict";

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

const astUtils = require("./utils/ast-utils");

//------------------------------------------------------------------------------
// Rule Definition
//------------------------------------------------------------------------------

/** @type {import('../shared/types').Rule} */
module.exports = {
    meta: {
        type: "suggestion",

        docs: {
            description: "Disallow `catch` clause parameters from shadowing variables in the outer scope",
            recommended: false,
            url: "https://eslint.org/docs/latest/rules/no-catch-shadow"
        },

        replacedBy: ["no-shadow"],

        deprecated: true,
        schema: [],

        messages: {
            mutable: "Value of '{{name}}' may be overwritten in IE 8 and earlier."
        }
    },

    create(context) {

        const sourceCode = context.sourceCode;

        //--------------------------------------------------------------------------
        // Helpers
        //--------------------------------------------------------------------------

        /**
         * Check if the parameters are been shadowed
         * @param {Object} scope current scope
         * @param {string} name parameter name
         * @returns {boolean} True is its been shadowed
         */
        function paramIsShadowing(scope, name) {
            return astUtils.getVariableByName(scope, name) !== null;
        }

        //--------------------------------------------------------------------------
        // Public API
        //--------------------------------------------------------------------------

        return {

            "CatchClause[param!=null]"(node) {
                let scope = sourceCode.getScope(node);

                /*
                 * When ecmaVersion >= 6, CatchClause creates its own scope
                 * so start from one upper scope to exclude the current node
                 */
                if (scope.block === node) {
                    scope = scope.upper;
                }

                if (paramIsShadowing(scope, node.param.name)) {
                    context.report({ node, messageId: "mutable", data: { name: node.param.name } });
                }
            }
        };

    }
};
