"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
exports.default = (0, util_1.createRule)({
    name: 'consistent-type-imports',
    meta: {
        type: 'suggestion',
        docs: {
            description: 'Enforce consistent usage of type imports',
        },
        messages: {
            typeOverValue: 'All imports in the declaration are only used as types. Use `import type`.',
            someImportsAreOnlyTypes: 'Imports {{typeImports}} are only used as types.',
            aImportIsOnlyTypes: 'Import {{typeImports}} is only used as types.',
            someImportsInDecoMeta: 'Type imports {{typeImports}} are used by decorator metadata.',
            aImportInDecoMeta: 'Type import {{typeImports}} is used by decorator metadata.',
            valueOverType: 'Use an `import` instead of an `import type`.',
            noImportTypeAnnotations: '`import()` type annotations are forbidden.',
        },
        schema: [
            {
                type: 'object',
                properties: {
                    prefer: {
                        type: 'string',
                        enum: ['type-imports', 'no-type-imports'],
                    },
                    disallowTypeAnnotations: {
                        type: 'boolean',
                    },
                    fixStyle: {
                        type: 'string',
                        enum: ['separate-type-imports', 'inline-type-imports'],
                    },
                },
                additionalProperties: false,
            },
        ],
        fixable: 'code',
    },
    defaultOptions: [
        {
            prefer: 'type-imports',
            disallowTypeAnnotations: true,
            fixStyle: 'separate-type-imports',
        },
    ],
    create(context, [option]) {
        const prefer = option.prefer ?? 'type-imports';
        const disallowTypeAnnotations = option.disallowTypeAnnotations !== false;
        const fixStyle = option.fixStyle ?? 'separate-type-imports';
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        const sourceImportsMap = {};
        return {
            ...(prefer === 'type-imports'
                ? {
                    // prefer type imports
                    ImportDeclaration(node) {
                        const source = node.source.value;
                        // sourceImports is the object containing all the specifics for a particular import source, type or value
                        sourceImportsMap[source] ??= {
                            source,
                            reportValueImports: [], // if there is a mismatch where type importKind but value specifiers
                            typeOnlyNamedImport: null, // if only type imports
                            valueOnlyNamedImport: null, // if only value imports with named specifiers
                            valueImport: null, // if only value imports
                        };
                        const sourceImports = sourceImportsMap[source];
                        if (node.importKind === 'type') {
                            if (!sourceImports.typeOnlyNamedImport &&
                                node.specifiers.every(specifier => specifier.type === utils_1.AST_NODE_TYPES.ImportSpecifier)) {
                                // definitely import type { TypeX }
                                sourceImports.typeOnlyNamedImport = node;
                            }
                        }
                        else {
                            if (!sourceImports.valueOnlyNamedImport &&
                                node.specifiers.every(specifier => specifier.type === utils_1.AST_NODE_TYPES.ImportSpecifier)) {
                                sourceImports.valueOnlyNamedImport = node;
                                sourceImports.valueImport = node;
                            }
                            else if (!sourceImports.valueImport &&
                                node.specifiers.some(specifier => specifier.type === utils_1.AST_NODE_TYPES.ImportDefaultSpecifier)) {
                                sourceImports.valueImport = node;
                            }
                        }
                        const typeSpecifiers = [];
                        const inlineTypeSpecifiers = [];
                        const valueSpecifiers = [];
                        const unusedSpecifiers = [];
                        for (const specifier of node.specifiers) {
                            if (specifier.type === utils_1.AST_NODE_TYPES.ImportSpecifier &&
                                specifier.importKind === 'type') {
                                inlineTypeSpecifiers.push(specifier);
                                continue;
                            }
                            const [variable] = (0, eslint_utils_1.getDeclaredVariables)(context, specifier);
                            if (variable.references.length === 0) {
                                unusedSpecifiers.push(specifier);
                            }
                            else {
                                const onlyHasTypeReferences = variable.references.every(ref => {
                                    /**
                                     * keep origin import kind when export
                                     * export { Type }
                                     * export default Type;
                                     * export = Type;
                                     */
                                    if (ref.identifier.parent.type ===
                                        utils_1.AST_NODE_TYPES.ExportSpecifier ||
                                        ref.identifier.parent.type ===
                                            utils_1.AST_NODE_TYPES.ExportDefaultDeclaration ||
                                        ref.identifier.parent.type ===
                                            utils_1.AST_NODE_TYPES.TSExportAssignment) {
                                        if (ref.isValueReference && ref.isTypeReference) {
                                            return node.importKind === 'type';
                                        }
                                    }
                                    if (ref.isValueReference) {
                                        let parent = ref.identifier.parent;
                                        let child = ref.identifier;
                                        while (parent) {
                                            switch (parent.type) {
                                                // CASE 1:
                                                // `type T = typeof foo` will create a value reference because "foo" must be a value type
                                                // however this value reference is safe to use with type-only imports
                                                case utils_1.AST_NODE_TYPES.TSTypeQuery:
                                                    return true;
                                                case utils_1.AST_NODE_TYPES.TSQualifiedName:
                                                    // TSTypeQuery must have a TSESTree.EntityName as its child, so we can filter here and break early
                                                    if (parent.left !== child) {
                                                        return false;
                                                    }
                                                    child = parent;
                                                    parent = parent.parent;
                                                    continue;
                                                // END CASE 1
                                                //////////////
                                                // CASE 2:
                                                // `type T = { [foo]: string }` will create a value reference because "foo" must be a value type
                                                // however this value reference is safe to use with type-only imports.
                                                // Also this is represented as a non-type AST - hence it uses MemberExpression
                                                case utils_1.AST_NODE_TYPES.TSPropertySignature:
                                                    return parent.key === child;
                                                case utils_1.AST_NODE_TYPES.MemberExpression:
                                                    if (parent.object !== child) {
                                                        return false;
                                                    }
                                                    child = parent;
                                                    parent = parent.parent;
                                                    continue;
                                                // END CASE 2
                                                default:
                                                    return false;
                                            }
                                        }
                                    }
                                    return ref.isTypeReference;
                                });
                                if (onlyHasTypeReferences) {
                                    typeSpecifiers.push(specifier);
                                }
                                else {
                                    valueSpecifiers.push(specifier);
                                }
                            }
                        }
                        if ((node.importKind === 'value' && typeSpecifiers.length) ||
                            (node.importKind === 'type' && valueSpecifiers.length)) {
                            sourceImports.reportValueImports.push({
                                node,
                                typeSpecifiers,
                                valueSpecifiers,
                                unusedSpecifiers,
                                inlineTypeSpecifiers,
                            });
                        }
                    },
                    'Program:exit'() {
                        for (const sourceImports of Object.values(sourceImportsMap)) {
                            if (sourceImports.reportValueImports.length === 0) {
                                // nothing to fix. value specifiers and type specifiers are correctly written
                                continue;
                            }
                            for (const report of sourceImports.reportValueImports) {
                                if (report.valueSpecifiers.length === 0 &&
                                    report.unusedSpecifiers.length === 0 &&
                                    report.node.importKind !== 'type') {
                                    /**
                                     * checks if import has type assertions
                                     * ```
                                     * import * as type from 'mod' assert { type: 'json' };
                                     * ```
                                     * https://github.com/typescript-eslint/typescript-eslint/issues/7527
                                     */
                                    if (report.node.attributes.length === 0) {
                                        context.report({
                                            node: report.node,
                                            messageId: 'typeOverValue',
                                            *fix(fixer) {
                                                yield* fixToTypeImportDeclaration(fixer, report, sourceImports);
                                            },
                                        });
                                    }
                                }
                                else {
                                    const isTypeImport = report.node.importKind === 'type';
                                    // we have a mixed type/value import or just value imports, so we need to split them out into multiple imports if separate-type-imports is configured
                                    const importNames = (isTypeImport
                                        ? report.valueSpecifiers // import type { A } from 'roo'; // WHERE A is used in value position
                                        : report.typeSpecifiers) // import { A, B } from 'roo'; // WHERE A is used in type position and B is in value position
                                        .map(specifier => `"${specifier.local.name}"`);
                                    const message = (() => {
                                        const typeImports = (0, util_1.formatWordList)(importNames);
                                        if (importNames.length === 1) {
                                            if (isTypeImport) {
                                                return {
                                                    messageId: 'aImportInDecoMeta',
                                                    data: { typeImports },
                                                };
                                            }
                                            return {
                                                messageId: 'aImportIsOnlyTypes',
                                                data: { typeImports },
                                            };
                                        }
                                        if (isTypeImport) {
                                            return {
                                                messageId: 'someImportsInDecoMeta',
                                                data: { typeImports }, // typeImports are all the value specifiers that are in the type position
                                            };
                                        }
                                        return {
                                            messageId: 'someImportsAreOnlyTypes',
                                            data: { typeImports }, // typeImports are all the type specifiers in the value position
                                        };
                                    })();
                                    context.report({
                                        node: report.node,
                                        ...message,
                                        *fix(fixer) {
                                            if (isTypeImport) {
                                                // take all the valueSpecifiers and put them on a new line
                                                yield* fixToValueImportDeclaration(fixer, report, sourceImports);
                                            }
                                            else {
                                                // take all the typeSpecifiers and put them on a new line
                                                yield* fixToTypeImportDeclaration(fixer, report, sourceImports);
                                            }
                                        },
                                    });
                                }
                            }
                        }
                    },
                }
                : {
                    // prefer no type imports
                    'ImportDeclaration[importKind = "type"]'(node) {
                        context.report({
                            node,
                            messageId: 'valueOverType',
                            fix(fixer) {
                                return fixRemoveTypeSpecifierFromImportDeclaration(fixer, node);
                            },
                        });
                    },
                    'ImportSpecifier[importKind = "type"]'(node) {
                        context.report({
                            node,
                            messageId: 'valueOverType',
                            fix(fixer) {
                                return fixRemoveTypeSpecifierFromImportSpecifier(fixer, node);
                            },
                        });
                    },
                }),
            ...(disallowTypeAnnotations
                ? {
                    // disallow `import()` type
                    TSImportType(node) {
                        context.report({
                            node,
                            messageId: 'noImportTypeAnnotations',
                        });
                    },
                }
                : {}),
        };
        function classifySpecifier(node) {
            const defaultSpecifier = node.specifiers[0].type === utils_1.AST_NODE_TYPES.ImportDefaultSpecifier
                ? node.specifiers[0]
                : null;
            const namespaceSpecifier = node.specifiers.find((specifier) => specifier.type === utils_1.AST_NODE_TYPES.ImportNamespaceSpecifier) ?? null;
            const namedSpecifiers = node.specifiers.filter((specifier) => specifier.type === utils_1.AST_NODE_TYPES.ImportSpecifier);
            return {
                defaultSpecifier,
                namespaceSpecifier,
                namedSpecifiers,
            };
        }
        /**
         * Returns information for fixing named specifiers, type or value
         */
        function getFixesNamedSpecifiers(fixer, node, subsetNamedSpecifiers, allNamedSpecifiers) {
            if (allNamedSpecifiers.length === 0) {
                return {
                    typeNamedSpecifiersText: '',
                    removeTypeNamedSpecifiers: [],
                };
            }
            const typeNamedSpecifiersTexts = [];
            const removeTypeNamedSpecifiers = [];
            if (subsetNamedSpecifiers.length === allNamedSpecifiers.length) {
                // import Foo, {Type1, Type2} from 'foo'
                // import DefType, {Type1, Type2} from 'foo'
                const openingBraceToken = (0, util_1.nullThrows)(sourceCode.getTokenBefore(subsetNamedSpecifiers[0], util_1.isOpeningBraceToken), util_1.NullThrowsReasons.MissingToken('{', node.type));
                const commaToken = (0, util_1.nullThrows)(sourceCode.getTokenBefore(openingBraceToken, util_1.isCommaToken), util_1.NullThrowsReasons.MissingToken(',', node.type));
                const closingBraceToken = (0, util_1.nullThrows)(sourceCode.getFirstTokenBetween(openingBraceToken, node.source, util_1.isClosingBraceToken), util_1.NullThrowsReasons.MissingToken('}', node.type));
                // import DefType, {...} from 'foo'
                //               ^^^^^^^ remove
                removeTypeNamedSpecifiers.push(fixer.removeRange([commaToken.range[0], closingBraceToken.range[1]]));
                typeNamedSpecifiersTexts.push(sourceCode.text.slice(openingBraceToken.range[1], closingBraceToken.range[0]));
            }
            else {
                const namedSpecifierGroups = [];
                let group = [];
                for (const namedSpecifier of allNamedSpecifiers) {
                    if (subsetNamedSpecifiers.includes(namedSpecifier)) {
                        group.push(namedSpecifier);
                    }
                    else if (group.length) {
                        namedSpecifierGroups.push(group);
                        group = [];
                    }
                }
                if (group.length) {
                    namedSpecifierGroups.push(group);
                }
                for (const namedSpecifiers of namedSpecifierGroups) {
                    const { removeRange, textRange } = getNamedSpecifierRanges(namedSpecifiers, allNamedSpecifiers);
                    removeTypeNamedSpecifiers.push(fixer.removeRange(removeRange));
                    typeNamedSpecifiersTexts.push(sourceCode.text.slice(...textRange));
                }
            }
            return {
                typeNamedSpecifiersText: typeNamedSpecifiersTexts.join(','),
                removeTypeNamedSpecifiers,
            };
        }
        /**
         * Returns ranges for fixing named specifier.
         */
        function getNamedSpecifierRanges(namedSpecifierGroup, allNamedSpecifiers) {
            const first = namedSpecifierGroup[0];
            const last = namedSpecifierGroup[namedSpecifierGroup.length - 1];
            const removeRange = [first.range[0], last.range[1]];
            const textRange = [...removeRange];
            const before = sourceCode.getTokenBefore(first);
            textRange[0] = before.range[1];
            if ((0, util_1.isCommaToken)(before)) {
                removeRange[0] = before.range[0];
            }
            else {
                removeRange[0] = before.range[1];
            }
            const isFirst = allNamedSpecifiers[0] === first;
            const isLast = allNamedSpecifiers[allNamedSpecifiers.length - 1] === last;
            const after = sourceCode.getTokenAfter(last);
            textRange[1] = after.range[0];
            if (isFirst || isLast) {
                if ((0, util_1.isCommaToken)(after)) {
                    removeRange[1] = after.range[1];
                }
            }
            return {
                textRange,
                removeRange,
            };
        }
        /**
         * insert specifiers to named import node.
         * e.g.
         * import type { Already, Type1, Type2 } from 'foo'
         *                        ^^^^^^^^^^^^^ insert
         */
        function fixInsertNamedSpecifiersInNamedSpecifierList(fixer, target, insertText) {
            const closingBraceToken = (0, util_1.nullThrows)(sourceCode.getFirstTokenBetween(sourceCode.getFirstToken(target), target.source, util_1.isClosingBraceToken), util_1.NullThrowsReasons.MissingToken('}', target.type));
            const before = sourceCode.getTokenBefore(closingBraceToken);
            if (!(0, util_1.isCommaToken)(before) && !(0, util_1.isOpeningBraceToken)(before)) {
                insertText = `,${insertText}`;
            }
            return fixer.insertTextBefore(closingBraceToken, insertText);
        }
        /**
         * insert type keyword to named import node.
         * e.g.
         * import ADefault, { Already, type Type1, type Type2 } from 'foo'
         *                             ^^^^ insert
         */
        function* fixInsertTypeKeywordInNamedSpecifierList(fixer, typeSpecifiers) {
            for (const spec of typeSpecifiers) {
                const insertText = sourceCode.text.slice(...spec.range);
                yield fixer.replaceTextRange(spec.range, `type ${insertText}`);
            }
        }
        function* fixInlineTypeImportDeclaration(fixer, report, sourceImports) {
            const { node } = report;
            // For a value import, will only add an inline type to named specifiers
            const { namedSpecifiers } = classifySpecifier(node);
            const typeNamedSpecifiers = namedSpecifiers.filter(specifier => report.typeSpecifiers.includes(specifier));
            if (sourceImports.valueImport) {
                // add import named type specifiers to its value import
                // import ValueA, { type A }
                //                  ^^^^ insert
                const { namedSpecifiers: valueImportNamedSpecifiers } = classifySpecifier(sourceImports.valueImport);
                if (sourceImports.valueOnlyNamedImport ||
                    valueImportNamedSpecifiers.length) {
                    yield* fixInsertTypeKeywordInNamedSpecifierList(fixer, typeNamedSpecifiers);
                }
            }
        }
        function* fixToTypeImportDeclaration(fixer, report, sourceImports) {
            const { node } = report;
            const { defaultSpecifier, namespaceSpecifier, namedSpecifiers } = classifySpecifier(node);
            if (namespaceSpecifier && !defaultSpecifier) {
                // import * as types from 'foo'
                // checks for presence of import assertions
                if (node.attributes.length === 0) {
                    yield* fixInsertTypeSpecifierForImportDeclaration(fixer, node, false);
                }
                return;
            }
            else if (defaultSpecifier) {
                if (report.typeSpecifiers.includes(defaultSpecifier) &&
                    namedSpecifiers.length === 0 &&
                    !namespaceSpecifier) {
                    // import Type from 'foo'
                    yield* fixInsertTypeSpecifierForImportDeclaration(fixer, node, true);
                    return;
                }
                else if (fixStyle === 'inline-type-imports' &&
                    !report.typeSpecifiers.includes(defaultSpecifier) &&
                    namedSpecifiers.length > 0 &&
                    !namespaceSpecifier) {
                    // if there is a default specifier but it isn't a type specifier, then just add the inline type modifier to the named specifiers
                    // import AValue, {BValue, Type1, Type2} from 'foo'
                    yield* fixInlineTypeImportDeclaration(fixer, report, sourceImports);
                    return;
                }
            }
            else if (!namespaceSpecifier) {
                if (fixStyle === 'inline-type-imports' &&
                    namedSpecifiers.some(specifier => report.typeSpecifiers.includes(specifier))) {
                    // import {AValue, Type1, Type2} from 'foo'
                    yield* fixInlineTypeImportDeclaration(fixer, report, sourceImports);
                    return;
                }
                else if (namedSpecifiers.every(specifier => report.typeSpecifiers.includes(specifier))) {
                    // import {Type1, Type2} from 'foo'
                    yield* fixInsertTypeSpecifierForImportDeclaration(fixer, node, false);
                    return;
                }
            }
            const typeNamedSpecifiers = namedSpecifiers.filter(specifier => report.typeSpecifiers.includes(specifier));
            const fixesNamedSpecifiers = getFixesNamedSpecifiers(fixer, node, typeNamedSpecifiers, namedSpecifiers);
            const afterFixes = [];
            if (typeNamedSpecifiers.length) {
                if (sourceImports.typeOnlyNamedImport) {
                    const insertTypeNamedSpecifiers = fixInsertNamedSpecifiersInNamedSpecifierList(fixer, sourceImports.typeOnlyNamedImport, fixesNamedSpecifiers.typeNamedSpecifiersText);
                    if (sourceImports.typeOnlyNamedImport.range[1] <= node.range[0]) {
                        yield insertTypeNamedSpecifiers;
                    }
                    else {
                        afterFixes.push(insertTypeNamedSpecifiers);
                    }
                }
                else {
                    // The import is both default and named.  Insert named on new line because can't mix default type import and named type imports
                    if (fixStyle === 'inline-type-imports') {
                        yield fixer.insertTextBefore(node, `import {${typeNamedSpecifiers
                            .map(spec => {
                            const insertText = sourceCode.text.slice(...spec.range);
                            return `type ${insertText}`;
                        })
                            .join(', ')}} from ${sourceCode.getText(node.source)};\n`);
                    }
                    else {
                        yield fixer.insertTextBefore(node, `import type {${fixesNamedSpecifiers.typeNamedSpecifiersText}} from ${sourceCode.getText(node.source)};\n`);
                    }
                }
            }
            const fixesRemoveTypeNamespaceSpecifier = [];
            if (namespaceSpecifier &&
                report.typeSpecifiers.includes(namespaceSpecifier)) {
                // import Foo, * as Type from 'foo'
                // import DefType, * as Type from 'foo'
                // import DefType, * as Type from 'foo'
                const commaToken = (0, util_1.nullThrows)(sourceCode.getTokenBefore(namespaceSpecifier, util_1.isCommaToken), util_1.NullThrowsReasons.MissingToken(',', node.type));
                // import Def, * as Ns from 'foo'
                //           ^^^^^^^^^ remove
                fixesRemoveTypeNamespaceSpecifier.push(fixer.removeRange([commaToken.range[0], namespaceSpecifier.range[1]]));
                // import type * as Ns from 'foo'
                // ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ insert
                yield fixer.insertTextBefore(node, `import type ${sourceCode.getText(namespaceSpecifier)} from ${sourceCode.getText(node.source)};\n`);
            }
            if (defaultSpecifier &&
                report.typeSpecifiers.includes(defaultSpecifier)) {
                if (report.typeSpecifiers.length === node.specifiers.length) {
                    const importToken = (0, util_1.nullThrows)(sourceCode.getFirstToken(node, util_1.isImportKeyword), util_1.NullThrowsReasons.MissingToken('import', node.type));
                    // import type Type from 'foo'
                    //        ^^^^ insert
                    yield fixer.insertTextAfter(importToken, ' type');
                }
                else {
                    const commaToken = (0, util_1.nullThrows)(sourceCode.getTokenAfter(defaultSpecifier, util_1.isCommaToken), util_1.NullThrowsReasons.MissingToken(',', defaultSpecifier.type));
                    // import Type , {...} from 'foo'
                    //        ^^^^^ pick
                    const defaultText = sourceCode.text
                        .slice(defaultSpecifier.range[0], commaToken.range[0])
                        .trim();
                    yield fixer.insertTextBefore(node, `import type ${defaultText} from ${sourceCode.getText(node.source)};\n`);
                    const afterToken = (0, util_1.nullThrows)(sourceCode.getTokenAfter(commaToken, { includeComments: true }), util_1.NullThrowsReasons.MissingToken('any token', node.type));
                    // import Type , {...} from 'foo'
                    //        ^^^^^^^ remove
                    yield fixer.removeRange([
                        defaultSpecifier.range[0],
                        afterToken.range[0],
                    ]);
                }
            }
            yield* fixesNamedSpecifiers.removeTypeNamedSpecifiers;
            yield* fixesRemoveTypeNamespaceSpecifier;
            yield* afterFixes;
        }
        function* fixInsertTypeSpecifierForImportDeclaration(fixer, node, isDefaultImport) {
            // import type Foo from 'foo'
            //       ^^^^^ insert
            const importToken = (0, util_1.nullThrows)(sourceCode.getFirstToken(node, util_1.isImportKeyword), util_1.NullThrowsReasons.MissingToken('import', node.type));
            yield fixer.insertTextAfter(importToken, ' type');
            if (isDefaultImport) {
                // Has default import
                const openingBraceToken = sourceCode.getFirstTokenBetween(importToken, node.source, util_1.isOpeningBraceToken);
                if (openingBraceToken) {
                    // Only braces. e.g. import Foo, {} from 'foo'
                    const commaToken = (0, util_1.nullThrows)(sourceCode.getTokenBefore(openingBraceToken, util_1.isCommaToken), util_1.NullThrowsReasons.MissingToken(',', node.type));
                    const closingBraceToken = (0, util_1.nullThrows)(sourceCode.getFirstTokenBetween(openingBraceToken, node.source, util_1.isClosingBraceToken), util_1.NullThrowsReasons.MissingToken('}', node.type));
                    // import type Foo, {} from 'foo'
                    //                  ^^ remove
                    yield fixer.removeRange([
                        commaToken.range[0],
                        closingBraceToken.range[1],
                    ]);
                    const specifiersText = sourceCode.text.slice(commaToken.range[1], closingBraceToken.range[1]);
                    if (node.specifiers.length > 1) {
                        yield fixer.insertTextAfter(node, `\nimport type${specifiersText} from ${sourceCode.getText(node.source)};`);
                    }
                }
            }
            // make sure we don't do anything like `import type {type T} from 'foo';`
            for (const specifier of node.specifiers) {
                if (specifier.type === utils_1.AST_NODE_TYPES.ImportSpecifier &&
                    specifier.importKind === 'type') {
                    yield* fixRemoveTypeSpecifierFromImportSpecifier(fixer, specifier);
                }
            }
        }
        function* fixToValueImportDeclaration(fixer, report, sourceImports) {
            const { node } = report;
            const { defaultSpecifier, namespaceSpecifier, namedSpecifiers } = classifySpecifier(node);
            if (namespaceSpecifier) {
                // import type * as types from 'foo'
                yield* fixRemoveTypeSpecifierFromImportDeclaration(fixer, node);
                return;
            }
            else if (defaultSpecifier) {
                if (report.valueSpecifiers.includes(defaultSpecifier) &&
                    namedSpecifiers.length === 0) {
                    // import type Type from 'foo'
                    yield* fixRemoveTypeSpecifierFromImportDeclaration(fixer, node);
                    return;
                }
            }
            else {
                if (namedSpecifiers.every(specifier => report.valueSpecifiers.includes(specifier))) {
                    // import type {Type1, Type2} from 'foo'
                    yield* fixRemoveTypeSpecifierFromImportDeclaration(fixer, node);
                    return;
                }
            }
            // we have some valueSpecifiers intermixed in types that need to be put on their own line
            // import type { Type1, A } from 'foo'
            // import type { A } from 'foo'
            const valueNamedSpecifiers = namedSpecifiers.filter(specifier => report.valueSpecifiers.includes(specifier));
            const fixesNamedSpecifiers = getFixesNamedSpecifiers(fixer, node, valueNamedSpecifiers, namedSpecifiers);
            const afterFixes = [];
            if (valueNamedSpecifiers.length) {
                if (sourceImports.valueOnlyNamedImport) {
                    const insertTypeNamedSpecifiers = fixInsertNamedSpecifiersInNamedSpecifierList(fixer, sourceImports.valueOnlyNamedImport, fixesNamedSpecifiers.typeNamedSpecifiersText);
                    if (sourceImports.valueOnlyNamedImport.range[1] <= node.range[0]) {
                        yield insertTypeNamedSpecifiers;
                    }
                    else {
                        afterFixes.push(insertTypeNamedSpecifiers);
                    }
                }
                else {
                    // some are types.
                    // Add new value import and later remove those value specifiers from import type
                    yield fixer.insertTextBefore(node, `import {${fixesNamedSpecifiers.typeNamedSpecifiersText}} from ${sourceCode.getText(node.source)};\n`);
                }
            }
            yield* fixesNamedSpecifiers.removeTypeNamedSpecifiers;
            yield* afterFixes;
        }
        function* fixRemoveTypeSpecifierFromImportDeclaration(fixer, node) {
            // import type Foo from 'foo'
            //        ^^^^ remove
            const importToken = (0, util_1.nullThrows)(sourceCode.getFirstToken(node, util_1.isImportKeyword), util_1.NullThrowsReasons.MissingToken('import', node.type));
            const typeToken = (0, util_1.nullThrows)(sourceCode.getFirstTokenBetween(importToken, node.specifiers[0]?.local ?? node.source, util_1.isTypeKeyword), util_1.NullThrowsReasons.MissingToken('type', node.type));
            const afterToken = (0, util_1.nullThrows)(sourceCode.getTokenAfter(typeToken, { includeComments: true }), util_1.NullThrowsReasons.MissingToken('any token', node.type));
            yield fixer.removeRange([typeToken.range[0], afterToken.range[0]]);
        }
        function* fixRemoveTypeSpecifierFromImportSpecifier(fixer, node) {
            // import { type Foo } from 'foo'
            //          ^^^^ remove
            const typeToken = (0, util_1.nullThrows)(sourceCode.getFirstToken(node, util_1.isTypeKeyword), util_1.NullThrowsReasons.MissingToken('type', node.type));
            const afterToken = (0, util_1.nullThrows)(sourceCode.getTokenAfter(typeToken, { includeComments: true }), util_1.NullThrowsReasons.MissingToken('any token', node.type));
            yield fixer.removeRange([typeToken.range[0], afterToken.range[0]]);
        }
    },
});
//# sourceMappingURL=consistent-type-imports.js.map