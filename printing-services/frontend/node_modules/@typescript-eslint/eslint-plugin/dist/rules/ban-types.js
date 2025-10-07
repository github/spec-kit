"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TYPE_KEYWORDS = void 0;
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
function removeSpaces(str) {
    return str.replace(/\s/g, '');
}
function stringifyNode(node, sourceCode) {
    return removeSpaces(sourceCode.getText(node));
}
function getCustomMessage(bannedType) {
    if (bannedType == null || bannedType === true) {
        return '';
    }
    if (typeof bannedType === 'string') {
        return ` ${bannedType}`;
    }
    if (bannedType.message) {
        return ` ${bannedType.message}`;
    }
    return '';
}
const defaultTypes = {
    String: {
        message: 'Use string instead',
        fixWith: 'string',
    },
    Boolean: {
        message: 'Use boolean instead',
        fixWith: 'boolean',
    },
    Number: {
        message: 'Use number instead',
        fixWith: 'number',
    },
    Symbol: {
        message: 'Use symbol instead',
        fixWith: 'symbol',
    },
    BigInt: {
        message: 'Use bigint instead',
        fixWith: 'bigint',
    },
    Function: {
        message: [
            'The `Function` type accepts any function-like value.',
            'It provides no type safety when calling the function, which can be a common source of bugs.',
            'It also accepts things like class declarations, which will throw at runtime as they will not be called with `new`.',
            'If you are expecting the function to accept certain arguments, you should explicitly define the function shape.',
        ].join('\n'),
    },
    // object typing
    Object: {
        message: [
            'The `Object` type actually means "any non-nullish value", so it is marginally better than `unknown`.',
            '- If you want a type meaning "any object", you probably want `object` instead.',
            '- If you want a type meaning "any value", you probably want `unknown` instead.',
            '- If you really want a type meaning "any non-nullish value", you probably want `NonNullable<unknown>` instead.',
        ].join('\n'),
        suggest: ['object', 'unknown', 'NonNullable<unknown>'],
    },
    '{}': {
        message: [
            '`{}` actually means "any non-nullish value".',
            '- If you want a type meaning "any object", you probably want `object` instead.',
            '- If you want a type meaning "any value", you probably want `unknown` instead.',
            '- If you want a type meaning "empty object", you probably want `Record<string, never>` instead.',
            '- If you really want a type meaning "any non-nullish value", you probably want `NonNullable<unknown>` instead.',
        ].join('\n'),
        suggest: [
            'object',
            'unknown',
            'Record<string, never>',
            'NonNullable<unknown>',
        ],
    },
};
exports.TYPE_KEYWORDS = {
    bigint: utils_1.AST_NODE_TYPES.TSBigIntKeyword,
    boolean: utils_1.AST_NODE_TYPES.TSBooleanKeyword,
    never: utils_1.AST_NODE_TYPES.TSNeverKeyword,
    null: utils_1.AST_NODE_TYPES.TSNullKeyword,
    number: utils_1.AST_NODE_TYPES.TSNumberKeyword,
    object: utils_1.AST_NODE_TYPES.TSObjectKeyword,
    string: utils_1.AST_NODE_TYPES.TSStringKeyword,
    symbol: utils_1.AST_NODE_TYPES.TSSymbolKeyword,
    undefined: utils_1.AST_NODE_TYPES.TSUndefinedKeyword,
    unknown: utils_1.AST_NODE_TYPES.TSUnknownKeyword,
    void: utils_1.AST_NODE_TYPES.TSVoidKeyword,
};
exports.default = (0, util_1.createRule)({
    name: 'ban-types',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Disallow certain types',
            recommended: 'recommended',
        },
        fixable: 'code',
        hasSuggestions: true,
        messages: {
            bannedTypeMessage: "Don't use `{{name}}` as a type.{{customMessage}}",
            bannedTypeReplacement: 'Replace `{{name}}` with `{{replacement}}`.',
        },
        schema: [
            {
                $defs: {
                    banConfig: {
                        oneOf: [
                            {
                                type: 'null',
                                description: 'Bans the type with the default message',
                            },
                            {
                                type: 'boolean',
                                enum: [false],
                                description: 'Un-bans the type (useful when paired with `extendDefaults`)',
                            },
                            {
                                type: 'boolean',
                                enum: [true],
                                description: 'Bans the type with the default message',
                            },
                            {
                                type: 'string',
                                description: 'Bans the type with a custom message',
                            },
                            {
                                type: 'object',
                                description: 'Bans a type',
                                properties: {
                                    message: {
                                        type: 'string',
                                        description: 'Custom error message',
                                    },
                                    fixWith: {
                                        type: 'string',
                                        description: 'Type to autofix replace with. Note that autofixers can be applied automatically - so you need to be careful with this option.',
                                    },
                                    suggest: {
                                        type: 'array',
                                        items: { type: 'string' },
                                        description: 'Types to suggest replacing with.',
                                        additionalItems: false,
                                    },
                                },
                                additionalProperties: false,
                            },
                        ],
                    },
                },
                type: 'object',
                properties: {
                    types: {
                        type: 'object',
                        additionalProperties: {
                            $ref: '#/items/0/$defs/banConfig',
                        },
                    },
                    extendDefaults: {
                        type: 'boolean',
                    },
                },
                additionalProperties: false,
            },
        ],
    },
    defaultOptions: [{}],
    create(context, [options]) {
        const extendDefaults = options.extendDefaults ?? true;
        const customTypes = options.types ?? {};
        const types = Object.assign({}, extendDefaults ? defaultTypes : {}, customTypes);
        const bannedTypes = new Map(Object.entries(types).map(([type, data]) => [removeSpaces(type), data]));
        function checkBannedTypes(typeNode, name = stringifyNode(typeNode, (0, eslint_utils_1.getSourceCode)(context))) {
            const bannedType = bannedTypes.get(name);
            if (bannedType === undefined || bannedType === false) {
                return;
            }
            const customMessage = getCustomMessage(bannedType);
            const fixWith = bannedType && typeof bannedType === 'object' && bannedType.fixWith;
            const suggest = bannedType && typeof bannedType === 'object'
                ? bannedType.suggest
                : undefined;
            context.report({
                node: typeNode,
                messageId: 'bannedTypeMessage',
                data: {
                    name,
                    customMessage,
                },
                fix: fixWith
                    ? (fixer) => fixer.replaceText(typeNode, fixWith)
                    : null,
                suggest: suggest?.map(replacement => ({
                    messageId: 'bannedTypeReplacement',
                    data: {
                        name,
                        replacement,
                    },
                    fix: (fixer) => fixer.replaceText(typeNode, replacement),
                })),
            });
        }
        const keywordSelectors = (0, util_1.objectReduceKey)(exports.TYPE_KEYWORDS, (acc, keyword) => {
            if (bannedTypes.has(keyword)) {
                acc[exports.TYPE_KEYWORDS[keyword]] = (node) => checkBannedTypes(node, keyword);
            }
            return acc;
        }, {});
        return {
            ...keywordSelectors,
            TSTypeLiteral(node) {
                if (node.members.length) {
                    return;
                }
                checkBannedTypes(node);
            },
            TSTupleType(node) {
                if (node.elementTypes.length === 0) {
                    checkBannedTypes(node);
                }
            },
            TSTypeReference(node) {
                checkBannedTypes(node.typeName);
                if (node.typeArguments) {
                    checkBannedTypes(node);
                }
            },
            TSInterfaceHeritage(node) {
                checkBannedTypes(node);
            },
            TSClassImplements(node) {
                checkBannedTypes(node);
            },
        };
    },
});
//# sourceMappingURL=ban-types.js.map