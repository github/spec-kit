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
const analyzeChain_1 = require("./prefer-optional-chain-utils/analyzeChain");
const gatherLogicalOperands_1 = require("./prefer-optional-chain-utils/gatherLogicalOperands");
exports.default = (0, util_1.createRule)({
    name: 'prefer-optional-chain',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Enforce using concise optional chain expressions instead of chained logical ands, negated logical ors, or empty objects',
            recommended: 'stylistic',
            requiresTypeChecking: true,
        },
        fixable: 'code',
        hasSuggestions: true,
        messages: {
            preferOptionalChain: "Prefer using an optional chain expression instead, as it's more concise and easier to read.",
            optionalChainSuggest: 'Change to an optional chain.',
        },
        schema: [
            {
                type: 'object',
                additionalProperties: false,
                properties: {
                    checkAny: {
                        type: 'boolean',
                        description: 'Check operands that are typed as `any` when inspecting "loose boolean" operands.',
                    },
                    checkUnknown: {
                        type: 'boolean',
                        description: 'Check operands that are typed as `unknown` when inspecting "loose boolean" operands.',
                    },
                    checkString: {
                        type: 'boolean',
                        description: 'Check operands that are typed as `string` when inspecting "loose boolean" operands.',
                    },
                    checkNumber: {
                        type: 'boolean',
                        description: 'Check operands that are typed as `number` when inspecting "loose boolean" operands.',
                    },
                    checkBoolean: {
                        type: 'boolean',
                        description: 'Check operands that are typed as `boolean` when inspecting "loose boolean" operands.',
                    },
                    checkBigInt: {
                        type: 'boolean',
                        description: 'Check operands that are typed as `bigint` when inspecting "loose boolean" operands.',
                    },
                    requireNullish: {
                        type: 'boolean',
                        description: 'Skip operands that are not typed with `null` and/or `undefined` when inspecting "loose boolean" operands.',
                    },
                    allowPotentiallyUnsafeFixesThatModifyTheReturnTypeIKnowWhatImDoing: {
                        type: 'boolean',
                        description: 'Allow autofixers that will change the return type of the expression. This option is considered unsafe as it may break the build.',
                    },
                },
            },
        ],
    },
    defaultOptions: [
        {
            checkAny: true,
            checkUnknown: true,
            checkString: true,
            checkNumber: true,
            checkBoolean: true,
            checkBigInt: true,
            requireNullish: false,
            allowPotentiallyUnsafeFixesThatModifyTheReturnTypeIKnowWhatImDoing: false,
        },
    ],
    create(context, [options]) {
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        const parserServices = (0, util_1.getParserServices)(context);
        const seenLogicals = new Set();
        return {
            // specific handling for `(foo ?? {}).bar` / `(foo || {}).bar`
            'LogicalExpression[operator="||"], LogicalExpression[operator="??"]'(node) {
                const leftNode = node.left;
                const rightNode = node.right;
                const parentNode = node.parent;
                const isRightNodeAnEmptyObjectLiteral = rightNode.type === utils_1.AST_NODE_TYPES.ObjectExpression &&
                    rightNode.properties.length === 0;
                if (!isRightNodeAnEmptyObjectLiteral ||
                    parentNode.type !== utils_1.AST_NODE_TYPES.MemberExpression ||
                    parentNode.optional) {
                    return;
                }
                seenLogicals.add(node);
                function isLeftSideLowerPrecedence() {
                    const logicalTsNode = parserServices.esTreeNodeToTSNodeMap.get(node);
                    const leftTsNode = parserServices.esTreeNodeToTSNodeMap.get(leftNode);
                    const operator = ts.isBinaryExpression(logicalTsNode)
                        ? logicalTsNode.operatorToken.kind
                        : ts.SyntaxKind.Unknown;
                    const leftPrecedence = (0, util_1.getOperatorPrecedence)(leftTsNode.kind, operator);
                    return leftPrecedence < util_1.OperatorPrecedence.LeftHandSide;
                }
                context.report({
                    node: parentNode,
                    messageId: 'preferOptionalChain',
                    suggest: [
                        {
                            messageId: 'optionalChainSuggest',
                            fix: (fixer) => {
                                const leftNodeText = sourceCode.getText(leftNode);
                                // Any node that is made of an operator with higher or equal precedence,
                                const maybeWrappedLeftNode = isLeftSideLowerPrecedence()
                                    ? `(${leftNodeText})`
                                    : leftNodeText;
                                const propertyToBeOptionalText = sourceCode.getText(parentNode.property);
                                const maybeWrappedProperty = parentNode.computed
                                    ? `[${propertyToBeOptionalText}]`
                                    : propertyToBeOptionalText;
                                return fixer.replaceTextRange(parentNode.range, `${maybeWrappedLeftNode}?.${maybeWrappedProperty}`);
                            },
                        },
                    ],
                });
            },
            'LogicalExpression[operator!="??"]'(node) {
                if (seenLogicals.has(node)) {
                    return;
                }
                const { operands, newlySeenLogicals } = (0, gatherLogicalOperands_1.gatherLogicalOperands)(node, parserServices, options);
                for (const logical of newlySeenLogicals) {
                    seenLogicals.add(logical);
                }
                let currentChain = [];
                for (const operand of operands) {
                    if (operand.type === "Invalid" /* OperandValidity.Invalid */) {
                        (0, analyzeChain_1.analyzeChain)(context, sourceCode, parserServices, options, node.operator, currentChain);
                        currentChain = [];
                    }
                    else {
                        currentChain.push(operand);
                    }
                }
                // make sure to check whatever's left
                if (currentChain.length > 0) {
                    (0, analyzeChain_1.analyzeChain)(context, sourceCode, parserServices, options, node.operator, currentChain);
                }
            },
        };
    },
});
//# sourceMappingURL=prefer-optional-chain.js.map