"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const ts = __importStar(require("typescript"));
const util_1 = require("../util");
const getWrappedCode_1 = require("../util/getWrappedCode");
exports.default = (0, util_1.createRule)({
    name: 'consistent-type-assertions',
    meta: {
        type: 'suggestion',
        fixable: 'code',
        hasSuggestions: true,
        docs: {
            description: 'Enforce consistent usage of type assertions',
            recommended: 'stylistic',
        },
        messages: {
            as: "Use 'as {{cast}}' instead of '<{{cast}}>'.",
            'angle-bracket': "Use '<{{cast}}>' instead of 'as {{cast}}'.",
            never: 'Do not use any type assertions.',
            unexpectedObjectTypeAssertion: 'Always prefer const x: T = { ... }.',
            replaceObjectTypeAssertionWithAnnotation: 'Use const x: {{cast}} = { ... } instead.',
            replaceObjectTypeAssertionWithSatisfies: 'Use const x = { ... } satisfies {{cast}} instead.',
        },
        schema: [
            {
                oneOf: [
                    {
                        type: 'object',
                        properties: {
                            assertionStyle: {
                                type: 'string',
                                enum: ['never'],
                            },
                        },
                        additionalProperties: false,
                        required: ['assertionStyle'],
                    },
                    {
                        type: 'object',
                        properties: {
                            assertionStyle: {
                                type: 'string',
                                enum: ['as', 'angle-bracket'],
                            },
                            objectLiteralTypeAssertions: {
                                type: 'string',
                                enum: ['allow', 'allow-as-parameter', 'never'],
                            },
                        },
                        additionalProperties: false,
                        required: ['assertionStyle'],
                    },
                ],
            },
        ],
    },
    defaultOptions: [
        {
            assertionStyle: 'as',
            objectLiteralTypeAssertions: 'allow',
        },
    ],
    create(context, [options]) {
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        const parserServices = (0, util_1.getParserServices)(context, true);
        function isConst(node) {
            if (node.type !== utils_1.AST_NODE_TYPES.TSTypeReference) {
                return false;
            }
            return (node.typeName.type === utils_1.AST_NODE_TYPES.Identifier &&
                node.typeName.name === 'const');
        }
        function getTextWithParentheses(node) {
            // Capture parentheses before and after the node
            let beforeCount = 0;
            let afterCount = 0;
            if ((0, util_1.isParenthesized)(node, sourceCode)) {
                const bodyOpeningParen = sourceCode.getTokenBefore(node, util_1.isOpeningParenToken);
                const bodyClosingParen = sourceCode.getTokenAfter(node, util_1.isClosingParenToken);
                beforeCount = node.range[0] - bodyOpeningParen.range[0];
                afterCount = bodyClosingParen.range[1] - node.range[1];
            }
            return sourceCode.getText(node, beforeCount, afterCount);
        }
        function reportIncorrectAssertionType(node) {
            const messageId = options.assertionStyle;
            // If this node is `as const`, then don't report an error.
            if (isConst(node.typeAnnotation) && messageId === 'never') {
                return;
            }
            context.report({
                node,
                messageId,
                data: messageId !== 'never'
                    ? { cast: sourceCode.getText(node.typeAnnotation) }
                    : {},
                fix: messageId === 'as'
                    ? (fixer) => {
                        const tsNode = parserServices.esTreeNodeToTSNodeMap.get(node);
                        /**
                         * AsExpression has lower precedence than TypeAssertionExpression,
                         * so we don't need to wrap expression and typeAnnotation in parens.
                         */
                        const expressionCode = sourceCode.getText(node.expression);
                        const typeAnnotationCode = sourceCode.getText(node.typeAnnotation);
                        const asPrecedence = (0, util_1.getOperatorPrecedence)(ts.SyntaxKind.AsExpression, ts.SyntaxKind.Unknown);
                        const parentPrecedence = (0, util_1.getOperatorPrecedence)(tsNode.parent.kind, ts.isBinaryExpression(tsNode.parent)
                            ? tsNode.parent.operatorToken.kind
                            : ts.SyntaxKind.Unknown, ts.isNewExpression(tsNode.parent)
                            ? tsNode.parent.arguments != null &&
                                tsNode.parent.arguments.length > 0
                            : undefined);
                        const text = `${expressionCode} as ${typeAnnotationCode}`;
                        return fixer.replaceText(node, (0, util_1.isParenthesized)(node, sourceCode)
                            ? text
                            : (0, getWrappedCode_1.getWrappedCode)(text, asPrecedence, parentPrecedence));
                    }
                    : undefined,
            });
        }
        function checkType(node) {
            switch (node.type) {
                case utils_1.AST_NODE_TYPES.TSAnyKeyword:
                case utils_1.AST_NODE_TYPES.TSUnknownKeyword:
                    return false;
                case utils_1.AST_NODE_TYPES.TSTypeReference:
                    return (
                    // Ignore `as const` and `<const>`
                    !isConst(node) ||
                        // Allow qualified names which have dots between identifiers, `Foo.Bar`
                        node.typeName.type === utils_1.AST_NODE_TYPES.TSQualifiedName);
                default:
                    return true;
            }
        }
        function checkExpression(node) {
            if (options.assertionStyle === 'never' ||
                options.objectLiteralTypeAssertions === 'allow' ||
                node.expression.type !== utils_1.AST_NODE_TYPES.ObjectExpression) {
                return;
            }
            if (options.objectLiteralTypeAssertions === 'allow-as-parameter' &&
                (node.parent.type === utils_1.AST_NODE_TYPES.NewExpression ||
                    node.parent.type === utils_1.AST_NODE_TYPES.CallExpression ||
                    node.parent.type === utils_1.AST_NODE_TYPES.ThrowStatement ||
                    node.parent.type === utils_1.AST_NODE_TYPES.AssignmentPattern ||
                    node.parent.type === utils_1.AST_NODE_TYPES.JSXExpressionContainer)) {
                return;
            }
            if (checkType(node.typeAnnotation)) {
                const suggest = [];
                if (node.parent.type === utils_1.AST_NODE_TYPES.VariableDeclarator &&
                    !node.parent.id.typeAnnotation) {
                    const { parent } = node;
                    suggest.push({
                        messageId: 'replaceObjectTypeAssertionWithAnnotation',
                        data: { cast: sourceCode.getText(node.typeAnnotation) },
                        fix: fixer => [
                            fixer.insertTextAfter(parent.id, `: ${sourceCode.getText(node.typeAnnotation)}`),
                            fixer.replaceText(node, getTextWithParentheses(node.expression)),
                        ],
                    });
                }
                suggest.push({
                    messageId: 'replaceObjectTypeAssertionWithSatisfies',
                    data: { cast: sourceCode.getText(node.typeAnnotation) },
                    fix: fixer => [
                        fixer.replaceText(node, getTextWithParentheses(node.expression)),
                        fixer.insertTextAfter(node, ` satisfies ${(0, eslint_utils_1.getSourceCode)(context).getText(node.typeAnnotation)}`),
                    ],
                });
                context.report({
                    node,
                    messageId: 'unexpectedObjectTypeAssertion',
                    suggest,
                });
            }
        }
        return {
            TSTypeAssertion(node) {
                if (options.assertionStyle !== 'angle-bracket') {
                    reportIncorrectAssertionType(node);
                    return;
                }
                checkExpression(node);
            },
            TSAsExpression(node) {
                if (options.assertionStyle !== 'as') {
                    reportIncorrectAssertionType(node);
                    return;
                }
                checkExpression(node);
            },
        };
    },
});
//# sourceMappingURL=consistent-type-assertions.js.map