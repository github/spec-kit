/**
 * @fileoverview Rule to flag fall-through cases in switch statements.
 * @author Matt DuVall <http://mattduvall.com/>
 */
"use strict";

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

const { directivesPattern } = require("../shared/directives");

//------------------------------------------------------------------------------
// Helpers
//------------------------------------------------------------------------------

const DEFAULT_FALLTHROUGH_COMMENT = /falls?\s?through/iu;

/**
 * Checks all segments in a set and returns true if any are reachable.
 * @param {Set<CodePathSegment>} segments The segments to check.
 * @returns {boolean} True if any segment is reachable; false otherwise.
 */
function isAnySegmentReachable(segments) {

    for (const segment of segments) {
        if (segment.reachable) {
            return true;
        }
    }

    return false;
}

/**
 * Checks whether or not a given comment string is really a fallthrough comment and not an ESLint directive.
 * @param {string} comment The comment string to check.
 * @param {RegExp} fallthroughCommentPattern The regular expression used for checking for fallthrough comments.
 * @returns {boolean} `true` if the comment string is truly a fallthrough comment.
 */
function isFallThroughComment(comment, fallthroughCommentPattern) {
    return fallthroughCommentPattern.test(comment) && !directivesPattern.test(comment.trim());
}

/**
 * Checks whether or not a given case has a fallthrough comment.
 * @param {ASTNode} caseWhichFallsThrough SwitchCase node which falls through.
 * @param {ASTNode} subsequentCase The case after caseWhichFallsThrough.
 * @param {RuleContext} context A rule context which stores comments.
 * @param {RegExp} fallthroughCommentPattern A pattern to match comment to.
 * @returns {boolean} `true` if the case has a valid fallthrough comment.
 */
function hasFallthroughComment(caseWhichFallsThrough, subsequentCase, context, fallthroughCommentPattern) {
    const sourceCode = context.sourceCode;

    if (caseWhichFallsThrough.consequent.length === 1 && caseWhichFallsThrough.consequent[0].type === "BlockStatement") {
        const trailingCloseBrace = sourceCode.getLastToken(caseWhichFallsThrough.consequent[0]);
        const commentInBlock = sourceCode.getCommentsBefore(trailingCloseBrace).pop();

        if (commentInBlock && isFallThroughComment(commentInBlock.value, fallthroughCommentPattern)) {
            return true;
        }
    }

    const comment = sourceCode.getCommentsBefore(subsequentCase).pop();

    return Boolean(comment && isFallThroughComment(comment.value, fallthroughCommentPattern));
}

/**
 * Checks whether a node and a token are separated by blank lines
 * @param {ASTNode} node The node to check
 * @param {Token} token The token to compare against
 * @returns {boolean} `true` if there are blank lines between node and token
 */
function hasBlankLinesBetween(node, token) {
    return token.loc.start.line > node.loc.end.line + 1;
}

//------------------------------------------------------------------------------
// Rule Definition
//------------------------------------------------------------------------------

/** @type {import('../shared/types').Rule} */
module.exports = {
    meta: {
        type: "problem",

        docs: {
            description: "Disallow fallthrough of `case` statements",
            recommended: true,
            url: "https://eslint.org/docs/latest/rules/no-fallthrough"
        },

        schema: [
            {
                type: "object",
                properties: {
                    commentPattern: {
                        type: "string",
                        default: ""
                    },
                    allowEmptyCase: {
                        type: "boolean",
                        default: false
                    }
                },
                additionalProperties: false
            }
        ],
        messages: {
            case: "Expected a 'break' statement before 'case'.",
            default: "Expected a 'break' statement before 'default'."
        }
    },

    create(context) {
        const options = context.options[0] || {};
        const codePathSegments = [];
        let currentCodePathSegments = new Set();
        const sourceCode = context.sourceCode;
        const allowEmptyCase = options.allowEmptyCase || false;

        /*
         * We need to use leading comments of the next SwitchCase node because
         * trailing comments is wrong if semicolons are omitted.
         */
        let fallthroughCase = null;
        let fallthroughCommentPattern = null;

        if (options.commentPattern) {
            fallthroughCommentPattern = new RegExp(options.commentPattern, "u");
        } else {
            fallthroughCommentPattern = DEFAULT_FALLTHROUGH_COMMENT;
        }
        return {

            onCodePathStart() {
                codePathSegments.push(currentCodePathSegments);
                currentCodePathSegments = new Set();
            },

            onCodePathEnd() {
                currentCodePathSegments = codePathSegments.pop();
            },

            onUnreachableCodePathSegmentStart(segment) {
                currentCodePathSegments.add(segment);
            },

            onUnreachableCodePathSegmentEnd(segment) {
                currentCodePathSegments.delete(segment);
            },

            onCodePathSegmentStart(segment) {
                currentCodePathSegments.add(segment);
            },

            onCodePathSegmentEnd(segment) {
                currentCodePathSegments.delete(segment);
            },


            SwitchCase(node) {

                /*
                 * Checks whether or not there is a fallthrough comment.
                 * And reports the previous fallthrough node if that does not exist.
                 */

                if (fallthroughCase && (!hasFallthroughComment(fallthroughCase, node, context, fallthroughCommentPattern))) {
                    context.report({
                        messageId: node.test ? "case" : "default",
                        node
                    });
                }
                fallthroughCase = null;
            },

            "SwitchCase:exit"(node) {
                const nextToken = sourceCode.getTokenAfter(node);

                /*
                 * `reachable` meant fall through because statements preceded by
                 * `break`, `return`, or `throw` are unreachable.
                 * And allows empty cases and the last case.
                 */
                if (isAnySegmentReachable(currentCodePathSegments) &&
                    (node.consequent.length > 0 || (!allowEmptyCase && hasBlankLinesBetween(node, nextToken))) &&
                    node.parent.cases[node.parent.cases.length - 1] !== node) {
                    fallthroughCase = node;
                }
            }
        };
    }
};
