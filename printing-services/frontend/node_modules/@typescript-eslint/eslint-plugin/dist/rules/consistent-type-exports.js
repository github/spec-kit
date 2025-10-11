"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const typescript_1 = require("typescript");
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'consistent-type-exports',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Enforce consistent usage of type exports',
            requiresTypeChecking: true,
        },
        messages: {
            typeOverValue: 'All exports in the declaration are only used as types. Use `export type`.',
            singleExportIsType: 'Type export {{exportNames}} is not a value and should be exported using `export type`.',
            multipleExportsAreTypes: 'Type exports {{exportNames}} are not values and should be exported using `export type`.',
        },
        schema: [
            {
                type: 'object',
                properties: {
                    fixMixedExportsWithInlineTypeSpecifier: {
                        type: 'boolean',
                    },
                },
                additionalProperties: false,
            },
        ],
        fixable: 'code',
    },
    defaultOptions: [
        {
            fixMixedExportsWithInlineTypeSpecifier: false,
        },
    ],
    create(context, [{ fixMixedExportsWithInlineTypeSpecifier }]) {
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        const sourceExportsMap = {};
        const services = (0, util_1.getParserServices)(context);
        /**
         * Helper for identifying if an export specifier resolves to a
         * JavaScript value or a TypeScript type.
         *
         * @returns True/false if is a type or not, or undefined if the specifier
         * can't be resolved.
         */
        function isSpecifierTypeBased(specifier) {
            const checker = services.program.getTypeChecker();
            const symbol = services.getSymbolAtLocation(specifier.exported);
            if (!symbol) {
                return undefined;
            }
            const aliasedSymbol = checker.getAliasedSymbol(symbol);
            // eslint-disable-next-line @typescript-eslint/no-unsafe-enum-comparison
            if (aliasedSymbol.escapedName === 'unknown') {
                return undefined;
            }
            return !(aliasedSymbol.flags & typescript_1.SymbolFlags.Value);
        }
        return {
            ExportNamedDeclaration(node) {
                // Coerce the source into a string for use as a lookup entry.
                const source = getSourceFromExport(node) ?? 'undefined';
                // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
                const sourceExports = (sourceExportsMap[source] ||= {
                    source,
                    reportValueExports: [],
                    typeOnlyNamedExport: null,
                    valueOnlyNamedExport: null,
                });
                // Cache the first encountered exports for the package. We will need to come
                // back to these later when fixing the problems.
                if (node.exportKind === 'type') {
                    if (sourceExports.typeOnlyNamedExport == null) {
                        // The export is a type export
                        sourceExports.typeOnlyNamedExport = node;
                    }
                }
                else if (sourceExports.valueOnlyNamedExport == null) {
                    // The export is a value export
                    sourceExports.valueOnlyNamedExport = node;
                }
                // Next for the current export, we will separate type/value specifiers.
                const typeBasedSpecifiers = [];
                const inlineTypeSpecifiers = [];
                const valueSpecifiers = [];
                // Note: it is valid to export values as types. We will avoid reporting errors
                // when this is encountered.
                if (node.exportKind !== 'type') {
                    for (const specifier of node.specifiers) {
                        if (specifier.exportKind === 'type') {
                            inlineTypeSpecifiers.push(specifier);
                            continue;
                        }
                        const isTypeBased = isSpecifierTypeBased(specifier);
                        if (isTypeBased === true) {
                            typeBasedSpecifiers.push(specifier);
                        }
                        else if (isTypeBased === false) {
                            // When isTypeBased is undefined, we should avoid reporting them.
                            valueSpecifiers.push(specifier);
                        }
                    }
                }
                if ((node.exportKind === 'value' && typeBasedSpecifiers.length) ||
                    (node.exportKind === 'type' && valueSpecifiers.length)) {
                    sourceExports.reportValueExports.push({
                        node,
                        typeBasedSpecifiers,
                        valueSpecifiers,
                        inlineTypeSpecifiers,
                    });
                }
            },
            'Program:exit'() {
                for (const sourceExports of Object.values(sourceExportsMap)) {
                    // If this export has no issues, move on.
                    if (sourceExports.reportValueExports.length === 0) {
                        continue;
                    }
                    for (const report of sourceExports.reportValueExports) {
                        if (report.valueSpecifiers.length === 0) {
                            // Export is all type-only with no type specifiers; convert the entire export to `export type`.
                            context.report({
                                node: report.node,
                                messageId: 'typeOverValue',
                                *fix(fixer) {
                                    yield* fixExportInsertType(fixer, sourceCode, report.node);
                                },
                            });
                            continue;
                        }
                        // We have both type and value violations.
                        const allExportNames = report.typeBasedSpecifiers.map(specifier => specifier.local.name);
                        if (allExportNames.length === 1) {
                            const exportNames = allExportNames[0];
                            context.report({
                                node: report.node,
                                messageId: 'singleExportIsType',
                                data: { exportNames },
                                *fix(fixer) {
                                    if (fixMixedExportsWithInlineTypeSpecifier) {
                                        yield* fixAddTypeSpecifierToNamedExports(fixer, report);
                                    }
                                    else {
                                        yield* fixSeparateNamedExports(fixer, sourceCode, report);
                                    }
                                },
                            });
                        }
                        else {
                            const exportNames = (0, util_1.formatWordList)(allExportNames);
                            context.report({
                                node: report.node,
                                messageId: 'multipleExportsAreTypes',
                                data: { exportNames },
                                *fix(fixer) {
                                    if (fixMixedExportsWithInlineTypeSpecifier) {
                                        yield* fixAddTypeSpecifierToNamedExports(fixer, report);
                                    }
                                    else {
                                        yield* fixSeparateNamedExports(fixer, sourceCode, report);
                                    }
                                },
                            });
                        }
                    }
                }
            },
        };
    },
});
/**
 * Inserts "type" into an export.
 *
 * Example:
 *
 * export type { Foo } from 'foo';
 *        ^^^^
 */
