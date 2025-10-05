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
    name: 'no-unnecessary-boolean-literal-compare',
    meta: {
        docs: {
            description: 'Disallow unnecessary equality comparisons against boolean literals',
            recommended: 'strict',
            requiresTypeChecking: true,
        },
        fixable: 'code',
        messages: {
            direct: 'This expression unnecessarily compares a boolean value to a boolean instead of using it directly.',
            negated: 'This expression unnecessarily compares a boolean value to a boolean instead of negating it.',
            comparingNullableToTrueDirect: 'This expression unnecessarily compares a nullable boolean value to true instead of using it directly.',
            comparingNullableToTrueNegated: 'This expression unnecessarily compares a nullable boolean value to true instead of negating it.',
            comparingNullableToFalse: 'This expression unnecessarily compares a nullable boolean value to false instead of using the ?? operator to provide a default.',
        },
        schema: [
            {
                type: 'object',
                properties: {
                    allowComparingNullableBooleansToTrue: {
                        description: 'Whether to allow comparisons between nullable boolean variables and `true`.',
                        type: 'boolean',
                    },
                    allowComparingNullableBooleansToFalse: {
                        description: 'Whether to allow comparisons between nullable boolean variables and `false`.',
                        type: 'boolean',
                    },
                },
                additionalProperties: false,
            },
        ],
        type: 'suggestion',
    },
    defaultOptions: [
        {
            allowComparingNullableBooleansToTrue: true,
            allowComparingNullableBooleansToFalse: true,
        },
    ],
    create(context, [options]) {
        const services = (0, util_1.getParserServices)(context);
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        function getBooleanComparison(node) {
            const comparison = deconstructComparison(node);
            if (!comparison) {
                return undefined;
            }
            const expressionType = services.getTypeAtLocation(comparison.expression);
            if (isBooleanType(expressionType)) {
                return {
                    ...comparison,
                    expressionIsNullableBoolean: false,
                };
            }
            if (isNullableBoolean(expressionType)) {
                return {
                    ...comparison,
                    expressionIsNullableBoolean: true,
                };
            }
            return undefined;
        }
        function isBooleanType(expressionType) {
            return tsutils.isTypeFlagSet(expressionType, ts.TypeFlags.Boolean | ts.TypeFlags.BooleanLiteral);
        }
        /**
         * checks if the expressionType is a union that
         *   1) contains at least one nullish type (null or undefined)
         *   2) contains at least once boolean type (true or false or boolean)
         *   3) does not contain any types besides nullish and boolean types
         */
        function isNullableBoolean(expressionType) {
            if (!expressionType.isUnion()) {
                return false;
            }
            const { types } = expressionType;
            const nonNullishTypes = types.filter(type => !tsutils.isTypeFlagSet(type, ts.TypeFlags.Undefined | ts.TypeFlags.Null));
            const hasNonNullishType = nonNullishTypes.length > 0;
            if (!hasNonNullishType) {
                return false;
            }
            const hasNullableType = nonNullishTypes.length < types.length;
            if (!hasNullableType) {
                return false;
            }
            const allNonNullishTypesAreBoolean = nonNullishTypes.every(isBooleanType);
            if (!allNonNullishTypesAreBoolean) {
                return false;
            }
            return true;
        }
        function deconstructComparison(node) {
            const comparisonType = getEqualsKind(node.operator);
            if (!comparisonType) {
                return undefined;
            }
            for (const [against, expression] of [
                [node.right, node.left],
                [node.left, node.right],
            ]) {
                if (against.type !== utils_1.AST_NODE_TYPES.Literal ||
                    typeof against.value !== 'boolean') {
                    continue;
                }
                const { value: literalBooleanInComparison } = against;
                const negated = !comparisonType.isPositive;
                return {
                    literalBooleanInComparison,
                    expression,
                    negated,
                };
            }
            return undefined;
        }
        function nodeIsUnaryNegation(node) {
            return (node.type === utils_1.AST_NODE_TYPES.UnaryExpression &&
                node.prefix &&
                node.operator === '!');
        }
        return {
            BinaryExpression(node) {
                const comparison = getBooleanComparison(node);
                if (comparison === undefined) {
                    return;
                }
                if (comparison.expressionIsNullableBoolean) {
                    if (comparison.literalBooleanInComparison &&
                        options.allowComparingNullableBooleansToTrue) {
                        return;
                    }
                    if (!comparison.literalBooleanInComparison &&
                        options.allowComparingNullableBooleansToFalse) {
                        return;
                    }
                }
                context.report({
                    fix: function* (fixer) {
                        // 1. isUnaryNegation - parent negation
                        // 2. literalBooleanInComparison - is compared to literal boolean
                        // 3. negated - is expression negated
                        const isUnaryNegation = nodeIsUnaryNegation(node.parent);
                        const shouldNegate = comparison.negated !== comparison.literalBooleanInComparison;
                        const mutatedNode = isUnaryNegation ? node.parent : node;
                        yield fixer.replaceText(mutatedNode, sourceCode.getText(comparison.expression));
                        // if `isUnaryNegation === literalBooleanInComparison === !negated` is true - negate the expression
                        if (shouldNegate === isUnaryNegation) {
                            yield fixer.insertTextBefore(mutatedNode, '!');
                            // if the expression `exp` is not a strong precedence node, wrap it in parentheses
                            if (!(0, util_1.isStrongPrecedenceNode)(comparison.expression)) {
                                yield fixer.insertTextBefore(mutatedNode, '(');
                                yield fixer.insertTextAfter(mutatedNode, ')');
                            }
                        }
                        // if the expression `exp` is nullable, and we're not comparing to `true`, insert `?? true`
                        if (comparison.expressionIsNullableBoolean &&
                            !comparison.literalBooleanInComparison) {
                            // provide the default `true`
                            yield fixer.insertTextBefore(mutatedNode, '(');
                            yield fixer.insertTextAfter(mutatedNode, ' ?? true)');
                        }
                    },
                    messageId: comparison.expressionIsNullableBoolean
                        ? comparison.literalBooleanInComparison
                            ? comparison.negated
                                ? 'comparingNullableToTrueNegated'
                                : 'comparingNullableToTrueDirect'
                            : 'comparingNullableToFalse'
                        : comparison.negated
                            ? 'negated'
                            : 'direct',
                    node,
                });
            },
        };
    },
});
function getEqualsKind(operator) {
    switch (operator) {
        case '==':
            return {
                isPositive: true,
                isStrict: false,
            };
        case '===':
            return {
                isPositive: true,
                isStrict: true,
            };
        case '!=':
            return {
                isPositive: false,
                isStrict: false,
            };
        case '!==':
            return {
                isPositive: false,
                isStrict: true,
            };
        default:
            return undefined;
    }
}
//# sourceMappingURL=no-unnecessary-boolean-literal-compare.js.map