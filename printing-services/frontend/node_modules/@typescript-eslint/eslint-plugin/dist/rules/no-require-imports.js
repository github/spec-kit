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
const util = __importStar(require("../util"));
exports.default = util.createRule({
    name: 'no-require-imports',
    meta: {
        type: 'problem',
        docs: {
            description: 'Disallow invocation of `require()`',
        },
        schema: [
            {
                type: 'object',
                properties: {
                    allow: {
                        type: 'array',
                        items: { type: 'string' },
                        description: 'Patterns of import paths to allow requiring from.',
                    },
                },
                additionalProperties: false,
            },
        ],
        messages: {
            noRequireImports: 'A `require()` style import is forbidden.',
        },
    },
    defaultOptions: [{ allow: [] }],
    create(context, options) {
        const allowPatterns = options[0].allow.map(pattern => new RegExp(pattern, 'u'));
        function isImportPathAllowed(importPath) {
            return allowPatterns.some(pattern => importPath.match(pattern));
        }
        return {
            'CallExpression[callee.name="require"]'(node) {
                if (node.arguments[0]?.type === utils_1.AST_NODE_TYPES.Literal &&
                    typeof node.arguments[0].value === 'string' &&
                    isImportPathAllowed(node.arguments[0].value)) {
                    return;
                }
                const variable = utils_1.ASTUtils.findVariable((0, eslint_utils_1.getScope)(context), 'require');
                // ignore non-global require usage as it's something user-land custom instead
                // of the commonjs standard
                if (!variable?.identifiers.length) {
                    context.report({
                        node,
                        messageId: 'noRequireImports',
                    });
                }
            },
            TSExternalModuleReference(node) {
                if (node.expression.type === utils_1.AST_NODE_TYPES.Literal &&
                    typeof node.expression.value === 'string' &&
                    isImportPathAllowed(node.expression.value)) {
                    return;
                }
                context.report({
                    node,
                    messageId: 'noRequireImports',
                });
            },
        };
    },
});
//# sourceMappingURL=no-require-imports.js.map