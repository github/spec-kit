"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
const isLastTokenEndOfLine = (token, line) => {
    const positionInLine = token.loc.start.column;
    return positionInLine === line.length - 1;
};
const isCommentsEndOfLine = (token, comments, line) => {
    if (!comments) {
        return false;
    }
    if (comments.loc.end.line > token.loc.end.line) {
        return true;
    }
    const positionInLine = comments.loc.end.column;
    return positionInLine === line.length;
};
const makeFixFunction = ({ optsNone, optsSemi, lastToken, commentsAfterLastToken, missingDelimiter, lastTokenLine, isSingleLine, }) => {
    // if removing is the action but last token is not the end of the line
    if (optsNone &&
        !isLastTokenEndOfLine(lastToken, lastTokenLine) &&
        !isCommentsEndOfLine(lastToken, commentsAfterLastToken, lastTokenLine) &&
        !isSingleLine) {
        return null;
    }
    return (fixer) => {
        if (optsNone) {
            // remove the unneeded token
            return fixer.remove(lastToken);
        }
        const token = optsSemi ? ';' : ',';
        if (missingDelimiter) {
            // add the missing delimiter
            return fixer.insertTextAfter(lastToken, token);
        }
        // correct the current delimiter
        return fixer.replaceText(lastToken, token);
    };
};
const BASE_SCHEMA = {
    type: 'object',
    properties: {
        multiline: {
            type: 'object',
            properties: {
                delimiter: { $ref: '#/items/0/$defs/multiLineOption' },
                requireLast: { type: 'boolean' },
            },
            additionalProperties: false,
        },
        singleline: {
            type: 'object',
            properties: {
                delimiter: { $ref: '#/items/0/$defs/singleLineOption' },
                requireLast: { type: 'boolean' },
            },
            additionalProperties: false,
        },
    },
    additionalProperties: false,
};
exports.default = (0, util_1.createRule)({
    name: 'member-delimiter-style',
    meta: {
        deprecated: true,
        replacedBy: ['@stylistic/ts/member-delimiter-style'],
        type: 'layout',
        docs: {
            description: 'Require a specific member delimiter style for interfaces and type literals',
        },
        fixable: 'whitespace',
        messages: {
            unexpectedComma: 'Unexpected separator (,).',
            unexpectedSemi: 'Unexpected separator (;).',
            expectedComma: 'Expected a comma.',
            expectedSemi: 'Expected a semicolon.',
        },
        schema: [
            {
                $defs: {
                    multiLineOption: {
                        type: 'string',
                        enum: ['none', 'semi', 'comma'],
                    },
                    // note can't have "none" for single line delimiter as it's invalid syntax
                    singleLineOption: {
                        type: 'string',
                        enum: ['semi', 'comma'],
                    },
                    // note - need to define this last as it references the enums
                    delimiterConfig: BASE_SCHEMA,
                },
                type: 'object',
                properties: {
                    ...BASE_SCHEMA.properties,
                    overrides: {
                        type: 'object',
                        properties: {
                            interface: {
                                $ref: '#/items/0/$defs/delimiterConfig',
                            },
                            typeLiteral: {
                                $ref: '#/items/0/$defs/delimiterConfig',
                            },
                        },
                        additionalProperties: false,
                    },
                    multilineDetection: {
                        type: 'string',
                        enum: ['brackets', 'last-member'],
                    },
                },
                additionalProperties: false,
            },
        ],
    },
    defaultOptions: [
        {
            multiline: {
                delimiter: 'semi',
                requireLast: true,
            },
            singleline: {
                delimiter: 'semi',
                requireLast: false,
            },
            multilineDetection: 'brackets',
        },
    ],
    create(context, [options]) {
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        // use the base options as the defaults for the cases
        const baseOptions = options;
        const overrides = baseOptions.overrides ?? {};
        const interfaceOptions = (0, util_1.deepMerge)(baseOptions, overrides.interface);
        const typeLiteralOptions = (0, util_1.deepMerge)(baseOptions, overrides.typeLiteral);
        /**
         * Check the last token in the given member.
         * @param member the member to be evaluated.
         * @param opts the options to be validated.
         * @param isLast a flag indicating `member` is the last in the interface or type literal.
         */
        function checkLastToken(member, opts, isLast) {
            /**
             * Resolves the boolean value for the given setting enum value
             * @param type the option name
             */
            function getOption(type) {
                if (isLast && !opts.requireLast) {
                    // only turn the option on if its expecting no delimiter for the last member
                    return type === 'none';
                }
                return opts.delimiter === type;
            }
            let messageId = null;
            let missingDelimiter = false;
            const lastToken = sourceCode.getLastToken(member, {
                includeComments: false,
            });
            if (!lastToken) {
                return;
            }
            const commentsAfterLastToken = sourceCode
                .getCommentsAfter(lastToken)
                .pop();
            const sourceCodeLines = sourceCode.getLines();
            const lastTokenLine = sourceCodeLines[lastToken.loc.start.line - 1];
            const optsSemi = getOption('semi');
            const optsComma = getOption('comma');
            const optsNone = getOption('none');
            if (lastToken.value === ';') {
                if (optsComma) {
                    messageId = 'expectedComma';
                }
                else if (optsNone) {
                    missingDelimiter = true;
                    messageId = 'unexpectedSemi';
                }
            }
            else if (lastToken.value === ',') {
                if (optsSemi) {
                    messageId = 'expectedSemi';
                }
                else if (optsNone) {
                    missingDelimiter = true;
                    messageId = 'unexpectedComma';
                }
            }
            else {
                if (optsSemi) {
                    missingDelimiter = true;
                    messageId = 'expectedSemi';
                }
                else if (optsComma) {
                    missingDelimiter = true;
                    messageId = 'expectedComma';
                }
            }
            if (messageId) {
                context.report({
                    node: lastToken,
                    loc: {
                        start: {
                            line: lastToken.loc.end.line,
                            column: lastToken.loc.end.column,
                        },
                        end: {
                            line: lastToken.loc.end.line,
                            column: lastToken.loc.end.column,
                        },
                    },
                    messageId,
                    fix: makeFixFunction({
                        optsNone,
                        optsSemi,
                        lastToken,
                        commentsAfterLastToken,
                        missingDelimiter,
                        lastTokenLine,
                        isSingleLine: opts.type === 'single-line',
                    }),
                });
            }
        }
        /**
         * Check the member separator being used matches the delimiter.
         * @param node the node to be evaluated.
         */
        function checkMemberSeparatorStyle(node) {
            const members = node.type === utils_1.AST_NODE_TYPES.TSInterfaceBody ? node.body : node.members;
            let isSingleLine = node.loc.start.line === node.loc.end.line;
            if (options.multilineDetection === 'last-member' &&
                !isSingleLine &&
                members.length > 0) {
                const lastMember = members[members.length - 1];
                if (lastMember.loc.end.line === node.loc.end.line) {
                    isSingleLine = true;
                }
            }
            const typeOpts = node.type === utils_1.AST_NODE_TYPES.TSInterfaceBody
                ? interfaceOptions
                : typeLiteralOptions;
            const opts = isSingleLine
                ? { ...typeOpts.singleline, type: 'single-line' }
                : { ...typeOpts.multiline, type: 'multi-line' };
            members.forEach((member, index) => {
                checkLastToken(member, opts, index === members.length - 1);
            });
        }
        return {
            TSInterfaceBody: checkMemberSeparatorStyle,
            TSTypeLiteral: checkMemberSeparatorStyle,
        };
    },
});
//# sourceMappingURL=member-delimiter-style.js.map