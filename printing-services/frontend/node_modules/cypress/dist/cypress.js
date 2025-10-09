"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
// https://github.com/cypress-io/cypress/issues/316
const tmp_1 = __importDefault(require("tmp"));
const fs_extra_1 = __importDefault(require("fs-extra"));
const open_1 = __importDefault(require("./exec/open"));
const run_1 = __importDefault(require("./exec/run"));
const util_1 = __importDefault(require("./util"));
const cli_1 = __importDefault(require("./cli"));
const cypressModuleApi = {
    /**
     * Opens Cypress GUI
     * @see https://on.cypress.io/module-api#cypress-open
     */
    open(options = {}) {
        options = util_1.default.normalizeModuleOptions(options);
        return open_1.default.start(options);
    },
    /**
     * Runs Cypress tests in the current project
     * @see https://on.cypress.io/module-api#cypress-run
     */
    run() {
        return __awaiter(this, arguments, void 0, function* (options = {}) {
            if (!run_1.default.isValidProject(options.project)) {
                throw new Error(`Invalid project path parameter: ${options.project}`);
            }
            options = util_1.default.normalizeModuleOptions(options);
            tmp_1.default.setGracefulCleanup();
            const outputPath = tmp_1.default.fileSync().name;
            options.outputPath = outputPath;
            const failedTests = yield run_1.default.start(options);
            const output = yield fs_extra_1.default.readJson(outputPath, { throws: false });
            if (!output) {
                return {
                    status: 'failed',
                    failures: failedTests,
                    message: 'Could not find Cypress test run results',
                };
            }
            return output;
        });
    },
    cli: {
        /**
         * Parses CLI arguments into an object that you can pass to "cypress.run"
         * @example
         *  const cypress = require('cypress')
         *  const cli = ['cypress', 'run', '--browser', 'firefox']
         *  const options = await cypress.cli.parseRunArguments(cli)
         *  // options is {browser: 'firefox'}
         *  await cypress.run(options)
         * @see https://on.cypress.io/module-api
         */
        parseRunArguments(args) {
            return cli_1.default.parseRunCommand(args);
        },
    },
    /**
     * Provides automatic code completion for configuration in many popular code editors.
     * While it's not strictly necessary for Cypress to parse your configuration, we
     * recommend wrapping your config object with `defineConfig()`
     * @example
     * module.exports = defineConfig({
     *   viewportWith: 400
     * })
     *
     * @see ../types/cypress-npm-api.d.ts
     * @param {Cypress.ConfigOptions} config
     * @returns {Cypress.ConfigOptions} the configuration passed in parameter
     */
    defineConfig(config) {
        return config;
    },
    /**
     * Provides automatic code completion for Component Frameworks Definitions.
     * While it's not strictly necessary for Cypress to parse your configuration, we
     * recommend wrapping your Component Framework Definition object with `defineComponentFramework()`
     * @example
     * module.exports = defineComponentFramework({
     *   type: 'cypress-ct-solid-js'
     *   // ...
     * })
     *
     * @see ../types/cypress-npm-api.d.ts
     * @param {Cypress.ThirdPartyComponentFrameworkDefinition} config
     * @returns {Cypress.ThirdPartyComponentFrameworkDefinition} the configuration passed in parameter
     */
    defineComponentFramework(config) {
        return config;
    },
};
module.exports = cypressModuleApi;
