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
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'prefer-find',
    meta: {
        docs: {
            description: 'Enforce the use of Array.prototype.find() over Array.prototype.filter() followed by [0] when looking for a single result',
            requiresTypeChecking: true,
        },
        messages: {
            preferFind: 'Prefer .find(...) instead of .filter(...)[0].',
            preferFindSuggestion: 'Use .find(...) instead of .filter(...)[0].',
        },
        schema: [],
        type: 'suggestion',
        hasSuggestions: true,
    },
    defaultOptions: [],
    create(context) {
        const globalScope = (0, eslint_utils_1.getScope)(context);
        const services = (0, util_1.getParserServices)(context);
        const checker = services.program.getTypeChecker();
        function parseIfArrayFilterExpression(expression) {
            if (expression.type === utils_1.AST_NODE_TYPES.SequenceExpression) {
                // Only the last expression in (a, b, [1, 2, 3].filter(condition))[0] matters
                const lastExpression = (0, util_1.nullThrows)(expression.expressions.at(-1), 'Expected to have more than zero expressions in a sequence expression');
                return parseIfArrayFilterExpression(lastExpression);
            }
            if (expression.type === utils_1.AST_NODE_TYPES.ChainExpression) {
                return parseIfArrayFilterExpression(expression.expression);
            }
            // Check if it looks like <<stuff>>(...), but not <<stuff>>?.(...)
            if (expression.type === utils_1.AST_NODE_TYPES.CallExpression &&
                !expression.optional) {
                const callee = expression.callee;
                // Check if it looks like <<stuff>>.filter(...) or <<stuff>>['filter'](...),
                // or the optional chaining variants.
                if (callee.type === utils_1.AST_NODE_TYPES.MemberExpression) {
                    const isBracketSyntaxForFilter = callee.computed;
                    if (isStaticMemberAccessOfValue(callee, 'filter', globalScope)) {
                        const filterNode = callee.property;
                        const filteredObjectType = (0, util_1.getConstrainedTypeAtLocation)(services, callee.object);
                        // As long as the object is a (possibly nullable) array,
                        // this is an Array.prototype.filter expression.
                        if (isArrayish(filteredObjectType)) {
                            return {
                                isBracketSyntaxForFilter,
                                filterNode,
                            };
                        }
                    }
                }
            }
            return undefined;
        }
        /**
         * Tells whether the type is a possibly nullable array/tuple or union thereof.
         */
        function isArrayish(type) {
            let isAtLeastOneArrayishComponent = false;
            for (const unionPart of tsutils.unionTypeParts(type)) {
                if (tsutils.isIntrinsicNullType(unionPart) ||
                    tsutils.isIntrinsicUndefinedType(unionPart)) {
                    continue;
                }
                // apparently checker.isArrayType(T[] & S[]) => false.
                // so we need to check the intersection parts individually.
                const isArrayOrIntersectionThereof = tsutils
                    .intersectionTypeParts(unionPart)
                    .every(intersectionPart => checker.isArrayType(intersectionPart) ||
                    checker.isTupleType(intersectionPart));
                if (!isArrayOrIntersectionThereof) {
                    // There is a non-array, non-nullish type component,
                    // so it's not an array.
                    return false;
                }
                isAtLeastOneArrayishComponent = true;
            }
            return isAtLeastOneArrayishComponent;
        }
        function getObjectIfArrayAtExpression(node) {
            // .at() should take exactly one argument.
            if (node.arguments.length !== 1) {
                return undefined;
            }
            const atArgument = (0, util_1.getStaticValue)(node.arguments[0], globalScope);
            if (atArgument != null && isTreatedAsZeroByArrayAt(atArgument.value)) {
                const callee = node.callee;
                if (callee.type === utils_1.AST_NODE_TYPES.MemberExpression &&
                    !callee.optional &&
                    isStaticMemberAccessOfValue(callee, 'at', globalScope)) {
                    return callee.object;
                }
            }
            return undefined;
        }
        /**
         * Implements the algorithm for array indexing by `.at()` method.
         * @see https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/at#parameters
         */
        function isTreatedAsZeroByArrayAt(value) {
            const asNumber = Number(value);
            if (isNaN(asNumber)) {
                return true;
            }
            return Math.trunc(asNumber) === 0;
        }
        function isMemberAccessOfZero(node) {
            const property = (0, util_1.getStaticValue)(node.property, globalScope);
            // Check if it looks like <<stuff>>[0] or <<stuff>>['0'], but not <<stuff>>?.[0]
            return (!node.optional &&
                property != null &&
                isTreatedAsZeroByMemberAccess(property.value));
        }
        /**
         * Implements the algorithm for array indexing by member operator.
         * @see https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array#array_indices
         */
        function isTreatedAsZeroByMemberAccess(value) {
            return String(value) === '0';
        }
        function generateFixToRemoveArrayElementAccess(fixer, arrayNode, wholeExpressionBeingFlagged, sourceCode) {
            const tokenToStartDeletingFrom = (0, util_1.nullThrows)(
            // The next `.` or `[` is what we're looking for.
            // think of (...).at(0) or (...)[0] or even (...)["at"](0).
            sourceCode.getTokenAfter(arrayNode, token => token.value === '.' || token.value === '['), 'Expected to find a member access token!');
            return fixer.removeRange([
                tokenToStartDeletingFrom.range[0],
                wholeExpressionBeingFlagged.range[1],
            ]);
        }
        function generateFixToReplaceFilterWithFind(fixer, filterExpression) {
            return fixer.replaceText(filterExpression.filterNode, filterExpression.isBracketSyntaxForFilter ? '"find"' : 'find');
        }
        return {
            // This query will be used to find things like `filteredResults.at(0)`.
            CallExpression(node) {
                const object = getObjectIfArrayAtExpression(node);
                if (object) {
                    const filterExpression = parseIfArrayFilterExpression(object);
                    if (filterExpression) {
                        context.report({
                            node,
                            messageId: 'preferFind',
                            suggest: [
                                {
                                    messageId: 'preferFindSuggestion',
                                    fix: (fixer) => {
                                        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
                                        return [
                                            generateFixToReplaceFilterWithFind(fixer, filterExpression),
                                            // Get rid of the .at(0) or ['at'](0).
                                            generateFixToRemoveArrayElementAccess(fixer, object, node, sourceCode),
                                        ];
                                    },
                                },
                            ],
                        });
                    }
                }
            },
            // This query will be used to find things like `filteredResults[0]`.
            //
            // Note: we're always looking for array member access to be "computed",
            // i.e. `filteredResults[0]`, since `filteredResults.0` isn't a thing.
            ['MemberExpression[computed=true]'](node) {
                if (isMemberAccessOfZero(node)) {
                    const object = node.object;
                    const filterExpression = parseIfArrayFilterExpression(object);
                    if (filterExpression) {
                        context.report({
                            node,
                            messageId: 'preferFind',
                            suggest: [
                                {
                                    messageId: 'preferFindSuggestion',
                                    fix: (fixer) => {
                                        const sourceCode = context.sourceCode;
                                        return [
                                            generateFixToReplaceFilterWithFind(fixer, filterExpression),
                                            // Get rid of the [0].
                                            generateFixToRemoveArrayElementAccess(fixer, object, node, sourceCode),
                                        ];
                                    },
                                },
                            ],
                        });
                    }
                }
            },
        };
    },
});
/**
 * Answers whether the member expression looks like
 * `x.memberName`, `x['memberName']`,
 * or even `const mn = 'memberName'; x[mn]` (or optional variants thereof).
 */
function isStaticMemberAccessOfValue(memberExpression, value, scope) {
    if (!memberExpression.computed) {
        // x.memberName case.
        return memberExpression.property.name === value;
    }
    // x['memberName'] cases.
    const staticValueResult = (0, util_1.getStaticValue)(memberExpression.property, scope);
    return staticValueResult != null && value === staticValueResult.value;
}
//# sourceMappingURL=prefer-find.js.map