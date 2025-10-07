"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'no-inferrable-types',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Disallow explicit type declarations for variables or parameters initialized to a number, string, or boolean',
            recommended: 'stylistic',
        },
        fixable: 'code',
        messages: {
            noInferrableType: 'Type {{type}} trivially inferred from a {{type}} literal, remove type annotation.',
        },
        schema: [
            {
                type: 'object',
                properties: {
                    ignoreParameters: {
                        type: 'boolean',
                    },
                    ignoreProperties: {
                        type: 'boolean',
                    },
                },
                additionalProperties: false,
            },
        ],
    },
    defaultOptions: [
        {
            ignoreParameters: false,
            ignoreProperties: false,
        },
    ],
    create(context, [{ ignoreParameters, ignoreProperties }]) {
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        function isFunctionCall(init, callName) {
            if (init.type === utils_1.AST_NODE_TYPES.ChainExpression) {
                return isFunctionCall(init.expression, callName);
            }
            return (init.type === utils_1.AST_NODE_TYPES.CallExpression &&
                init.callee.type === utils_1.AST_NODE_TYPES.Identifier &&
                init.callee.name === callName);
        }
        function isLiteral(init, typeName) {
            return (init.type === utils_1.AST_NODE_TYPES.Literal && typeof init.value === typeName);
        }
        function isIdentifier(init, ...names) {
            return (init.type === utils_1.AST_NODE_TYPES.Identifier && names.includes(init.name));
        }
        function hasUnaryPrefix(init, ...operators) {
            return (init.type === utils_1.AST_NODE_TYPES.UnaryExpression &&
                operators.includes(init.operator));
        }
        const keywordMap = {
            [utils_1.AST_NODE_TYPES.TSBigIntKeyword]: 'bigint',
            [utils_1.AST_NODE_TYPES.TSBooleanKeyword]: 'boolean',
            [utils_1.AST_NODE_TYPES.TSNumberKeyword]: 'number',
            [utils_1.AST_NODE_TYPES.TSNullKeyword]: 'null',
            [utils_1.AST_NODE_TYPES.TSStringKeyword]: 'string',
            [utils_1.AST_NODE_TYPES.TSSymbolKeyword]: 'symbol',
            [utils_1.AST_NODE_TYPES.TSUndefinedKeyword]: 'undefined',
        };
        /**
         * Returns whether a node has an inferrable value or not
         */
        function isInferrable(annotation, init) {
            switch (annotation.type) {
                case utils_1.AST_NODE_TYPES.TSBigIntKeyword: {
                    // note that bigint cannot have + prefixed to it
                    const unwrappedInit = hasUnaryPrefix(init, '-')
                        ? init.argument
                        : init;
                    return (isFunctionCall(unwrappedInit, 'BigInt') ||
                        (unwrappedInit.type === utils_1.AST_NODE_TYPES.Literal &&
                            'bigint' in unwrappedInit));
                }
                case utils_1.AST_NODE_TYPES.TSBooleanKeyword:
                    return (hasUnaryPrefix(init, '!') ||
                        isFunctionCall(init, 'Boolean') ||
                        isLiteral(init, 'boolean'));
                case utils_1.AST_NODE_TYPES.TSNumberKeyword: {
                    const unwrappedInit = hasUnaryPrefix(init, '+', '-')
                        ? init.argument
                        : init;
                    return (isIdentifier(unwrappedInit, 'Infinity', 'NaN') ||
                        isFunctionCall(unwrappedInit, 'Number') ||
                        isLiteral(unwrappedInit, 'number'));
                }
                case utils_1.AST_NODE_TYPES.TSNullKeyword:
                    return init.type === utils_1.AST_NODE_TYPES.Literal && init.value == null;
                case utils_1.AST_NODE_TYPES.TSStringKeyword:
                    return (isFunctionCall(init, 'String') ||
                        isLiteral(init, 'string') ||
                        init.type === utils_1.AST_NODE_TYPES.TemplateLiteral);
                case utils_1.AST_NODE_TYPES.TSSymbolKeyword:
                    return isFunctionCall(init, 'Symbol');
                case utils_1.AST_NODE_TYPES.TSTypeReference: {
                    if (annotation.typeName.type === utils_1.AST_NODE_TYPES.Identifier &&
                        annotation.typeName.name === 'RegExp') {
                        const isRegExpLiteral = init.type === utils_1.AST_NODE_TYPES.Literal &&
                            init.value instanceof RegExp;
                        const isRegExpNewCall = init.type === utils_1.AST_NODE_TYPES.NewExpression &&
                            init.callee.type === utils_1.AST_NODE_TYPES.Identifier &&
                            init.callee.name === 'RegExp';
                        const isRegExpCall = isFunctionCall(init, 'RegExp');
                        return isRegExpLiteral || isRegExpCall || isRegExpNewCall;
                    }
                    return false;
                }
                case utils_1.AST_NODE_TYPES.TSUndefinedKeyword:
                    return (hasUnaryPrefix(init, 'void') || isIdentifier(init, 'undefined'));
            }
            return false;
        }
        /**
         * Reports an inferrable type declaration, if any
         */
        function reportInferrableType(node, typeNode, initNode) {
            if (!typeNode || !initNode) {
                return;
            }
            if (!isInferrable(typeNode.typeAnnotation, initNode)) {
                return;
            }
            const type = typeNode.typeAnnotation.type === utils_1.AST_NODE_TYPES.TSTypeReference
                ? // TODO - if we add more references
                    'RegExp'
                : keywordMap[typeNode.typeAnnotation.type];
            context.report({
                node,
                messageId: 'noInferrableType',
                data: {
                    type,
                },
                *fix(fixer) {
                    if ((node.type === utils_1.AST_NODE_TYPES.AssignmentPattern &&
                        node.left.optional) ||
                        (node.type === utils_1.AST_NODE_TYPES.PropertyDefinition && node.definite)) {
                        yield fixer.remove(sourceCode.getTokenBefore(typeNode));
                    }
                    yield fixer.remove(typeNode);
                },
            });
        }
        function inferrableVariableVisitor(node) {
            reportInferrableType(node, node.id.typeAnnotation, node.init);
        }
        function inferrableParameterVisitor(node) {
            if (ignoreParameters) {
                return;
            }
            node.params.forEach(param => {
                if (param.type === utils_1.AST_NODE_TYPES.TSParameterProperty) {
                    param = param.parameter;
                }
                if (param.type === utils_1.AST_NODE_TYPES.AssignmentPattern) {
                    reportInferrableType(param, param.left.typeAnnotation, param.right);
                }
            });
        }
        function inferrablePropertyVisitor(node) {
            // We ignore `readonly` because of Microsoft/TypeScript#14416
            // Essentially a readonly property without a type
            // will result in its value being the type, leading to
            // compile errors if the type is stripped.
            if (ignoreProperties || node.readonly || node.optional) {
                return;
            }
            reportInferrableType(node, node.typeAnnotation, node.value);
        }
        return {
            VariableDeclarator: inferrableVariableVisitor,
            FunctionExpression: inferrableParameterVisitor,
            FunctionDeclaration: inferrableParameterVisitor,
            ArrowFunctionExpression: inferrableParameterVisitor,
            PropertyDefinition: inferrablePropertyVisitor,
        };
    },
});
//# sourceMappingURL=no-inferrable-types.js.map