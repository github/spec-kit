"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'no-array-constructor',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Disallow generic `Array` constructors',
            recommended: 'recommended',
            extendsBaseRule: true,
        },
        fixable: 'code',
        messages: {
            useLiteral: 'The array literal notation [] is preferable.',
        },
        schema: [],
    },
    defaultOptions: [],
    create(context) {
        /**
         * Disallow construction of dense arrays using the Array constructor
         * @param node node to evaluate
         */
        function check(node) {
            if (node.arguments.length !== 1 &&
                node.callee.type === utils_1.AST_NODE_TYPES.Identifier &&
                node.callee.name === 'Array' &&
                !node.typeArguments &&
                !(0, util_1.isOptionalCallExpression)(node)) {
                context.report({
                    node,
                    messageId: 'useLiteral',
                    fix(fixer) {
                        if (node.arguments.length === 0) {
                            return fixer.replaceText(node, '[]');
                        }
                        const fullText = (0, eslint_utils_1.getSourceCode)(context).getText(node);
                        const preambleLength = node.callee.range[1] - node.range[0];
                        return fixer.replaceText(node, `[${fullText.slice(preambleLength + 1, -1)}]`);
                    },
                });
            }
        }
        return {
            CallExpression: check,
            NewExpression: check,
        };
    },
});
//# sourceMappingURL=no-array-constructor.js.map