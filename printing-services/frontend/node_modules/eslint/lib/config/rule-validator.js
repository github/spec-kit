/**
 * @fileoverview Rule Validator
 * @author Nicholas C. Zakas
 */

"use strict";

//-----------------------------------------------------------------------------
// Requirements
//-----------------------------------------------------------------------------

const ajvImport = require("../shared/ajv");
const ajv = ajvImport();
const {
    parseRuleId,
    getRuleFromConfig,
    getRuleOptionsSchema
} = require("./flat-config-helpers");
const ruleReplacements = require("../../conf/replacements.json");

//-----------------------------------------------------------------------------
// Helpers
//-----------------------------------------------------------------------------

/**
 * Throws a helpful error when a rule cannot be found.
 * @param {Object} ruleId The rule identifier.
 * @param {string} ruleId.pluginName The ID of the rule to find.
 * @param {string} ruleId.ruleName The ID of the rule to find.
 * @param {Object} config The config to search in.
 * @throws {TypeError} For missing plugin or rule.
 * @returns {void}
 */
function throwRuleNotFoundError({ pluginName, ruleName }, config) {

    const ruleId = pluginName === "@" ? ruleName : `${pluginName}/${ruleName}`;

    const errorMessageHeader = `Key "rules": Key "${ruleId}"`;
    let errorMessage = `${errorMessageHeader}: Could not find plugin "${pluginName}".`;

    // if the plugin exists then we need to check if the rule exists
    if (config.plugins && config.plugins[pluginName]) {
        const replacementRuleName = ruleReplacements.rules[ruleName];

        if (pluginName === "@" && replacementRuleName) {

            errorMessage = `${errorMessageHeader}: Rule "${ruleName}" was removed and replaced by "${replacementRuleName}".`;

        } else {

            errorMessage = `${errorMessageHeader}: Could not find "${ruleName}" in plugin "${pluginName}".`;

            // otherwise, let's see if we can find the rule name elsewhere
            for (const [otherPluginName, otherPlugin] of Object.entries(config.plugins)) {
                if (otherPlugin.rules && otherPlugin.rules[ruleName]) {
                    errorMessage += ` Did you mean "${otherPluginName}/${ruleName}"?`;
                    break;
                }
            }

        }

        // falls through to throw error
    }

    throw new TypeError(errorMessage);
}

//-----------------------------------------------------------------------------
// Exports
//-----------------------------------------------------------------------------

/**
 * Implements validation functionality for the rules portion of a config.
 */
class RuleValidator {

    /**
     * Creates a new instance.
     */
    constructor() {

        /**
         * A collection of compiled validators for rules that have already
         * been validated.
         * @type {WeakMap}
         */
        this.validators = new WeakMap();
    }

    /**
     * Validates all of the rule configurations in a config against each
     * rule's schema.
     * @param {Object} config The full config to validate. This object must
     *      contain both the rules section and the plugins section.
     * @returns {void}
     * @throws {Error} If a rule's configuration does not match its schema.
     */
    validate(config) {

        if (!config.rules) {
            return;
        }

        for (const [ruleId, ruleOptions] of Object.entries(config.rules)) {

            // check for edge case
            if (ruleId === "__proto__") {
                continue;
            }

            /*
             * If a rule is disabled, we don't do any validation. This allows
             * users to safely set any value to 0 or "off" without worrying
             * that it will cause a validation error.
             *
             * Note: ruleOptions is always an array at this point because
             * this validation occurs after FlatConfigArray has merged and
             * normalized values.
             */
            if (ruleOptions[0] === 0) {
                continue;
            }

            const rule = getRuleFromConfig(ruleId, config);

            if (!rule) {
                throwRuleNotFoundError(parseRuleId(ruleId), config);
            }

            // Precompile and cache validator the first time
            if (!this.validators.has(rule)) {
                const schema = getRuleOptionsSchema(rule);

                if (schema) {
                    this.validators.set(rule, ajv.compile(schema));
                }
            }

            const validateRule = this.validators.get(rule);

            if (validateRule) {

                validateRule(ruleOptions.slice(1));

                if (validateRule.errors) {
                    throw new Error(`Key "rules": Key "${ruleId}": ${
                        validateRule.errors.map(
                            error => `\tValue ${JSON.stringify(error.data)} ${error.message}.\n`
                        ).join("")
                    }`);
                }
            }
        }
    }
}

exports.RuleValidator = RuleValidator;
