"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'no-extraneous-class',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Disallow classes used as namespaces',
            recommended: 'strict',
        },
        schema: [
            {
                type: 'object',
                additionalProperties: false,
                properties: {
                    allowConstructorOnly: {
                        description: 'Whether to allow extraneous classes that contain only a constructor.',
                        type: 'boolean',
                    },
                    allowEmpty: {
                        description: 'Whether to allow extraneous classes that have no body (i.e. are empty).',
                        type: 'boolean',
                    },
                    allowStaticOnly: {
                        description: 'Whether to allow extraneous classes that only contain static members.',
                        type: 'boolean',
                    },
                    allowWithDecorator: {
                        description: 'Whether to allow extraneous classes that include a decorator.',
                        type: 'boolean',
                    },
                },
            },
        ],
        messages: {
            empty: 'Unexpected empty class.',
            onlyStatic: 'Unexpected class with only static properties.',
            onlyConstructor: 'Unexpected class with only a constructor.',
        },
    },
    defaultOptions: [
        {
            allowConstructorOnly: false,
            allowEmpty: false,
            allowStaticOnly: false,
            allowWithDecorator: false,
        },
    ],
    create(context, [{ allowConstructorOnly, allowEmpty, allowStaticOnly, allowWithDecorator }]) {
        const isAllowWithDecorator = (node) => {
            return !!(allowWithDecorator &&
                node?.decorators &&
                node.decorators.length !== 0);
        };
        return {
            ClassBody(node) {
                const parent = node.parent;
                if (parent.superClass || isAllowWithDecorator(parent)) {
                    return;
                }
                const reportNode = 'id' in parent && parent.id ? parent.id : parent;
                if (node.body.length === 0) {
                    if (allowEmpty) {
                        return;
                    }
                    context.report({
                        node: reportNode,
                        messageId: 'empty',
                    });
                    return;
                }
                let onlyStatic = true;
                let onlyConstructor = true;
                for (const prop of node.body) {
                    if ('kind' in prop && prop.kind === 'constructor') {
                        if (prop.value.params.some(param => param.type === utils_1.AST_NODE_TYPES.TSParameterProperty)) {
                            onlyConstructor = false;
                            onlyStatic = false;
                        }
                    }
                    else {
                        onlyConstructor = false;
                        if ('static' in prop && !prop.static) {
                            onlyStatic = false;
                        }
                    }
                    if (!(onlyStatic || onlyConstructor)) {
                        break;
                    }
                }
                if (onlyConstructor) {
                    if (!allowConstructorOnly) {
                        context.report({
                            node: reportNode,
                            messageId: 'onlyConstructor',
                        });
                    }
                    return;
                }
                if (onlyStatic && !allowStaticOnly) {
                    context.report({
                        node: reportNode,
                        messageId: 'onlyStatic',
                    });
                }
            },
        };
    },
});
//# sourceMappingURL=no-extraneous-class.js.map