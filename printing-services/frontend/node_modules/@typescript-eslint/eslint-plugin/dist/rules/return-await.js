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
const tsutils = __importStar(require("ts-api-utils"));
const ts = __importStar(require("typescript"));
const util_1 = require("../util");
const getOperatorPrecedence_1 = require("../util/getOperatorPrecedence");
exports.default = (0, util_1.createRule)({
    name: 'return-await',
    meta: {
        docs: {
            description: 'Enforce consistent returning of awaited values',
            requiresTypeChecking: true,
            extendsBaseRule: 'no-return-await',
        },
        fixable: 'code',
        hasSuggestions: true,
        type: 'problem',
        messages: {
            nonPromiseAwait: 'Returning an awaited value that is not a promise is not allowed.',
            disallowedPromiseAwait: 'Returning an awaited promise is not allowed in this context.',
            requiredPromiseAwait: 'Returning an awaited promise is required in this context.',
        },
        schema: [
            {
                type: 'string',
                enum: ['in-try-catch', 'always', 'never'],
            },
        ],
    },
    defaultOptions: ['in-try-catch'],
    create(context, [option]) {
        const services = (0, util_1.getParserServices)(context);
        const checker = services.program.getTypeChecker();
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        const scopeInfoStack = [];
        function enterFunction(node) {
            scopeInfoStack.push({
                hasAsync: node.async,
                owningFunc: node,
            });
        }
        function exitFunction() {
            scopeInfoStack.pop();
        }
        function inTry(node) {
            let ancestor = node.parent;
            while (ancestor && !ts.isFunctionLike(ancestor)) {
                if (ts.isTryStatement(ancestor)) {
                    return true;
                }
                ancestor = ancestor.parent;
            }
            return false;
        }
        function inCatch(node) {
            let ancestor = node.parent;
            while (ancestor && !ts.isFunctionLike(ancestor)) {
                if (ts.isCatchClause(ancestor)) {
                    return true;
                }
                ancestor = ancestor.parent;
            }
            return false;
        }
        function isReturnPromiseInFinally(node) {
            let ancestor = node.parent;
            while (ancestor && !ts.isFunctionLike(ancestor)) {
                if (ts.isTryStatement(ancestor.parent) &&
                    ts.isBlock(ancestor) &&
                    ancestor.parent.end === ancestor.end) {
                    return true;
                }
                ancestor = ancestor.parent;
            }
            return false;
        }
        function hasFinallyBlock(node) {
            let ancestor = node.parent;
            while (ancestor && !ts.isFunctionLike(ancestor)) {
                if (ts.isTryStatement(ancestor)) {
                    return !!ancestor.finallyBlock;
                }
                ancestor = ancestor.parent;
            }
            return false;
        }
        // function findTokensToRemove()
        function removeAwait(fixer, node) {
            // Should always be an await node; but let's be safe.
            /* istanbul ignore if */ if (!(0, util_1.isAwaitExpression)(node)) {
                return null;
            }
            const awaitToken = sourceCode.getFirstToken(node, util_1.isAwaitKeyword);
            // Should always be the case; but let's be safe.
            /* istanbul ignore if */ if (!awaitToken) {
                return null;
            }
            const startAt = awaitToken.range[0];
            let endAt = awaitToken.range[1];
            // Also remove any extraneous whitespace after `await`, if there is any.
            const nextToken = sourceCode.getTokenAfter(awaitToken, {
                includeComments: true,
            });
            if (nextToken) {
                endAt = nextToken.range[0];
            }
            return fixer.removeRange([startAt, endAt]);
        }
        function insertAwait(fixer, node, isHighPrecendence) {
            if (isHighPrecendence) {
                return fixer.insertTextBefore(node, 'await ');
            }
            return [
                fixer.insertTextBefore(node, 'await ('),
                fixer.insertTextAfter(node, ')'),
            ];
        }
        function isHigherPrecedenceThanAwait(node) {
            const operator = ts.isBinaryExpression(node)
                ? node.operatorToken.kind
                : ts.SyntaxKind.Unknown;
            const nodePrecedence = (0, getOperatorPrecedence_1.getOperatorPrecedence)(node.kind, operator);
            const awaitPrecedence = (0, getOperatorPrecedence_1.getOperatorPrecedence)(ts.SyntaxKind.AwaitExpression, ts.SyntaxKind.Unknown);
            return nodePrecedence > awaitPrecedence;
        }
        function test(node, expression) {
            let child;
            const isAwait = ts.isAwaitExpression(expression);
            if (isAwait) {
                child = expression.getChildAt(1);
            }
            else {
                child = expression;
            }
            const type = checker.getTypeAtLocation(child);
            const isThenable = tsutils.isThenableType(checker, expression, type);
            if (!isAwait && !isThenable) {
                return;
            }
            if (isAwait && !isThenable) {
                // any/unknown could be thenable; do not auto-fix
                const useAutoFix = !((0, util_1.isTypeAnyType)(type) || (0, util_1.isTypeUnknownType)(type));
                const fix = (fixer) => removeAwait(fixer, node);
                context.report({
                    messageId: 'nonPromiseAwait',
                    node,
                    ...(useAutoFix
                        ? { fix }
                        : {
                            suggest: [
                                {
                                    messageId: 'nonPromiseAwait',
                                    fix,
                                },
                            ],
                        }),
                });
                return;
            }
            if (option === 'always') {
                if (!isAwait && isThenable) {
                    context.report({
                        messageId: 'requiredPromiseAwait',
                        node,
                        fix: fixer => insertAwait(fixer, node, isHigherPrecedenceThanAwait(expression)),
                    });
                }
                return;
            }
            if (option === 'never') {
                if (isAwait) {
                    context.report({
                        messageId: 'disallowedPromiseAwait',
                        node,
                        fix: fixer => removeAwait(fixer, node),
                    });
                }
                return;
            }
            if (option === 'in-try-catch') {
                const isInTryCatch = inTry(expression) || inCatch(expression);
                if (isAwait && !isInTryCatch) {
                    context.report({
                        messageId: 'disallowedPromiseAwait',
                        node,
                        fix: fixer => removeAwait(fixer, node),
                    });
                }
                else if (!isAwait && isInTryCatch) {
                    if (inCatch(expression) && !hasFinallyBlock(expression)) {
                        return;
                    }
                    if (isReturnPromiseInFinally(expression)) {
                        return;
                    }
                    context.report({
                        messageId: 'requiredPromiseAwait',
                        node,
                        fix: fixer => insertAwait(fixer, node, isHigherPrecedenceThanAwait(expression)),
                    });
                }
                return;
            }
        }
        function findPossiblyReturnedNodes(node) {
            if (node.type === utils_1.AST_NODE_TYPES.ConditionalExpression) {
                return [
                    ...findPossiblyReturnedNodes(node.alternate),
                    ...findPossiblyReturnedNodes(node.consequent),
                ];
            }
            return [node];
        }
        return {
            FunctionDeclaration: enterFunction,
            FunctionExpression: enterFunction,
            ArrowFunctionExpression: enterFunction,
            'FunctionDeclaration:exit': exitFunction,
            'FunctionExpression:exit': exitFunction,
            'ArrowFunctionExpression:exit': exitFunction,
            // executes after less specific handler, so exitFunction is called
            'ArrowFunctionExpression[async = true]:exit'(node) {
                if (node.body.type !== utils_1.AST_NODE_TYPES.BlockStatement) {
                    findPossiblyReturnedNodes(node.body).forEach(node => {
                        const tsNode = services.esTreeNodeToTSNodeMap.get(node);
                        test(node, tsNode);
                    });
                }
            },
            ReturnStatement(node) {
                const scopeInfo = scopeInfoStack.at(-1);
                if (!scopeInfo?.hasAsync || !node.argument) {
                    return;
                }
                findPossiblyReturnedNodes(node.argument).forEach(node => {
                    const tsNode = services.esTreeNodeToTSNodeMap.get(node);
                    test(node, tsNode);
                });
            },
        };
    },
});
//# sourceMappingURL=return-await.js.map