//
// Cypress NPM api type declarations
// https://on.cypress.io/module-api
// https://github.com/cypress-io/cypress/issues/2141
//
// in the future the NPM module itself will be in TypeScript
// but for now describe it as an ambient module

declare namespace CypressCommandLine {
  /**
   * All options that one can pass to "cypress.run"
   * @see https://on.cypress.io/module-api#cypress-run
   * @example
    ```
    const cypress = require('cypress')
    cypress.run({
      reporter: 'junit',
      browser: 'chrome',
      config: {
        baseUrl: 'http://localhost:8080',
        chromeWebSecurity: false,
      },
      env: {
        foo: 'bar',
        baz: 'quux',
      }
    })
    ```
   */
  interface CypressRunOptions extends CypressCommonOptions {
    /**
     * Specify browser to run tests in, either by name or by filesystem path
     */
    browser: string
    /**
     * Specify a unique identifier for a run to enable grouping or parallelization
     */
    ciBuildId: string
    /**
     * Group recorded tests together under a single run name
     */
    group: string
    /**
     * Tag string for the recorded run, like "production,nightly"
     */
    tag: string
    /**
     * Display the browser instead of running headlessly
     */
    headed: boolean
    /**
     * Hide the browser instead of running headed
     */
    headless: boolean
    /**
     * Specify your secret Record Key
     */
    key: string
    /**
     * Keep Cypress open after all tests run
     */
    noExit: boolean
    /**
     * Run recorded specs in parallel across multiple machines
     */
    parallel: boolean
    /**
     * Override default port
     */
    port: number
    /**
     * Use POSIX exit codes for error handling
     */
    posixExitCodes: boolean
    /**
     * Run quietly, using only the configured reporter
     */
    quiet: boolean
    /**
     * Whether to record the test run
     */
    record: boolean
    /**
     * Specify a mocha reporter
     */
    reporter: string
    /**
     * Specify mocha reporter options
     */
    reporterOptions: any
    /**
     * Specify the specs to run
     */
    spec: string
    /**
     * Specify the number of failures to cancel a run being recorded to the Cloud or false to disable auto-cancellation.
     */
    autoCancelAfterFailures: number | false
    /**
     * Whether to display the Cypress Runner UI
     */
    runnerUi: boolean
  }

  /**
   * All options that one can pass to "cypress.open"
   * @see https://on.cypress.io/module-api#cypress-open
   * @example
    ```
    const cypress = require('cypress')
    cypress.open({
      env: {
        username: 'Joe Doe',
        email: 'joe@acme.co'
      },
      project: '~/demos/my-project'
    })
    ```
   */
  interface CypressOpenOptions extends CypressCommonOptions {
    /**
     * Specify browser to run tests in, either by name or by filesystem path
     */
    browser: string
    /**
     * Open Cypress in detached mode
     */
    detached: boolean
    /**
     * Run in global mode
     */
    global: boolean
    /**
     * Override default port
     */
    port: number
  }

  /**
   * Options available for `cypress.open` and `cypress.run`
   */
  interface CypressCommonOptions {
    /**
     * Specify configuration
     */
    config: Cypress.ConfigOptions
    /**
     * Path to the config file to be used.
     *
     * @default "cypress.config.{js,ts,mjs,cjs}"
     */
    configFile: string
    /**
     * Specify environment variables.
     * TODO: isn't this duplicate of config.env?!
     */
    env: object
    /**
     * Path to a specific project
     */
    project: string
    /**
     * Specify the type of tests to execute.
     * @default "e2e"
     */
    testingType: Cypress.TestingType
  }

  // small utility types to better express meaning of other types
  type dateTimeISO = string
  type ms = number
  type pixels = number

  /**
   * Cypress single test result
   */
  interface TestResult {
    duration: number
    title: string[]
    state: string
    /**
     * Error string as it's presented in console if the test fails
     */
    displayError: string | null
    attempts: AttemptResult[]
  }

  interface AttemptResult {
    state: string
  }

  /**
   * Information about a single screenshot.
   */
  interface ScreenshotInformation {
    name: string
    takenAt: dateTimeISO
    /**
     * Absolute path to the saved image
     */
    path: string
    height: pixels
    width: pixels
  }

  interface SpecResult {
    /**
     * resolved filename of the spec
     */
    absolute: string
    /**
     * file extension like ".js"
     */
    fileExtension: string
    /**
     * file name without extension like "spec"
     */
    fileName: string
    /**
     * filename like "spec.js"
     */
    name: string
    /**
     * name relative to the project root, like "cypress/integration/spec.js"
     */
    relative: string
  }

  /**
   * Cypress test run result for a single spec.
  */
  interface RunResult {
    error: string | null
    /**
     * Reporter name like "spec"
     */
    reporter: string
    /**
     * This is controlled by the reporter, and Cypress cannot guarantee
     * the properties. Usually this object has suites, tests, passes, etc
     */
    reporterStats: object
    screenshots: ScreenshotInformation[]
    /**
     * Accurate test results collected by Cypress.
     */
    stats: {
      duration?: ms
      endedAt: dateTimeISO
      failures: number
      passes: number
      pending: number
      skipped: number
      startedAt: dateTimeISO
      suites: number
      tests: number
    }
    /**
     * information about the spec test file.
     */
    spec: SpecResult
    tests: TestResult[]
    video: string | null
  }

