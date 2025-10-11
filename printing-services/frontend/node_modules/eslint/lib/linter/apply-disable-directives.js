/**
 * @fileoverview A module that filters reported problems based on `eslint-disable` and `eslint-enable` comments
 * @author Teddy Katz
 */

"use strict";

//------------------------------------------------------------------------------
// Typedefs
//------------------------------------------------------------------------------

/** @typedef {import("../shared/types").LintMessage} LintMessage */

//------------------------------------------------------------------------------
// Module Definition
//------------------------------------------------------------------------------

const escapeRegExp = require("escape-string-regexp");

/**
 * Compares the locations of two objects in a source file
 * @param {{line: number, column: number}} itemA The first object
 * @param {{line: number, column: number}} itemB The second object
 * @returns {number} A value less than 1 if itemA appears before itemB in the source file, greater than 1 if
 * itemA appears after itemB in the source file, or 0 if itemA and itemB have the same location.
 */
function compareLocations(itemA, itemB) {
    return itemA.line - itemB.line || itemA.column - itemB.column;
}

/**
 * Groups a set of directives into sub-arrays by their parent comment.
 * @param {Iterable<Directive>} directives Unused directives to be removed.
 * @returns {Directive[][]} Directives grouped by their parent comment.
 */
function groupByParentComment(directives) {
    const groups = new Map();

    for (const directive of directives) {
        const { unprocessedDirective: { parentComment } } = directive;

        if (groups.has(parentComment)) {
            groups.get(parentComment).push(directive);
        } else {
            groups.set(parentComment, [directive]);
        }
    }

    return [...groups.values()];
}

/**
 * Creates removal details for a set of directives within the same comment.
 * @param {Directive[]} directives Unused directives to be removed.
 * @param {Token} commentToken The backing Comment token.
 * @returns {{ description, fix, unprocessedDirective }[]} Details for later creation of output Problems.
 */
function createIndividualDirectivesRemoval(directives, commentToken) {

    /*
     * `commentToken.value` starts right after `//` or `/*`.
     * All calculated offsets will be relative to this index.
     */
    const commentValueStart = commentToken.range[0] + "//".length;

    // Find where the list of rules starts. `\S+` matches with the directive name (e.g. `eslint-disable-line`)
    const listStartOffset = /^\s*\S+\s+/u.exec(commentToken.value)[0].length;

    /*
     * Get the list text without any surrounding whitespace. In order to preserve the original
     * formatting, we don't want to change that whitespace.
     *
     *     // eslint-disable-line rule-one , rule-two , rule-three -- comment
     *                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
     */
    const listText = commentToken.value
        .slice(listStartOffset) // remove directive name and all whitespace before the list
        .split(/\s-{2,}\s/u)[0] // remove `-- comment`, if it exists
        .trimEnd(); // remove all whitespace after the list

    /*
     * We can assume that `listText` contains multiple elements.
     * Otherwise, this function wouldn't be called - if there is
     * only one rule in the list, then the whole comment must be removed.
     */

    return directives.map(directive => {
        const { ruleId } = directive;

        const regex = new RegExp(String.raw`(?:^|\s*,\s*)(?<quote>['"]?)${escapeRegExp(ruleId)}\k<quote>(?:\s*,\s*|$)`, "u");
        const match = regex.exec(listText);
        const matchedText = match[0];
        const matchStartOffset = listStartOffset + match.index;
        const matchEndOffset = matchStartOffset + matchedText.length;

        const firstIndexOfComma = matchedText.indexOf(",");
        const lastIndexOfComma = matchedText.lastIndexOf(",");

        let removalStartOffset, removalEndOffset;

        if (firstIndexOfComma !== lastIndexOfComma) {

            /*
             * Since there are two commas, this must one of the elements in the middle of the list.
             * Matched range starts where the previous rule name ends, and ends where the next rule name starts.
             *
             *     // eslint-disable-line rule-one , rule-two , rule-three -- comment
             *                                    ^^^^^^^^^^^^^^
             *
             * We want to remove only the content between the two commas, and also one of the commas.
             *
             *     // eslint-disable-line rule-one , rule-two , rule-three -- comment
             *                                     ^^^^^^^^^^^
             */
            removalStartOffset = matchStartOffset + firstIndexOfComma;
            removalEndOffset = matchStartOffset + lastIndexOfComma;

        } else {

            /*
             * This is either the first element or the last element.
             *
             * If this is the first element, matched range starts where the first rule name starts
             * and ends where the second rule name starts. This is exactly the range we want
             * to remove so that the second rule name will start where the first one was starting
             * and thus preserve the original formatting.
             *
             *     // eslint-disable-line rule-one , rule-two , rule-three -- comment
             *                            ^^^^^^^^^^^
             *
             * Similarly, if this is the last element, we've already matched the range we want to
             * remove. The previous rule name will end where the last one was ending, relative
             * to the content on the right side.
             *
             *     // eslint-disable-line rule-one , rule-two , rule-three -- comment
             *                                               ^^^^^^^^^^^^^
             */
            removalStartOffset = matchStartOffset;
            removalEndOffset = matchEndOffset;
        }

        return {
            description: `'${ruleId}'`,
            fix: {
                range: [
                    commentValueStart + removalStartOffset,
                    commentValueStart + removalEndOffset
                ],
                text: ""
            },
            unprocessedDirective: directive.unprocessedDirective
        };
    });
}

