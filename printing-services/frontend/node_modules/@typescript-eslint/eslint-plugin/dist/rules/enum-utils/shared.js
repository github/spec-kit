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
exports.getEnumKeyForLiteral = exports.getEnumTypes = exports.getEnumLiterals = void 0;
const tsutils = __importStar(require("ts-api-utils"));
const ts = __importStar(require("typescript"));
const util_1 = require("../../util");
/*
 * If passed an enum member, returns the type of the parent. Otherwise,
 * returns itself.
 *
 * For example:
 * - `Fruit` --> `Fruit`
 * - `Fruit.Apple` --> `Fruit`
 */
function getBaseEnumType(typeChecker, type) {
    const symbol = type.getSymbol();
    if (!tsutils.isSymbolFlagSet(symbol, ts.SymbolFlags.EnumMember)) {
        return type;
    }
    return typeChecker.getTypeAtLocation(symbol.valueDeclaration.parent);
}
/**
 * Retrieve only the Enum literals from a type. for example:
 * - 123 --> []
 * - {} --> []
 * - Fruit.Apple --> [Fruit.Apple]
 * - Fruit.Apple | Vegetable.Lettuce --> [Fruit.Apple, Vegetable.Lettuce]
 * - Fruit.Apple | Vegetable.Lettuce | 123 --> [Fruit.Apple, Vegetable.Lettuce]
 * - T extends Fruit --> [Fruit]
 */
function getEnumLiterals(type) {
    return tsutils
        .unionTypeParts(type)
        .filter((subType) => (0, util_1.isTypeFlagSet)(subType, ts.TypeFlags.EnumLiteral));
}
exports.getEnumLiterals = getEnumLiterals;
/**
 * A type can have 0 or more enum types. For example:
 * - 123 --> []
 * - {} --> []
 * - Fruit.Apple --> [Fruit]
 * - Fruit.Apple | Vegetable.Lettuce --> [Fruit, Vegetable]
 * - Fruit.Apple | Vegetable.Lettuce | 123 --> [Fruit, Vegetable]
 * - T extends Fruit --> [Fruit]
 */
function getEnumTypes(typeChecker, type) {
    return getEnumLiterals(type).map(type => getBaseEnumType(typeChecker, type));
}
exports.getEnumTypes = getEnumTypes;
/**
 * Returns the enum key that matches the given literal node, or null if none
 * match. For example:
 * ```ts
 * enum Fruit {
 *   Apple = 'apple',
 *   Banana = 'banana',
 * }
 *
 * getEnumKeyForLiteral([Fruit.Apple, Fruit.Banana], 'apple') --> 'Fruit.Apple'
 * getEnumKeyForLiteral([Fruit.Apple, Fruit.Banana], 'banana') --> 'Fruit.Banana'
 * getEnumKeyForLiteral([Fruit.Apple, Fruit.Banana], 'cherry') --> null
 * ```
 */
function getEnumKeyForLiteral(enumLiterals, literal) {
    for (const enumLiteral of enumLiterals) {
        if (enumLiteral.value === literal) {
            const { symbol } = enumLiteral;
            const memberDeclaration = symbol.valueDeclaration;
            const enumDeclaration = memberDeclaration.parent;
            const memberNameIdentifier = memberDeclaration.name;
            const enumName = enumDeclaration.name.text;
            switch (memberNameIdentifier.kind) {
                case ts.SyntaxKind.Identifier:
                    return `${enumName}.${memberNameIdentifier.text}`;
                case ts.SyntaxKind.StringLiteral: {
                    const memberName = memberNameIdentifier.text.replace(/'/g, "\\'");
                    return `${enumName}['${memberName}']`;
                }
                case ts.SyntaxKind.ComputedPropertyName:
                    return `${enumName}[${memberNameIdentifier.expression.getText()}]`;
                default:
                    break;
            }
        }
    }
    return null;
}
exports.getEnumKeyForLiteral = getEnumKeyForLiteral;
//# sourceMappingURL=shared.js.map