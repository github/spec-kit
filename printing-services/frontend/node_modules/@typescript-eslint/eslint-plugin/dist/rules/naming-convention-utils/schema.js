"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SCHEMA = void 0;
const util_1 = require("../../util");
const enums_1 = require("./enums");
const $DEFS = {
    // enums
    underscoreOptions: {
        type: 'string',
        enum: (0, util_1.getEnumNames)(enums_1.UnderscoreOptions),
    },
    predefinedFormats: {
        type: 'string',
        enum: (0, util_1.getEnumNames)(enums_1.PredefinedFormats),
    },
    typeModifiers: {
        type: 'string',
        enum: (0, util_1.getEnumNames)(enums_1.TypeModifiers),
    },
    // repeated types
    prefixSuffixConfig: {
        type: 'array',
        items: {
            type: 'string',
            minLength: 1,
        },
        additionalItems: false,
    },
    matchRegexConfig: {
        type: 'object',
        additionalProperties: false,
        properties: {
            match: { type: 'boolean' },
            regex: { type: 'string' },
        },
        required: ['match', 'regex'],
    },
    formatOptionsConfig: {
        oneOf: [
            {
                type: 'array',
                items: {
                    $ref: '#/$defs/predefinedFormats',
                },
                additionalItems: false,
            },
            {
                type: 'null',
            },
        ],
    },
};
const UNDERSCORE_SCHEMA = {
    $ref: '#/$defs/underscoreOptions',
};
const PREFIX_SUFFIX_SCHEMA = {
    $ref: '#/$defs/prefixSuffixConfig',
};
const MATCH_REGEX_SCHEMA = {
    $ref: '#/$defs/matchRegexConfig',
};
const FORMAT_OPTIONS_PROPERTIES = {
    format: {
        $ref: '#/$defs/formatOptionsConfig',
    },
    custom: MATCH_REGEX_SCHEMA,
    leadingUnderscore: UNDERSCORE_SCHEMA,
    trailingUnderscore: UNDERSCORE_SCHEMA,
    prefix: PREFIX_SUFFIX_SCHEMA,
    suffix: PREFIX_SUFFIX_SCHEMA,
    failureMessage: {
        type: 'string',
    },
};
function selectorSchema(selectorString, allowType, modifiers) {
    const selector = {
        filter: {
            oneOf: [
                {
                    type: 'string',
                    minLength: 1,
                },
                MATCH_REGEX_SCHEMA,
            ],
        },
        selector: {
            type: 'string',
            enum: [selectorString],
        },
    };
    if (modifiers && modifiers.length > 0) {
        selector.modifiers = {
            type: 'array',
            items: {
                type: 'string',
                enum: modifiers,
            },
            additionalItems: false,
        };
    }
    if (allowType) {
        selector.types = {
            type: 'array',
            items: {
                $ref: '#/$defs/typeModifiers',
            },
            additionalItems: false,
        };
    }
    return [
        {
            type: 'object',
            description: `Selector '${selectorString}'`,
            properties: {
                ...FORMAT_OPTIONS_PROPERTIES,
                ...selector,
            },
            required: ['selector', 'format'],
            additionalProperties: false,
        },
    ];
}
function selectorsSchema() {
    return {
        type: 'object',
        description: 'Multiple selectors in one config',
        properties: {
            ...FORMAT_OPTIONS_PROPERTIES,
            ...{
                filter: {
                    oneOf: [
                        {
                            type: 'string',
                            minLength: 1,
                        },
                        MATCH_REGEX_SCHEMA,
                    ],
                },
                selector: {
                    type: 'array',
                    items: {
                        type: 'string',
                        enum: [...(0, util_1.getEnumNames)(enums_1.MetaSelectors), ...(0, util_1.getEnumNames)(enums_1.Selectors)],
                    },
                    additionalItems: false,
                },
                modifiers: {
                    type: 'array',
                    items: {
                        type: 'string',
                        enum: (0, util_1.getEnumNames)(enums_1.Modifiers),
                    },
                    additionalItems: false,
                },
                types: {
                    type: 'array',
                    items: {
                        $ref: '#/$defs/typeModifiers',
                    },
                    additionalItems: false,
                },
            },
        },
        required: ['selector', 'format'],
        additionalProperties: false,
    };
}
const SCHEMA = {
    $defs: $DEFS,
    type: 'array',
    items: {
        oneOf: [
            selectorsSchema(),
            ...selectorSchema('default', false, (0, util_1.getEnumNames)(enums_1.Modifiers)),
            ...selectorSchema('variableLike', false, ['unused', 'async']),
            ...selectorSchema('variable', true, [
                'const',
                'destructured',
                'exported',
                'global',
                'unused',
                'async',
            ]),
            ...selectorSchema('function', false, [
                'exported',
                'global',
                'unused',
                'async',
            ]),
            ...selectorSchema('parameter', true, ['destructured', 'unused']),
            ...selectorSchema('memberLike', false, [
                'abstract',
                'private',
                '#private',
                'protected',
                'public',
                'readonly',
                'requiresQuotes',
                'static',
                'override',
                'async',
            ]),
            ...selectorSchema('classProperty', true, [
                'abstract',
                'private',
                '#private',
                'protected',
                'public',
                'readonly',
                'requiresQuotes',
                'static',
                'override',
            ]),
            ...selectorSchema('objectLiteralProperty', true, [
                'public',
                'requiresQuotes',
            ]),
            ...selectorSchema('typeProperty', true, [
                'public',
                'readonly',
                'requiresQuotes',
            ]),
            ...selectorSchema('parameterProperty', true, [
                'private',
                'protected',
                'public',
                'readonly',
            ]),
            ...selectorSchema('property', true, [
                'abstract',
                'private',
                '#private',
                'protected',
                'public',
                'readonly',
                'requiresQuotes',
                'static',
                'override',
                'async',
            ]),
            ...selectorSchema('classMethod', false, [
                'abstract',
                'private',
                '#private',
                'protected',
                'public',
                'requiresQuotes',
                'static',
                'override',
                'async',
            ]),
            ...selectorSchema('objectLiteralMethod', false, [
                'public',
                'requiresQuotes',
                'async',
            ]),
            ...selectorSchema('typeMethod', false, ['public', 'requiresQuotes']),
            ...selectorSchema('method', false, [
                'abstract',
                'private',
                '#private',
                'protected',
                'public',
                'requiresQuotes',
                'static',
                'override',
                'async',
            ]),
            ...selectorSchema('accessor', true, [
                'abstract',
                'private',
                'protected',
                'public',
                'requiresQuotes',
                'static',
                'override',
            ]),
            ...selectorSchema('enumMember', false, ['requiresQuotes']),
            ...selectorSchema('typeLike', false, ['abstract', 'exported', 'unused']),
            ...selectorSchema('class', false, ['abstract', 'exported', 'unused']),
            ...selectorSchema('interface', false, ['exported', 'unused']),
            ...selectorSchema('typeAlias', false, ['exported', 'unused']),
            ...selectorSchema('enum', false, ['exported', 'unused']),
            ...selectorSchema('typeParameter', false, ['unused']),
            ...selectorSchema('import', false, ['default', 'namespace']),
        ],
    },
    additionalItems: false,
};
exports.SCHEMA = SCHEMA;
//# sourceMappingURL=schema.js.map