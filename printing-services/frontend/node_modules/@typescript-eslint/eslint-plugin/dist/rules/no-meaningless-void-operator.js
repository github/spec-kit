"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const tsutils = __importStar(require("ts-api-utils"));
const ts = __importStar(require("typescript"));
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'no-meaningless-void-operator',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Disallow the `void` operator except when used to discard a value',
            recommended: 'strict',
            requiresTypeChecking: true,
        },
        fixable: 'code',
        hasSuggestions: true,
        messages: {
            meaninglessVoidOperator: "void operator shouldn't be used on {{type}}; it should convey that a return value is being ignored",
            removeVoid: "Remove 'void'",
        },
        schema: [
            {
                type: 'object',
                properties: {
                    checkNever: {
                        type: 'boolean',
                        default: false,
                    },
                },
                additionalProperties: false,
            },
        ],
    },
    defaultOptions: [{ checkNever: false }],
    create(context, [{ checkNever }]) {
        const services = utils_1.ESLintUtils.getParserServices(context);
        const checker = services.program.getTypeChecker();
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        return {
            'UnaryExpression[operator="void"]'(node) {
                const fix = (fixer) => {
                    return fixer.removeRange([
                        sourceCode.getTokens(node)[0].range[0],
                        sourceCode.getTokens(node)[1].range[0],
                    ]);
                };
                const argType = services.getTypeAtLocation(node.argument);
                const unionParts = tsutils.unionTypeParts(argType);
                if (unionParts.every(part => part.flags & (ts.TypeFlags.Void | ts.TypeFlags.Undefined))) {
                    context.report({
                        node,
                        messageId: 'meaninglessVoidOperator',
                        data: { type: checker.typeToString(argType) },
                        fix,
                    });
                }
                else if (checkNever &&
                    unionParts.every(part => part.flags &
                        (ts.TypeFlags.Void | ts.TypeFlags.Undefined | ts.TypeFlags.Never))) {
                    context.report({
                        node,
                        messageId: 'meaninglessVoidOperator',
                        data: { type: checker.typeToString(argType) },
                        suggest: [{ messageId: 'removeVoid', fix }],
                    });
                }
            },
        };
    },
});
//# sourceMappingURL=no-meaningless-void-operator.js.map