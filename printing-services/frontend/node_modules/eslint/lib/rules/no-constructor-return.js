/**
 * @fileoverview Rule to disallow returning value from constructor.
 * @author Pig Fang <https://github.com/g-plane>
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
            description: "Disallow returning value from constructor",
            recommended: false,
            url: "https://eslint.org/docs/latest/rules/no-constructor-return"
        },

        schema: {},

        fixable: null,

        messages: {
            unexpected: "Unexpected return statement in constructor."
        }
    },

    create(context) {
        const stack = [];

        return {
            onCodePathStart(_, node) {
                stack.push(node);
            },
            onCodePathEnd() {
                stack.pop();
            },
            ReturnStatement(node) {
                const last = stack[stack.length - 1];

                if (!last.parent) {
                    return;
                }

                if (
                    last.parent.type === "MethodDefinition" &&
                    last.parent.kind === "constructor" &&
                    (node.parent.parent === last || node.argument)
                ) {
                    context.report({
                        node,
                        messageId: "unexpected"
                    });
                }
            }
        };
    }
};
