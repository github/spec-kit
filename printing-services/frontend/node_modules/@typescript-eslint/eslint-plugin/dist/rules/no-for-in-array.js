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
const ts = __importStar(require("typescript"));
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'no-for-in-array',
    meta: {
        docs: {
            description: 'Disallow iterating over an array with a for-in loop',
            recommended: 'recommended',
            requiresTypeChecking: true,
        },
        messages: {
            forInViolation: 'For-in loops over arrays skips holes, returns indices as strings, and may visit the prototype chain or other enumerable properties. Use a more robust iteration method such as for-of or array.forEach instead.',
        },
        schema: [],
        type: 'problem',
    },
    defaultOptions: [],
    create(context) {
        return {
            ForInStatement(node) {
                const services = (0, util_1.getParserServices)(context);
                const checker = services.program.getTypeChecker();
                const type = (0, util_1.getConstrainedTypeAtLocation)(services, node.right);
                if ((0, util_1.isTypeArrayTypeOrUnionOfArrayTypes)(type, checker) ||
                    (type.flags & ts.TypeFlags.StringLike) !== 0) {
                    context.report({
                        node,
                        messageId: 'forInViolation',
                    });
                }
            },
        };
    },
});
//# sourceMappingURL=no-for-in-array.js.map