/**
 * Creates a description of deleting an entire unused disable comment.
 * @param {Directive[]} directives Unused directives to be removed.
 * @param {Token} commentToken The backing Comment token.
 * @returns {{ description, fix, unprocessedDirective }} Details for later creation of an output Problem.
 */
function createCommentRemoval(directives, commentToken) {
    const { range } = commentToken;
    const ruleIds = directives.filter(directive => directive.ruleId).map(directive => `'${directive.ruleId}'`);

    return {
        description: ruleIds.length <= 2
            ? ruleIds.join(" or ")
            : `${ruleIds.slice(0, ruleIds.length - 1).join(", ")}, or ${ruleIds[ruleIds.length - 1]}`,
        fix: {
            range,
            text: " "
        },
        unprocessedDirective: directives[0].unprocessedDirective
    };
}

/**
 * Parses details from directives to create output Problems.
 * @param {Iterable<Directive>} allDirectives Unused directives to be removed.
 * @returns {{ description, fix, unprocessedDirective }[]} Details for later creation of output Problems.
 */
function processUnusedDirectives(allDirectives) {
    const directiveGroups = groupByParentComment(allDirectives);

    return directiveGroups.flatMap(
        directives => {
            const { parentComment } = directives[0].unprocessedDirective;
            const remainingRuleIds = new Set(parentComment.ruleIds);

            for (const directive of directives) {
                remainingRuleIds.delete(directive.ruleId);
            }

            return remainingRuleIds.size
                ? createIndividualDirectivesRemoval(directives, parentComment.commentToken)
                : [createCommentRemoval(directives, parentComment.commentToken)];
        }
    );
}

/**
 * Collect eslint-enable comments that are removing suppressions by eslint-disable comments.
 * @param {Directive[]} directives The directives to check.
 * @returns {Set<Directive>} The used eslint-enable comments
 */
