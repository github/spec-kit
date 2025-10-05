"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'no-confusing-non-null-assertion',
    meta: {
        type: 'problem',
        docs: {
            description: 'Disallow non-null assertion in locations that may be confusing',
            recommended: 'stylistic',
        },
        hasSuggestions: true,
        messages: {
            confusingEqual: 'Confusing combinations of non-null assertion and equal test like "a! == b", which looks very similar to not equal "a !== b".',
            confusingAssign: 'Confusing combinations of non-null assertion and equal test like "a! = b", which looks very similar to not equal "a != b".',
            notNeedInEqualTest: 'Unnecessary non-null assertion (!) in equal test.',
            notNeedInAssign: 'Unnecessary non-null assertion (!) in assignment left hand.',
            wrapUpLeft: 'Wrap up left hand to avoid putting non-null assertion "!" and "=" together.',
        },
        schema: [],
    },
    defaultOptions: [],
    create(context) {
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        return {
            'BinaryExpression, AssignmentExpression'(node) {
                function isLeftHandPrimaryExpression(node) {
                    return node.type === utils_1.AST_NODE_TYPES.TSNonNullExpression;
                }
                if (node.operator === '==' ||
                    node.operator === '===' ||
                    node.operator === '=') {
                    const isAssign = node.operator === '=';
                    const leftHandFinalToken = sourceCode.getLastToken(node.left);
                    const tokenAfterLeft = sourceCode.getTokenAfter(node.left);
                    if (leftHandFinalToken?.type === utils_1.AST_TOKEN_TYPES.Punctuator &&
                        leftHandFinalToken.value === '!' &&
                        tokenAfterLeft?.value !== ')') {
                        if (isLeftHandPrimaryExpression(node.left)) {
                            context.report({
                                node,
                                messageId: isAssign ? 'confusingAssign' : 'confusingEqual',
                                suggest: [
                                    {
                                        messageId: isAssign
                                            ? 'notNeedInAssign'
                                            : 'notNeedInEqualTest',
                                        fix: (fixer) => [
                                            fixer.remove(leftHandFinalToken),
                                        ],
                                    },
                                ],
                            });
                        }
                        else {
                            context.report({
                                node,
                                messageId: isAssign ? 'confusingAssign' : 'confusingEqual',
                                suggest: [
                                    {
                                        messageId: 'wrapUpLeft',
                                        fix: (fixer) => [
                                            fixer.insertTextBefore(node.left, '('),
                                            fixer.insertTextAfter(node.left, ')'),
                                        ],
                                    },
                                ],
                            });
                        }
                    }
                }
            },
        };
    },
});
//# sourceMappingURL=no-confusing-non-null-assertion.js.map