  type PublicConfig = Omit<Cypress.ResolvedConfigOptions, 'additionalIgnorePattern' | 'autoOpen' | 'browser' | 'browsers' | 'browserUrl' | 'clientRoute' | 'cypressEnv' | 'devServerPublicPathRoute' | 'morgan' | 'namespace' | 'proxyServer' | 'proxyUrl' | 'rawJson' | 'remote' | 'repoRoot' | 'report' | 'reporterRoute' | 'reporterUrl' | 'resolved' | 'setupNodeEvents' | 'socketId' | 'socketIoCookie' | 'socketIoRoute' | 'specs' | 'state' | 'supportFolder'> & {
    browsers: Cypress.PublicBrowser[]
    cypressInternalEnv: string
  }

  /**
   * Results returned by the test run.
   * @see https://on.cypress.io/module-api
   */
  interface CypressRunResult {
    browserName: string
    browserPath: string
    browserVersion: string
    config: PublicConfig
    cypressVersion: string
    endedTestsAt: dateTimeISO
    osName: string
    osVersion: string
    runs: RunResult[]
    /**
     * If Cypress test run was recorded, full url will be provided.
     * @see https://on.cypress.io/cloud-introduction
     */
    runUrl?: string
    startedTestsAt: dateTimeISO
    totalDuration: number
    totalFailed: number
    totalPassed: number
    totalPending: number
    totalSkipped: number
    totalSuites: number
    totalTests: number
  }

  /**
     * If Cypress fails to run at all (for example, if there are no spec files to run),
     * then it will return a CypressFailedRunResult. Check the failures attribute.
     * @example
      ```
      const result = await cypress.run()
      if (result.status === 'failed') {
        console.error('failures %d', result.failures)
        console.error(result.message)
        process.exit(result.failures)
      }
      ```
     *
  **/
  interface CypressFailedRunResult {
    status: 'failed'
    failures: number
    message: string
  }

  /**
   * Methods allow parsing given CLI arguments the same way Cypress CLI does it.
   */
  interface CypressCliParser {
    /**
     * Parses the given array of string arguments to "cypress run"
     * just like Cypress CLI does it.
     * @see https://on.cypress.io/module-api
     * @example
     *  const cypress = require('cypress')
     *  const args = ['cypress', 'run', '--browser', 'chrome']
     *  const options = await cypress.cli.parseRunArguments(args)
     *  // options is {browser: 'chrome'}
     *  // pass the options to cypress.run()
     *  const results = await cypress.run(options)
     */
    parseRunArguments(args: string[]): Promise<Partial<CypressRunOptions>>
  }
}

declare module 'cypress' {
  /**
   * Cypress NPM module interface.
   * @see https://on.cypress.io/module-api
   * @example
    ```
    const cypress = require('cypress')
    cypress.run().then(results => ...)
    ```
  */
  interface CypressNpmApi {
    /**
     * Execute a headless Cypress test run.
     * @see https://on.cypress.io/module-api#cypress-run
     * @example
     ```
     const cypress = require('cypress')
     // runs all spec files matching a wildcard
     cypress.run({
       spec: 'cypress/integration/admin*-spec.js'
     }).then(results => {
       if (results.status === 'failed') {
          // Cypress could not run
        } else {
          // inspect results object
       }
     })
     ```
     */
    run(options?: Partial<CypressCommandLine.CypressRunOptions>): Promise<CypressCommandLine.CypressRunResult | CypressCommandLine.CypressFailedRunResult>
    /**
     * Opens Cypress GUI. Resolves with void when the
     * GUI is closed.
     * @see https://on.cypress.io/module-api#cypress-open
     */
    open(options?: Partial<CypressCommandLine.CypressOpenOptions>): Promise<void>

    /**
     * Utility functions for parsing CLI arguments the same way
     * Cypress does
     */
    cli: CypressCommandLine.CypressCliParser

    /**
     * Provides automatic code completion for configuration in many popular code editors.
     * While it's not strictly necessary for Cypress to parse your configuration, we
     * recommend wrapping your config object with `defineConfig()`
     * @example
     * module.exports = defineConfig({
     *    viewportWidth: 400
     * })
     *
     * @see ../types/cypress-npm-api.d.ts
     * @param {Cypress.ConfigOptions} config
     * @returns {Cypress.ConfigOptions} the configuration passed in parameter
     */
    defineConfig<ComponentDevServerOpts = any>(config: Cypress.ConfigOptions<ComponentDevServerOpts>): Cypress.ConfigOptions

    /**
     * Provides automatic code completion for Component Frameworks Definitions.
     * While it's not strictly necessary for Cypress to parse your configuration, we
     * recommend wrapping your Component Framework Definition object with `defineComponentFramework()`
     * @example
     * module.exports = defineComponentFramework({
     *   type: 'cypress-ct-solid-js'
     * })
     *
     * @see ../types/cypress-npm-api.d.ts
     * @param {Cypress.ThirdPartyComponentFrameworkDefinition} config
     * @returns {Cypress.ThirdPartyComponentFrameworkDefinition} the configuration passed in parameter
     */
    defineComponentFramework(config: Cypress.ThirdPartyComponentFrameworkDefinition): Cypress.ThirdPartyComponentFrameworkDefinition
  }

  // export Cypress NPM module interface
  const cypress: CypressNpmApi
  export = cypress
}
