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
const path_1 = require("path");
const ts = __importStar(require("typescript"));
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'no-unnecessary-type-constraint',
    meta: {
        docs: {
            description: 'Disallow unnecessary constraints on generic types',
            recommended: 'recommended',
        },
        hasSuggestions: true,
        messages: {
            unnecessaryConstraint: 'Constraining the generic type `{{name}}` to `{{constraint}}` does nothing and is unnecessary.',
            removeUnnecessaryConstraint: 'Remove the unnecessary `{{constraint}}` constraint.',
        },
        schema: [],
        type: 'suggestion',
    },
    defaultOptions: [],
    create(context) {
        // In theory, we could use the type checker for more advanced constraint types...
        // ...but in practice, these types are rare, and likely not worth requiring type info.
        // https://github.com/typescript-eslint/typescript-eslint/pull/2516#discussion_r495731858
        const unnecessaryConstraints = new Map([
            [utils_1.AST_NODE_TYPES.TSAnyKeyword, 'any'],
            [utils_1.AST_NODE_TYPES.TSUnknownKeyword, 'unknown'],
        ]);
        function checkRequiresGenericDeclarationDisambiguation(filename) {
            const pathExt = (0, path_1.extname)(filename).toLocaleLowerCase();
            switch (pathExt) {
                case ts.Extension.Cts:
                case ts.Extension.Mts:
                case ts.Extension.Tsx:
                    return true;
                default:
                    return false;
            }
        }
        const requiresGenericDeclarationDisambiguation = checkRequiresGenericDeclarationDisambiguation((0, eslint_utils_1.getFilename)(context));
        const source = (0, eslint_utils_1.getSourceCode)(context);
        const checkNode = (node, inArrowFunction) => {
            const constraint = unnecessaryConstraints.get(node.constraint.type);
            function shouldAddTrailingComma() {
                if (!inArrowFunction || !requiresGenericDeclarationDisambiguation) {
                    return false;
                }
                // Only <T>() => {} would need trailing comma
                return (node.parent.params.length ===
                    1 &&
                    source.getTokensAfter(node)[0].value !== ',' &&
                    !node.default);
            }
            if (constraint) {
                context.report({
                    data: {
                        constraint,
                        name: node.name.name,
                    },
                    suggest: [
                        {
                            messageId: 'removeUnnecessaryConstraint',
                            data: {
                                constraint,
                            },
                            fix(fixer) {
                                return fixer.replaceTextRange([node.name.range[1], node.constraint.range[1]], shouldAddTrailingComma() ? ',' : '');
                            },
                        },
                    ],
                    messageId: 'unnecessaryConstraint',
                    node,
                });
            }
        };
        return {
            ':not(ArrowFunctionExpression) > TSTypeParameterDeclaration > TSTypeParameter[constraint]'(node) {
                checkNode(node, false);
            },
            'ArrowFunctionExpression > TSTypeParameterDeclaration > TSTypeParameter[constraint]'(node) {
                checkNode(node, true);
            },
        };
    },
});
//# sourceMappingURL=no-unnecessary-type-constraint.js.map