function collectUsedEnableDirectives(directives) {

    /**
     * A Map of `eslint-enable` keyed by ruleIds that may be marked as used.
     * If `eslint-enable` does not have a ruleId, the key will be `null`.
     * @type {Map<string|null, Directive>}
     */
    const enabledRules = new Map();

    /**
     * A Set of `eslint-enable` marked as used.
     * It is also the return value of `collectUsedEnableDirectives` function.
     * @type {Set<Directive>}
     */
    const usedEnableDirectives = new Set();

    /*
     * Checks the directives backwards to see if the encountered `eslint-enable` is used by the previous `eslint-disable`,
     * and if so, stores the `eslint-enable` in `usedEnableDirectives`.
     */
    for (let index = directives.length - 1; index >= 0; index--) {
        const directive = directives[index];

        if (directive.type === "disable") {
            if (enabledRules.size === 0) {
                continue;
            }
            if (directive.ruleId === null) {

                // If encounter `eslint-disable` without ruleId,
                // mark all `eslint-enable` currently held in enabledRules as used.
                // e.g.
                //    /* eslint-disable */ <- current directive
                //    /* eslint-enable rule-id1 */ <- used
                //    /* eslint-enable rule-id2 */ <- used
                //    /* eslint-enable */ <- used
                for (const enableDirective of enabledRules.values()) {
                    usedEnableDirectives.add(enableDirective);
                }
                enabledRules.clear();
            } else {
                const enableDirective = enabledRules.get(directive.ruleId);

                if (enableDirective) {

                    // If encounter `eslint-disable` with ruleId, and there is an `eslint-enable` with the same ruleId in enabledRules,
                    // mark `eslint-enable` with ruleId as used.
                    // e.g.
                    //    /* eslint-disable rule-id */ <- current directive
                    //    /* eslint-enable rule-id */ <- used
                    usedEnableDirectives.add(enableDirective);
                } else {
                    const enabledDirectiveWithoutRuleId = enabledRules.get(null);

                    if (enabledDirectiveWithoutRuleId) {

                        // If encounter `eslint-disable` with ruleId, and there is no `eslint-enable` with the same ruleId in enabledRules,
                        // mark `eslint-enable` without ruleId as used.
                        // e.g.
                        //    /* eslint-disable rule-id */ <- current directive
                        //    /* eslint-enable */ <- used
                        usedEnableDirectives.add(enabledDirectiveWithoutRuleId);
                    }
                }
            }
        } else if (directive.type === "enable") {
            if (directive.ruleId === null) {

                // If encounter `eslint-enable` without ruleId, the `eslint-enable` that follows it are unused.
                // So clear enabledRules.
                // e.g.
                //    /* eslint-enable */ <- current directive
                //    /* eslint-enable rule-id *// <- unused
                //    /* eslint-enable */ <- unused
                enabledRules.clear();
                enabledRules.set(null, directive);
            } else {
                enabledRules.set(directive.ruleId, directive);
            }
        }
    }
    return usedEnableDirectives;
}

/**
 * This is the same as the exported function, except that it
 * doesn't handle disable-line and disable-next-line directives, and it always reports unused
 * disable directives.
 * @param {Object} options options for applying directives. This is the same as the options
 * for the exported function, except that `reportUnusedDisableDirectives` is not supported
 * (this function always reports unused disable directives).
 * @returns {{problems: LintMessage[], unusedDirectives: LintMessage[]}} An object with a list
 * of problems (including suppressed ones) and unused eslint-disable directives
 */
function applyDirectives(options) {
    const problems = [];
    const usedDisableDirectives = new Set();

    for (const problem of options.problems) {
        let disableDirectivesForProblem = [];
        let nextDirectiveIndex = 0;

        while (
            nextDirectiveIndex < options.directives.length &&
            compareLocations(options.directives[nextDirectiveIndex], problem) <= 0
        ) {
            const directive = options.directives[nextDirectiveIndex++];

            if (directive.ruleId === null || directive.ruleId === problem.ruleId) {
                switch (directive.type) {
                    case "disable":
                        disableDirectivesForProblem.push(directive);
                        break;

                    case "enable":
                        disableDirectivesForProblem = [];
                        break;

                    // no default
                }
            }
        }

        if (disableDirectivesForProblem.length > 0) {
            const suppressions = disableDirectivesForProblem.map(directive => ({
                kind: "directive",
                justification: directive.unprocessedDirective.justification
            }));

            if (problem.suppressions) {
                problem.suppressions = problem.suppressions.concat(suppressions);
            } else {
                problem.suppressions = suppressions;
                usedDisableDirectives.add(disableDirectivesForProblem[disableDirectivesForProblem.length - 1]);
            }
        }

        problems.push(problem);
    }

    const unusedDisableDirectivesToReport = options.directives
        .filter(directive => directive.type === "disable" && !usedDisableDirectives.has(directive));


    const unusedEnableDirectivesToReport = new Set(
        options.directives.filter(directive => directive.unprocessedDirective.type === "enable")
    );

    /*
     * If directives has the eslint-enable directive,
     * check whether the eslint-enable comment is used.
     */
    if (unusedEnableDirectivesToReport.size > 0) {
        for (const directive of collectUsedEnableDirectives(options.directives)) {
            unusedEnableDirectivesToReport.delete(directive);
        }
    }

    const processed = processUnusedDirectives(unusedDisableDirectivesToReport)
        .concat(processUnusedDirectives(unusedEnableDirectivesToReport));

    const unusedDirectives = processed
        .map(({ description, fix, unprocessedDirective }) => {
            const { parentComment, type, line, column } = unprocessedDirective;

            let message;

            if (type === "enable") {
                message = description
                    ? `Unused eslint-enable directive (no matching eslint-disable directives were found for ${description}).`
                    : "Unused eslint-enable directive (no matching eslint-disable directives were found).";
            } else {
                message = description
                    ? `Unused eslint-disable directive (no problems were reported from ${description}).`
                    : "Unused eslint-disable directive (no problems were reported).";
            }
            return {
                ruleId: null,
                message,
                line: type === "disable-next-line" ? parentComment.commentToken.loc.start.line : line,
                column: type === "disable-next-line" ? parentComment.commentToken.loc.start.column + 1 : column,
                severity: options.reportUnusedDisableDirectives === "warn" ? 1 : 2,
                nodeType: null,
                ...options.disableFixes ? {} : { fix }
            };
        });

    return { problems, unusedDirectives };
}

