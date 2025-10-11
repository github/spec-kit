"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'prefer-promise-reject-errors',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Require using Error objects as Promise rejection reasons',
            recommended: 'strict',
            extendsBaseRule: true,
            requiresTypeChecking: true,
        },
        schema: [
            {
                type: 'object',
                properties: {
                    allowEmptyReject: {
                        type: 'boolean',
                    },
                },
                additionalProperties: false,
            },
        ],
        messages: {
            rejectAnError: 'Expected the Promise rejection reason to be an Error.',
        },
    },
    defaultOptions: [
        {
            allowEmptyReject: false,
        },
    ],
    create(context, [options]) {
        const services = (0, util_1.getParserServices)(context);
        function checkRejectCall(callExpression) {
            const argument = callExpression.arguments.at(0);
            if (argument) {
                const type = services.getTypeAtLocation(argument);
                if ((0, util_1.isErrorLike)(services.program, type) ||
                    (0, util_1.isReadonlyErrorLike)(services.program, type)) {
                    return;
                }
            }
            else if (options.allowEmptyReject) {
                return;
            }
            context.report({
                node: callExpression,
                messageId: 'rejectAnError',
            });
        }
        function skipChainExpression(node) {
            return node.type === utils_1.AST_NODE_TYPES.ChainExpression
                ? node.expression
                : node;
        }
        function typeAtLocationIsLikePromise(node) {
            const type = services.getTypeAtLocation(node);
            return ((0, util_1.isPromiseConstructorLike)(services.program, type) ||
                (0, util_1.isPromiseLike)(services.program, type));
        }
        return {
            CallExpression(node) {
                const callee = skipChainExpression(node.callee);
                if (callee.type !== utils_1.AST_NODE_TYPES.MemberExpression) {
                    return;
                }
                const rejectMethodCalled = callee.computed
                    ? callee.property.type === utils_1.AST_NODE_TYPES.Literal &&
                        callee.property.value === 'reject'
                    : callee.property.name === 'reject';
                if (!rejectMethodCalled ||
                    !typeAtLocationIsLikePromise(callee.object)) {
                    return;
                }
                checkRejectCall(node);
            },
            NewExpression(node) {
                const callee = skipChainExpression(node.callee);
                if (!(0, util_1.isPromiseConstructorLike)(services.program, services.getTypeAtLocation(callee))) {
                    return;
                }
                const executor = node.arguments.at(0);
                if (!executor || !(0, util_1.isFunction)(executor)) {
                    return;
                }
                const rejectParamNode = executor.params.at(1);
                if (!rejectParamNode || !(0, util_1.isIdentifier)(rejectParamNode)) {
                    return;
                }
                // reject param is always present in variables declared by executor
                const rejectVariable = (0, eslint_utils_1.getDeclaredVariables)(context, executor).find(variable => variable.identifiers.includes(rejectParamNode));
                rejectVariable.references.forEach(ref => {
                    if (ref.identifier.parent.type !== utils_1.AST_NODE_TYPES.CallExpression ||
                        ref.identifier !== ref.identifier.parent.callee) {
                        return;
                    }
                    checkRejectCall(ref.identifier.parent);
                });
            },
        };
    },
});
//# sourceMappingURL=prefer-promise-reject-errors.js.map