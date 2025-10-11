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
const ts = __importStar(require("typescript"));
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'restrict-template-expressions',
    meta: {
        type: 'problem',
        docs: {
            description: 'Enforce template literal expressions to be of `string` type',
            recommended: 'recommended',
            requiresTypeChecking: true,
        },
        messages: {
            invalidType: 'Invalid type "{{type}}" of template literal expression.',
        },
        schema: [
            {
                type: 'object',
                additionalProperties: false,
                properties: {
                    allowAny: {
                        description: 'Whether to allow `any` typed values in template expressions.',
                        type: 'boolean',
                    },
                    allowBoolean: {
                        description: 'Whether to allow `boolean` typed values in template expressions.',
                        type: 'boolean',
                    },
                    allowNullish: {
                        description: 'Whether to allow `nullish` typed values in template expressions.',
                        type: 'boolean',
                    },
                    allowNumber: {
                        description: 'Whether to allow `number` typed values in template expressions.',
                        type: 'boolean',
                    },
                    allowRegExp: {
                        description: 'Whether to allow `regexp` typed values in template expressions.',
                        type: 'boolean',
                    },
                    allowNever: {
                        description: 'Whether to allow `never` typed values in template expressions.',
                        type: 'boolean',
                    },
                },
            },
        ],
    },
    defaultOptions: [
        {
            allowAny: true,
            allowBoolean: true,
            allowNullish: true,
            allowNumber: true,
            allowRegExp: true,
        },
    ],
    create(context, [options]) {
        const services = (0, util_1.getParserServices)(context);
        const checker = services.program.getTypeChecker();
        function isUnderlyingTypePrimitive(type) {
            if ((0, util_1.isTypeFlagSet)(type, ts.TypeFlags.StringLike)) {
                return true;
            }
            if (options.allowNumber &&
                (0, util_1.isTypeFlagSet)(type, ts.TypeFlags.NumberLike | ts.TypeFlags.BigIntLike)) {
                return true;
            }
            if (options.allowBoolean &&
                (0, util_1.isTypeFlagSet)(type, ts.TypeFlags.BooleanLike)) {
                return true;
            }
            if (options.allowAny && (0, util_1.isTypeAnyType)(type)) {
                return true;
            }
            if (options.allowRegExp && (0, util_1.getTypeName)(checker, type) === 'RegExp') {
                return true;
            }
            if (options.allowNullish &&
                (0, util_1.isTypeFlagSet)(type, ts.TypeFlags.Null | ts.TypeFlags.Undefined)) {
                return true;
            }
            if (options.allowNever && (0, util_1.isTypeNeverType)(type)) {
                return true;
            }
            return false;
        }
        return {
            TemplateLiteral(node) {
                // don't check tagged template literals
                if (node.parent.type === utils_1.AST_NODE_TYPES.TaggedTemplateExpression) {
                    return;
                }
                for (const expression of node.expressions) {
                    const expressionType = (0, util_1.getConstrainedTypeAtLocation)(services, expression);
                    if (!isInnerUnionOrIntersectionConformingTo(expressionType, isUnderlyingTypePrimitive)) {
                        context.report({
                            node: expression,
                            messageId: 'invalidType',
                            data: { type: checker.typeToString(expressionType) },
                        });
                    }
                }
            },
        };
        function isInnerUnionOrIntersectionConformingTo(type, predicate) {
            return rec(type);
            function rec(innerType) {
                if (innerType.isUnion()) {
                    return innerType.types.every(rec);
                }
                if (innerType.isIntersection()) {
                    return innerType.types.some(rec);
                }
                return predicate(innerType);
            }
        }
    },
});
//# sourceMappingURL=restrict-template-expressions.js.map