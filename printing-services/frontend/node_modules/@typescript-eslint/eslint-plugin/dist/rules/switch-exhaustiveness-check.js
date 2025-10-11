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
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const tsutils = __importStar(require("ts-api-utils"));
const ts = __importStar(require("typescript"));
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'switch-exhaustiveness-check',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Require switch-case statements to be exhaustive',
            requiresTypeChecking: true,
        },
        hasSuggestions: true,
        schema: [
            {
                type: 'object',
                properties: {
                    allowDefaultCaseForExhaustiveSwitch: {
                        description: `If 'true', allow 'default' cases on switch statements with exhaustive cases.`,
                        type: 'boolean',
                    },
                    requireDefaultForNonUnion: {
                        description: `If 'true', require a 'default' clause for switches on non-union types.`,
                        type: 'boolean',
                    },
                },
                additionalProperties: false,
            },
        ],
        messages: {
            switchIsNotExhaustive: 'Switch is not exhaustive. Cases not matched: {{missingBranches}}',
            dangerousDefaultCase: 'The switch statement is exhaustive, so the default case is unnecessary.',
            addMissingCases: 'Add branches for missing cases.',
        },
    },
    defaultOptions: [
        {
            allowDefaultCaseForExhaustiveSwitch: true,
            requireDefaultForNonUnion: false,
        },
    ],
    create(context, [{ allowDefaultCaseForExhaustiveSwitch, requireDefaultForNonUnion }]) {
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        const services = (0, util_1.getParserServices)(context);
        const checker = services.program.getTypeChecker();
        const compilerOptions = services.program.getCompilerOptions();
        function getSwitchMetadata(node) {
            const defaultCase = node.cases.find(switchCase => switchCase.test == null);
            const discriminantType = (0, util_1.getConstrainedTypeAtLocation)(services, node.discriminant);
            const symbolName = discriminantType.getSymbol()?.escapedName;
            const containsNonLiteralType = doesTypeContainNonLiteralType(discriminantType);
            const caseTypes = new Set();
            for (const switchCase of node.cases) {
                // If the `test` property of the switch case is `null`, then we are on a
                // `default` case.
                if (switchCase.test == null) {
                    continue;
                }
                const caseType = (0, util_1.getConstrainedTypeAtLocation)(services, switchCase.test);
                caseTypes.add(caseType);
            }
            const missingLiteralBranchTypes = [];
            for (const unionPart of tsutils.unionTypeParts(discriminantType)) {
                for (const intersectionPart of tsutils.intersectionTypeParts(unionPart)) {
                    if (caseTypes.has(intersectionPart) ||
                        !isTypeLiteralLikeType(intersectionPart)) {
                        continue;
                    }
                    missingLiteralBranchTypes.push(intersectionPart);
                }
            }
            return {
                symbolName,
                missingLiteralBranchTypes,
                defaultCase,
                containsNonLiteralType,
            };
        }
        function checkSwitchExhaustive(node, switchMetadata) {
            const { missingLiteralBranchTypes, symbolName, defaultCase } = switchMetadata;
            // We only trigger the rule if a `default` case does not exist, since that
            // would disqualify the switch statement from having cases that exactly
            // match the members of a union.
            if (missingLiteralBranchTypes.length > 0 && defaultCase === undefined) {
                context.report({
                    node: node.discriminant,
                    messageId: 'switchIsNotExhaustive',
                    data: {
                        missingBranches: missingLiteralBranchTypes
                            .map(missingType => tsutils.isTypeFlagSet(missingType, ts.TypeFlags.ESSymbolLike)
                            ? `typeof ${missingType.getSymbol()?.escapedName}`
                            : checker.typeToString(missingType))
                            .join(' | '),
                    },
                    suggest: [
                        {
                            messageId: 'addMissingCases',
                            fix(fixer) {
                                return fixSwitch(fixer, node, missingLiteralBranchTypes, symbolName?.toString());
                            },
                        },
                    ],
                });
            }
        }
        function fixSwitch(fixer, node, missingBranchTypes, // null means default branch
        symbolName) {
            const lastCase = node.cases.length > 0 ? node.cases[node.cases.length - 1] : null;
            const caseIndent = lastCase
                ? ' '.repeat(lastCase.loc.start.column)
                : // If there are no cases, use indentation of the switch statement and
                    // leave it to the user to format it correctly.
                    ' '.repeat(node.loc.start.column);
            const missingCases = [];
            for (const missingBranchType of missingBranchTypes) {
                if (missingBranchType == null) {
                    missingCases.push(`default: { throw new Error('default case') }`);
                    continue;
                }
                const missingBranchName = missingBranchType.getSymbol()?.escapedName;
                let caseTest = tsutils.isTypeFlagSet(missingBranchType, ts.TypeFlags.ESSymbolLike)
                    ? missingBranchName
                    : checker.typeToString(missingBranchType);
                if (symbolName &&
                    (missingBranchName || missingBranchName === '') &&
                    (0, util_1.requiresQuoting)(missingBranchName.toString(), compilerOptions.target)) {
                    const escapedBranchName = missingBranchName
                        .replace(/'/g, "\\'")
                        .replace(/\n/g, '\\n')
                        .replace(/\r/g, '\\r');
                    caseTest = `${symbolName}['${escapedBranchName}']`;
                }
                const errorMessage = `Not implemented yet: ${caseTest} case`;
                const escapedErrorMessage = errorMessage.replace(/'/g, "\\'");
                missingCases.push(`case ${caseTest}: { throw new Error('${escapedErrorMessage}') }`);
            }
            const fixString = missingCases
                .map(code => `${caseIndent}${code}`)
                .join('\n');
            if (lastCase) {
                return fixer.insertTextAfter(lastCase, `\n${fixString}`);
            }
            // There were no existing cases.
            const openingBrace = sourceCode.getTokenAfter(node.discriminant, util_1.isOpeningBraceToken);
            const closingBrace = sourceCode.getTokenAfter(node.discriminant, util_1.isClosingBraceToken);
            return fixer.replaceTextRange([openingBrace.range[0], closingBrace.range[1]], ['{', fixString, `${caseIndent}}`].join('\n'));
        }
        function checkSwitchUnnecessaryDefaultCase(switchMetadata) {
            if (allowDefaultCaseForExhaustiveSwitch) {
                return;
            }
            const { missingLiteralBranchTypes, defaultCase, containsNonLiteralType } = switchMetadata;
            if (missingLiteralBranchTypes.length === 0 &&
                defaultCase !== undefined &&
                !containsNonLiteralType) {
                context.report({
                    node: defaultCase,
                    messageId: 'dangerousDefaultCase',
                });
            }
        }
        function checkSwitchNoUnionDefaultCase(node, switchMetadata) {
            if (!requireDefaultForNonUnion) {
                return;
            }
            const { defaultCase, containsNonLiteralType } = switchMetadata;
            if (containsNonLiteralType && defaultCase === undefined) {
                context.report({
                    node: node.discriminant,
                    messageId: 'switchIsNotExhaustive',
                    data: {
                        missingBranches: 'default',
                    },
                    suggest: [
                        {
                            messageId: 'addMissingCases',
                            fix(fixer) {
                                return fixSwitch(fixer, node, [null]);
                            },
                        },
                    ],
                });
            }
        }
        return {
            SwitchStatement(node) {
                const switchMetadata = getSwitchMetadata(node);
                checkSwitchExhaustive(node, switchMetadata);
                checkSwitchUnnecessaryDefaultCase(switchMetadata);
                checkSwitchNoUnionDefaultCase(node, switchMetadata);
            },
        };
    },
});
function isTypeLiteralLikeType(type) {
    return tsutils.isTypeFlagSet(type, ts.TypeFlags.Literal |
        ts.TypeFlags.Undefined |
        ts.TypeFlags.Null |
        ts.TypeFlags.UniqueESSymbol);
}
/**
 * For example:
 *
 * - `"foo" | "bar"` is a type with all literal types.
 * - `"foo" | number` is a type that contains non-literal types.
 * - `"foo" & { bar: 1 }` is a type that contains non-literal types.
 *
 * Default cases are never superfluous in switches with non-literal types.
 */
function doesTypeContainNonLiteralType(type) {
    return tsutils
        .unionTypeParts(type)
        .some(type => tsutils
        .intersectionTypeParts(type)
        .every(subType => !isTypeLiteralLikeType(subType)));
}
//# sourceMappingURL=switch-exhaustiveness-check.js.map