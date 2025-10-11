/**
 * @fileoverview Rule to enforce declarations in program or function body root.
 * @author Brandon Mills
 */

"use strict";

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

const astUtils = require("./utils/ast-utils");

//------------------------------------------------------------------------------
// Rule Definition
//------------------------------------------------------------------------------

const validParent = new Set(["Program", "StaticBlock", "ExportNamedDeclaration", "ExportDefaultDeclaration"]);
const validBlockStatementParent = new Set(["FunctionDeclaration", "FunctionExpression", "ArrowFunctionExpression"]);

/**
 * Finds the nearest enclosing context where this rule allows declarations and returns its description.
 * @param {ASTNode} node Node to search from.
 * @returns {string} Description. One of "program", "function body", "class static block body".
 */
function getAllowedBodyDescription(node) {
    let { parent } = node;

    while (parent) {

        if (parent.type === "StaticBlock") {
            return "class static block body";
        }

        if (astUtils.isFunction(parent)) {
            return "function body";
        }

        ({ parent } = parent);
    }

    return "program";
}

/** @type {import('../shared/types').Rule} */
module.exports = {
    meta: {
        type: "problem",

        docs: {
            description: "Disallow variable or `function` declarations in nested blocks",
            recommended: true,
            url: "https://eslint.org/docs/latest/rules/no-inner-declarations"
        },

        schema: [
            {
                enum: ["functions", "both"]
            }
        ],

        messages: {
            moveDeclToRoot: "Move {{type}} declaration to {{body}} root."
        }
    },

    create(context) {

        /**
         * Ensure that a given node is at a program or function body's root.
         * @param {ASTNode} node Declaration node to check.
         * @returns {void}
         */
        function check(node) {
            const parent = node.parent;

            if (
                parent.type === "BlockStatement" && validBlockStatementParent.has(parent.parent.type)
            ) {
                return;
            }

            if (validParent.has(parent.type)) {
                return;
            }

            context.report({
                node,
                messageId: "moveDeclToRoot",
                data: {
                    type: (node.type === "FunctionDeclaration" ? "function" : "variable"),
                    body: getAllowedBodyDescription(node)
                }
            });
        }


        return {

            FunctionDeclaration: check,
            VariableDeclaration(node) {
                if (context.options[0] === "both" && node.kind === "var") {
                    check(node);
                }
            }

        };

    }
};