/**
 * Given a list of directive comments (i.e. metadata about eslint-disable and eslint-enable comments) and a list
 * of reported problems, adds the suppression information to the problems.
 * @param {Object} options Information about directives and problems
 * @param {{
 *      type: ("disable"|"enable"|"disable-line"|"disable-next-line"),
 *      ruleId: (string|null),
 *      line: number,
 *      column: number,
 *      justification: string
 * }} options.directives Directive comments found in the file, with one-based columns.
 * Two directive comments can only have the same location if they also have the same type (e.g. a single eslint-disable
 * comment for two different rules is represented as two directives).
 * @param {{ruleId: (string|null), line: number, column: number}[]} options.problems
 * A list of problems reported by rules, sorted by increasing location in the file, with one-based columns.
 * @param {"off" | "warn" | "error"} options.reportUnusedDisableDirectives If `"warn"` or `"error"`, adds additional problems for unused directives
 * @param {boolean} options.disableFixes If true, it doesn't make `fix` properties.
 * @returns {{ruleId: (string|null), line: number, column: number, suppressions?: {kind: string, justification: string}}[]}
 * An object with a list of reported problems, the suppressed of which contain the suppression information.
 */
module.exports = ({ directives, disableFixes, problems, reportUnusedDisableDirectives = "off" }) => {
    const blockDirectives = directives
        .filter(directive => directive.type === "disable" || directive.type === "enable")
        .map(directive => Object.assign({}, directive, { unprocessedDirective: directive }))
        .sort(compareLocations);

    const lineDirectives = directives.flatMap(directive => {
        switch (directive.type) {
            case "disable":
            case "enable":
                return [];

            case "disable-line":
                return [
                    { type: "disable", line: directive.line, column: 1, ruleId: directive.ruleId, unprocessedDirective: directive },
                    { type: "enable", line: directive.line + 1, column: 0, ruleId: directive.ruleId, unprocessedDirective: directive }
                ];

            case "disable-next-line":
                return [
                    { type: "disable", line: directive.line + 1, column: 1, ruleId: directive.ruleId, unprocessedDirective: directive },
                    { type: "enable", line: directive.line + 2, column: 0, ruleId: directive.ruleId, unprocessedDirective: directive }
                ];

            default:
                throw new TypeError(`Unrecognized directive type '${directive.type}'`);
        }
    }).sort(compareLocations);

    const blockDirectivesResult = applyDirectives({
        problems,
        directives: blockDirectives,
        disableFixes,
        reportUnusedDisableDirectives
    });
    const lineDirectivesResult = applyDirectives({
        problems: blockDirectivesResult.problems,
        directives: lineDirectives,
        disableFixes,
        reportUnusedDisableDirectives
    });

    return reportUnusedDisableDirectives !== "off"
        ? lineDirectivesResult.problems
            .concat(blockDirectivesResult.unusedDirectives)
            .concat(lineDirectivesResult.unusedDirectives)
            .sort(compareLocations)
        : lineDirectivesResult.problems;
};
