"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
const getESLintCoreRule_1 = require("../util/getESLintCoreRule");
const baseRule = (0, getESLintCoreRule_1.getESLintCoreRule)('keyword-spacing');
// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
const baseSchema = Array.isArray(baseRule.meta.schema)
    ? baseRule.meta.schema[0]
    : baseRule.meta.schema;
const schema = (0, util_1.deepMerge)(
// eslint-disable-next-line @typescript-eslint/no-unsafe-argument -- https://github.com/microsoft/TypeScript/issues/17002
baseSchema, {
    properties: {
        overrides: {
            properties: {
                // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
                type: baseSchema.properties.overrides.properties.import,
            },
        },
    },
});
exports.default = (0, util_1.createRule)({
    name: 'keyword-spacing',
    meta: {
        deprecated: true,
        replacedBy: ['@stylistic/ts/keyword-spacing'],
        type: 'layout',
        docs: {
            description: 'Enforce consistent spacing before and after keywords',
            extendsBaseRule: true,
        },
        fixable: 'whitespace',
        hasSuggestions: baseRule.meta.hasSuggestions,
        schema: [schema],
        messages: baseRule.meta.messages,
    },
    defaultOptions: [{}],
    create(context, [{ after, overrides }]) {
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        const baseRules = baseRule.create(context);
        return {
            ...baseRules,
            TSAsExpression(node) {
                const asToken = (0, util_1.nullThrows)(sourceCode.getTokenAfter(node.expression, token => token.value === 'as'), util_1.NullThrowsReasons.MissingToken('as', node.type));
                const oldTokenType = asToken.type;
                // as is a contextual keyword, so it's always reported as an Identifier
                // the rule looks for keyword tokens, so we temporarily override it
                // we mutate it at the token level because the rule calls sourceCode.getFirstToken,
                // so mutating a copy would not change the underlying copy returned by that method
                asToken.type = utils_1.AST_TOKEN_TYPES.Keyword;
                // use this selector just because it is just a call to `checkSpacingAroundFirstToken`
                baseRules.DebuggerStatement(asToken);
                // make sure to reset the type afterward so we don't permanently mutate the AST
                asToken.type = oldTokenType;
            },
            'ImportDeclaration[importKind=type]'(node) {
                const { type: typeOptionOverride = {} } = overrides ?? {};
                const typeToken = sourceCode.getFirstToken(node, { skip: 1 });
                const punctuatorToken = sourceCode.getTokenAfter(typeToken);
                if (node.specifiers[0]?.type === utils_1.AST_NODE_TYPES.ImportDefaultSpecifier) {
                    return;
                }
                const spacesBetweenTypeAndPunctuator = punctuatorToken.range[0] - typeToken.range[1];
                if ((typeOptionOverride.after ?? after) === true &&
                    spacesBetweenTypeAndPunctuator === 0) {
                    context.report({
                        loc: typeToken.loc,
                        messageId: 'expectedAfter',
                        data: { value: 'type' },
                        fix(fixer) {
                            return fixer.insertTextAfter(typeToken, ' ');
                        },
                    });
                }
                if ((typeOptionOverride.after ?? after) === false &&
                    spacesBetweenTypeAndPunctuator > 0) {
                    context.report({
                        loc: typeToken.loc,
                        messageId: 'unexpectedAfter',
                        data: { value: 'type' },
                        fix(fixer) {
                            return fixer.removeRange([
                                typeToken.range[1],
                                typeToken.range[1] + spacesBetweenTypeAndPunctuator,
                            ]);
                        },
                    });
                }
            },
        };
    },
});
//# sourceMappingURL=keyword-spacing.js.map