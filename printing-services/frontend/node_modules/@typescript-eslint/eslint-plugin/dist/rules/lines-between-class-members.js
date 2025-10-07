"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const util_1 = require("../util");
const getESLintCoreRule_1 = require("../util/getESLintCoreRule");
const baseRule = (0, getESLintCoreRule_1.getESLintCoreRule)('lines-between-class-members');
const schema = Object.values((0, util_1.deepMerge)({ ...baseRule.meta.schema }, {
    1: {
        properties: {
            exceptAfterOverload: {
                type: 'boolean',
                default: true,
            },
        },
    },
}));
exports.default = (0, util_1.createRule)({
    name: 'lines-between-class-members',
    meta: {
        deprecated: true,
        replacedBy: ['@stylistic/ts/lines-between-class-members'],
        type: 'layout',
        docs: {
            description: 'Require or disallow an empty line between class members',
            extendsBaseRule: true,
        },
        fixable: 'whitespace',
        hasSuggestions: baseRule.meta.hasSuggestions,
        schema,
        messages: baseRule.meta.messages,
    },
    defaultOptions: [
        'always',
        {
            exceptAfterOverload: true,
            exceptAfterSingleLine: false,
        },
    ],
    create(context, [firstOption, secondOption]) {
        const rules = baseRule.create(context);
        const exceptAfterOverload = secondOption?.exceptAfterOverload && firstOption === 'always';
        function isOverload(node) {
            return ((node.type === utils_1.AST_NODE_TYPES.TSAbstractMethodDefinition ||
                node.type === utils_1.AST_NODE_TYPES.MethodDefinition) &&
                node.value.type === utils_1.AST_NODE_TYPES.TSEmptyBodyFunctionExpression);
        }
        return {
            ClassBody(node) {
                const body = exceptAfterOverload
                    ? node.body.filter(node => !isOverload(node))
                    : node.body;
                rules.ClassBody({ ...node, body });
            },
        };
    },
});
//# sourceMappingURL=lines-between-class-members.js.map