/**
 * @fileoverview Rule for disallowing require() outside of the top-level module context
 * @author Jamund Ferguson
 * @deprecated in ESLint v7.0.0
 */

"use strict";

const ACCEPTABLE_PARENTS = new Set([
    "AssignmentExpression",
    "VariableDeclarator",
    "MemberExpression",
    "ExpressionStatement",
    "CallExpression",
    "ConditionalExpression",
    "Program",
    "VariableDeclaration",
    "ChainExpression"
]);

/**
 * Finds the eslint-scope reference in the given scope.
 * @param {Object} scope The scope to search.
 * @param {ASTNode} node The identifier node.
 * @returns {Reference|null} Returns the found reference or null if none were found.
 */
function findReference(scope, node) {
    const references = scope.references.filter(reference => reference.identifier.range[0] === node.range[0] &&
            reference.identifier.range[1] === node.range[1]);

    if (references.length === 1) {
        return references[0];
    }

    /* c8 ignore next */
    return null;

}

/**
 * Checks if the given identifier node is shadowed in the given scope.
 * @param {Object} scope The current scope.
 * @param {ASTNode} node The identifier node to check.
 * @returns {boolean} Whether or not the name is shadowed.
 */
function isShadowed(scope, node) {
    const reference = findReference(scope, node);

    return reference && reference.resolved && reference.resolved.defs.length > 0;
}

/** @type {import('../shared/types').Rule} */
module.exports = {
    meta: {
        deprecated: true,

        replacedBy: [],

        type: "suggestion",

        docs: {
            description: "Require `require()` calls to be placed at top-level module scope",
            recommended: false,
            url: "https://eslint.org/docs/latest/rules/global-require"
        },

        schema: [],
        messages: {
            unexpected: "Unexpected require()."
        }
    },

    create(context) {
        const sourceCode = context.sourceCode;

        return {
            CallExpression(node) {
                const currentScope = sourceCode.getScope(node);

                if (node.callee.name === "require" && !isShadowed(currentScope, node.callee)) {
                    const isGoodRequire = sourceCode.getAncestors(node).every(parent => ACCEPTABLE_PARENTS.has(parent.type));

                    if (!isGoodRequire) {
                        context.report({ node, messageId: "unexpected" });
                    }
                }
            }
        };
    }
};
