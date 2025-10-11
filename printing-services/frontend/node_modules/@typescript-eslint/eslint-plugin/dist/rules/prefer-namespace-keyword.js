"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'prefer-namespace-keyword',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Require using `namespace` keyword over `module` keyword to declare custom TypeScript modules',
            recommended: 'stylistic',
        },
        fixable: 'code',
        messages: {
            useNamespace: "Use 'namespace' instead of 'module' to declare custom TypeScript modules.",
        },
        schema: [],
    },
    defaultOptions: [],
    create(context) {
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        return {
            TSModuleDeclaration(node) {
                // Do nothing if the name is a string.
                if (node.id.type === utils_1.AST_NODE_TYPES.Literal) {
                    return;
                }
                // Get tokens of the declaration header.
                const moduleType = sourceCode.getTokenBefore(node.id);
                if (moduleType &&
                    moduleType.type === utils_1.AST_TOKEN_TYPES.Identifier &&
                    moduleType.value === 'module') {
                    context.report({
                        node,
                        messageId: 'useNamespace',
                        fix(fixer) {
                            return fixer.replaceText(moduleType, 'namespace');
                        },
                    });
                }
            },
        };
    },
});
//# sourceMappingURL=prefer-namespace-keyword.js.map