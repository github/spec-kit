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
const tsutils = __importStar(require("ts-api-utils"));
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'no-unsafe-assignment',
    meta: {
        type: 'problem',
        docs: {
            description: 'Disallow assigning a value with type `any` to variables and properties',
            recommended: 'recommended',
            requiresTypeChecking: true,
        },
        messages: {
            anyAssignment: 'Unsafe assignment of an `any` value.',
            anyAssignmentThis: [
                'Unsafe assignment of an `any` value. `this` is typed as `any`.',
                'You can try to fix this by turning on the `noImplicitThis` compiler option, or adding a `this` parameter to the function.',
            ].join('\n'),
            unsafeArrayPattern: 'Unsafe array destructuring of an `any` array value.',
            unsafeArrayPatternFromTuple: 'Unsafe array destructuring of a tuple element with an `any` value.',
            unsafeAssignment: 'Unsafe assignment of type {{sender}} to a variable of type {{receiver}}.',
            unsafeArraySpread: 'Unsafe spread of an `any` value in an array.',
        },
        schema: [],
    },
    defaultOptions: [],
    create(context) {
        const services = (0, util_1.getParserServices)(context);
        const checker = services.program.getTypeChecker();
        const compilerOptions = services.program.getCompilerOptions();
        const isNoImplicitThis = tsutils.isStrictCompilerOptionEnabled(compilerOptions, 'noImplicitThis');
        // returns true if the assignment reported
        function checkArrayDestructureHelper(receiverNode, senderNode) {
            if (receiverNode.type !== utils_1.AST_NODE_TYPES.ArrayPattern) {
                return false;
            }
            const senderTsNode = services.esTreeNodeToTSNodeMap.get(senderNode);
            const senderType = services.getTypeAtLocation(senderNode);
            return checkArrayDestructure(receiverNode, senderType, senderTsNode);
        }
        // returns true if the assignment reported
        function checkArrayDestructure(receiverNode, senderType, senderNode) {
            // any array
            // const [x] = ([] as any[]);
            if ((0, util_1.isTypeAnyArrayType)(senderType, checker)) {
                context.report({
                    node: receiverNode,
                    messageId: 'unsafeArrayPattern',
                });
                return false;
            }
            if (!checker.isTupleType(senderType)) {
                return true;
            }
            const tupleElements = checker.getTypeArguments(senderType);
            // tuple with any
            // const [x] = [1 as any];
            let didReport = false;
            for (let receiverIndex = 0; receiverIndex < receiverNode.elements.length; receiverIndex += 1) {
                const receiverElement = receiverNode.elements[receiverIndex];
                if (!receiverElement) {
                    continue;
                }
                if (receiverElement.type === utils_1.AST_NODE_TYPES.RestElement) {
                    // don't handle rests as they're not a 1:1 assignment
                    continue;
                }
                const senderType = tupleElements[receiverIndex];
                if (!senderType) {
                    continue;
                }
                // check for the any type first so we can handle [[[x]]] = [any]
                if ((0, util_1.isTypeAnyType)(senderType)) {
                    context.report({
                        node: receiverElement,
                        messageId: 'unsafeArrayPatternFromTuple',
                    });
                    // we want to report on every invalid element in the tuple
                    didReport = true;
                }
                else if (receiverElement.type === utils_1.AST_NODE_TYPES.ArrayPattern) {
                    didReport = checkArrayDestructure(receiverElement, senderType, senderNode);
                }
                else if (receiverElement.type === utils_1.AST_NODE_TYPES.ObjectPattern) {
                    didReport = checkObjectDestructure(receiverElement, senderType, senderNode);
                }
            }
            return didReport;
        }
        // returns true if the assignment reported
        function checkObjectDestructureHelper(receiverNode, senderNode) {
            if (receiverNode.type !== utils_1.AST_NODE_TYPES.ObjectPattern) {
                return false;
            }
            const senderTsNode = services.esTreeNodeToTSNodeMap.get(senderNode);
            const senderType = services.getTypeAtLocation(senderNode);
            return checkObjectDestructure(receiverNode, senderType, senderTsNode);
        }
        // returns true if the assignment reported
        function checkObjectDestructure(receiverNode, senderType, senderNode) {
            const properties = new Map(senderType
                .getProperties()
                .map(property => [
                property.getName(),
                checker.getTypeOfSymbolAtLocation(property, senderNode),
            ]));
            let didReport = false;
            for (const receiverProperty of receiverNode.properties) {
                if (receiverProperty.type === utils_1.AST_NODE_TYPES.RestElement) {
                    // don't bother checking rest
                    continue;
                }
                let key;
                if (!receiverProperty.computed) {
                    key =
                        receiverProperty.key.type === utils_1.AST_NODE_TYPES.Identifier
                            ? receiverProperty.key.name
                            : String(receiverProperty.key.value);
                }
                else if (receiverProperty.key.type === utils_1.AST_NODE_TYPES.Literal) {
                    key = String(receiverProperty.key.value);
                }
                else if (receiverProperty.key.type === utils_1.AST_NODE_TYPES.TemplateLiteral &&
                    receiverProperty.key.quasis.length === 1) {
                    key = String(receiverProperty.key.quasis[0].value.cooked);
                }
                else {
                    // can't figure out the name, so skip it
                    continue;
                }
                const senderType = properties.get(key);
                if (!senderType) {
                    continue;
                }
                // check for the any type first so we can handle {x: {y: z}} = {x: any}
                if ((0, util_1.isTypeAnyType)(senderType)) {
                    context.report({
                        node: receiverProperty.value,
                        messageId: 'unsafeArrayPatternFromTuple',
                    });
                    didReport = true;
                }
                else if (receiverProperty.value.type === utils_1.AST_NODE_TYPES.ArrayPattern) {
                    didReport = checkArrayDestructure(receiverProperty.value, senderType, senderNode);
                }
                else if (receiverProperty.value.type === utils_1.AST_NODE_TYPES.ObjectPattern) {
                    didReport = checkObjectDestructure(receiverProperty.value, senderType, senderNode);
                }
            }
            return didReport;
        }
        // returns true if the assignment reported
        function checkAssignment(receiverNode, senderNode, reportingNode, comparisonType) {
            const receiverTsNode = services.esTreeNodeToTSNodeMap.get(receiverNode);
            const receiverType = comparisonType === 2 /* ComparisonType.Contextual */
                ? (0, util_1.getContextualType)(checker, receiverTsNode) ??
                    services.getTypeAtLocation(receiverNode)
                : services.getTypeAtLocation(receiverNode);
            const senderType = services.getTypeAtLocation(senderNode);
            if ((0, util_1.isTypeAnyType)(senderType)) {
                // handle cases when we assign any ==> unknown.
                if ((0, util_1.isTypeUnknownType)(receiverType)) {
                    return false;
                }
                let messageId = 'anyAssignment';
                if (!isNoImplicitThis) {
                    // `var foo = this`
                    const thisExpression = (0, util_1.getThisExpression)(senderNode);
                    if (thisExpression &&
                        (0, util_1.isTypeAnyType)((0, util_1.getConstrainedTypeAtLocation)(services, thisExpression))) {
                        messageId = 'anyAssignmentThis';
                    }
                }
                context.report({
                    node: reportingNode,
                    messageId,
                });
                return true;
            }
            if (comparisonType === 0 /* ComparisonType.None */) {
                return false;
            }
            const result = (0, util_1.isUnsafeAssignment)(senderType, receiverType, checker, senderNode);
            if (!result) {
                return false;
            }
            const { sender, receiver } = result;
            context.report({
                node: reportingNode,
                messageId: 'unsafeAssignment',
                data: {
                    sender: checker.typeToString(sender),
                    receiver: checker.typeToString(receiver),
                },
            });
            return true;
        }
        function getComparisonType(typeAnnotation) {
            return typeAnnotation
                ? // if there's a type annotation, we can do a comparison
                    1 /* ComparisonType.Basic */
                : // no type annotation means the variable's type will just be inferred, thus equal
                    0 /* ComparisonType.None */;
        }
        return {
            'VariableDeclarator[init != null]'(node) {
                const init = (0, util_1.nullThrows)(node.init, util_1.NullThrowsReasons.MissingToken(node.type, 'init'));
                let didReport = checkAssignment(node.id, init, node, getComparisonType(node.id.typeAnnotation));
                if (!didReport) {
                    didReport = checkArrayDestructureHelper(node.id, init);
                }
                if (!didReport) {
                    checkObjectDestructureHelper(node.id, init);
                }
            },
            'PropertyDefinition[value != null]'(node) {
                checkAssignment(node.key, node.value, node, getComparisonType(node.typeAnnotation));
            },
            'AssignmentExpression[operator = "="], AssignmentPattern'(node) {
                let didReport = checkAssignment(node.left, node.right, node, 1 /* ComparisonType.Basic */);
                if (!didReport) {
                    didReport = checkArrayDestructureHelper(node.left, node.right);
                }
                if (!didReport) {
                    checkObjectDestructureHelper(node.left, node.right);
                }
            },
            // object pattern props are checked via assignments
            ':not(ObjectPattern) > Property'(node) {
                if (node.value.type === utils_1.AST_NODE_TYPES.AssignmentPattern ||
                    node.value.type === utils_1.AST_NODE_TYPES.TSEmptyBodyFunctionExpression) {
                    // handled by other selector
                    return;
                }
                checkAssignment(node.key, node.value, node, 2 /* ComparisonType.Contextual */);
            },
            'ArrayExpression > SpreadElement'(node) {
                const restType = services.getTypeAtLocation(node.argument);
                if ((0, util_1.isTypeAnyType)(restType) || (0, util_1.isTypeAnyArrayType)(restType, checker)) {
                    context.report({
                        node: node,
                        messageId: 'unsafeArraySpread',
                    });
                }
            },
            'JSXAttribute[value != null]'(node) {
                const value = (0, util_1.nullThrows)(node.value, util_1.NullThrowsReasons.MissingToken(node.type, 'value'));
                if (value.type !== utils_1.AST_NODE_TYPES.JSXExpressionContainer ||
                    value.expression.type === utils_1.AST_NODE_TYPES.JSXEmptyExpression) {
                    return;
                }
                checkAssignment(node.name, value.expression, value.expression, 2 /* ComparisonType.Contextual */);
            },
        };
    },
});
//# sourceMappingURL=no-unsafe-assignment.js.map