/**
 * @fileoverview Disallow the use of process.env()
 * @author Vignesh Anand
 * @deprecated in ESLint v7.0.0
 */
"use strict";

//------------------------------------------------------------------------------
// Rule Definition
//------------------------------------------------------------------------------

/** @type {import('../shared/types').Rule} */
module.exports = {
    meta: {
        deprecated: true,

        replacedBy: [],

        type: "suggestion",

        docs: {
            description: "Disallow the use of `process.env`",
            recommended: false,
            url: "https://eslint.org/docs/latest/rules/no-process-env"
        },

        schema: [],

        messages: {
            unexpectedProcessEnv: "Unexpected use of process.env."
        }
    },

    create(context) {

        return {

            MemberExpression(node) {
                const objectName = node.object.name,
                    propertyName = node.property.name;

                if (objectName === "process" && !node.computed && propertyName && propertyName === "env") {
                    context.report({ node, messageId: "unexpectedProcessEnv" });
                }

            }

        };

    }
};
