"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const util_1 = require("../util");
const getESLintCoreRule_1 = require("../util/getESLintCoreRule");
const baseRule = (0, getESLintCoreRule_1.getESLintCoreRule)('max-params');
exports.default = (0, util_1.createRule)({
    name: 'max-params',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Enforce a maximum number of parameters in function definitions',
            extendsBaseRule: true,
        },
        schema: [
            {
                type: 'object',
                properties: {
                    maximum: {
                        type: 'integer',
                        minimum: 0,
                    },
                    max: {
                        type: 'integer',
                        minimum: 0,
                    },
                    countVoidThis: {
                        type: 'boolean',
                    },
                },
                additionalProperties: false,
            },
        ],
        messages: baseRule.meta.messages,
    },
    defaultOptions: [{ max: 3, countVoidThis: false }],
    create(context, [{ countVoidThis }]) {
        const baseRules = baseRule.create(context);
        if (countVoidThis === true) {
            return baseRules;
        }
        const removeVoidThisParam = (node) => {
            if (node.params.length === 0 ||
                node.params[0].type !== utils_1.AST_NODE_TYPES.Identifier ||
                node.params[0].name !== 'this' ||
                node.params[0].typeAnnotation?.typeAnnotation.type !==
                    utils_1.AST_NODE_TYPES.TSVoidKeyword) {
                return node;
            }
            return {
                ...node,
                params: node.params.slice(1),
            };
        };
        const wrapListener = (listener) => {
            return (node) => {
                listener(removeVoidThisParam(node));
            };
        };
        return {
            ArrowFunctionExpression: wrapListener(baseRules.ArrowFunctionExpression),
            FunctionDeclaration: wrapListener(baseRules.FunctionDeclaration),
            FunctionExpression: wrapListener(baseRules.FunctionExpression),
        };
    },
});
//# sourceMappingURL=max-params.js.map