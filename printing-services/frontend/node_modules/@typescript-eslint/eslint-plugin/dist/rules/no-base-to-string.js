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
const ts = __importStar(require("typescript"));
const util_1 = require("../util");
var Usefulness;
(function (Usefulness) {
    Usefulness["Always"] = "always";
    Usefulness["Never"] = "will";
    Usefulness["Sometimes"] = "may";
})(Usefulness || (Usefulness = {}));
exports.default = (0, util_1.createRule)({
    name: 'no-base-to-string',
    meta: {
        docs: {
            description: 'Require `.toString()` to only be called on objects which provide useful information when stringified',
            recommended: 'recommended',
            requiresTypeChecking: true,
        },
        messages: {
            baseToString: "'{{name}}' {{certainty}} evaluate to '[object Object]' when stringified.",
        },
        schema: [
            {
                type: 'object',
                properties: {
                    ignoredTypeNames: {
                        type: 'array',
                        items: {
                            type: 'string',
                        },
                    },
                },
                additionalProperties: false,
            },
        ],
        type: 'suggestion',
    },
    defaultOptions: [
        {
            ignoredTypeNames: ['Error', 'RegExp', 'URL', 'URLSearchParams'],
        },
    ],
    create(context, [option]) {
        const services = (0, util_1.getParserServices)(context);
        const checker = services.program.getTypeChecker();
        const ignoredTypeNames = option.ignoredTypeNames ?? [];
        function checkExpression(node, type) {
            if (node.type === utils_1.AST_NODE_TYPES.Literal) {
                return;
            }
            const certainty = collectToStringCertainty(type ?? services.getTypeAtLocation(node));
            if (certainty === Usefulness.Always) {
                return;
            }
            context.report({
                data: {
                    certainty,
                    name: (0, eslint_utils_1.getSourceCode)(context).getText(node),
                },
                messageId: 'baseToString',
                node,
            });
        }
        function collectToStringCertainty(type) {
            const toString = checker.getPropertyOfType(type, 'toString');
            const declarations = toString?.getDeclarations();
            if (!toString || !declarations || declarations.length === 0) {
                return Usefulness.Always;
            }
            // Patch for old version TypeScript, the Boolean type definition missing toString()
            if (type.flags & ts.TypeFlags.Boolean ||
                type.flags & ts.TypeFlags.BooleanLiteral) {
                return Usefulness.Always;
            }
            if (ignoredTypeNames.includes((0, util_1.getTypeName)(checker, type))) {
                return Usefulness.Always;
            }
            if (declarations.every(({ parent }) => !ts.isInterfaceDeclaration(parent) || parent.name.text !== 'Object')) {
                return Usefulness.Always;
            }
            if (type.isIntersection()) {
                for (const subType of type.types) {
                    const subtypeUsefulness = collectToStringCertainty(subType);
                    if (subtypeUsefulness === Usefulness.Always) {
                        return Usefulness.Always;
                    }
                }
                return Usefulness.Never;
            }
            if (!type.isUnion()) {
                return Usefulness.Never;
            }
            let allSubtypesUseful = true;
            let someSubtypeUseful = false;
            for (const subType of type.types) {
                const subtypeUsefulness = collectToStringCertainty(subType);
                if (subtypeUsefulness !== Usefulness.Always && allSubtypesUseful) {
                    allSubtypesUseful = false;
                }
                if (subtypeUsefulness !== Usefulness.Never && !someSubtypeUseful) {
                    someSubtypeUseful = true;
                }
            }
            if (allSubtypesUseful && someSubtypeUseful) {
                return Usefulness.Always;
            }
            if (someSubtypeUseful) {
                return Usefulness.Sometimes;
            }
            return Usefulness.Never;
        }
        return {
            'AssignmentExpression[operator = "+="], BinaryExpression[operator = "+"]'(node) {
                const leftType = services.getTypeAtLocation(node.left);
                const rightType = services.getTypeAtLocation(node.right);
                if ((0, util_1.getTypeName)(checker, leftType) === 'string') {
                    checkExpression(node.right, rightType);
                }
                else if ((0, util_1.getTypeName)(checker, rightType) === 'string' &&
                    node.left.type !== utils_1.AST_NODE_TYPES.PrivateIdentifier) {
                    checkExpression(node.left, leftType);
                }
            },
            'CallExpression > MemberExpression.callee > Identifier[name = "toString"].property'(node) {
                const memberExpr = node.parent;
                checkExpression(memberExpr.object);
            },
            TemplateLiteral(node) {
                if (node.parent.type === utils_1.AST_NODE_TYPES.TaggedTemplateExpression) {
                    return;
                }
                for (const expression of node.expressions) {
                    checkExpression(expression);
                }
            },
        };
    },
});
//# sourceMappingURL=no-base-to-string.js.map