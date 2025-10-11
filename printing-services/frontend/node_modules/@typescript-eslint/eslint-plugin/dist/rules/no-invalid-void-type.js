"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'no-invalid-void-type',
    meta: {
        type: 'problem',
        docs: {
            description: 'Disallow `void` type outside of generic or return types',
            recommended: 'strict',
        },
        messages: {
            invalidVoidForGeneric: '{{ generic }} may not have void as a type argument.',
            invalidVoidNotReturnOrGeneric: 'void is only valid as a return type or generic type argument.',
            invalidVoidNotReturn: 'void is only valid as a return type.',
            invalidVoidNotReturnOrThisParam: 'void is only valid as return type or type of `this` parameter.',
            invalidVoidNotReturnOrThisParamOrGeneric: 'void is only valid as a return type or generic type argument or the type of a `this` parameter.',
            invalidVoidUnionConstituent: 'void is not valid as a constituent in a union type',
        },
        schema: [
            {
                type: 'object',
                properties: {
                    allowInGenericTypeArguments: {
                        oneOf: [
                            { type: 'boolean' },
                            {
                                type: 'array',
                                items: { type: 'string' },
                                minItems: 1,
                            },
                        ],
                    },
                    allowAsThisParameter: {
                        type: 'boolean',
                    },
                },
                additionalProperties: false,
            },
        ],
    },
    defaultOptions: [
        { allowInGenericTypeArguments: true, allowAsThisParameter: false },
    ],
    create(context, [{ allowInGenericTypeArguments, allowAsThisParameter }]) {
        const validParents = [
            utils_1.AST_NODE_TYPES.TSTypeAnnotation, //
        ];
        const invalidGrandParents = [
            utils_1.AST_NODE_TYPES.TSPropertySignature,
            utils_1.AST_NODE_TYPES.CallExpression,
            utils_1.AST_NODE_TYPES.PropertyDefinition,
            utils_1.AST_NODE_TYPES.Identifier,
        ];
        const validUnionMembers = [
            utils_1.AST_NODE_TYPES.TSVoidKeyword,
            utils_1.AST_NODE_TYPES.TSNeverKeyword,
        ];
        if (allowInGenericTypeArguments === true) {
            validParents.push(utils_1.AST_NODE_TYPES.TSTypeParameterInstantiation);
        }
        /**
         * @brief check if the given void keyword is used as a valid generic type
         *
         * reports if the type parametrized by void is not in the whitelist, or
         * allowInGenericTypeArguments is false.
         * no-op if the given void keyword is not used as generic type
         */
        function checkGenericTypeArgument(node) {
            // only matches T<..., void, ...>
            // extra check for precaution
            /* istanbul ignore next */
            if (node.parent.type !== utils_1.AST_NODE_TYPES.TSTypeParameterInstantiation ||
                node.parent.parent.type !== utils_1.AST_NODE_TYPES.TSTypeReference) {
                return;
            }
            // check whitelist
            if (Array.isArray(allowInGenericTypeArguments)) {
                const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
                const fullyQualifiedName = sourceCode
                    .getText(node.parent.parent.typeName)
                    .replace(/ /gu, '');
                if (!allowInGenericTypeArguments
                    .map(s => s.replace(/ /gu, ''))
                    .includes(fullyQualifiedName)) {
                    context.report({
                        messageId: 'invalidVoidForGeneric',
                        data: { generic: fullyQualifiedName },
                        node,
                    });
                }
                return;
            }
            if (!allowInGenericTypeArguments) {
                context.report({
                    messageId: allowAsThisParameter
                        ? 'invalidVoidNotReturnOrThisParam'
                        : 'invalidVoidNotReturn',
                    node,
                });
            }
        }
        /**
         * @brief checks if the generic type parameter defaults to void
         */
        function checkDefaultVoid(node, parentNode) {
            if (parentNode.default !== node) {
                context.report({
                    messageId: getNotReturnOrGenericMessageId(node),
                    node,
                });
            }
        }
        /**
         * @brief checks that a union containing void is valid
         * @return true if every member of the union is specified as a valid type in
         * validUnionMembers, or is a valid generic type parametrized by void
         */
        function isValidUnionType(node) {
            return node.types.every(member => validUnionMembers.includes(member.type) ||
                // allows any T<..., void, ...> here, checked by checkGenericTypeArgument
                (member.type === utils_1.AST_NODE_TYPES.TSTypeReference &&
                    member.typeArguments?.type ===
                        utils_1.AST_NODE_TYPES.TSTypeParameterInstantiation &&
                    member.typeArguments.params
                        .map(param => param.type)
                        .includes(utils_1.AST_NODE_TYPES.TSVoidKeyword)));
        }
        return {
            TSVoidKeyword(node) {
                // checks T<..., void, ...> against specification of allowInGenericArguments option
                if (node.parent.type === utils_1.AST_NODE_TYPES.TSTypeParameterInstantiation &&
                    node.parent.parent.type === utils_1.AST_NODE_TYPES.TSTypeReference) {
                    checkGenericTypeArgument(node);
                    return;
                }
                // allow <T = void> if allowInGenericTypeArguments is specified, and report if the generic type parameter extends void
                if (allowInGenericTypeArguments &&
                    node.parent.type === utils_1.AST_NODE_TYPES.TSTypeParameter &&
                    node.parent.default?.type === utils_1.AST_NODE_TYPES.TSVoidKeyword) {
                    checkDefaultVoid(node, node.parent);
                    return;
                }
                // union w/ void must contain types from validUnionMembers, or a valid generic void type
                if (node.parent.type === utils_1.AST_NODE_TYPES.TSUnionType &&
                    isValidUnionType(node.parent)) {
                    return;
                }
                // this parameter is ok to be void.
                if (allowAsThisParameter &&
                    node.parent.type === utils_1.AST_NODE_TYPES.TSTypeAnnotation &&
                    node.parent.parent.type === utils_1.AST_NODE_TYPES.Identifier &&
                    node.parent.parent.name === 'this') {
                    return;
                }
                // default cases
                if (validParents.includes(node.parent.type) &&
                    !invalidGrandParents.includes(node.parent.parent.type)) {
                    return;
                }
                context.report({
                    messageId: allowInGenericTypeArguments && allowAsThisParameter
                        ? 'invalidVoidNotReturnOrThisParamOrGeneric'
                        : allowInGenericTypeArguments
                            ? getNotReturnOrGenericMessageId(node)
                            : allowAsThisParameter
                                ? 'invalidVoidNotReturnOrThisParam'
                                : 'invalidVoidNotReturn',
                    node,
                });
            },
        };
    },
});
function getNotReturnOrGenericMessageId(node) {
    return node.parent.type === utils_1.AST_NODE_TYPES.TSUnionType
        ? 'invalidVoidUnionConstituent'
        : 'invalidVoidNotReturnOrGeneric';
}
//# sourceMappingURL=no-invalid-void-type.js.map