"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.defaultMinimumDescriptionLength = void 0;
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
exports.defaultMinimumDescriptionLength = 3;
exports.default = (0, util_1.createRule)({
    name: 'ban-ts-comment',
    meta: {
        type: 'problem',
        docs: {
            description: 'Disallow `@ts-<directive>` comments or require descriptions after directives',
            recommended: 'recommended',
        },
        messages: {
            tsDirectiveComment: 'Do not use "@ts-{{directive}}" because it alters compilation errors.',
            tsIgnoreInsteadOfExpectError: 'Use "@ts-expect-error" instead of "@ts-ignore", as "@ts-ignore" will do nothing if the following line is error-free.',
            tsDirectiveCommentRequiresDescription: 'Include a description after the "@ts-{{directive}}" directive to explain why the @ts-{{directive}} is necessary. The description must be {{minimumDescriptionLength}} characters or longer.',
            tsDirectiveCommentDescriptionNotMatchPattern: 'The description for the "@ts-{{directive}}" directive must match the {{format}} format.',
            replaceTsIgnoreWithTsExpectError: 'Replace "@ts-ignore" with "@ts-expect-error".',
        },
        hasSuggestions: true,
        schema: [
            {
                $defs: {
                    directiveConfigSchema: {
                        oneOf: [
                            {
                                type: 'boolean',
                                default: true,
                            },
                            {
                                type: 'string',
                                enum: ['allow-with-description'],
                            },
                            {
                                type: 'object',
                                additionalProperties: false,
                                properties: {
                                    descriptionFormat: { type: 'string' },
                                },
                            },
                        ],
                    },
                },
                properties: {
                    'ts-expect-error': { $ref: '#/items/0/$defs/directiveConfigSchema' },
                    'ts-ignore': { $ref: '#/items/0/$defs/directiveConfigSchema' },
                    'ts-nocheck': { $ref: '#/items/0/$defs/directiveConfigSchema' },
                    'ts-check': { $ref: '#/items/0/$defs/directiveConfigSchema' },
                    minimumDescriptionLength: {
                        type: 'number',
                        default: exports.defaultMinimumDescriptionLength,
                    },
                },
                type: 'object',
                additionalProperties: false,
            },
        ],
    },
    defaultOptions: [
        {
            'ts-expect-error': 'allow-with-description',
            'ts-ignore': true,
            'ts-nocheck': true,
            'ts-check': false,
            minimumDescriptionLength: exports.defaultMinimumDescriptionLength,
        },
    ],
    create(context, [options]) {
        /*
          The regex used are taken from the ones used in the official TypeScript repo -
          https://github.com/microsoft/TypeScript/blob/408c760fae66080104bc85c449282c2d207dfe8e/src/compiler/scanner.ts#L288-L296
        */
        const commentDirectiveRegExSingleLine = /^\/*\s*@ts-(?<directive>expect-error|ignore|check|nocheck)(?<description>.*)/;
        const commentDirectiveRegExMultiLine = /^\s*(?:\/|\*)*\s*@ts-(?<directive>expect-error|ignore|check|nocheck)(?<description>.*)/;
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        const descriptionFormats = new Map();
        for (const directive of [
            'ts-expect-error',
            'ts-ignore',
            'ts-nocheck',
            'ts-check',
        ]) {
            const option = options[directive];
            if (typeof option === 'object' && option.descriptionFormat) {
                descriptionFormats.set(directive, new RegExp(option.descriptionFormat));
            }
        }
        return {
            Program() {
                const comments = sourceCode.getAllComments();
                comments.forEach(comment => {
                    const regExp = comment.type === utils_1.AST_TOKEN_TYPES.Line
                        ? commentDirectiveRegExSingleLine
                        : commentDirectiveRegExMultiLine;
                    const match = regExp.exec(comment.value);
                    if (!match) {
                        return;
                    }
                    const { directive, description } = match.groups;
                    const fullDirective = `ts-${directive}`;
                    const option = options[fullDirective];
                    if (option === true) {
                        if (directive === 'ignore') {
                            // Special case to suggest @ts-expect-error instead of @ts-ignore
                            context.report({
                                node: comment,
                                messageId: 'tsIgnoreInsteadOfExpectError',
                                suggest: [
                                    {
                                        messageId: 'replaceTsIgnoreWithTsExpectError',
                                        fix(fixer) {
                                            const commentText = comment.value.replace(/@ts-ignore/, '@ts-expect-error');
                                            return fixer.replaceText(comment, comment.type === utils_1.AST_TOKEN_TYPES.Line
                                                ? `//${commentText}`
                                                : `/*${commentText}*/`);
                                        },
                                    },
                                ],
                            });
                        }
                        else {
                            context.report({
                                data: { directive },
                                node: comment,
                                messageId: 'tsDirectiveComment',
                            });
                        }
                    }
                    if (option === 'allow-with-description' ||
                        (typeof option === 'object' && option.descriptionFormat)) {
                        const { minimumDescriptionLength = exports.defaultMinimumDescriptionLength, } = options;
                        const format = descriptionFormats.get(fullDirective);
                        if ((0, util_1.getStringLength)(description.trim()) < minimumDescriptionLength) {
                            context.report({
                                data: { directive, minimumDescriptionLength },
                                node: comment,
                                messageId: 'tsDirectiveCommentRequiresDescription',
                            });
                        }
                        else if (format && !format.test(description)) {
                            context.report({
                                data: { directive, format: format.source },
                                node: comment,
                                messageId: 'tsDirectiveCommentDescriptionNotMatchPattern',
                            });
                        }
                    }
                });
            },
        };
    },
});
//# sourceMappingURL=ban-ts-comment.js.map