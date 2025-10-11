"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'no-namespace',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Disallow TypeScript namespaces',
            recommended: 'recommended',
        },
        messages: {
            moduleSyntaxIsPreferred: 'ES2015 module syntax is preferred over namespaces.',
        },
        schema: [
            {
                type: 'object',
                properties: {
                    allowDeclarations: {
                        description: 'Whether to allow `declare` with custom TypeScript namespaces.',
                        type: 'boolean',
                    },
                    allowDefinitionFiles: {
                        description: 'Whether to allow `declare` with custom TypeScript namespaces inside definition files.',
                        type: 'boolean',
                    },
                },
                additionalProperties: false,
            },
        ],
    },
    defaultOptions: [
        {
            allowDeclarations: false,
            allowDefinitionFiles: true,
        },
    ],
    create(context, [{ allowDeclarations, allowDefinitionFiles }]) {
        const filename = (0, eslint_utils_1.getFilename)(context);
        function isDeclaration(node) {
            if (node.type === utils_1.AST_NODE_TYPES.TSModuleDeclaration && node.declare) {
                return true;
            }
            return node.parent != null && isDeclaration(node.parent);
        }
        return {
            "TSModuleDeclaration[global!=true][id.type!='Literal']"(node) {
                if (node.parent.type === utils_1.AST_NODE_TYPES.TSModuleDeclaration ||
                    (allowDefinitionFiles && (0, util_1.isDefinitionFile)(filename)) ||
                    (allowDeclarations && isDeclaration(node))) {
                    return;
                }
                context.report({
                    node,
                    messageId: 'moduleSyntaxIsPreferred',
                });
            },
        };
    },
});
//# sourceMappingURL=no-namespace.js.map