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
exports.gatherLogicalOperands = void 0;
const utils_1 = require("@typescript-eslint/utils");
const ts_api_utils_1 = require("ts-api-utils");
const ts = __importStar(require("typescript"));
const util_1 = require("../../util");
const NULLISH_FLAGS = ts.TypeFlags.Null | ts.TypeFlags.Undefined;
function isValidFalseBooleanCheckType(node, operator, checkType, parserServices, options) {
    const type = parserServices.getTypeAtLocation(node);
    const types = (0, ts_api_utils_1.unionTypeParts)(type);
    const disallowFalseyLiteral = (operator === '||' && checkType === 'false') ||
        (operator === '&&' && checkType === 'true');
    if (disallowFalseyLiteral) {
        /*
        ```
        declare const x: false | {a: string};
        x && x.a;
        !x || x.a;
        ```
    
        We don't want to consider these two cases because the boolean expression
        narrows out the non-nullish falsy cases - so converting the chain to `x?.a`
        would introduce a build error
        */
        if (types.some(t => (0, ts_api_utils_1.isBooleanLiteralType)(t) && t.intrinsicName === 'false') ||
            types.some(t => (0, ts_api_utils_1.isStringLiteralType)(t) && t.value === '') ||
            types.some(t => (0, ts_api_utils_1.isNumberLiteralType)(t) && t.value === 0) ||
            types.some(t => (0, ts_api_utils_1.isBigIntLiteralType)(t) && t.value.base10Value === '0')) {
            return false;
        }
    }
    if (options.requireNullish === true) {
        return types.some(t => (0, util_1.isTypeFlagSet)(t, NULLISH_FLAGS));
    }
    let allowedFlags = NULLISH_FLAGS | ts.TypeFlags.Object;
    if (options.checkAny === true) {
        allowedFlags |= ts.TypeFlags.Any;
    }
    if (options.checkUnknown === true) {
        allowedFlags |= ts.TypeFlags.Unknown;
    }
    if (options.checkString === true) {
        allowedFlags |= ts.TypeFlags.StringLike;
    }
    if (options.checkNumber === true) {
        allowedFlags |= ts.TypeFlags.NumberLike;
    }
    if (options.checkBoolean === true) {
        allowedFlags |= ts.TypeFlags.BooleanLike;
    }
    if (options.checkBigInt === true) {
        allowedFlags |= ts.TypeFlags.BigIntLike;
    }
    return types.every(t => (0, util_1.isTypeFlagSet)(t, allowedFlags));
}
function gatherLogicalOperands(node, parserServices, options) {
    const result = [];
    const { operands, newlySeenLogicals } = flattenLogicalOperands(node);
    for (const operand of operands) {
        switch (operand.type) {
            case utils_1.AST_NODE_TYPES.BinaryExpression: {
                // check for "yoda" style logical: null != x
                const { comparedExpression, comparedValue, isYoda } = (() => {
                    // non-yoda checks are by far the most common, so check for them first
                    const comparedValueRight = getComparisonValueType(operand.right);
                    if (comparedValueRight) {
                        return {
                            comparedExpression: operand.left,
                            comparedValue: comparedValueRight,
                            isYoda: false,
                        };
                    }
                    return {
                        comparedExpression: operand.right,
                        comparedValue: getComparisonValueType(operand.left),
                        isYoda: true,
                    };
                })();
                if (comparedValue === "UndefinedStringLiteral" /* ComparisonValueType.UndefinedStringLiteral */) {
                    if (comparedExpression.type === utils_1.AST_NODE_TYPES.UnaryExpression &&
                        comparedExpression.operator === 'typeof') {
                        // typeof x === 'undefined'
                        result.push({
                            type: "Valid" /* OperandValidity.Valid */,
                            comparedName: comparedExpression.argument,
                            comparisonType: operand.operator.startsWith('!')
                                ? "NotStrictEqualUndefined" /* NullishComparisonType.NotStrictEqualUndefined */
                                : "StrictEqualUndefined" /* NullishComparisonType.StrictEqualUndefined */,
                            isYoda,
                            node: operand,
                        });
                        continue;
                    }
                    // y === 'undefined'
                    result.push({ type: "Invalid" /* OperandValidity.Invalid */ });
                    continue;
                }
                switch (operand.operator) {
                    case '!=':
                    case '==':
                        if (comparedValue === "Null" /* ComparisonValueType.Null */ ||
                            comparedValue === "Undefined" /* ComparisonValueType.Undefined */) {
                            // x == null, x == undefined
                            result.push({
                                type: "Valid" /* OperandValidity.Valid */,
                                comparedName: comparedExpression,
                                comparisonType: operand.operator.startsWith('!')
                                    ? "NotEqualNullOrUndefined" /* NullishComparisonType.NotEqualNullOrUndefined */
                                    : "EqualNullOrUndefined" /* NullishComparisonType.EqualNullOrUndefined */,
                                isYoda,
                                node: operand,
                            });
                            continue;
                        }
                        // x == something :(
                        result.push({ type: "Invalid" /* OperandValidity.Invalid */ });
                        continue;
                    case '!==':
                    case '===': {
                        const comparedName = comparedExpression;
                        switch (comparedValue) {
                            case "Null" /* ComparisonValueType.Null */:
                                result.push({
                                    type: "Valid" /* OperandValidity.Valid */,
                                    comparedName,
                                    comparisonType: operand.operator.startsWith('!')
                                        ? "NotStrictEqualNull" /* NullishComparisonType.NotStrictEqualNull */
                                        : "StrictEqualNull" /* NullishComparisonType.StrictEqualNull */,
                                    isYoda,
                                    node: operand,
                                });
                                continue;
                            case "Undefined" /* ComparisonValueType.Undefined */:
                                result.push({
                                    type: "Valid" /* OperandValidity.Valid */,
                                    comparedName,
                                    comparisonType: operand.operator.startsWith('!')
                                        ? "NotStrictEqualUndefined" /* NullishComparisonType.NotStrictEqualUndefined */
                                        : "StrictEqualUndefined" /* NullishComparisonType.StrictEqualUndefined */,
                                    isYoda,
                                    node: operand,
                                });
                                continue;
                            default:
                                // x === something :(
                                result.push({ type: "Invalid" /* OperandValidity.Invalid */ });
                                continue;
                        }
                    }
                }
                result.push({ type: "Invalid" /* OperandValidity.Invalid */ });
                continue;
            }
            case utils_1.AST_NODE_TYPES.UnaryExpression:
                if (operand.operator === '!' &&
                    isValidFalseBooleanCheckType(operand.argument, node.operator, 'false', parserServices, options)) {
                    result.push({
                        type: "Valid" /* OperandValidity.Valid */,
                        comparedName: operand.argument,
                        comparisonType: "NotBoolean" /* NullishComparisonType.NotBoolean */,
                        isYoda: false,
                        node: operand,
                    });
                    continue;
                }
                result.push({ type: "Invalid" /* OperandValidity.Invalid */ });
                continue;
            case utils_1.AST_NODE_TYPES.LogicalExpression:
                // explicitly ignore the mixed logical expression cases
                result.push({ type: "Invalid" /* OperandValidity.Invalid */ });
                continue;
            default:
                if (isValidFalseBooleanCheckType(operand, node.operator, 'true', parserServices, options)) {
                    result.push({
                        type: "Valid" /* OperandValidity.Valid */,
                        comparedName: operand,
                        comparisonType: "Boolean" /* NullishComparisonType.Boolean */,
                        isYoda: false,
                        node: operand,
                    });
                }
                else {
                    result.push({ type: "Invalid" /* OperandValidity.Invalid */ });
                }
                continue;
        }
    }
    return {
        operands: result,
        newlySeenLogicals,
    };
    /*
    The AST is always constructed such the first element is always the deepest element.
    I.e. for this code: `foo && foo.bar && foo.bar.baz && foo.bar.baz.buzz`
    The AST will look like this:
    {
      left: {
        left: {
          left: foo
          right: foo.bar
        }
        right: foo.bar.baz
      }
      right: foo.bar.baz.buzz
    }
  
    So given any logical expression, we can perform a depth-first traversal to get
    the operands in order.
  
    Note that this function purposely does not inspect mixed logical expressions
    like `foo || foo.bar && foo.bar.baz` - separate selector
    */
    function flattenLogicalOperands(node) {
        const operands = [];
        const newlySeenLogicals = new Set([node]);
        const stack = [node.right, node.left];
        let current;
        while ((current = stack.pop())) {
            if (current.type === utils_1.AST_NODE_TYPES.LogicalExpression &&
                current.operator === node.operator) {
                newlySeenLogicals.add(current);
                stack.push(current.right);
                stack.push(current.left);
            }
            else {
                operands.push(current);
            }
        }
        return {
            operands,
            newlySeenLogicals,
        };
    }
    function getComparisonValueType(node) {
        switch (node.type) {
            case utils_1.AST_NODE_TYPES.Literal:
                // eslint-disable-next-line eqeqeq -- intentional exact comparison against null
                if (node.value === null && node.raw === 'null') {
                    return "Null" /* ComparisonValueType.Null */;
                }
                if (node.value === 'undefined') {
                    return "UndefinedStringLiteral" /* ComparisonValueType.UndefinedStringLiteral */;
                }
                return null;
            case utils_1.AST_NODE_TYPES.Identifier:
                if (node.name === 'undefined') {
                    return "Undefined" /* ComparisonValueType.Undefined */;
                }
                return null;
        }
        return null;
    }
}
exports.gatherLogicalOperands = gatherLogicalOperands;
//# sourceMappingURL=gatherLogicalOperands.js.map