"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'consistent-type-definitions',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Enforce type definitions to consistently use either `interface` or `type`',
            recommended: 'stylistic',
        },
        messages: {
            interfaceOverType: 'Use an `interface` instead of a `type`.',
            typeOverInterface: 'Use a `type` instead of an `interface`.',
        },
        schema: [
            {
                type: 'string',
                enum: ['interface', 'type'],
            },
        ],
        fixable: 'code',
    },
    defaultOptions: ['interface'],
    create(context, [option]) {
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        /**
         * Iterates from the highest parent to the currently traversed node
         * to determine whether any node in tree is globally declared module declaration
         */
        function isCurrentlyTraversedNodeWithinModuleDeclaration() {
            return (0, eslint_utils_1.getAncestors)(context).some(node => node.type === utils_1.AST_NODE_TYPES.TSModuleDeclaration &&
                node.declare &&
                node.global);
        }
        return {
            ...(option === 'interface' && {
                "TSTypeAliasDeclaration[typeAnnotation.type='TSTypeLiteral']"(node) {
                    context.report({
                        node: node.id,
                        messageId: 'interfaceOverType',
                        fix(fixer) {
                            const typeNode = node.typeParameters ?? node.id;
                            const fixes = [];
                            const firstToken = sourceCode.getTokenBefore(node.id);
                            if (firstToken) {
                                fixes.push(fixer.replaceText(firstToken, 'interface'));
                                fixes.push(fixer.replaceTextRange([typeNode.range[1], node.typeAnnotation.range[0]], ' '));
                            }
                            const afterToken = sourceCode.getTokenAfter(node.typeAnnotation);
                            if (afterToken &&
                                afterToken.type === utils_1.AST_TOKEN_TYPES.Punctuator &&
                                afterToken.value === ';') {
                                fixes.push(fixer.remove(afterToken));
                            }
                            return fixes;
                        },
                    });
                },
            }),
            ...(option === 'type' && {
                TSInterfaceDeclaration(node) {
                    const fix = isCurrentlyTraversedNodeWithinModuleDeclaration()
                        ? null
                        : (fixer) => {
                            const typeNode = node.typeParameters ?? node.id;
                            const fixes = [];
                            const firstToken = sourceCode.getTokenBefore(node.id);
                            if (firstToken) {
                                fixes.push(fixer.replaceText(firstToken, 'type'));
                                fixes.push(fixer.replaceTextRange([typeNode.range[1], node.body.range[0]], ' = '));
                            }
                            node.extends.forEach(heritage => {
                                const typeIdentifier = sourceCode.getText(heritage);
                                fixes.push(fixer.insertTextAfter(node.body, ` & ${typeIdentifier}`));
                            });
                            if (node.parent.type === utils_1.AST_NODE_TYPES.ExportDefaultDeclaration) {
                                fixes.push(fixer.removeRange([node.parent.range[0], node.range[0]]), fixer.insertTextAfter(node.body, `\nexport default ${node.id.name}`));
                            }
                            return fixes;
                        };
                    context.report({
                        node: node.id,
                        messageId: 'typeOverInterface',
                        /**
                         * remove automatically fix when the interface is within a declare global
                         * @see {@link https://github.com/typescript-eslint/typescript-eslint/issues/2707}
                         */
                        fix,
                    });
                },
            }),
        };
    },
});
//# sourceMappingURL=consistent-type-definitions.js.map