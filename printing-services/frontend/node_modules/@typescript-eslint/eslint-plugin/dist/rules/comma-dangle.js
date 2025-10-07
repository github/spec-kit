"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
const getESLintCoreRule_1 = require("../util/getESLintCoreRule");
const baseRule = (0, getESLintCoreRule_1.getESLintCoreRule)('comma-dangle');
const OPTION_VALUE_SCHEME = [
    'always-multiline',
    'always',
    'never',
    'only-multiline',
];
const DEFAULT_OPTION_VALUE = 'never';
function normalizeOptions(options) {
    if (typeof options === 'string') {
        return {
            enums: options,
            generics: options,
            tuples: options,
        };
    }
    return {
        enums: options.enums ?? DEFAULT_OPTION_VALUE,
        generics: options.generics ?? DEFAULT_OPTION_VALUE,
        tuples: options.tuples ?? DEFAULT_OPTION_VALUE,
    };
}
exports.default = (0, util_1.createRule)({
    name: 'comma-dangle',
    meta: {
        deprecated: true,
        replacedBy: ['@stylistic/ts/comma-dangle'],
        type: 'layout',
        docs: {
            description: 'Require or disallow trailing commas',
            extendsBaseRule: true,
        },
        schema: {
            $defs: {
                value: {
                    type: 'string',
                    enum: OPTION_VALUE_SCHEME,
                },
                valueWithIgnore: {
                    type: 'string',
                    enum: [...OPTION_VALUE_SCHEME, 'ignore'],
                },
            },
            type: 'array',
            items: [
                {
                    oneOf: [
                        {
                            $ref: '#/$defs/value',
                        },
                        {
                            type: 'object',
                            properties: {
                                arrays: { $ref: '#/$defs/valueWithIgnore' },
                                objects: { $ref: '#/$defs/valueWithIgnore' },
                                imports: { $ref: '#/$defs/valueWithIgnore' },
                                exports: { $ref: '#/$defs/valueWithIgnore' },
                                functions: { $ref: '#/$defs/valueWithIgnore' },
                                enums: { $ref: '#/$defs/valueWithIgnore' },
                                generics: { $ref: '#/$defs/valueWithIgnore' },
                                tuples: { $ref: '#/$defs/valueWithIgnore' },
                            },
                            additionalProperties: false,
                        },
                    ],
                },
            ],
            additionalItems: false,
        },
        fixable: 'code',
        hasSuggestions: baseRule.meta.hasSuggestions,
        messages: baseRule.meta.messages,
    },
    defaultOptions: ['never'],
    create(context, [options]) {
        const rules = baseRule.create(context);
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        const normalizedOptions = normalizeOptions(options);
        const predicate = {
            always: forceComma,
            'always-multiline': forceCommaIfMultiline,
            'only-multiline': allowCommaIfMultiline,
            never: forbidComma,
            // https://github.com/typescript-eslint/typescript-eslint/issues/7220
            // eslint-disable-next-line @typescript-eslint/explicit-function-return-type, @typescript-eslint/no-empty-function
            ignore: () => { },
        };
        function last(nodes) {
            return nodes[nodes.length - 1] ?? null;
        }
        function getLastItem(node) {
            switch (node.type) {
                case utils_1.AST_NODE_TYPES.TSEnumDeclaration:
                    return last(node.members);
                case utils_1.AST_NODE_TYPES.TSTypeParameterDeclaration:
                    return last(node.params);
                case utils_1.AST_NODE_TYPES.TSTupleType:
                    return last(node.elementTypes);
                default:
                    return null;
            }
        }
        function getTrailingToken(node) {
            const last = getLastItem(node);
            const trailing = last && sourceCode.getTokenAfter(last);
            return trailing;
        }
        function isMultiline(node) {
            const last = getLastItem(node);
            const lastToken = sourceCode.getLastToken(node);
            return last?.loc.end.line !== lastToken?.loc.end.line;
        }
        function forbidComma(node) {
            const last = getLastItem(node);
            const trailing = getTrailingToken(node);
            if (last && trailing && (0, util_1.isCommaToken)(trailing)) {
                context.report({
                    node,
                    messageId: 'unexpected',
                    fix(fixer) {
                        return fixer.remove(trailing);
                    },
                });
            }
        }
        function forceComma(node) {
            const last = getLastItem(node);
            const trailing = getTrailingToken(node);
            if (last && trailing && !(0, util_1.isCommaToken)(trailing)) {
                context.report({
                    node,
                    messageId: 'missing',
                    fix(fixer) {
                        return fixer.insertTextAfter(last, ',');
                    },
                });
            }
        }
        function allowCommaIfMultiline(node) {
            if (!isMultiline(node)) {
                forbidComma(node);
            }
        }
        function forceCommaIfMultiline(node) {
            if (isMultiline(node)) {
                forceComma(node);
            }
            else {
                forbidComma(node);
            }
        }
        return {
            ...rules,
            TSEnumDeclaration: predicate[normalizedOptions.enums],
            TSTypeParameterDeclaration: predicate[normalizedOptions.generics],
            TSTupleType: predicate[normalizedOptions.tuples],
        };
    },
});
//# sourceMappingURL=comma-dangle.js.map