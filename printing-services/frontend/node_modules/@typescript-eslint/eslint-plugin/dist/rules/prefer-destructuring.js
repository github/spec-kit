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
const util_1 = require("../util");
const getESLintCoreRule_1 = require("../util/getESLintCoreRule");
const baseRule = (0, getESLintCoreRule_1.getESLintCoreRule)('prefer-destructuring');
const destructuringTypeConfig = {
    type: 'object',
    properties: {
        array: {
            type: 'boolean',
        },
        object: {
            type: 'boolean',
        },
    },
    additionalProperties: false,
};
const schema = [
    {
        oneOf: [
            {
                type: 'object',
                properties: {
                    VariableDeclarator: destructuringTypeConfig,
                    AssignmentExpression: destructuringTypeConfig,
                },
                additionalProperties: false,
            },
            destructuringTypeConfig,
        ],
    },
    {
        type: 'object',
        properties: {
            enforceForRenamedProperties: {
                type: 'boolean',
            },
            enforceForDeclarationWithTypeAnnotation: {
                type: 'boolean',
            },
        },
    },
];
exports.default = (0, util_1.createRule)({
    name: 'prefer-destructuring',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Require destructuring from arrays and/or objects',
            extendsBaseRule: true,
            requiresTypeChecking: true,
        },
        schema,
        fixable: baseRule.meta.fixable,
        hasSuggestions: baseRule.meta.hasSuggestions,
        messages: baseRule.meta.messages,
    },
    defaultOptions: [
        {
            VariableDeclarator: {
                array: true,
                object: true,
            },
            AssignmentExpression: {
                array: true,
                object: true,
            },
        },
        {},
    ],
    create(context, [enabledTypes, options]) {
        const { enforceForRenamedProperties = false, enforceForDeclarationWithTypeAnnotation = false, } = options;
        const { program, esTreeNodeToTSNodeMap } = (0, util_1.getParserServices)(context);
        const typeChecker = program.getTypeChecker();
        const baseRules = baseRule.create(context);
        let baseRulesWithoutFixCache = null;
        return {
            VariableDeclarator(node) {
                performCheck(node.id, node.init, node);
            },
            AssignmentExpression(node) {
                if (node.operator !== '=') {
                    return;
                }
                performCheck(node.left, node.right, node);
            },
        };
        function performCheck(leftNode, rightNode, reportNode) {
            const rules = leftNode.type === utils_1.AST_NODE_TYPES.Identifier &&
                leftNode.typeAnnotation === undefined
                ? baseRules
                : baseRulesWithoutFix();
            if ('typeAnnotation' in leftNode &&
                leftNode.typeAnnotation !== undefined &&
                !enforceForDeclarationWithTypeAnnotation) {
                return;
            }
            if (rightNode != null &&
                isArrayLiteralIntegerIndexAccess(rightNode) &&
                rightNode.object.type !== utils_1.AST_NODE_TYPES.Super) {
                const tsObj = esTreeNodeToTSNodeMap.get(rightNode.object);
                const objType = typeChecker.getTypeAtLocation(tsObj);
                if (!isTypeAnyOrIterableType(objType, typeChecker)) {
                    if (!enforceForRenamedProperties ||
                        !getNormalizedEnabledType(reportNode.type, 'object')) {
                        return;
                    }
                    context.report({
                        node: reportNode,
                        messageId: 'preferDestructuring',
                        data: { type: 'object' },
                    });
                    return;
                }
            }
            if (reportNode.type === utils_1.AST_NODE_TYPES.AssignmentExpression) {
                rules.AssignmentExpression(reportNode);
            }
            else {
                rules.VariableDeclarator(reportNode);
            }
        }
        function getNormalizedEnabledType(nodeType, destructuringType) {
            if ('object' in enabledTypes || 'array' in enabledTypes) {
                return enabledTypes[destructuringType];
            }
            return enabledTypes[nodeType][destructuringType];
        }
        function baseRulesWithoutFix() {
            baseRulesWithoutFixCache ??= baseRule.create(noFixContext(context));
            return baseRulesWithoutFixCache;
        }
    },
});
function noFixContext(context) {
    const customContext = {
        report: (descriptor) => {
            context.report({
                ...descriptor,
                fix: undefined,
            });
        },
    };
    // we can't directly proxy `context` because its `report` property is non-configurable
    // and non-writable. So we proxy `customContext` and redirect all
    // property access to the original context except for `report`
    return new Proxy(customContext, {
        get(target, path, receiver) {
            if (path !== 'report') {
                return Reflect.get(context, path, receiver);
            }
            return Reflect.get(target, path, receiver);
        },
    });
}
function isTypeAnyOrIterableType(type, typeChecker) {
    if ((0, util_1.isTypeAnyType)(type)) {
        return true;
    }
    if (!type.isUnion()) {
        const iterator = tsutils.getWellKnownSymbolPropertyOfType(type, 'iterator', typeChecker);
        return iterator !== undefined;
    }
    return type.types.every(t => isTypeAnyOrIterableType(t, typeChecker));
}
function isArrayLiteralIntegerIndexAccess(node) {
    if (node.type !== utils_1.AST_NODE_TYPES.MemberExpression) {
        return false;
    }
    if (node.property.type !== utils_1.AST_NODE_TYPES.Literal) {
        return false;
    }
    return Number.isInteger(node.property.value);
}
//# sourceMappingURL=prefer-destructuring.js.map