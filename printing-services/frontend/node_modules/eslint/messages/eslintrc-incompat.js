"use strict";

/* eslint consistent-return: 0 -- no default case */

const messages = {

    env: `
A config object is using the "env" key, which is not supported in flat config system.

Flat config uses "languageOptions.globals" to define global variables for your files.

Please see the following page for information on how to convert your config object into the correct format:
https://eslint.org/docs/latest/use/configure/migration-guide#configuring-language-options
`,

    extends: `
A config object is using the "extends" key, which is not supported in flat config system.

Instead of "extends", you can include config objects that you'd like to extend from directly in the flat config array.

Please see the following page for more information:
https://eslint.org/docs/latest/use/configure/migration-guide#predefined-and-shareable-configs
`,

    globals: `
A config object is using the "globals" key, which is not supported in flat config system.

Flat config uses "languageOptions.globals" to define global variables for your files.

Please see the following page for information on how to convert your config object into the correct format:
https://eslint.org/docs/latest/use/configure/migration-guide#configuring-language-options
`,

    ignorePatterns: `
A config object is using the "ignorePatterns" key, which is not supported in flat config system.

Flat config uses "ignores" to specify files to ignore.

Please see the following page for information on how to convert your config object into the correct format:
https://eslint.org/docs/latest/use/configure/migration-guide#ignoring-files
`,

    noInlineConfig: `
A config object is using the "noInlineConfig" key, which is not supported in flat config system.

Flat config uses "linterOptions.noInlineConfig" to specify files to ignore.

Please see the following page for information on how to convert your config object into the correct format:
https://eslint.org/docs/latest/use/configure/migration-guide#linter-options
`,

    overrides: `
A config object is using the "overrides" key, which is not supported in flat config system.

Flat config is an array that acts like the eslintrc "overrides" array.

Please see the following page for information on how to convert your config object into the correct format:
https://eslint.org/docs/latest/use/configure/migration-guide#glob-based-configs
`,

    parser: `
A config object is using the "parser" key, which is not supported in flat config system.

Flat config uses "languageOptions.parser" to override the default parser.

Please see the following page for information on how to convert your config object into the correct format:
https://eslint.org/docs/latest/use/configure/migration-guide#custom-parsers
`,

    parserOptions: `
A config object is using the "parserOptions" key, which is not supported in flat config system.

Flat config uses "languageOptions.parserOptions" to specify parser options.

Please see the following page for information on how to convert your config object into the correct format:
https://eslint.org/docs/latest/use/configure/migration-guide#configuring-language-options
`,

    reportUnusedDisableDirectives: `
A config object is using the "reportUnusedDisableDirectives" key, which is not supported in flat config system.

Flat config uses "linterOptions.reportUnusedDisableDirectives" to specify files to ignore.

Please see the following page for information on how to convert your config object into the correct format:
https://eslint.org/docs/latest/use/configure/migration-guide#linter-options
`,

    root: `
A config object is using the "root" key, which is not supported in flat config system.

Flat configs always act as if they are the root config file, so this key can be safely removed.
`
};

module.exports = function({ key }) {

    return messages[key].trim();
};
