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
const tsutils = __importStar(require("ts-api-utils"));
const ts = __importStar(require("typescript"));
const util_1 = require("../util");
const messageBase = 'Promises must be awaited, end with a call to .catch, or end with a call to .then with a rejection handler.';
const messageBaseVoid = 'Promises must be awaited, end with a call to .catch, end with a call to .then with a rejection handler' +
    ' or be explicitly marked as ignored with the `void` operator.';
const messageRejectionHandler = 'A rejection handler that is not a function will be ignored.';
const messagePromiseArray = "An array of Promises may be unintentional. Consider handling the promises' fulfillment or rejection with Promise.all or similar.";
const messagePromiseArrayVoid = "An array of Promises may be unintentional. Consider handling the promises' fulfillment or rejection with Promise.all or similar," +
    ' or explicitly marking the expression as ignored with the `void` operator.';
exports.default = (0, util_1.createRule)({
    name: 'no-floating-promises',
    meta: {
        docs: {
            description: 'Require Promise-like statements to be handled appropriately',
            recommended: 'recommended',
            requiresTypeChecking: true,
        },
        hasSuggestions: true,
        messages: {
            floating: messageBase,
            floatingFixAwait: 'Add await operator.',
            floatingVoid: messageBaseVoid,
            floatingFixVoid: 'Add void operator to ignore.',
            floatingUselessRejectionHandler: messageBase + ' ' + messageRejectionHandler,
            floatingUselessRejectionHandlerVoid: messageBaseVoid + ' ' + messageRejectionHandler,
            floatingPromiseArray: messagePromiseArray,
            floatingPromiseArrayVoid: messagePromiseArrayVoid,
        },
        schema: [
            {
                type: 'object',
                properties: {
                    ignoreVoid: {
                        description: 'Whether to ignore `void` expressions.',
                        type: 'boolean',
                    },
                    ignoreIIFE: {
                        description: 'Whether to ignore async IIFEs (Immediately Invoked Function Expressions).',
                        type: 'boolean',
                    },
                },
                additionalProperties: false,
            },
        ],
        type: 'problem',
    },
    defaultOptions: [
        {
            ignoreVoid: true,
            ignoreIIFE: false,
        },
    ],
    create(context, [options]) {
        const services = (0, util_1.getParserServices)(context);
        const checker = services.program.getTypeChecker();
        return {
            ExpressionStatement(node) {
                if (options.ignoreIIFE && isAsyncIife(node)) {
                    return;
                }
                let expression = node.expression;
                if (expression.type === utils_1.AST_NODE_TYPES.ChainExpression) {
                    expression = expression.expression;
                }
                const { isUnhandled, nonFunctionHandler, promiseArray } = isUnhandledPromise(checker, expression);
                if (isUnhandled) {
                    if (promiseArray) {
                        context.report({
                            node,
                            messageId: options.ignoreVoid
                                ? 'floatingPromiseArrayVoid'
                                : 'floatingPromiseArray',
                        });
                    }
                    else if (options.ignoreVoid) {
                        context.report({
                            node,
                            messageId: nonFunctionHandler
                                ? 'floatingUselessRejectionHandlerVoid'
                                : 'floatingVoid',
                            suggest: [
                                {
                                    messageId: 'floatingFixVoid',
                                    fix(fixer) {
                                        const tsNode = services.esTreeNodeToTSNodeMap.get(node.expression);
                                        if (isHigherPrecedenceThanUnary(tsNode)) {
                                            return fixer.insertTextBefore(node, 'void ');
                                        }
                                        return [
                                            fixer.insertTextBefore(node, 'void ('),
                                            fixer.insertTextAfterRange([expression.range[1], expression.range[1]], ')'),
                                        ];
                                    },
                                },
                            ],
                        });
                    }
                    else {
                        context.report({
                            node,
                            messageId: nonFunctionHandler
                                ? 'floatingUselessRejectionHandler'
                                : 'floating',
                            suggest: [
                                {
                                    messageId: 'floatingFixAwait',
                                    fix(fixer) {
                                        if (expression.type === utils_1.AST_NODE_TYPES.UnaryExpression &&
                                            expression.operator === 'void') {
                                            return fixer.replaceTextRange([expression.range[0], expression.range[0] + 4], 'await');
                                        }
                                        const tsNode = services.esTreeNodeToTSNodeMap.get(node.expression);
                                        if (isHigherPrecedenceThanUnary(tsNode)) {
                                            return fixer.insertTextBefore(node, 'await ');
                                        }
                                        return [
                                            fixer.insertTextBefore(node, 'await ('),
                                            fixer.insertTextAfterRange([expression.range[1], expression.range[1]], ')'),
                                        ];
                                    },
                                },
                            ],
                        });
                    }
                }
            },
        };
        function isHigherPrecedenceThanUnary(node) {
            const operator = ts.isBinaryExpression(node)
                ? node.operatorToken.kind
                : ts.SyntaxKind.Unknown;
            const nodePrecedence = (0, util_1.getOperatorPrecedence)(node.kind, operator);
            return nodePrecedence > util_1.OperatorPrecedence.Unary;
        }
        function isAsyncIife(node) {
            if (node.expression.type !== utils_1.AST_NODE_TYPES.CallExpression) {
                return false;
            }
            return (node.expression.callee.type ===
                utils_1.AST_NODE_TYPES.ArrowFunctionExpression ||
                node.expression.callee.type === utils_1.AST_NODE_TYPES.FunctionExpression);
        }
        function isValidRejectionHandler(rejectionHandler) {
            return (services.program
                .getTypeChecker()
                .getTypeAtLocation(services.esTreeNodeToTSNodeMap.get(rejectionHandler))
                .getCallSignatures().length > 0);
        }
        function isUnhandledPromise(checker, node) {
            // First, check expressions whose resulting types may not be promise-like
            if (node.type === utils_1.AST_NODE_TYPES.SequenceExpression) {
                // Any child in a comma expression could return a potentially unhandled
                // promise, so we check them all regardless of whether the final returned
                // value is promise-like.
                return (node.expressions
                    .map(item => isUnhandledPromise(checker, item))
                    .find(result => result.isUnhandled) ?? { isUnhandled: false });
            }
            if (!options.ignoreVoid &&
                node.type === utils_1.AST_NODE_TYPES.UnaryExpression &&
                node.operator === 'void') {
                // Similarly, a `void` expression always returns undefined, so we need to
                // see what's inside it without checking the type of the overall expression.
                return isUnhandledPromise(checker, node.argument);
            }
            const tsNode = services.esTreeNodeToTSNodeMap.get(node);
            // Check the type. At this point it can't be unhandled if it isn't a promise
            // or array thereof.
            if (isPromiseArray(checker, tsNode)) {
                return { isUnhandled: true, promiseArray: true };
            }
            if (!isPromiseLike(checker, tsNode)) {
                return { isUnhandled: false };
            }
            if (node.type === utils_1.AST_NODE_TYPES.CallExpression) {
                // If the outer expression is a call, a `.catch()` or `.then()` with
                // rejection handler handles the promise.
                const catchRejectionHandler = getRejectionHandlerFromCatchCall(node);
                if (catchRejectionHandler) {
                    if (isValidRejectionHandler(catchRejectionHandler)) {
                        return { isUnhandled: false };
                    }
                    return { isUnhandled: true, nonFunctionHandler: true };
                }
                const thenRejectionHandler = getRejectionHandlerFromThenCall(node);
                if (thenRejectionHandler) {
                    if (isValidRejectionHandler(thenRejectionHandler)) {
                        return { isUnhandled: false };
                    }
                    return { isUnhandled: true, nonFunctionHandler: true };
                }
                // `x.finally()` is transparent to resolution of the promise, so check `x`.
                // ("object" in this context is the `x` in `x.finally()`)
                const promiseFinallyObject = getObjectFromFinallyCall(node);
                if (promiseFinallyObject) {
                    return isUnhandledPromise(checker, promiseFinallyObject);
                }
                // All other cases are unhandled.
                return { isUnhandled: true };
            }
            else if (node.type === utils_1.AST_NODE_TYPES.ConditionalExpression) {
                // We must be getting the promise-like value from one of the branches of the
                // ternary. Check them directly.
                const alternateResult = isUnhandledPromise(checker, node.alternate);
                if (alternateResult.isUnhandled) {
                    return alternateResult;
                }
                return isUnhandledPromise(checker, node.consequent);
            }
            else if (node.type === utils_1.AST_NODE_TYPES.MemberExpression ||
                node.type === utils_1.AST_NODE_TYPES.Identifier ||
                node.type === utils_1.AST_NODE_TYPES.NewExpression) {
                // If it is just a property access chain or a `new` call (e.g. `foo.bar` or
                // `new Promise()`), the promise is not handled because it doesn't have the
                // necessary then/catch call at the end of the chain.
                return { isUnhandled: true };
            }
            else if (node.type === utils_1.AST_NODE_TYPES.LogicalExpression) {
                const leftResult = isUnhandledPromise(checker, node.left);
                if (leftResult.isUnhandled) {
                    return leftResult;
                }
                return isUnhandledPromise(checker, node.right);
            }
            // We conservatively return false for all other types of expressions because
            // we don't want to accidentally fail if the promise is handled internally but
            // we just can't tell.
            return { isUnhandled: false };
        }
    },
});
function isPromiseArray(checker, node) {
    const type = checker.getTypeAtLocation(node);
    for (const ty of tsutils
        .unionTypeParts(type)
        .map(t => checker.getApparentType(t))) {
        if (checker.isArrayType(ty)) {
            const arrayType = checker.getTypeArguments(ty)[0];
            if (isPromiseLike(checker, node, arrayType)) {
                return true;
            }
        }
        if (checker.isTupleType(ty)) {
            for (const tupleElementType of checker.getTypeArguments(ty)) {
                if (isPromiseLike(checker, node, tupleElementType)) {
                    return true;
                }
            }
        }
    }
    return false;
}
// Modified from tsutils.isThenable() to only consider thenables which can be
// rejected/caught via a second parameter. Original source (MIT licensed):
//
//   https://github.com/ajafff/tsutils/blob/49d0d31050b44b81e918eae4fbaf1dfe7b7286af/util/type.ts#L95-L125
function isPromiseLike(checker, node, type) {
    type ??= checker.getTypeAtLocation(node);
    for (const ty of tsutils.unionTypeParts(checker.getApparentType(type))) {
        const then = ty.getProperty('then');
        if (then === undefined) {
            continue;
        }
        const thenType = checker.getTypeOfSymbolAtLocation(then, node);
        if (hasMatchingSignature(thenType, signature => signature.parameters.length >= 2 &&
            isFunctionParam(checker, signature.parameters[0], node) &&
            isFunctionParam(checker, signature.parameters[1], node))) {
            return true;
        }
    }
    return false;
}
function hasMatchingSignature(type, matcher) {
    for (const t of tsutils.unionTypeParts(type)) {
        if (t.getCallSignatures().some(matcher)) {
            return true;
        }
    }
    return false;
}
function isFunctionParam(checker, param, node) {
    const type = checker.getApparentType(checker.getTypeOfSymbolAtLocation(param, node));
    for (const t of tsutils.unionTypeParts(type)) {
        if (t.getCallSignatures().length !== 0) {
            return true;
        }
    }
    return false;
}
function getRejectionHandlerFromCatchCall(expression) {
    if (expression.callee.type === utils_1.AST_NODE_TYPES.MemberExpression &&
        expression.callee.property.type === utils_1.AST_NODE_TYPES.Identifier &&
        expression.callee.property.name === 'catch' &&
        expression.arguments.length >= 1) {
        return expression.arguments[0];
    }
    return undefined;
}
function getRejectionHandlerFromThenCall(expression) {
    if (expression.callee.type === utils_1.AST_NODE_TYPES.MemberExpression &&
        expression.callee.property.type === utils_1.AST_NODE_TYPES.Identifier &&
        expression.callee.property.name === 'then' &&
        expression.arguments.length >= 2) {
        return expression.arguments[1];
    }
    return undefined;
}
function getObjectFromFinallyCall(expression) {
    return expression.callee.type === utils_1.AST_NODE_TYPES.MemberExpression &&
        expression.callee.property.type === utils_1.AST_NODE_TYPES.Identifier &&
        expression.callee.property.name === 'finally'
        ? expression.callee.object
        : undefined;
}
//# sourceMappingURL=no-floating-promises.js.map