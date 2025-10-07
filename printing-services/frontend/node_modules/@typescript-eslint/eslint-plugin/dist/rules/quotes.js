"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const util_1 = require("../util");
const getESLintCoreRule_1 = require("../util/getESLintCoreRule");
const baseRule = (0, getESLintCoreRule_1.getESLintCoreRule)('quotes');
exports.default = (0, util_1.createRule)({
    name: 'quotes',
    meta: {
        deprecated: true,
        replacedBy: ['@stylistic/ts/quotes'],
        type: 'layout',
        docs: {
            description: 'Enforce the consistent use of either backticks, double, or single quotes',
            extendsBaseRule: true,
        },
        fixable: 'code',
        hasSuggestions: baseRule.meta.hasSuggestions,
        messages: baseRule.meta.messages,
        schema: baseRule.meta.schema,
    },
    defaultOptions: [
        'double',
        {
            allowTemplateLiterals: false,
            avoidEscape: false,
        },
    ],
    create(context, [option]) {
        const rules = baseRule.create(context);
        function isAllowedAsNonBacktick(node) {
            const parent = node.parent;
            switch (parent.type) {
                case utils_1.AST_NODE_TYPES.TSAbstractMethodDefinition:
                case utils_1.AST_NODE_TYPES.TSMethodSignature:
                case utils_1.AST_NODE_TYPES.TSPropertySignature:
                case utils_1.AST_NODE_TYPES.TSModuleDeclaration:
                case utils_1.AST_NODE_TYPES.TSLiteralType:
                case utils_1.AST_NODE_TYPES.TSExternalModuleReference:
                    return true;
                case utils_1.AST_NODE_TYPES.TSEnumMember:
                    return node === parent.id;
                case utils_1.AST_NODE_TYPES.TSAbstractPropertyDefinition:
                case utils_1.AST_NODE_TYPES.PropertyDefinition:
                    return node === parent.key;
                default:
                    return false;
            }
        }
        return {
            Literal(node) {
                if (option === 'backtick' && isAllowedAsNonBacktick(node)) {
                    return;
                }
                rules.Literal(node);
            },
            TemplateLiteral(node) {
                rules.TemplateLiteral(node);
            },
        };
    },
});
//# sourceMappingURL=quotes.js.map