/**
 * @fileoverview Rule to enforce the use of `u` flag on RegExp.
 * @author Toru Nagashima
 */

"use strict";

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

const {
    CALL,
    CONSTRUCT,
    ReferenceTracker,
    getStringIfConstant
} = require("@eslint-community/eslint-utils");
const astUtils = require("./utils/ast-utils.js");
const { isValidWithUnicodeFlag } = require("./utils/regular-expressions");

//------------------------------------------------------------------------------
// Rule Definition
//------------------------------------------------------------------------------

/** @type {import('../shared/types').Rule} */
module.exports = {
    meta: {
        type: "suggestion",

        docs: {
            description: "Enforce the use of `u` or `v` flag on RegExp",
            recommended: false,
            url: "https://eslint.org/docs/latest/rules/require-unicode-regexp"
        },

        hasSuggestions: true,

        messages: {
            addUFlag: "Add the 'u' flag.",
            requireUFlag: "Use the 'u' flag."
        },

        schema: []
    },

    create(context) {

        const sourceCode = context.sourceCode;

        return {
            "Literal[regex]"(node) {
                const flags = node.regex.flags || "";

                if (!flags.includes("u") && !flags.includes("v")) {
                    context.report({
                        messageId: "requireUFlag",
                        node,
                        suggest: isValidWithUnicodeFlag(context.languageOptions.ecmaVersion, node.regex.pattern)
                            ? [
                                {
                                    fix(fixer) {
                                        return fixer.insertTextAfter(node, "u");
                                    },
                                    messageId: "addUFlag"
                                }
                            ]
                            : null
                    });
                }
            },

            Program(node) {
                const scope = sourceCode.getScope(node);
                const tracker = new ReferenceTracker(scope);
                const trackMap = {
                    RegExp: { [CALL]: true, [CONSTRUCT]: true }
                };

                for (const { node: refNode } of tracker.iterateGlobalReferences(trackMap)) {
                    const [patternNode, flagsNode] = refNode.arguments;

                    if (patternNode && patternNode.type === "SpreadElement") {
                        continue;
                    }
                    const pattern = getStringIfConstant(patternNode, scope);
                    const flags = getStringIfConstant(flagsNode, scope);

                    if (!flagsNode || (typeof flags === "string" && !flags.includes("u") && !flags.includes("v"))) {
                        context.report({
                            messageId: "requireUFlag",
                            node: refNode,
                            suggest: typeof pattern === "string" && isValidWithUnicodeFlag(context.languageOptions.ecmaVersion, pattern)
                                ? [
                                    {
                                        fix(fixer) {
                                            if (flagsNode) {
                                                if ((flagsNode.type === "Literal" && typeof flagsNode.value === "string") || flagsNode.type === "TemplateLiteral") {
                                                    const flagsNodeText = sourceCode.getText(flagsNode);

                                                    return fixer.replaceText(flagsNode, [
                                                        flagsNodeText.slice(0, flagsNodeText.length - 1),
                                                        flagsNodeText.slice(flagsNodeText.length - 1)
                                                    ].join("u"));
                                                }

                                                // We intentionally don't suggest concatenating + "u" to non-literals
                                                return null;
                                            }

                                            const penultimateToken = sourceCode.getLastToken(refNode, { skip: 1 }); // skip closing parenthesis

                                            return fixer.insertTextAfter(
                                                penultimateToken,
                                                astUtils.isCommaToken(penultimateToken)
                                                    ? ' "u",'
                                                    : ', "u"'
                                            );
                                        },
                                        messageId: "addUFlag"
                                    }
                                ]
                                : null
                        });
                    }
                }
            }
        };
    }
};
