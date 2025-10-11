"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const util_1 = require("../util");
const getESLintCoreRule_1 = require("../util/getESLintCoreRule");
const baseRule = (0, getESLintCoreRule_1.getESLintCoreRule)('no-unused-expressions');
exports.default = (0, util_1.createRule)({
    name: 'no-unused-expressions',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Disallow unused expressions',
            extendsBaseRule: true,
        },
        hasSuggestions: baseRule.meta.hasSuggestions,
        schema: baseRule.meta.schema,
        messages: baseRule.meta.messages,
    },
    defaultOptions: [
        {
            allowShortCircuit: false,
            allowTernary: false,
            allowTaggedTemplates: false,
        },
    ],
    create(context, [{ allowShortCircuit = false, allowTernary = false }]) {
        const rules = baseRule.create(context);
        function isValidExpression(node) {
            if (allowShortCircuit && node.type === utils_1.AST_NODE_TYPES.LogicalExpression) {
                return isValidExpression(node.right);
            }
            if (allowTernary && node.type === utils_1.AST_NODE_TYPES.ConditionalExpression) {
                return (isValidExpression(node.alternate) &&
                    isValidExpression(node.consequent));
            }
            return ((node.type === utils_1.AST_NODE_TYPES.ChainExpression &&
                node.expression.type === utils_1.AST_NODE_TYPES.CallExpression) ||
                node.type === utils_1.AST_NODE_TYPES.ImportExpression);
        }
        return {
            ExpressionStatement(node) {
                if (node.directive || isValidExpression(node.expression)) {
                    return;
                }
                if (node.expression.type ===
                    utils_1.TSESTree.AST_NODE_TYPES.TSInstantiationExpression) {
                    rules.ExpressionStatement({
                        ...node,
                        expression: node.expression.expression,
                    });
                    return;
                }
                rules.ExpressionStatement(node);
            },
        };
    },
});
//# sourceMappingURL=no-unused-expressions.js.map