function* fixExportInsertType(fixer, sourceCode, node) {
    const exportToken = (0, util_1.nullThrows)(sourceCode.getFirstToken(node), util_1.NullThrowsReasons.MissingToken('export', node.type));
    yield fixer.insertTextAfter(exportToken, ' type');
    for (const specifier of node.specifiers) {
        if (specifier.exportKind === 'type') {
            const kindToken = (0, util_1.nullThrows)(sourceCode.getFirstToken(specifier), util_1.NullThrowsReasons.MissingToken('export', specifier.type));
            const firstTokenAfter = (0, util_1.nullThrows)(sourceCode.getTokenAfter(kindToken, {
                includeComments: true,
            }), 'Missing token following the export kind.');
            yield fixer.removeRange([kindToken.range[0], firstTokenAfter.range[0]]);
        }
    }
}
/**
 * Separates the exports which mismatch the kind of export the given
 * node represents. For example, a type export's named specifiers which
 * represent values will be inserted in a separate `export` statement.
 */
function* fixSeparateNamedExports(fixer, sourceCode, report) {
    const { node, typeBasedSpecifiers, inlineTypeSpecifiers, valueSpecifiers } = report;
    const typeSpecifiers = typeBasedSpecifiers.concat(inlineTypeSpecifiers);
    const source = getSourceFromExport(node);
    const specifierNames = typeSpecifiers.map(getSpecifierText).join(', ');
    const exportToken = (0, util_1.nullThrows)(sourceCode.getFirstToken(node), util_1.NullThrowsReasons.MissingToken('export', node.type));
    // Filter the bad exports from the current line.
    const filteredSpecifierNames = valueSpecifiers
        .map(getSpecifierText)
        .join(', ');
    const openToken = (0, util_1.nullThrows)(sourceCode.getFirstToken(node, util_1.isOpeningBraceToken), util_1.NullThrowsReasons.MissingToken('{', node.type));
    const closeToken = (0, util_1.nullThrows)(sourceCode.getLastToken(node, util_1.isClosingBraceToken), util_1.NullThrowsReasons.MissingToken('}', node.type));
    // Remove exports from the current line which we're going to re-insert.
    yield fixer.replaceTextRange([openToken.range[1], closeToken.range[0]], ` ${filteredSpecifierNames} `);
    // Insert the bad exports into a new export line above.
    yield fixer.insertTextBefore(exportToken, `export type { ${specifierNames} }${source ? ` from '${source}'` : ''};\n`);
}
function* fixAddTypeSpecifierToNamedExports(fixer, report) {
    if (report.node.exportKind === 'type') {
        return;
    }
    for (const specifier of report.typeBasedSpecifiers) {
        yield fixer.insertTextBefore(specifier, 'type ');
    }
}
/**
 * Returns the source of the export, or undefined if the named export has no source.
 */
function getSourceFromExport(node) {
    if (node.source?.type === utils_1.AST_NODE_TYPES.Literal &&
        typeof node.source.value === 'string') {
        return node.source.value;
    }
    return undefined;
}
/**
 * Returns the specifier text for the export. If it is aliased, we take care to return
 * the proper formatting.
 */
function getSpecifierText(specifier) {
    return `${specifier.local.name}${specifier.exported.name !== specifier.local.name
        ? ` as ${specifier.exported.name}`
        : ''}`;
}
//# sourceMappingURL=consistent-type-exports.js.map