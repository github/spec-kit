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
const ts = __importStar(require("typescript"));
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'no-useless-template-literals',
    meta: {
        fixable: 'code',
        type: 'suggestion',
        docs: {
            description: 'Disallow unnecessary template literals',
            recommended: 'strict',
            requiresTypeChecking: true,
        },
        messages: {
            noUselessTemplateLiteral: 'Template literal expression is unnecessary and can be simplified.',
        },
        schema: [],
    },
    defaultOptions: [],
    create(context) {
        const services = (0, util_1.getParserServices)(context);
        function isUnderlyingTypeString(expression) {
            const type = (0, util_1.getConstrainedTypeAtLocation)(services, expression);
            const isString = (t) => {
                return (0, util_1.isTypeFlagSet)(t, ts.TypeFlags.StringLike);
            };
            if (type.isUnion()) {
                return type.types.every(isString);
            }
            if (type.isIntersection()) {
                return type.types.some(isString);
            }
            return isString(type);
        }
        function isLiteral(expression) {
            return expression.type === utils_1.AST_NODE_TYPES.Literal;
        }
        function isInfinityIdentifier(expression) {
            return (expression.type === utils_1.AST_NODE_TYPES.Identifier &&
                expression.name === 'Infinity');
        }
        function isNaNIdentifier(expression) {
            return (expression.type === utils_1.AST_NODE_TYPES.Identifier &&
                expression.name === 'NaN');
        }
        return {
            TemplateLiteral(node) {
                if (node.parent.type === utils_1.AST_NODE_TYPES.TaggedTemplateExpression) {
                    return;
                }
                const hasSingleStringVariable = node.quasis.length === 2 &&
                    node.quasis[0].value.raw === '' &&
                    node.quasis[1].value.raw === '' &&
                    node.expressions.length === 1 &&
                    isUnderlyingTypeString(node.expressions[0]);
                if (hasSingleStringVariable) {
                    context.report({
                        node: node.expressions[0],
                        messageId: 'noUselessTemplateLiteral',
                        fix(fixer) {
                            const [prevQuasi, nextQuasi] = node.quasis;
                            // Remove the quasis and backticks.
                            return [
                                fixer.removeRange([
                                    prevQuasi.range[1] - 3,
                                    node.expressions[0].range[0],
                                ]),
                                fixer.removeRange([
                                    node.expressions[0].range[1],
                                    nextQuasi.range[0] + 2,
                                ]),
                            ];
                        },
                    });
                    return;
                }
                const fixableExpressions = node.expressions.filter((expression) => isLiteral(expression) ||
                    (0, util_1.isUndefinedIdentifier)(expression) ||
                    isInfinityIdentifier(expression) ||
                    isNaNIdentifier(expression));
                fixableExpressions.forEach(expression => {
                    context.report({
                        node: expression,
                        messageId: 'noUselessTemplateLiteral',
                        fix(fixer) {
                            const index = node.expressions.indexOf(expression);
                            const prevQuasi = node.quasis[index];
                            const nextQuasi = node.quasis[index + 1];
                            // Remove the quasis' parts that are related to the current expression.
                            const fixes = [
                                fixer.removeRange([
                                    prevQuasi.range[1] - 2,
                                    expression.range[0],
                                ]),
                                fixer.removeRange([
                                    expression.range[1],
                                    nextQuasi.range[0] + 1,
                                ]),
                            ];
                            const stringValue = (0, util_1.getStaticStringValue)(expression);
                            if (stringValue != null) {
                                const escapedValue = stringValue.replace(/([`$\\])/g, '\\$1');
                                fixes.push(fixer.replaceText(expression, escapedValue));
                            }
                            return fixes;
                        },
                    });
                });
            },
        };
    },
});
//# sourceMappingURL=no-useless-template-literals.js.map