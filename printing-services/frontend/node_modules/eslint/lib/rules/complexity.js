/**
 * @fileoverview Counts the cyclomatic complexity of each function of the script. See http://en.wikipedia.org/wiki/Cyclomatic_complexity.
 * Counts the number of if, conditional, for, while, try, switch/case,
 * @author Patrick Brosset
 */

"use strict";

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

const astUtils = require("./utils/ast-utils");
const { upperCaseFirst } = require("../shared/string-utils");

//------------------------------------------------------------------------------
// Rule Definition
//------------------------------------------------------------------------------

/** @type {import('../shared/types').Rule} */
module.exports = {
    meta: {
        type: "suggestion",

        docs: {
            description: "Enforce a maximum cyclomatic complexity allowed in a program",
            recommended: false,
            url: "https://eslint.org/docs/latest/rules/complexity"
        },

        schema: [
            {
                oneOf: [
                    {
                        type: "integer",
                        minimum: 0
                    },
                    {
                        type: "object",
                        properties: {
                            maximum: {
                                type: "integer",
                                minimum: 0
                            },
                            max: {
                                type: "integer",
                                minimum: 0
                            }
                        },
                        additionalProperties: false
                    }
                ]
            }
        ],

        messages: {
            complex: "{{name}} has a complexity of {{complexity}}. Maximum allowed is {{max}}."
        }
    },

    create(context) {
        const option = context.options[0];
        let THRESHOLD = 20;

        if (
            typeof option === "object" &&
            (Object.prototype.hasOwnProperty.call(option, "maximum") || Object.prototype.hasOwnProperty.call(option, "max"))
        ) {
            THRESHOLD = option.maximum || option.max;
        } else if (typeof option === "number") {
            THRESHOLD = option;
        }

        //--------------------------------------------------------------------------
        // Helpers
        //--------------------------------------------------------------------------

        // Using a stack to store complexity per code path
        const complexities = [];

        /**
         * Increase the complexity of the code path in context
         * @returns {void}
         * @private
         */
        function increaseComplexity() {
            complexities[complexities.length - 1]++;
        }

        //--------------------------------------------------------------------------
        // Public API
        //--------------------------------------------------------------------------

        return {

            onCodePathStart() {

                // The initial complexity is 1, representing one execution path in the CodePath
                complexities.push(1);
            },

            // Each branching in the code adds 1 to the complexity
            CatchClause: increaseComplexity,
            ConditionalExpression: increaseComplexity,
            LogicalExpression: increaseComplexity,
            ForStatement: increaseComplexity,
            ForInStatement: increaseComplexity,
            ForOfStatement: increaseComplexity,
            IfStatement: increaseComplexity,
            WhileStatement: increaseComplexity,
            DoWhileStatement: increaseComplexity,

            // Avoid `default`
            "SwitchCase[test]": increaseComplexity,

            // Logical assignment operators have short-circuiting behavior
            AssignmentExpression(node) {
                if (astUtils.isLogicalAssignmentOperator(node.operator)) {
                    increaseComplexity();
                }
            },

            onCodePathEnd(codePath, node) {
                const complexity = complexities.pop();

                /*
                 * This rule only evaluates complexity of functions, so "program" is excluded.
                 * Class field initializers and class static blocks are implicit functions. Therefore,
                 * they shouldn't contribute to the enclosing function's complexity, but their
                 * own complexity should be evaluated.
                 */
                if (
                    codePath.origin !== "function" &&
                    codePath.origin !== "class-field-initializer" &&
                    codePath.origin !== "class-static-block"
                ) {
                    return;
                }

                if (complexity > THRESHOLD) {
                    let name;

                    if (codePath.origin === "class-field-initializer") {
                        name = "class field initializer";
                    } else if (codePath.origin === "class-static-block") {
                        name = "class static block";
                    } else {
                        name = astUtils.getFunctionNameWithKind(node);
                    }

                    context.report({
                        node,
                        messageId: "complex",
                        data: {
                            name: upperCaseFirst(name),
                            complexity,
                            max: THRESHOLD
                        }
                    });
                }
            }
        };

    }
};
