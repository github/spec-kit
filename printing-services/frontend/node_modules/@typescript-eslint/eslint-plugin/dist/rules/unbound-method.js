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
/**
 * Static methods on these globals are either not `this`-aware or supported being
 * called without `this`.
 *
 * - `Promise` is not in the list because it supports subclassing by using `this`
 * - `Array` is in the list because although it supports subclassing, the `this`
 *   value defaults to `Array` when unbound
 *
 * This is now a language-design invariant: static methods are never `this`-aware
 * because TC39 wants to make `array.map(Class.method)` work!
 */
const SUPPORTED_GLOBALS = [
    'Number',
    'Object',
    'String', // eslint-disable-line @typescript-eslint/internal/prefer-ast-types-enum
    'RegExp',
    'Symbol',
    'Array',
    'Proxy',
    'Date',
    'Atomics',
    'Reflect',
    'console',
    'Math',
    'JSON',
    'Intl',
];
const nativelyBoundMembers = new Set(SUPPORTED_GLOBALS.flatMap(namespace => {
    if (!(namespace in global)) {
        // node.js might not have namespaces like Intl depending on compilation options
        // https://nodejs.org/api/intl.html#intl_options_for_building_node_js
        return [];
    }
    const object = global[namespace];
    return Object.getOwnPropertyNames(object)
        .filter(name => !name.startsWith('_') &&
        typeof object[name] === 'function')
        .map(name => `${namespace}.${name}`);
}));
const isNotImported = (symbol, currentSourceFile) => {
    const { valueDeclaration } = symbol;
    if (!valueDeclaration) {
        // working around https://github.com/microsoft/TypeScript/issues/31294
        return false;
    }
    return (!!currentSourceFile &&
        currentSourceFile !== valueDeclaration.getSourceFile());
};
const getNodeName = (node) => node.type === utils_1.AST_NODE_TYPES.Identifier ? node.name : null;
const getMemberFullName = (node) => `${getNodeName(node.object)}.${getNodeName(node.property)}`;
const BASE_MESSAGE = 'Avoid referencing unbound methods which may cause unintentional scoping of `this`.';
exports.default = (0, util_1.createRule)({
    name: 'unbound-method',
    meta: {
        docs: {
            description: 'Enforce unbound methods are called with their expected scope',
            recommended: 'recommended',
            requiresTypeChecking: true,
        },
        messages: {
            unbound: BASE_MESSAGE,
            unboundWithoutThisAnnotation: BASE_MESSAGE +
                '\n' +
                'If your function does not access `this`, you can annotate it with `this: void`, or consider using an arrow function instead.',
        },
        schema: [
            {
                type: 'object',
                properties: {
                    ignoreStatic: {
                        description: 'Whether to skip checking whether `static` methods are correctly bound.',
                        type: 'boolean',
                    },
                },
                additionalProperties: false,
            },
        ],
        type: 'problem',
    },
    defaultOptions: [
        {
            ignoreStatic: false,
        },
    ],
    create(context, [{ ignoreStatic }]) {
        const services = (0, util_1.getParserServices)(context);
        const currentSourceFile = services.program.getSourceFile((0, eslint_utils_1.getFilename)(context));
        function checkMethodAndReport(node, symbol) {
            if (!symbol) {
                return;
            }
            const { dangerous, firstParamIsThis } = checkMethod(symbol, ignoreStatic);
            if (dangerous) {
                context.report({
                    messageId: firstParamIsThis === false
                        ? 'unboundWithoutThisAnnotation'
                        : 'unbound',
                    node,
                });
            }
        }
        return {
            MemberExpression(node) {
                if (isSafeUse(node)) {
                    return;
                }
                const objectSymbol = services.getSymbolAtLocation(node.object);
                if (objectSymbol &&
                    nativelyBoundMembers.has(getMemberFullName(node)) &&
                    isNotImported(objectSymbol, currentSourceFile)) {
                    return;
                }
                checkMethodAndReport(node, services.getSymbolAtLocation(node));
            },
            'VariableDeclarator, AssignmentExpression'(node) {
                const [idNode, initNode] = node.type === utils_1.AST_NODE_TYPES.VariableDeclarator
                    ? [node.id, node.init]
                    : [node.left, node.right];
                if (initNode && idNode.type === utils_1.AST_NODE_TYPES.ObjectPattern) {
                    const rightSymbol = services.getSymbolAtLocation(initNode);
                    const initTypes = services.getTypeAtLocation(initNode);
                    const notImported = rightSymbol && isNotImported(rightSymbol, currentSourceFile);
                    idNode.properties.forEach(property => {
                        if (property.type === utils_1.AST_NODE_TYPES.Property &&
                            property.key.type === utils_1.AST_NODE_TYPES.Identifier) {
                            if (notImported &&
                                (0, util_1.isIdentifier)(initNode) &&
                                nativelyBoundMembers.has(`${initNode.name}.${property.key.name}`)) {
                                return;
                            }
                            checkMethodAndReport(property.key, initTypes.getProperty(property.key.name));
                        }
                    });
                }
            },
        };
    },
});
function checkMethod(symbol, ignoreStatic) {
    const { valueDeclaration } = symbol;
    if (!valueDeclaration) {
        // working around https://github.com/microsoft/TypeScript/issues/31294
        return { dangerous: false };
    }
    switch (valueDeclaration.kind) {
        case ts.SyntaxKind.PropertyDeclaration:
            return {
                dangerous: valueDeclaration.initializer?.kind ===
                    ts.SyntaxKind.FunctionExpression,
            };
        case ts.SyntaxKind.MethodDeclaration:
        case ts.SyntaxKind.MethodSignature: {
            const decl = valueDeclaration;
            const firstParam = decl.parameters.at(0);
            const firstParamIsThis = firstParam?.name.kind === ts.SyntaxKind.Identifier &&
                // eslint-disable-next-line @typescript-eslint/no-unsafe-enum-comparison
                firstParam.name.escapedText === 'this';
            const thisArgIsVoid = firstParamIsThis && firstParam.type?.kind === ts.SyntaxKind.VoidKeyword;
            return {
                dangerous: !thisArgIsVoid &&
                    !(ignoreStatic &&
                        tsutils.includesModifier((0, util_1.getModifiers)(valueDeclaration), ts.SyntaxKind.StaticKeyword)),
                firstParamIsThis,
            };
        }
    }
    return { dangerous: false };
}
function isSafeUse(node) {
    const parent = node.parent;
    switch (parent?.type) {
        case utils_1.AST_NODE_TYPES.IfStatement:
        case utils_1.AST_NODE_TYPES.ForStatement:
        case utils_1.AST_NODE_TYPES.MemberExpression:
        case utils_1.AST_NODE_TYPES.SwitchStatement:
        case utils_1.AST_NODE_TYPES.UpdateExpression:
        case utils_1.AST_NODE_TYPES.WhileStatement:
            return true;
        case utils_1.AST_NODE_TYPES.CallExpression:
            return parent.callee === node;
        case utils_1.AST_NODE_TYPES.ConditionalExpression:
            return parent.test === node;
        case utils_1.AST_NODE_TYPES.TaggedTemplateExpression:
            return parent.tag === node;
        case utils_1.AST_NODE_TYPES.UnaryExpression:
            // the first case is safe for obvious
            // reasons. The second one is also fine
            // since we're returning something falsy
            return ['typeof', '!', 'void', 'delete'].includes(parent.operator);
        case utils_1.AST_NODE_TYPES.BinaryExpression:
            return ['instanceof', '==', '!=', '===', '!=='].includes(parent.operator);
        case utils_1.AST_NODE_TYPES.AssignmentExpression:
            return (parent.operator === '=' &&
                (node === parent.left ||
                    (node.type === utils_1.AST_NODE_TYPES.MemberExpression &&
                        node.object.type === utils_1.AST_NODE_TYPES.Super &&
                        parent.left.type === utils_1.AST_NODE_TYPES.MemberExpression &&
                        parent.left.object.type === utils_1.AST_NODE_TYPES.ThisExpression)));
        case utils_1.AST_NODE_TYPES.ChainExpression:
        case utils_1.AST_NODE_TYPES.TSNonNullExpression:
        case utils_1.AST_NODE_TYPES.TSAsExpression:
        case utils_1.AST_NODE_TYPES.TSTypeAssertion:
            return isSafeUse(parent);
        case utils_1.AST_NODE_TYPES.LogicalExpression:
            if (parent.operator === '&&' && parent.left === node) {
                // this is safe, as && will return the left if and only if it's falsy
                return true;
            }
            // in all other cases, it's likely the logical expression will return the method ref
            // so make sure the parent is a safe usage
            return isSafeUse(parent);
    }
    return false;
}
//# sourceMappingURL=unbound-method.js.map