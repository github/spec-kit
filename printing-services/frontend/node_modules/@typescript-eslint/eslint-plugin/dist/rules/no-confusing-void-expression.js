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
exports.default = (0, util_1.createRule)({
    name: 'no-confusing-void-expression',
    meta: {
        docs: {
            description: 'Require expressions of type void to appear in statement position',
            recommended: 'strict',
            requiresTypeChecking: true,
        },
        messages: {
            invalidVoidExpr: 'Placing a void expression inside another expression is forbidden. ' +
                'Move it to its own statement instead.',
            invalidVoidExprWrapVoid: 'Void expressions used inside another expression ' +
                'must be moved to its own statement ' +
                'or marked explicitly with the `void` operator.',
            invalidVoidExprArrow: 'Returning a void expression from an arrow function shorthand is forbidden. ' +
                'Please add braces to the arrow function.',
            invalidVoidExprArrowWrapVoid: 'Void expressions returned from an arrow function shorthand ' +
                'must be marked explicitly with the `void` operator.',
            invalidVoidExprReturn: 'Returning a void expression from a function is forbidden. ' +
                'Please move it before the `return` statement.',
            invalidVoidExprReturnLast: 'Returning a void expression from a function is forbidden. ' +
                'Please remove the `return` statement.',
            invalidVoidExprReturnWrapVoid: 'Void expressions returned from a function ' +
                'must be marked explicitly with the `void` operator.',
            voidExprWrapVoid: 'Mark with an explicit `void` operator.',
        },
        schema: [
            {
                type: 'object',
                properties: {
                    ignoreArrowShorthand: { type: 'boolean' },
                    ignoreVoidOperator: { type: 'boolean' },
                },
                additionalProperties: false,
            },
        ],
        type: 'problem',
        fixable: 'code',
        hasSuggestions: true,
    },
    defaultOptions: [{}],
    create(context, [options]) {
        return {
            'AwaitExpression, CallExpression, TaggedTemplateExpression'(node) {
                const services = (0, util_1.getParserServices)(context);
                const type = (0, util_1.getConstrainedTypeAtLocation)(services, node);
                if (!tsutils.isTypeFlagSet(type, ts.TypeFlags.VoidLike)) {
                    // not a void expression
                    return;
                }
                const invalidAncestor = findInvalidAncestor(node);
                if (invalidAncestor == null) {
                    // void expression is in valid position
                    return;
                }
                const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
                const wrapVoidFix = (fixer) => {
                    const nodeText = sourceCode.getText(node);
                    const newNodeText = `void ${nodeText}`;
                    return fixer.replaceText(node, newNodeText);
                };
                if (invalidAncestor.type === utils_1.AST_NODE_TYPES.ArrowFunctionExpression) {
                    // handle arrow function shorthand
                    if (options.ignoreVoidOperator) {
                        // handle wrapping with `void`
                        return context.report({
                            node,
                            messageId: 'invalidVoidExprArrowWrapVoid',
                            fix: wrapVoidFix,
                        });
                    }
                    // handle wrapping with braces
                    const arrowFunction = invalidAncestor;
                    return context.report({
                        node,
                        messageId: 'invalidVoidExprArrow',
                        fix(fixer) {
                            if (!canFix(arrowFunction)) {
                                return null;
                            }
                            const arrowBody = arrowFunction.body;
                            const arrowBodyText = sourceCode.getText(arrowBody);
                            const newArrowBodyText = `{ ${arrowBodyText}; }`;
                            if ((0, util_1.isParenthesized)(arrowBody, sourceCode)) {
                                const bodyOpeningParen = sourceCode.getTokenBefore(arrowBody, util_1.isOpeningParenToken);
                                const bodyClosingParen = sourceCode.getTokenAfter(arrowBody, util_1.isClosingParenToken);
                                return fixer.replaceTextRange([bodyOpeningParen.range[0], bodyClosingParen.range[1]], newArrowBodyText);
                            }
                            return fixer.replaceText(arrowBody, newArrowBodyText);
                        },
                    });
                }
                if (invalidAncestor.type === utils_1.AST_NODE_TYPES.ReturnStatement) {
                    // handle return statement
                    if (options.ignoreVoidOperator) {
                        // handle wrapping with `void`
                        return context.report({
                            node,
                            messageId: 'invalidVoidExprReturnWrapVoid',
                            fix: wrapVoidFix,
                        });
                    }
                    const returnStmt = invalidAncestor;
                    if (isFinalReturn(returnStmt)) {
                        // remove the `return` keyword
                        return context.report({
                            node,
                            messageId: 'invalidVoidExprReturnLast',
                            fix(fixer) {
                                if (!canFix(returnStmt)) {
                                    return null;
                                }
                                const returnValue = returnStmt.argument;
                                const returnValueText = sourceCode.getText(returnValue);
                                let newReturnStmtText = `${returnValueText};`;
                                if (isPreventingASI(returnValue, sourceCode)) {
                                    // put a semicolon at the beginning of the line
                                    newReturnStmtText = `;${newReturnStmtText}`;
                                }
                                return fixer.replaceText(returnStmt, newReturnStmtText);
                            },
                        });
                    }
                    // move before the `return` keyword
                    return context.report({
                        node,
                        messageId: 'invalidVoidExprReturn',
                        fix(fixer) {
                            const returnValue = returnStmt.argument;
                            const returnValueText = sourceCode.getText(returnValue);
                            let newReturnStmtText = `${returnValueText}; return;`;
                            if (isPreventingASI(returnValue, sourceCode)) {
                                // put a semicolon at the beginning of the line
                                newReturnStmtText = `;${newReturnStmtText}`;
                            }
                            if (returnStmt.parent.type !== utils_1.AST_NODE_TYPES.BlockStatement) {
                                // e.g. `if (cond) return console.error();`
                                // add braces if not inside a block
                                newReturnStmtText = `{ ${newReturnStmtText} }`;
                            }
                            return fixer.replaceText(returnStmt, newReturnStmtText);
                        },
                    });
                }
                // handle generic case
                if (options.ignoreVoidOperator) {
                    // this would be reported by this rule btw. such irony
                    return context.report({
                        node,
                        messageId: 'invalidVoidExprWrapVoid',
                        suggest: [{ messageId: 'voidExprWrapVoid', fix: wrapVoidFix }],
                    });
                }
                context.report({
                    node,
                    messageId: 'invalidVoidExpr',
                });
            },
        };
        /**
         * Inspects the void expression's ancestors and finds closest invalid one.
         * By default anything other than an ExpressionStatement is invalid.
         * Parent expressions which can be used for their short-circuiting behavior
         * are ignored and their parents are checked instead.
         * @param node The void expression node to check.
         * @returns Invalid ancestor node if it was found. `null` otherwise.
         */
        function findInvalidAncestor(node) {
            const parent = (0, util_1.nullThrows)(node.parent, util_1.NullThrowsReasons.MissingParent);
            if (parent.type === utils_1.AST_NODE_TYPES.SequenceExpression) {
                if (node !== parent.expressions[parent.expressions.length - 1]) {
                    return null;
                }
            }
            if (parent.type === utils_1.AST_NODE_TYPES.ExpressionStatement) {
                // e.g. `{ console.log("foo"); }`
                // this is always valid
                return null;
            }
            if (parent.type === utils_1.AST_NODE_TYPES.LogicalExpression) {
                if (parent.right === node) {
                    // e.g. `x && console.log(x)`
                    // this is valid only if the next ancestor is valid
                    return findInvalidAncestor(parent);
                }
            }
            if (parent.type === utils_1.AST_NODE_TYPES.ConditionalExpression) {
                if (parent.consequent === node || parent.alternate === node) {
                    // e.g. `cond ? console.log(true) : console.log(false)`
                    // this is valid only if the next ancestor is valid
                    return findInvalidAncestor(parent);
                }
            }
            if (parent.type === utils_1.AST_NODE_TYPES.ArrowFunctionExpression) {
                // e.g. `() => console.log("foo")`
                // this is valid with an appropriate option
                if (options.ignoreArrowShorthand) {
                    return null;
                }
            }
            if (parent.type === utils_1.AST_NODE_TYPES.UnaryExpression) {
                if (parent.operator === 'void') {
                    // e.g. `void console.log("foo")`
                    // this is valid with an appropriate option
                    if (options.ignoreVoidOperator) {
                        return null;
                    }
                }
            }
            if (parent.type === utils_1.AST_NODE_TYPES.ChainExpression) {
                // e.g. `console?.log('foo')`
                return findInvalidAncestor(parent);
            }
            // any other parent is invalid
            return parent;
        }
        /** Checks whether the return statement is the last statement in a function body. */
        function isFinalReturn(node) {
            // the parent must be a block
            const block = (0, util_1.nullThrows)(node.parent, util_1.NullThrowsReasons.MissingParent);
            if (block.type !== utils_1.AST_NODE_TYPES.BlockStatement) {
                // e.g. `if (cond) return;` (not in a block)
                return false;
            }
            // the block's parent must be a function
            const blockParent = (0, util_1.nullThrows)(block.parent, util_1.NullThrowsReasons.MissingParent);
            if (![
                utils_1.AST_NODE_TYPES.FunctionDeclaration,
                utils_1.AST_NODE_TYPES.FunctionExpression,
                utils_1.AST_NODE_TYPES.ArrowFunctionExpression,
            ].includes(blockParent.type)) {
                // e.g. `if (cond) { return; }`
                // not in a top-level function block
                return false;
            }
            // must be the last child of the block
            if (block.body.indexOf(node) < block.body.length - 1) {
                // not the last statement in the block
                return false;
            }
            return true;
        }
        /**
         * Checks whether the given node, if placed on its own line,
         * would prevent automatic semicolon insertion on the line before.
         *
         * This happens if the line begins with `(`, `[` or `` ` ``
         */
        function isPreventingASI(node, sourceCode) {
            const startToken = (0, util_1.nullThrows)(sourceCode.getFirstToken(node), util_1.NullThrowsReasons.MissingToken('first token', node.type));
            return ['(', '[', '`'].includes(startToken.value);
        }
        function canFix(node) {
            const services = (0, util_1.getParserServices)(context);
            const targetNode = node.type === utils_1.AST_NODE_TYPES.ReturnStatement
                ? node.argument
                : node.body;
            const type = (0, util_1.getConstrainedTypeAtLocation)(services, targetNode);
            return tsutils.isTypeFlagSet(type, ts.TypeFlags.VoidLike);
        }
    },
});
//# sourceMappingURL=no-confusing-void-expression.js.map