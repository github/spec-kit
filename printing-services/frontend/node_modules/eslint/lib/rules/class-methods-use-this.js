/**
 * @fileoverview Rule to enforce that all class methods use 'this'.
 * @author Patrick Williams
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
            description: "Enforce that class methods utilize `this`",
            recommended: false,
            url: "https://eslint.org/docs/latest/rules/class-methods-use-this"
        },

        schema: [{
            type: "object",
            properties: {
                exceptMethods: {
                    type: "array",
                    items: {
                        type: "string"
                    }
                },
                enforceForClassFields: {
                    type: "boolean",
                    default: true
                }
            },
            additionalProperties: false
        }],

        messages: {
            missingThis: "Expected 'this' to be used by class {{name}}."
        }
    },
    create(context) {
        const config = Object.assign({}, context.options[0]);
        const enforceForClassFields = config.enforceForClassFields !== false;
        const exceptMethods = new Set(config.exceptMethods || []);

        const stack = [];

        /**
         * Push `this` used flag initialized with `false` onto the stack.
         * @returns {void}
         */
        function pushContext() {
            stack.push(false);
        }

        /**
         * Pop `this` used flag from the stack.
         * @returns {boolean | undefined} `this` used flag
         */
        function popContext() {
            return stack.pop();
        }

        /**
         * Initializes the current context to false and pushes it onto the stack.
         * These booleans represent whether 'this' has been used in the context.
         * @returns {void}
         * @private
         */
        function enterFunction() {
            pushContext();
        }

        /**
         * Check if the node is an instance method
         * @param {ASTNode} node node to check
         * @returns {boolean} True if its an instance method
         * @private
         */
        function isInstanceMethod(node) {
            switch (node.type) {
                case "MethodDefinition":
                    return !node.static && node.kind !== "constructor";
                case "PropertyDefinition":
                    return !node.static && enforceForClassFields;
                default:
                    return false;
            }
        }

        /**
         * Check if the node is an instance method not excluded by config
         * @param {ASTNode} node node to check
         * @returns {boolean} True if it is an instance method, and not excluded by config
         * @private
         */
        function isIncludedInstanceMethod(node) {
            if (isInstanceMethod(node)) {
                if (node.computed) {
                    return true;
                }

                const hashIfNeeded = node.key.type === "PrivateIdentifier" ? "#" : "";
                const name = node.key.type === "Literal"
                    ? astUtils.getStaticStringValue(node.key)
                    : (node.key.name || "");

                return !exceptMethods.has(hashIfNeeded + name);
            }
            return false;
        }

        /**
         * Checks if we are leaving a function that is a method, and reports if 'this' has not been used.
         * Static methods and the constructor are exempt.
         * Then pops the context off the stack.
         * @param {ASTNode} node A function node that was entered.
         * @returns {void}
         * @private
         */
        function exitFunction(node) {
            const methodUsesThis = popContext();

            if (isIncludedInstanceMethod(node.parent) && !methodUsesThis) {
                context.report({
                    node,
                    loc: astUtils.getFunctionHeadLoc(node, context.sourceCode),
                    messageId: "missingThis",
                    data: {
                        name: astUtils.getFunctionNameWithKind(node)
                    }
                });
            }
        }

        /**
         * Mark the current context as having used 'this'.
         * @returns {void}
         * @private
         */
        function markThisUsed() {
            if (stack.length) {
                stack[stack.length - 1] = true;
            }
        }

        return {
            FunctionDeclaration: enterFunction,
            "FunctionDeclaration:exit": exitFunction,
            FunctionExpression: enterFunction,
            "FunctionExpression:exit": exitFunction,

            /*
             * Class field value are implicit functions.
             */
            "PropertyDefinition > *.key:exit": pushContext,
            "PropertyDefinition:exit": popContext,

            /*
             * Class static blocks are implicit functions. They aren't required to use `this`,
             * but we have to push context so that it captures any use of `this` in the static block
             * separately from enclosing contexts, because static blocks have their own `this` and it
             * shouldn't count as used `this` in enclosing contexts.
             */
            StaticBlock: pushContext,
            "StaticBlock:exit": popContext,

            ThisExpression: markThisUsed,
            Super: markThisUsed,
            ...(
                enforceForClassFields && {
                    "PropertyDefinition > ArrowFunctionExpression.value": enterFunction,
                    "PropertyDefinition > ArrowFunctionExpression.value:exit": exitFunction
                }
            )
        };
    }
};
