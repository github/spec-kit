"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const util_1 = require("../util");
const getESLintCoreRule_1 = require("../util/getESLintCoreRule");
const baseRule = (0, getESLintCoreRule_1.getESLintCoreRule)('semi');
exports.default = (0, util_1.createRule)({
    name: 'semi',
    meta: {
        deprecated: true,
        replacedBy: ['@stylistic/ts/semi'],
        type: 'layout',
        docs: {
            description: 'Require or disallow semicolons instead of ASI',
            // too opinionated to be recommended
            extendsBaseRule: true,
        },
        fixable: 'code',
        hasSuggestions: baseRule.meta.hasSuggestions,
        schema: baseRule.meta.schema,
        messages: baseRule.meta.messages,
    },
    defaultOptions: [
        'always',
        {
            omitLastInOneLineBlock: false,
            beforeStatementContinuationChars: 'any',
        },
    ],
    create(context) {
        const rules = baseRule.create(context);
        const checkForSemicolon = rules.ExpressionStatement;
        /*
          The following nodes are handled by the member-delimiter-style rule
          AST_NODE_TYPES.TSCallSignatureDeclaration,
          AST_NODE_TYPES.TSConstructSignatureDeclaration,
          AST_NODE_TYPES.TSIndexSignature,
          AST_NODE_TYPES.TSMethodSignature,
          AST_NODE_TYPES.TSPropertySignature,
        */
        const nodesToCheck = [
            utils_1.AST_NODE_TYPES.PropertyDefinition,
            utils_1.AST_NODE_TYPES.TSAbstractPropertyDefinition,
            utils_1.AST_NODE_TYPES.TSDeclareFunction,
            utils_1.AST_NODE_TYPES.TSExportAssignment,
            utils_1.AST_NODE_TYPES.TSImportEqualsDeclaration,
            utils_1.AST_NODE_TYPES.TSTypeAliasDeclaration,
            utils_1.AST_NODE_TYPES.TSEmptyBodyFunctionExpression,
        ].reduce((acc, node) => {
            acc[node] = checkForSemicolon;
            return acc;
        }, {});
        return {
            ...rules,
            ...nodesToCheck,
            ExportDefaultDeclaration(node) {
                if (node.declaration.type !== utils_1.AST_NODE_TYPES.TSInterfaceDeclaration) {
                    rules.ExportDefaultDeclaration(node);
                }
            },
        };
    },
});
//# sourceMappingURL=semi.js.map