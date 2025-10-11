"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'no-var-requires',
    meta: {
        type: 'problem',
        docs: {
            description: 'Disallow `require` statements except in import statements',
            recommended: 'recommended',
        },
        messages: {
            noVarReqs: 'Require statement not part of import statement.',
        },
        schema: [
            {
                type: 'object',
                properties: {
                    allow: {
                        type: 'array',
                        items: { type: 'string' },
                        description: 'Patterns of import paths to allow requiring from.',
                    },
                },
                additionalProperties: false,
            },
        ],
    },
    defaultOptions: [{ allow: [] }],
    create(context, options) {
        const allowPatterns = options[0].allow.map(pattern => new RegExp(pattern, 'u'));
        function isImportPathAllowed(importPath) {
            return allowPatterns.some(pattern => importPath.match(pattern));
        }
        return {
            'CallExpression[callee.name="require"]'(node) {
                if (node.arguments[0]?.type === utils_1.AST_NODE_TYPES.Literal &&
                    typeof node.arguments[0].value === 'string' &&
                    isImportPathAllowed(node.arguments[0].value)) {
                    return;
                }
                const parent = node.parent.type === utils_1.AST_NODE_TYPES.ChainExpression
                    ? node.parent.parent
                    : node.parent;
                if ([
                    utils_1.AST_NODE_TYPES.CallExpression,
                    utils_1.AST_NODE_TYPES.MemberExpression,
                    utils_1.AST_NODE_TYPES.NewExpression,
                    utils_1.AST_NODE_TYPES.TSAsExpression,
                    utils_1.AST_NODE_TYPES.TSTypeAssertion,
                    utils_1.AST_NODE_TYPES.VariableDeclarator,
                ].includes(parent.type)) {
                    const variable = utils_1.ASTUtils.findVariable((0, eslint_utils_1.getScope)(context), 'require');
                    if (!variable?.identifiers.length) {
                        context.report({
                            node,
                            messageId: 'noVarReqs',
                        });
                    }
                }
            },
        };
    },
});
//# sourceMappingURL=no-var-requires.js.map