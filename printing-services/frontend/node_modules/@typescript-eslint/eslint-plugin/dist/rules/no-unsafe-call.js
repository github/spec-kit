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
const tsutils = __importStar(require("ts-api-utils"));
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'no-unsafe-call',
    meta: {
        type: 'problem',
        docs: {
            description: 'Disallow calling a value with type `any`',
            recommended: 'recommended',
            requiresTypeChecking: true,
        },
        messages: {
            unsafeCall: 'Unsafe call of an `any` typed value.',
            unsafeCallThis: [
                'Unsafe call of an `any` typed value. `this` is typed as `any`.',
                'You can try to fix this by turning on the `noImplicitThis` compiler option, or adding a `this` parameter to the function.',
            ].join('\n'),
            unsafeNew: 'Unsafe construction of an any type value.',
            unsafeTemplateTag: 'Unsafe any typed template tag.',
        },
        schema: [],
    },
    defaultOptions: [],
    create(context) {
        const services = (0, util_1.getParserServices)(context);
        const compilerOptions = services.program.getCompilerOptions();
        const isNoImplicitThis = tsutils.isStrictCompilerOptionEnabled(compilerOptions, 'noImplicitThis');
        function checkCall(node, reportingNode, messageId) {
            const type = (0, util_1.getConstrainedTypeAtLocation)(services, node);
            if ((0, util_1.isTypeAnyType)(type)) {
                if (!isNoImplicitThis) {
                    // `this()` or `this.foo()` or `this.foo[bar]()`
                    const thisExpression = (0, util_1.getThisExpression)(node);
                    if (thisExpression &&
                        (0, util_1.isTypeAnyType)((0, util_1.getConstrainedTypeAtLocation)(services, thisExpression))) {
                        messageId = 'unsafeCallThis';
                    }
                }
                context.report({
                    node: reportingNode,
                    messageId: messageId,
                });
            }
        }
        return {
            'CallExpression > *.callee'(node) {
                checkCall(node, node, 'unsafeCall');
            },
            NewExpression(node) {
                checkCall(node.callee, node, 'unsafeNew');
            },
            'TaggedTemplateExpression > *.tag'(node) {
                checkCall(node, node, 'unsafeTemplateTag');
            },
        };
    },
});
//# sourceMappingURL=no-unsafe-call.js.map