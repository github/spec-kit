"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const scope_manager_1 = require("@typescript-eslint/scope-manager");
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'no-empty-interface',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Disallow the declaration of empty interfaces',
            recommended: 'stylistic',
        },
        fixable: 'code',
        hasSuggestions: true,
        messages: {
            noEmpty: 'An empty interface is equivalent to `{}`.',
            noEmptyWithSuper: 'An interface declaring no members is equivalent to its supertype.',
        },
        schema: [
            {
                type: 'object',
                additionalProperties: false,
                properties: {
                    allowSingleExtends: {
                        type: 'boolean',
                    },
                },
            },
        ],
    },
    defaultOptions: [
        {
            allowSingleExtends: false,
        },
    ],
    create(context, [{ allowSingleExtends }]) {
        return {
            TSInterfaceDeclaration(node) {
                const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
                const filename = (0, eslint_utils_1.getFilename)(context);
                if (node.body.body.length !== 0) {
                    // interface contains members --> Nothing to report
                    return;
                }
                const extend = node.extends;
                if (extend.length === 0) {
                    context.report({
                        node: node.id,
                        messageId: 'noEmpty',
                    });
                }
                else if (extend.length === 1) {
                    // interface extends exactly 1 interface --> Report depending on rule setting
                    if (!allowSingleExtends) {
                        const fix = (fixer) => {
                            let typeParam = '';
                            if (node.typeParameters) {
                                typeParam = sourceCode.getText(node.typeParameters);
                            }
                            return fixer.replaceText(node, `type ${sourceCode.getText(node.id)}${typeParam} = ${sourceCode.getText(extend[0])}`);
                        };
                        const scope = (0, eslint_utils_1.getScope)(context);
                        const mergedWithClassDeclaration = scope.set
                            .get(node.id.name)
                            ?.defs.some(def => def.node.type === utils_1.AST_NODE_TYPES.ClassDeclaration);
                        const isInAmbientDeclaration = !!((0, util_1.isDefinitionFile)(filename) &&
                            scope.type === scope_manager_1.ScopeType.tsModule &&
                            scope.block.declare);
                        const useAutoFix = !(isInAmbientDeclaration || mergedWithClassDeclaration);
                        context.report({
                            node: node.id,
                            messageId: 'noEmptyWithSuper',
                            ...(useAutoFix
                                ? { fix }
                                : !mergedWithClassDeclaration
                                    ? {
                                        suggest: [
                                            {
                                                messageId: 'noEmptyWithSuper',
                                                fix,
                                            },
                                        ],
                                    }
                                    : null),
                        });
                    }
                }
            },
        };
    },
});
//# sourceMappingURL=no-empty-interface.js.map