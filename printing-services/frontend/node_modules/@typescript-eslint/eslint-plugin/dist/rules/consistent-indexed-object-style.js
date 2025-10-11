"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'consistent-indexed-object-style',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Require or disallow the `Record` type',
            recommended: 'stylistic',
        },
        messages: {
            preferRecord: 'A record is preferred over an index signature.',
            preferIndexSignature: 'An index signature is preferred over a record.',
        },
        fixable: 'code',
        schema: [
            {
                type: 'string',
                enum: ['record', 'index-signature'],
            },
        ],
    },
    defaultOptions: ['record'],
    create(context, [mode]) {
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        function checkMembers(members, node, parentId, prefix, postfix, safeFix = true) {
            if (members.length !== 1) {
                return;
            }
            const [member] = members;
            if (member.type !== utils_1.AST_NODE_TYPES.TSIndexSignature) {
                return;
            }
            const parameter = member.parameters.at(0);
            if (parameter?.type !== utils_1.AST_NODE_TYPES.Identifier) {
                return;
            }
            const keyType = parameter.typeAnnotation;
            if (!keyType) {
                return;
            }
            const valueType = member.typeAnnotation;
            if (!valueType) {
                return;
            }
            if (parentId) {
                const scope = (0, eslint_utils_1.getScope)(context);
                const superVar = utils_1.ASTUtils.findVariable(scope, parentId.name);
                if (superVar) {
                    const isCircular = superVar.references.some(item => item.isTypeReference &&
                        node.range[0] <= item.identifier.range[0] &&
                        node.range[1] >= item.identifier.range[1]);
                    if (isCircular) {
                        return;
                    }
                }
            }
            context.report({
                node,
                messageId: 'preferRecord',
                fix: safeFix
                    ? (fixer) => {
                        const key = sourceCode.getText(keyType.typeAnnotation);
                        const value = sourceCode.getText(valueType.typeAnnotation);
                        const record = member.readonly
                            ? `Readonly<Record<${key}, ${value}>>`
                            : `Record<${key}, ${value}>`;
                        return fixer.replaceText(node, `${prefix}${record}${postfix}`);
                    }
                    : null,
            });
        }
        return {
            ...(mode === 'index-signature' && {
                TSTypeReference(node) {
                    const typeName = node.typeName;
                    if (typeName.type !== utils_1.AST_NODE_TYPES.Identifier) {
                        return;
                    }
                    if (typeName.name !== 'Record') {
                        return;
                    }
                    const params = node.typeArguments?.params;
                    if (params?.length !== 2) {
                        return;
                    }
                    context.report({
                        node,
                        messageId: 'preferIndexSignature',
                        fix(fixer) {
                            const key = sourceCode.getText(params[0]);
                            const type = sourceCode.getText(params[1]);
                            return fixer.replaceText(node, `{ [key: ${key}]: ${type} }`);
                        },
                    });
                },
            }),
            ...(mode === 'record' && {
                TSTypeLiteral(node) {
                    const parent = findParentDeclaration(node);
                    checkMembers(node.members, node, parent?.id, '', '');
                },
                TSInterfaceDeclaration(node) {
                    let genericTypes = '';
                    if (node.typeParameters?.params.length) {
                        genericTypes = `<${node.typeParameters.params
                            .map(p => sourceCode.getText(p))
                            .join(', ')}>`;
                    }
                    checkMembers(node.body.body, node, node.id, `type ${node.id.name}${genericTypes} = `, ';', !node.extends.length);
                },
            }),
        };
    },
});
function findParentDeclaration(node) {
    if (node.parent && node.parent.type !== utils_1.AST_NODE_TYPES.TSTypeAnnotation) {
        if (node.parent.type === utils_1.AST_NODE_TYPES.TSTypeAliasDeclaration) {
            return node.parent;
        }
        return findParentDeclaration(node.parent);
    }
    return undefined;
}
//# sourceMappingURL=consistent-indexed-object-style.js.map