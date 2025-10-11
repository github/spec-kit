/**
 * @fileoverview enforce default parameters to be last
 * @author Chiawen Chen
 */

"use strict";

/** @type {import('../shared/types').Rule} */
module.exports = {
    meta: {
        type: "suggestion",

        docs: {
            description: "Enforce default parameters to be last",
            recommended: false,
            url: "https://eslint.org/docs/latest/rules/default-param-last"
        },

        schema: [],

        messages: {
            shouldBeLast: "Default parameters should be last."
        }
    },

    create(context) {

        /**
         * Handler for function contexts.
         * @param {ASTNode} node function node
         * @returns {void}
         */
        function handleFunction(node) {
            let hasSeenPlainParam = false;

            for (let i = node.params.length - 1; i >= 0; i -= 1) {
                const param = node.params[i];

                if (
                    param.type !== "AssignmentPattern" &&
                    param.type !== "RestElement"
                ) {
                    hasSeenPlainParam = true;
                    continue;
                }

                if (hasSeenPlainParam && param.type === "AssignmentPattern") {
                    context.report({
                        node: param,
                        messageId: "shouldBeLast"
                    });
                }
            }
        }

        return {
            FunctionDeclaration: handleFunction,
            FunctionExpression: handleFunction,
            ArrowFunctionExpression: handleFunction
        };
    }
};
