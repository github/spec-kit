"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@typescript-eslint/utils");
const eslint_utils_1 = require("@typescript-eslint/utils/eslint-utils");
const util_1 = require("../util");
const getESLintCoreRule_1 = require("../util/getESLintCoreRule");
const baseRule = (0, getESLintCoreRule_1.getESLintCoreRule)('key-spacing');
// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
const baseSchema = Array.isArray(baseRule.meta.schema)
    ? baseRule.meta.schema[0]
    : baseRule.meta.schema;
exports.default = (0, util_1.createRule)({
    name: 'key-spacing',
    meta: {
        deprecated: true,
        replacedBy: ['@stylistic/ts/key-spacing'],
        type: 'layout',
        docs: {
            description: 'Enforce consistent spacing between property names and type annotations in types and interfaces',
            extendsBaseRule: true,
        },
        fixable: 'whitespace',
        hasSuggestions: baseRule.meta.hasSuggestions,
        schema: [baseSchema],
        messages: baseRule.meta.messages,
    },
    defaultOptions: [{}],
    create(context, [options]) {
        const sourceCode = (0, eslint_utils_1.getSourceCode)(context);
        const baseRules = baseRule.create(context);
        /**
         * @returns the column of the position after converting all unicode characters in the line to 1 char length
         */
        function adjustedColumn(position) {
            const line = position.line - 1; // position.line is 1-indexed
            return (0, util_1.getStringLength)(sourceCode.lines.at(line).slice(0, position.column));
        }
        /**
         * Starting from the given a node (a property.key node here) looks forward
         * until it finds the last token before a colon punctuator and returns it.
         */
        function getLastTokenBeforeColon(node) {
            const colonToken = sourceCode.getTokenAfter(node, util_1.isColonToken);
            return sourceCode.getTokenBefore(colonToken);
        }
        function isKeyTypeNode(node) {
            return ((node.type === utils_1.AST_NODE_TYPES.TSPropertySignature ||
                node.type === utils_1.AST_NODE_TYPES.TSIndexSignature ||
                node.type === utils_1.AST_NODE_TYPES.PropertyDefinition) &&
                !!node.typeAnnotation);
        }
        function isApplicable(node) {
            return (isKeyTypeNode(node) &&
                node.typeAnnotation.loc.start.line === node.loc.end.line);
        }
        /**
         * To handle index signatures, to get the whole text for the parameters
         */
        function getKeyText(node) {
            if (node.type !== utils_1.AST_NODE_TYPES.TSIndexSignature) {
                return sourceCode.getText(node.key);
            }
            const code = sourceCode.getText(node);
            return code.slice(0, sourceCode.getTokenAfter(node.parameters.at(-1), util_1.isClosingBracketToken).range[1] - node.range[0]);
        }
        /**
         * To handle index signatures, be able to get the end position of the parameters
         */
        function getKeyLocEnd(node) {
            return getLastTokenBeforeColon(node.type !== utils_1.AST_NODE_TYPES.TSIndexSignature
                ? node.key
                : node.parameters.at(-1)).loc.end;
        }
        function checkBeforeColon(node, expectedWhitespaceBeforeColon, mode) {
            const { typeAnnotation } = node;
            const colon = typeAnnotation.loc.start.column;
            const keyEnd = getKeyLocEnd(node);
            const difference = colon - keyEnd.column - expectedWhitespaceBeforeColon;
            if (mode === 'strict' ? difference : difference < 0) {
                context.report({
                    node,
                    messageId: difference > 0 ? 'extraKey' : 'missingKey',
                    fix: fixer => {
                        if (difference > 0) {
                            return fixer.removeRange([
                                typeAnnotation.range[0] - difference,
                                typeAnnotation.range[0],
                            ]);
                        }
                        return fixer.insertTextBefore(typeAnnotation, ' '.repeat(-difference));
                    },
                    data: {
                        computed: '',
                        key: getKeyText(node),
                    },
                });
            }
        }
        function checkAfterColon(node, expectedWhitespaceAfterColon, mode) {
            const { typeAnnotation } = node;
            const colonToken = sourceCode.getFirstToken(typeAnnotation);
            const typeStart = sourceCode.getTokenAfter(colonToken, {
                includeComments: true,
            }).loc.start.column;
            const difference = typeStart -
                colonToken.loc.start.column -
                1 -
                expectedWhitespaceAfterColon;
            if (mode === 'strict' ? difference : difference < 0) {
                context.report({
                    node,
                    messageId: difference > 0 ? 'extraValue' : 'missingValue',
                    fix: fixer => {
                        if (difference > 0) {
                            return fixer.removeRange([
                                colonToken.range[1],
                                colonToken.range[1] + difference,
                            ]);
                        }
                        return fixer.insertTextAfter(colonToken, ' '.repeat(-difference));
                    },
                    data: {
                        computed: '',
                        key: getKeyText(node),
                    },
                });
            }
        }
        // adapted from  https://github.com/eslint/eslint/blob/ba74253e8bd63e9e163bbee0540031be77e39253/lib/rules/key-spacing.js#L356
        function continuesAlignGroup(lastMember, candidate) {
            const groupEndLine = lastMember.loc.start.line;
            const candidateValueStartLine = (isKeyTypeNode(candidate) ? candidate.typeAnnotation : candidate).loc.start.line;
            if (candidateValueStartLine === groupEndLine) {
                return false;
            }
            if (candidateValueStartLine - groupEndLine === 1) {
                return true;
            }
            /*
             * Check that the first comment is adjacent to the end of the group, the
             * last comment is adjacent to the candidate property, and that successive
             * comments are adjacent to each other.
             */
            const leadingComments = sourceCode.getCommentsBefore(candidate);
            if (leadingComments.length &&
                leadingComments[0].loc.start.line - groupEndLine <= 1 &&
                candidateValueStartLine - leadingComments.at(-1).loc.end.line <= 1) {
                for (let i = 1; i < leadingComments.length; i++) {
                    if (leadingComments[i].loc.start.line -
                        leadingComments[i - 1].loc.end.line >
                        1) {
                        return false;
                    }
                }
                return true;
            }
            return false;
        }
        function checkAlignGroup(group) {
            let alignColumn = 0;
            const align = (typeof options.align === 'object'
                ? options.align.on
                : typeof options.multiLine?.align === 'object'
                    ? options.multiLine.align.on
                    : options.multiLine?.align ?? options.align) ?? 'colon';
            const beforeColon = (typeof options.align === 'object'
                ? options.align.beforeColon
                : options.multiLine
                    ? typeof options.multiLine.align === 'object'
                        ? options.multiLine.align.beforeColon
                        : options.multiLine.beforeColon
                    : options.beforeColon) ?? false;
            const expectedWhitespaceBeforeColon = beforeColon ? 1 : 0;
            const afterColon = (typeof options.align === 'object'
                ? options.align.afterColon
                : options.multiLine
                    ? typeof options.multiLine.align === 'object'
                        ? options.multiLine.align.afterColon
                        : options.multiLine.afterColon
                    : options.afterColon) ?? true;
            const expectedWhitespaceAfterColon = afterColon ? 1 : 0;
            const mode = (typeof options.align === 'object'
                ? options.align.mode
                : options.multiLine
                    ? typeof options.multiLine.align === 'object'
                        ? // same behavior as in original rule
                            options.multiLine.align.mode ?? options.multiLine.mode
                        : options.multiLine.mode
                    : options.mode) ?? 'strict';
            for (const node of group) {
                if (isKeyTypeNode(node)) {
                    const keyEnd = adjustedColumn(getKeyLocEnd(node));
                    alignColumn = Math.max(alignColumn, align === 'colon'
                        ? keyEnd + expectedWhitespaceBeforeColon
                        : keyEnd +
                            ':'.length +
                            expectedWhitespaceAfterColon +
                            expectedWhitespaceBeforeColon);
                }
            }
            for (const node of group) {
                if (!isApplicable(node)) {
                    continue;
                }
                const { typeAnnotation } = node;
                const toCheck = align === 'colon' ? typeAnnotation : typeAnnotation.typeAnnotation;
                const difference = adjustedColumn(toCheck.loc.start) - alignColumn;
                if (difference) {
                    context.report({
                        node,
                        messageId: difference > 0
                            ? align === 'colon'
                                ? 'extraKey'
                                : 'extraValue'
                            : align === 'colon'
                                ? 'missingKey'
                                : 'missingValue',
                        fix: fixer => {
                            if (difference > 0) {
                                return fixer.removeRange([
                                    toCheck.range[0] - difference,
                                    toCheck.range[0],
                                ]);
                            }
                            return fixer.insertTextBefore(toCheck, ' '.repeat(-difference));
                        },
                        data: {
                            computed: '',
                            key: getKeyText(node),
                        },
                    });
                }
                if (align === 'colon') {
                    checkAfterColon(node, expectedWhitespaceAfterColon, mode);
                }
                else {
                    checkBeforeColon(node, expectedWhitespaceBeforeColon, mode);
                }
            }
        }
        function checkIndividualNode(node, { singleLine }) {
            const beforeColon = (singleLine
                ? options.singleLine
                    ? options.singleLine.beforeColon
                    : options.beforeColon
                : options.multiLine
                    ? options.multiLine.beforeColon
                    : options.beforeColon) ?? false;
            const expectedWhitespaceBeforeColon = beforeColon ? 1 : 0;
            const afterColon = (singleLine
                ? options.singleLine
                    ? options.singleLine.afterColon
                    : options.afterColon
                : options.multiLine
                    ? options.multiLine.afterColon
                    : options.afterColon) ?? true;
            const expectedWhitespaceAfterColon = afterColon ? 1 : 0;
            const mode = (singleLine
                ? options.singleLine
                    ? options.singleLine.mode
                    : options.mode
                : options.multiLine
                    ? options.multiLine.mode
                    : options.mode) ?? 'strict';
            if (isApplicable(node)) {
                checkBeforeColon(node, expectedWhitespaceBeforeColon, mode);
                checkAfterColon(node, expectedWhitespaceAfterColon, mode);
            }
        }
        function validateBody(body) {
            const isSingleLine = body.loc.start.line === body.loc.end.line;
            const members = body.type === utils_1.AST_NODE_TYPES.TSTypeLiteral ? body.members : body.body;
            let alignGroups = [];
            let unalignedElements = [];
            if (options.align || options.multiLine?.align) {
                let currentAlignGroup = [];
                alignGroups.push(currentAlignGroup);
                let prevNode = undefined;
                for (const node of members) {
                    let prevAlignedNode = currentAlignGroup.at(-1);
                    if (prevAlignedNode !== prevNode) {
                        prevAlignedNode = undefined;
                    }
                    if (prevAlignedNode && continuesAlignGroup(prevAlignedNode, node)) {
                        currentAlignGroup.push(node);
                    }
                    else if (prevNode?.loc.start.line === node.loc.start.line) {
                        if (prevAlignedNode) {
                            // Here, prevNode === prevAlignedNode === currentAlignGroup.at(-1)
                            unalignedElements.push(prevAlignedNode);
                            currentAlignGroup.pop();
                        }
                        unalignedElements.push(node);
                    }
                    else {
                        currentAlignGroup = [node];
                        alignGroups.push(currentAlignGroup);
                    }
                    prevNode = node;
                }
                unalignedElements = unalignedElements.concat(...alignGroups.filter(group => group.length === 1));
                alignGroups = alignGroups.filter(group => group.length >= 2);
            }
            else {
                unalignedElements = members;
            }
            for (const group of alignGroups) {
                checkAlignGroup(group);
            }
            for (const node of unalignedElements) {
                checkIndividualNode(node, { singleLine: isSingleLine });
            }
        }
        return {
            ...baseRules,
            TSTypeLiteral: validateBody,
            TSInterfaceBody: validateBody,
            ClassBody: validateBody,
        };
    },
});
//# sourceMappingURL=key-spacing.js.map