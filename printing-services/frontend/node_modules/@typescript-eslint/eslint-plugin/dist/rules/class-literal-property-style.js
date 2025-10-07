"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
const printNodeModifiers = (node, final) => `${node.accessibility ?? ''}${node.static ? ' static' : ''} ${final} `.trimStart();
const isSupportedLiteral = (node) => {
    if (node.type === utils_1.AST_NODE_TYPES.Literal) {
        return true;
    }
    if (node.type === utils_1.AST_NODE_TYPES.TaggedTemplateExpression ||
        node.type === utils_1.AST_NODE_TYPES.TemplateLiteral) {
        return ('quasi' in node ? node.quasi.quasis : node.quasis).length === 1;
    }
    return false;
};
exports.default = (0, util_1.createRule)({
    name: 'class-literal-property-style',
    meta: {
        type: 'problem',
        docs: {
            description: 'Enforce that literals on classes are exposed in a consistent style',
            recommended: 'stylistic',
        },
        hasSuggestions: true,
        messages: {
            preferFieldStyle: 'Literals should be exposed using readonly fields.',
            preferFieldStyleSuggestion: 'Replace the literals with readonly fields.',
            preferGetterStyle: 'Literals should be exposed using getters.',
            preferGetterStyleSuggestion: 'Replace the literals with getters.',
        },
        schema: [
            {
                type: 'string',
                enum: ['fields', 'getters'],
            },
        ],
    },
    defaultOptions: ['fields'],
    create(context, [style]) {
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        function getMethodName(node) {
            return (0, util_1.getStaticStringValue)(node.key) ?? sourceCode.getText(node.key);
        }
        return {
            ...(style === 'fields' && {
                MethodDefinition(node) {
                    if (node.kind !== 'get' ||
                        !node.value.body ||
                        node.value.body.body.length === 0) {
                        return;
                    }
                    const [statement] = node.value.body.body;
                    if (statement.type !== utils_1.AST_NODE_TYPES.ReturnStatement) {
                        return;
                    }
                    const { argument } = statement;
                    if (!argument || !isSupportedLiteral(argument)) {
                        return;
                    }
                    const name = getMethodName(node);
                    if (node.parent.type === utils_1.AST_NODE_TYPES.ClassBody) {
                        const hasDuplicateKeySetter = node.parent.body.some(element => {
                            return (element.type === utils_1.AST_NODE_TYPES.MethodDefinition &&
                                element.kind === 'set' &&
                                getMethodName(element) === name);
                        });
                        if (hasDuplicateKeySetter) {
                            return;
                        }
                    }
                    context.report({
                        node: node.key,
                        messageId: 'preferFieldStyle',
                        suggest: [
                            {
                                messageId: 'preferFieldStyleSuggestion',
                                fix(fixer) {
                                    const name = sourceCode.getText(node.key);
                                    let text = '';
                                    text += printNodeModifiers(node, 'readonly');
                                    text += node.computed ? `[${name}]` : name;
                                    text += ` = ${sourceCode.getText(argument)};`;
                                    return fixer.replaceText(node, text);
                                },
                            },
                        ],
                    });
                },
            }),
            ...(style === 'getters' && {
                PropertyDefinition(node) {
                    if (!node.readonly || node.declare) {
                        return;
                    }
                    const { value } = node;
                    if (!value || !isSupportedLiteral(value)) {
                        return;
                    }
                    context.report({
                        node: node.key,
                        messageId: 'preferGetterStyle',
                        suggest: [
                            {
                                messageId: 'preferGetterStyleSuggestion',
                                fix(fixer) {
                                    const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
                                    const name = sourceCode.getText(node.key);
                                    let text = '';
                                    text += printNodeModifiers(node, 'get');
                                    text += node.computed ? `[${name}]` : name;
                                    text += `() { return ${sourceCode.getText(value)}; }`;
                                    return fixer.replaceText(node, text);
                                },
                            },
                        ],
                    });
                },
            }),
        };
    },
});
//# sourceMappingURL=class-literal-property-style.js.map