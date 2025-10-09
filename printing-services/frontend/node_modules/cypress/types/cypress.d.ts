/// <reference path="./cypress-npm-api.d.ts" />
/// <reference path="./cypress-eventemitter.d.ts" />
/// <reference path="./cypress-type-helpers.d.ts" />
/// <reference path="./cypress-automation.d.ts" />
declare namespace Cypress {
  type FileContents = string | any[] | object
  type HistoryDirection = 'back' | 'forward'
  type HttpMethod = string
  type RequestBody = string | object | boolean | null
  type ViewportOrientation = 'portrait' | 'landscape'
  type PrevSubject = keyof PrevSubjectMap
  type TestingType = 'e2e' | 'component'
  type PluginConfig = (on: PluginEvents, config: PluginConfigOptions) => void | ConfigOptions | Promise<ConfigOptions>
  interface JQueryWithSelector<TElement = HTMLElement> extends JQuery<TElement> {
    selector?: string | null
  }

  interface PrevSubjectMap<O = unknown> {
    optional: O
    element: JQueryWithSelector
    document: Document
    window: Window
  }

  interface CommandOptions {
    prevSubject: boolean | PrevSubject | PrevSubject[]
  }
  interface CommandFn<T extends keyof ChainableMethods> {
    (this: Mocha.Context, ...args: Parameters<ChainableMethods[T]>): ReturnType<ChainableMethods[T]> | void
  }
  interface CommandFns {
    [name: string]: (this: Mocha.Context, ...args: any) => any
  }
  interface CommandFnWithSubject<T extends keyof ChainableMethods, S> {
    (this: Mocha.Context, prevSubject: S, ...args: Parameters<ChainableMethods[T]>): ReturnType<ChainableMethods[T]> | void
  }
  interface CommandFnsWithSubject<S> {
    [name: string]: (this: Mocha.Context, prevSubject: S, ...args: any) => any
  }
  interface CommandOriginalFn<T extends keyof ChainableMethods> extends CallableFunction {
    (...args: Parameters<ChainableMethods[T]>): ReturnType<ChainableMethods[T]>
  }
  interface CommandOriginalFnWithSubject<T extends keyof ChainableMethods, S> extends CallableFunction {
    (prevSubject: S, ...args: Parameters<ChainableMethods[T]>): ReturnType<ChainableMethods[T]>
  }
  interface CommandFnWithOriginalFn<T extends keyof Chainable> {
    (this: Mocha.Context, originalFn: CommandOriginalFn<T>, ...args: Parameters<ChainableMethods[T]>): ReturnType<ChainableMethods[T]> | void
  }
  interface CommandFnWithOriginalFnAndSubject<T extends keyof Chainable, S> {
    (this: Mocha.Context, originalFn: CommandOriginalFnWithSubject<T, S>, prevSubject: S, ...args: Parameters<ChainableMethods[T]>): ReturnType<ChainableMethods[T]> | void
  }
  interface QueryFn<T extends keyof ChainableMethods> {
    (this: Command, ...args: Parameters<ChainableMethods[T]>): (subject: any) => any
  }
  interface QueryFnWithOriginalFn<T extends keyof Chainable> {
    (this: Command, originalFn: QueryFn<T>, ...args: Parameters<ChainableMethods[T]>): (subject: any) => any
  }
  interface ObjectLike {
    [key: string]: any
  }
  interface PromptOptions {
    placeholders?: Record<string, string>
  }
  interface Auth {
    username: string
    password: string
  }

  interface RemoteState {
    auth?: Auth
    domainName: string
    strategy: 'file' | 'http'
    origin: string
    fileServer: string | null
    props: Record<string, any> | null
  }

  interface Backend {
    (task: 'net', eventName: string, frame: any): Promise<void>
  }

  type BrowserName = 'electron' | 'chrome' | 'chromium' | 'firefox' | 'edge' | string

  type BrowserChannel = 'stable' | 'canary' | 'beta' | 'dev' | 'nightly' | string

  type BrowserFamily = 'chromium' | 'firefox' | 'webkit'

  /**
   * Describes a browser Cypress can control
   */
  interface Browser {
    /**
     * Short browser name.
     */
    name: BrowserName
    /**
     * The underlying engine for this browser.
     */
    family: BrowserFamily
    /**
     * The release channel of the browser.
     */
    channel: BrowserChannel
    /**
     * Human-readable browser name.
     */
    displayName: string
    version: string
    majorVersion: number | string
    path: string
    isHeaded: boolean
    isHeadless: boolean
    /**
     * Informational text to accompany this browser. Shown in desktop-gui.
     */
    info?: string
    /**
     * Warning text to accompany this browser. Shown in desktop-gui.
     */
    warning?: string
    /**
     * If `true`, this browser version is not supported in Cypress.
     */
    unsupportedVersion?: boolean
  }

  /**
   * Browser that's exposed in public APIs
   */
  interface PublicBrowser {
    channel: BrowserChannel
    displayName: string
    family: string
    majorVersion?: string | number | null
    name: BrowserName
    path: string
    version: string
  }

  interface Ensure {
    /**
     * Throws an error if `subject` is not one of the passed in `type`s.
     */
    isType(subject: any, type: PrevSubject[], commandName: string, cy: Chainable): void

    /**
     * Throws an error if `subject` is not a DOM element.
     */
    isElement(subject: any, commandName: string, cy: Chainable): void

    /**
     * Throws an error if `subject` is not a `document`.
     */
    isDocument(subject: any, commandName: string, cy: Chainable): void

    /**
     * Throws an error if `subject` is not a `window`.
     */
    isWindow(subject: any, commandName: string, cy: Chainable): void

    /**
     * Throws an error if `subject` is not a DOM element attached to the application under test.
     */
    isAttached(subject: any, commandName: string, cy: Chainable, onFail?: Log): void

    /**
     * Throws an error if `subject` is a disabled DOM element.
     */
    isNotDisabled(subject: any, commandName: string, onFail?: Log): void

    /**
     * Throws an error if `subject` is a DOM element hidden by any of its parent elements.
     */
    isNotHiddenByAncestors(subject: any, commandName: string, onFail?: Log): void

    /**
     * Throws an error if `subject` is a read-only form element.
     */
    isNotReadonly(subject: any, commandName: string, onFail?: Log): void

    /**
     * Throws an error if `subject` is a read-only form element.
     */
    isScrollable(subject: any, commandName: string, onFail?: Log): void

    /**
     * Throws an error if `subject` is not a DOM element visible in the AUT.
     */
    isVisible(subject: any, commandName: string, onFail?: Log): void
  }

  interface LocalStorage {
    /**
     * Called internally to clear `localStorage` in two situations.
     *
     * 1. Before every test, this is called with no argument to clear all keys.
     * 2. On `cy.clearLocalStorage(keys)` this is called with `keys` as an argument.
     *
     * You should not call this method directly to clear `localStorage`; instead, use `cy.clearLocalStorage(key)`.
     *
     * @see https://on.cypress.io/clearlocalstorage
     */
    clear: (keys?: string[]) => void
  }

  // TODO: raise minimum required TypeScript version to 3.7
  // and make this recursive
  // https://github.com/cypress-io/cypress/issues/24875
  type Storable =
    | string
    | number
    | boolean
    | null
    | StorableObject
    | StorableArray

  interface StorableObject {
    [key: string]: Storable
  }

  interface StorableArray extends Array<Storable> { }

  type StorableRecord = Record<string, Storable>

  interface OriginStorage {
    origin: string
    value: StorableRecord
  }

  interface Storages {
    localStorage: OriginStorage[]
    sessionStorage: OriginStorage[]
  }

  interface StorageByOrigin {
    [key: string]: StorableRecord
  }

  type IsBrowserMatcher = BrowserName | Partial<Browser> | Array<BrowserName | Partial<Browser>>

  interface ViewportPosition extends WindowPosition {
    right: number
    bottom: number
  }

  interface WindowPosition {
    top: number
    left: number
    topCenter: number
    leftCenter: number
  }

  interface ElementPositioning {
    scrollTop: number
    scrollLeft: number
    width: number
    height: number
    fromElViewport: ViewportPosition
    fromElWindow: WindowPosition
    fromAutWindow: WindowPosition
  }

  interface ElementCoordinates {
    width: number
    height: number
    fromElViewport: ViewportPosition & { x: number, y: number }
    fromElWindow: WindowPosition & { x: number, y: number }
    fromAutWindow: WindowPosition & { x: number, y: number }
  }

  /**
   * Spec type for the given test. "integration" is the default, but
   * tests run using `open --component` will be "component"
   *
   * @see https://on.cypress.io/experiments
   */
  type CypressSpecType = 'integration' | 'component'

  /**
   * A Cypress spec.
   */
  interface Spec {
    name: string // "config_passing_spec.js"
    relative: string // "cypress/e2e/config_passing_spec.cy.js" or "__all" if clicked all specs button
    absolute: string // "/Users/janelane/app/cypress/e2e/config_passing_spec.cy.js"
    specFilter?: string // optional spec filter used by the user
    specType?: CypressSpecType
    baseName?: string // "config_passing_spec.cy.js"
    fileExtension?: string // ".js"
    fileName?: string // "config_passing_spec.cy"
    id?: string // "U3BlYzovVXNlcnMvamFuZWxhbmUvYXBwL2N5cHJlc3MvZTJlL2NvbmZpZ19wYXNzaW5nX3NwZWMuY3kuanM="
  }

  /**
   * Window type for Application Under Test(AUT)
   */
  type AUTWindow = Window & typeof globalThis & ApplicationWindow

  /**
   * The interface for user-defined properties in Window object under test.
   */
  interface ApplicationWindow { } // tslint:disable-line

  /**
   * The configuration for Cypress.
   */
  type Config = ResolvedConfigOptions & RuntimeConfigOptions & RuntimeServerConfigOptions

  /**
   * Several libraries are bundled with Cypress by default.
   *
   * @see https://on.cypress.io/api
   */
  interface Cypress {
    /**
     * Lodash library
     *
     * @see https://on.cypress.io/_
     * @example
     *    Cypress._.keys(obj)
     */
    _: _.LoDashStatic
    /**
     * jQuery library
     *
     * @see https://on.cypress.io/$
     * @example
     *    Cypress.$('p')
     */
    $: JQueryStatic
    /**
     * Cypress automatically includes a Blob library and exposes it as Cypress.Blob.
     *
     * @see https://on.cypress.io/blob
     * @see https://github.com/nolanlawson/blob-util
     * @example
     *    Cypress.Blob.method()
     */
    Blob: BlobUtil.BlobUtilStatic
    /**
     * Cypress automatically includes a Buffer library and exposes it as Cypress.Buffer.
     *
     * @see https://on.cypress.io/buffer
     * @see https://github.com/feross/buffer
     * @example
     *    Cypress.Buffer.method()
     */
    Buffer: BufferType
    /**
     * Cypress automatically includes minimatch and exposes it as Cypress.minimatch.
     *
     * @see https://on.cypress.io/minimatch
     */
    minimatch: typeof Minimatch.minimatch
    /**
     * Cypress automatically includes Bluebird and exposes it as Cypress.Promise.
     *
     * @see https://on.cypress.io/promise
     * @see https://github.com/petkaantonov/bluebird
     * @example
     *   new Cypress.Promise((resolve, reject) => { ... })
     */
    Promise: Bluebird.BluebirdStatic
    /**
     * Cypress includes Sinon.js library used in `cy.spy` and `cy.stub`.
     *
     * @see https://sinonjs.org/
     * @see https://on.cypress.io/stubs-spies-and-clocks
     * @see https://example.cypress.io/commands/spies-stubs-clocks
     */
    sinon: sinon.SinonStatic

    /**
     * Utility functions for ensuring various properties about a subject.
     * @see https://on.cypress.io/api/custom-queries
     */
    ensure: Ensure

    /**
     * Cypress version string. i.e. "1.1.2"
     * @see https://on.cypress.io/version
     * @example
      ```
      expect(Cypress.version).to.be.a('string')
      if (Cypress.version === '1.2.0') {
        // test something specific
      }
      ```
     */
    version: string

    /**
     * OS platform name, from Node `os.platform()`
     *
     * @see https://nodejs.org/api/os.html#os_os_platform
     * @example
     *    Cypress.platform // "darwin"
     */
    platform: string

    /**
     * CPU architecture, from Node `os.arch()`
     *
     * @see https://nodejs.org/api/os.html#os_os_arch
     * @example
     *    Cypress.arch // "x64"
     */
    arch: string

    /**
     * Currently executing spec file.
     * @example
     * ```
     * Cypress.spec
     * // {
     * //  name: "config_passing_spec.coffee",
     * //  relative: "cypress/integration/config_passing_spec.coffee",
     * //  absolute: "/users/smith/projects/web/cypress/integration/config_passing_spec.coffee"
     * //  specType: "integration"
     * // }
     * ```
     */
    spec: Spec

    /**
     * Currently executing test runnable instance.
     */
    currentTest: {
      title: string
      titlePath: string[]
    }

    /**
     * Information about current test retry
     */
    currentRetry: number

    /**
     * Information about the browser currently running the tests
     */
    browser: Browser

    /**
     * Internal class for LocalStorage management.
     */
    LocalStorage: LocalStorage

    /**
     * Internal class for session management.
     */
    session: Session

    /**
     * Current testing type, determined by the Test Runner chosen to run.
     */
    testingType: TestingType

    /**
     * Fire automation:request event for internal use.
     */
    automation(eventName: string, ...args: any[]): Bluebird.Promise<any>

    /**
     * Promise wrapper for certain internal tasks.
     */
    backend: Backend

    /**
     * Returns all configuration objects.
     * @see https://on.cypress.io/config
     * @example
    ```
    Cypress.config()
    // {defaultCommandTimeout: 10000, pageLoadTimeout: 30000, ...}
    ```
     */
    config(): Config
    /**
     * Returns one configuration value.
     * @see https://on.cypress.io/config
     * @example
    ```
    Cypress.config('pageLoadTimeout')
    // 60000
    ```
     */
    config<K extends keyof Config>(key: K): Config[K]
    /**
     * Sets one configuration value.
     * @see https://on.cypress.io/config
     * @example
    ```
    Cypress.config('viewportWidth', 800)
    ```
     */
    config<K extends keyof TestConfigOverrides>(key: K, value: TestConfigOverrides[K]): void
    /**
     * Sets multiple configuration values at once.
     * @see https://on.cypress.io/config
     * @example
    ```
    Cypress.config({
      defaultCommandTimeout: 10000,
      viewportHeight: 900
    })
    ```
     */
    config(Object: TestConfigOverrides): void

    // no real way to type without generics
    /**
     * Returns all environment variables set with CYPRESS_ prefix or in "env" object in "cypress.config.{js,ts,mjs,cjs}"
     *
     * @see https://on.cypress.io/env
     */
    env(): ObjectLike
    /**
     * Returns specific environment variable or undefined
     * @see https://on.cypress.io/env
     * @example
     *    // cypress.config.js
     *    { "env": { "foo": "bar" } }
     *    Cypress.env("foo") // => bar
     */
    env(key: string): any
    /**
     * Set value for a variable.
     * Any value you change will be permanently changed for the remainder of your tests.
     * @see https://on.cypress.io/env
     * @example
     *    Cypress.env("host", "http://server.dev.local")
     */
    env(key: string, value: any): void
    /**
     * Set values for multiple variables at once. Values are merged with existing values.
     * @see https://on.cypress.io/env
     * @example
     *    Cypress.env({ host: "http://server.dev.local", foo: "foo" })
     */
    env(object: ObjectLike): void

    /**
     * @returns the number of test retries currently enabled for the run
     */
    getTestRetries(): number | null

    /**
     * Checks if a variable is a valid instance of `cy` or a `cy` chainable.
     *
     * @see https://on.cypress.io/iscy
     * @example
     *    Cypress.isCy(cy) // => true
     */
    isCy<TSubject = any>(obj: Chainable<TSubject>): obj is Chainable<TSubject>
    isCy(obj: any): obj is Chainable

    /**
     * Returns true if currently running the supplied browser name or matcher object. Also accepts an array of matchers.
     * @example isBrowser('chrome') will be true for the browser 'chrome:canary' and 'chrome:stable'
     * @example isBrowser({ name: 'firefox', channel: 'dev' }) will be true only for the browser 'firefox:dev' (Firefox Developer Edition)
     * @example isBrowser(['firefox', 'edge']) will be true only for the browsers 'firefox' and 'edge'
     * @example isBrowser('!firefox') will be true for every browser other than 'firefox'
     * @example isBrowser({ family: '!chromium'}) will be true for every browser not matching { family: 'chromium' }
     * @param matcher browser name or matcher object to check.
     */
    isBrowser(name: IsBrowserMatcher): boolean

    /**
     * Internal options for "cy.log" used in custom commands.
     *
     * @see https://on.cypress.io/cypress-log
     */
    log(options: Partial<LogConfig>): Log

    /**
     * Stop the Cypress App on the current machine while tests are running
     * @see https://on.cypress.io/cypress-stop
     * @example
     *    Cypress.stop()
     */
    stop(): void

    Commands: Commands

    /**
     * @see https://on.cypress.io/cookies
     */
    Cookies: {
      debug(enabled: boolean, options?: Partial<DebugOptions>): void
    }

    /**
     * @see https://on.cypress.io/dom
     */
    dom: {
      /**
       * Returns a jQuery object obtained by wrapping an object in jQuery.
       */
      wrap(wrappingElement_function: JQuery.Selector | JQuery.htmlString | Element | JQuery | ((index: number) => string | JQuery)): JQuery
      query(selector: JQuery.Selector, context?: Element | JQuery): JQuery
      /**
       * Returns an array of raw elements pulled out from a jQuery object.
       */
      unwrap(obj: any): any
      /**
       * Returns a boolean indicating whether an object is a DOM object.
       */
      isDom(obj: any): boolean
      isType(element: JQuery | HTMLElement, type: string): boolean
      /**
       * Returns a boolean indicating whether an element is visible.
       */
      isVisible(element: JQuery | HTMLElement): boolean
      /**
       * Returns a boolean indicating whether an element is hidden.
       */
      isHidden(element: JQuery | HTMLElement, methodName?: string, options?: object): boolean
      /**
       * Returns a boolean indicating whether an element can receive focus.
       */
      isFocusable(element: JQuery | HTMLElement): boolean
      isTextLike(element: JQuery | HTMLElement): boolean
      /**
       * Returns a boolean indicating whether an element is scrollable.
       */
      isScrollable(element: Window | JQuery | HTMLElement): boolean
      /**
       * Returns a boolean indicating whether an element currently has focus.
       */
      isFocused(element: JQuery | HTMLElement): boolean
      /**
       * Returns a boolean indicating whether an element is detached from the DOM.
       */
      isDetached(element: JQuery | HTMLElement): boolean
      /**
       * Returns a boolean indicating whether an element is attached to the DOM.
       */
      isAttached(element: JQuery | HTMLElement | Window | Document): boolean
      isSelector(element: JQuery | HTMLElement, selector: JQuery.Selector): boolean
      /**
       * Returns a boolean indicating whether an element is a descendent of another element.
       */
      isDescendent(element1: JQuery | HTMLElement, element2: JQuery | HTMLElement): boolean
      /**
       * Returns a boolean indicating whether object is undefined or html, body, or document.
       */
      isUndefinedOrHTMLBodyDoc(obj: any): boolean
      /**
       * Returns a boolean indicating whether an object is a DOM element.
       */
      isElement(obj: any): boolean
      /**
       * Returns a boolean indicating whether a node is of document type.
       */
      isDocument(obj: any): boolean
      /**
       * Returns a boolean indicating whether an object is a window object.
       */
      isWindow(obj: any): obj is Window
      /**
       * Returns a boolean indicating whether an object is a jQuery object.
       */
      isJquery(obj: any): obj is JQuery
      isInputType(element: JQuery | HTMLElement, type: string | string[]): boolean
      stringify(element: JQuery | HTMLElement, form: string): string
      getElements(element: JQuery): JQuery | HTMLElement[]
      getContainsSelector(text: string, filter?: string, options?: CaseMatchable): JQuery.Selector
      getFirstDeepestElement(elements: HTMLElement[], index?: number): HTMLElement
      getWindowByElement(element: JQuery | HTMLElement): JQuery | HTMLElement
      getReasonIsHidden(element: JQuery | HTMLElement, options?: object): string
      getFirstScrollableParent(element: JQuery | HTMLElement): JQuery | HTMLElement
      getFirstFixedOrStickyPositionParent(element: JQuery | HTMLElement): JQuery | HTMLElement
      getFirstStickyPositionParent(element: JQuery | HTMLElement): JQuery | HTMLElement
      getCoordsByPosition(left: number, top: number, xPosition?: string, yPosition?: string): number
      getElementPositioning(element: JQuery | HTMLElement): ElementPositioning
      getElementAtPointFromViewport(doc: Document, x: number, y: number): Element | null
      getElementCoordinatesByPosition(element: JQuery | HTMLElement, position?: string): ElementCoordinates
      getElementCoordinatesByPositionRelativeToXY(element: JQuery | HTMLElement, x: number, y: number): ElementPositioning
      getHostContenteditable(element: HTMLElement): HTMLElement
      getSelectionBounds(element: HTMLElement): { start: number, end: number }
    }

    /**
     * @see https://on.cypress.io/keyboard-api
     */
    Keyboard: {
      defaults(options: Partial<KeyboardDefaultsOptions>): void
      Keys: {
        DOWN: 'ArrowDown'
        LEFT: 'ArrowLeft'
        RIGHT: 'ArrowRight'
        UP: 'ArrowUp'
        END: 'End'
        HOME: 'Home'
        PAGEDOWN: 'PageDown'
        PAGEUP: 'PageUp'
        ENTER: 'Enter'
        TAB: 'Tab'
        BACKSPACE: 'Backspace'
        SPACE: 'Space'
        DELETE: 'Delete'
        INSERT: 'Insert'
        ESC: 'Escape'
      }
    }

    /**
     * @see https://on.cypress.io/screenshot-api
     */
    Screenshot: {
      defaults(options: Partial<ScreenshotDefaultsOptions>): void
    }

    /**
     * Element selector logic used for generating selectors for elements
     * in the Selector Playground and Cypress Studio.
     * @see https://on.cypress.io/element-selector-api
     */
    ElementSelector: {
      defaults(options: Partial<ElementSelectorDefaultsOptions>): void
    }

    /**
     * @deprecated Use ElementSelector instead
     * @see https://on.cypress.io/element-selector-api
     */
    SelectorPlayground: {
      defaults(options: Partial<ElementSelectorDefaultsOptions>): void
      getSelector($el: JQuery): JQuery.Selector
    }

    /**
     * These events come from Cypress as it issues commands and reacts to their state. These are all useful to listen to for debugging purposes.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    on: Actions

    /**
     * These events come from Cypress as it issues commands and reacts to their state. These are all useful to listen to for debugging purposes.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    once: Actions

    /**
     * These events come from Cypress as it issues commands and reacts to their state. These are all useful to listen to for debugging purposes.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    off: Actions

    /**
     * Used to include dependencies within the cy.origin() callback
     * @see https://on.cypress.io/origin
     */
    require: <T = any>(id: string) => T

    /**
     * Trigger action
     * @private
     */
    action: <T = (any[] | void)>(action: string, ...args: any[]) => T

    /**
     * Load files
     * @private
     */
    onSpecWindow: (window: Window, specList: string[] | Array<() => Promise<void>>) => void
  }

  interface Commands {
      /**
       * Add a custom command
       * @see https://on.cypress.io/api/commands
       */
      add<T extends keyof Chainable>(name: T, fn: CommandFn<T>): void

      /**
       * Add a custom parent command
       * @see https://on.cypress.io/api/commands#Parent-Commands
       */
      add<T extends keyof Chainable>(name: T, options: CommandOptions & { prevSubject: false }, fn: CommandFn<T>): void

      /**
       * Add a custom child command
       * @see https://on.cypress.io/api/commands#Child-Commands
       */
      add<T extends keyof Chainable, S = any>(name: T, options: CommandOptions & { prevSubject: true }, fn: CommandFnWithSubject<T, S>): void

      /**
       * Add a custom child or dual command
       * @see https://on.cypress.io/api/commands#Validations
       */
      add<T extends keyof Chainable, S extends PrevSubject>(
        name: T, options: CommandOptions & { prevSubject: S | ['optional'] }, fn: CommandFnWithSubject<T, PrevSubjectMap[S]>,
      ): void

      /**
       * Add a custom command that allows multiple types as the prevSubject
       * @see https://on.cypress.io/api/commands#Validations#Allow-Multiple-Types
       */
      add<T extends keyof Chainable, S extends PrevSubject>(
        name: T, options: CommandOptions & { prevSubject: S[] }, fn: CommandFnWithSubject<T, PrevSubjectMap<void>[S]>,
      ): void

      /**
       * Add one or more custom commands
       * @see https://on.cypress.io/api/commands
       */
      addAll<T extends keyof Chainable>(fns: CommandFns): void

      /**
       * Add one or more custom parent commands
       * @see https://on.cypress.io/api/commands#Parent-Commands
       */
      addAll<T extends keyof Chainable>(options: CommandOptions & { prevSubject: false }, fns: CommandFns): void

      /**
       * Add one or more custom child commands
       * @see https://on.cypress.io/api/commands#Child-Commands
       */
      addAll<T extends keyof Chainable, S = any>(options: CommandOptions & { prevSubject: true }, fns: CommandFnsWithSubject<S>): void

      /**
       * Add one or more custom commands that validate their prevSubject
       * @see https://on.cypress.io/api/commands#Validations
       */
      addAll<T extends keyof Chainable, S extends PrevSubject>(
        options: CommandOptions & { prevSubject: S | ['optional'] }, fns: CommandFnsWithSubject<PrevSubjectMap[S]>,
      ): void

      /**
       * Add one or more custom commands that allow multiple types as their prevSubject
       * @see https://on.cypress.io/api/commands#Allow-Multiple-Types
       */
      addAll<T extends keyof Chainable, S extends PrevSubject>(
        options: CommandOptions & { prevSubject: S[] }, fns: CommandFnsWithSubject<PrevSubjectMap<void>[S]>,
      ): void

      /**
       * Overwrite an existing Cypress command with a new implementation
       * @see https://on.cypress.io/api/commands#Overwrite-Existing-Commands
       */
      overwrite<T extends keyof Chainable>(name: T, fn: CommandFnWithOriginalFn<T>): void

      /**
       * Overwrite an existing Cypress command with a new implementation
       * @see https://on.cypress.io/api/commands#Overwrite-Existing-Commands
       */
      overwrite<T extends keyof Chainable, S extends PrevSubject>(name: T, fn: CommandFnWithOriginalFnAndSubject<T, PrevSubjectMap[S]>): void

      /**
       * Add a custom query
       * @see https://on.cypress.io/api/custom-queries
       */
      addQuery<T extends keyof Chainable>(name: T, fn: QueryFn<T>): void

      /**
       * Overwrite an existing Cypress query with a new implementation
       * @see https://on.cypress.io/api/custom-queries
       */
      overwriteQuery<T extends keyof Chainable>(name: T, fn: QueryFnWithOriginalFn<T>): void
  }

  type CanReturnChainable = void | Chainable | Promise<unknown>
  type ThenReturn<S, R> =
    R extends void ? Chainable<S> :
    R extends R | undefined ? Chainable<S | Exclude<R, undefined>> :
    Chainable<S>

  /**
   * Chainable interface for non-array Subjects
   */
  interface Chainable<Subject = any> {
    /**
     * Create an assertion. Assertions are automatically retried until they pass or time out.
     *
     * @alias should
     * @see https://on.cypress.io/and
     */
    and: Chainer<Subject>

    /**
     * Assign an alias for later use. Reference the alias later within a
     * [cy.get()](https://on.cypress.io/get) or
     * [cy.wait()](https://on.cypress.io/wait) command with a `@` prefix.
     * You can alias DOM elements, routes, stubs and spies.
     *
     * @see https://on.cypress.io/as
     * @see https://on.cypress.io/variables-and-aliases
     * @see https://on.cypress.io/get
     * @example
     *    // Get the aliased 'todos' elements
     *    cy.get('ul#todos').as('todos')
     *
     *    // later retrieve the todos
     *    cy.get('@todos')
     */
    as(alias: string, options?: Partial<AsOptions>): Chainable<Subject>

    /**
     * Blur a focused element. This element must currently be in focus.
     * If you want to ensure an element is focused before blurring,
     * try using .focus() before .blur().
     *
     * @see https://on.cypress.io/blur
     */
    blur(options?: Partial<BlurOptions>): Chainable<Subject>

    /**
     * Check checkbox(es) or radio(s). This element must be an `<input>` with type `checkbox` or `radio`.
     *
     * @see https://on.cypress.io/check
     * @example
     *    // Check checkbox element
     *    cy.get('[type="checkbox"]').check()
     *    // Check first radio element
     *    cy.get('[type="radio"]').first().check()
     */
    check(options?: Partial<CheckClearOptions>): Chainable<Subject>
    /**
     * Check checkbox(es) or radio(s). This element must be an `<input>` with type `checkbox` or `radio`.
     *
     * @see https://on.cypress.io/check
     * @example
     *    // Select the radio with the value of 'US'
     *    cy.get('[type="radio"]').check('US')
     *    // Check the checkboxes with the values 'ga' and 'ca'
     *    cy.get('[type="checkbox"]').check(['ga', 'ca'])
     */
    check(value: string | string[], options?: Partial<CheckClearOptions>): Chainable<Subject>

    /**
     * Get the children of each DOM element within a set of DOM elements.
     *
     * @see https://on.cypress.io/children
     */
    children<E extends Node = HTMLElement>(options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>
    children<K extends keyof HTMLElementTagNameMap>(selector: K, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<HTMLElementTagNameMap[K]>>
    children<E extends Node = HTMLElement>(selector: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>

    /**
     * Clear the value of an `input` or `textarea`.
     * An alias for `.type({selectall}{del})`
     *
     * @see https://on.cypress.io/clear
     */
    clear(options?: Partial<CheckClearOptions>): Chainable<Subject>

    /**
     * Clear a specific browser cookie for a domain.
     *
     * Cypress automatically clears all cookies _before_ each test to prevent
     * state from being shared across tests when test isolation is enabled.
     * You shouldn't need to use this command unless you're using it to clear
     * a specific cookie inside a single test or test isolation is disabled.
     *
     * @see https://on.cypress.io/clearcookie
     */
    clearCookie(name: string, options?: CookieOptions): Chainable<null>

    /**
     * Clear browser cookies for a domain.
     *
     * Cypress automatically clears all cookies _before_ each test to prevent
     * state from being shared across tests when test isolation is enabled.
     * You shouldn't need to use this command unless you're using it to clear
     * specific cookies inside a single test or test isolation is disabled.
     *
     * @see https://on.cypress.io/clearcookies
     */
    clearCookies(options?: CookieOptions): Chainable<null>

    /**
     * Clear all browser cookies.
     *
     * Cypress automatically clears all cookies _before_ each test to prevent
     * state from being shared across tests when test isolation is enabled.
     * You shouldn't need to use this command unless you're using it to clear
     * all cookie inside a single test or test isolation is disabled.
     *
     * @see https://on.cypress.io/clearallcookies
     */
    clearAllCookies(options?: Partial<Loggable & Timeoutable>): Chainable<null>

    /**
     * Get local storage for all origins.
     *
     * @see https://on.cypress.io/getalllocalstorage
     */
    getAllLocalStorage(options?: Partial<Loggable>): Chainable<StorageByOrigin>

    /**
     * Clear local storage for all origins.
     *
     * Cypress automatically clears all local storage _before_ each test to
     * prevent state from being shared across tests when test isolation
     * is enabled. You shouldn't need to use this command unless you're using it
     * to clear localStorage inside a single test or test isolation is disabled.
     *
     * @see https://on.cypress.io/clearalllocalstorage
     */
    clearAllLocalStorage(options?: Partial<Loggable>): Chainable<null>

    /**
     * Get session storage for all origins.
     *
     * @see https://on.cypress.io/getallsessionstorage
     */
    getAllSessionStorage(options?: Partial<Loggable>): Chainable<StorageByOrigin>

    /**
     * Clear session storage for all origins.
     *
     * @see https://on.cypress.io/clearallsessionstorage
     */
    clearAllSessionStorage(options?: Partial<Loggable>): Chainable<null>

    /**
     * Clear data in local storage for the current origin.
     *
     * Cypress automatically clears all local storage _before_ each test to
     * prevent state from being shared across tests when test isolation
     * is enabled. You shouldn't need to use this command unless you're using it
     * to clear localStorage inside a single test or test isolation is disabled.
     *
     * @see https://on.cypress.io/clearlocalstorage
     * @param {string} [key] - name of a particular item to remove (optional).
     * @example
      ```
      // Removes all local storage keys
      cy.clearLocalStorage()
        .should(ls => {
          expect(ls.getItem('prop1')).to.be.null
        })
      // Removes item "todos"
      cy.clearLocalStorage("todos")
      ```
     */
    clearLocalStorage(key?: string): Chainable<Storage>
    /**
     * Clear keys in local storage that match given regular expression.
     *
     * @see https://on.cypress.io/clearlocalstorage
     * @param {RegExp} re - regular expression to match.
     * @example
    ```
    // Clears all local storage matching /app-/
    cy.clearLocalStorage(/app-/)
    ```
     */
    clearLocalStorage(re: RegExp): Chainable<Storage>
    /**
      * Clear data in local storage.
      * Cypress automatically runs this command before each test to prevent state from being
      * shared across tests. You shouldn't need to use this command unless you're using it
      * to clear localStorage inside a single test. Yields `localStorage` object.
      *
      * @see https://on.cypress.io/clearlocalstorage
      * @param {options} [object] - options object
      * @example
       ```
       // Removes all local storage items, without logging
       cy.clearLocalStorage({ log: false })
       ```
      */
    clearLocalStorage(options: Partial<Loggable>): Chainable<Storage>
    /**
      * Clear data in local storage.
      * Cypress automatically runs this command before each test to prevent state from being
      * shared across tests. You shouldn't need to use this command unless you're using it
      * to clear localStorage inside a single test. Yields `localStorage` object.
      *
      * @see https://on.cypress.io/clearlocalstorage
      * @param {string} [key] - name of a particular item to remove (optional).
      * @param {options} [object] - options object
      * @example
       ```
       // Removes item "todos" without logging
       cy.clearLocalStorage("todos", { log: false })
       ```
      */
    clearLocalStorage(key: string, options: Partial<Loggable>): Chainable<Storage>

    /**
     * Click a DOM element.
     *
     * @see https://on.cypress.io/click
     * @example
     *    cy.get('button').click()          // Click on button
     *    cy.focused().click()              // Click on el with focus
     *    cy.contains('Welcome').click()    // Click on first el containing 'Welcome'
     */
    click(options?: Partial<ClickOptions>): Chainable<Subject>
    /**
     * Click a DOM element at specific corner / side.
     *
     * @param {PositionType} position - The position where the click should be issued.
     * The `center` position is the default position.
     * @see https://on.cypress.io/click
     * @example
     *    cy.get('button').click('topRight')
     */
    click(position: PositionType, options?: Partial<ClickOptions>): Chainable<Subject>
    /**
     * Click a DOM element at specific coordinates
     *
     * @param {number} x The distance in pixels from the element's left to issue the click.
     * @param {number} y The distance in pixels from the element's top to issue the click.
     * @see https://on.cypress.io/click
     * @example
    ```
    // The click below will be issued inside of the element
    // (15px from the left and 40px from the top).
    cy.get('button').click(15, 40)
    ```
     */
    click(x: number, y: number, options?: Partial<ClickOptions>): Chainable<Subject>

    /**
     * `cy.clock()` overrides native global functions related to time allowing them to be controlled
     * synchronously via [cy.tick()](https://on.cypress.io/tick) or the yielded clock object.
     * This includes controlling:
     * * `setTimeout`
     * * `clearTimeout`
     * * `setInterval`
     * * `clearInterval`
     * * `Date` Objects
     *
     * The clock starts at the unix epoch (timestamp of 0).
     * This means that when you instantiate new Date in your application,
     * it will have a time of January 1st, 1970.
     *
     * To restore the real clock call `.restore()`
     *
     * @example
     *  cy.clock()
     *  ...
     *  // restore the application clock
     *  cy.clock().then(clock => {
     *    clock.restore()
     *  })
     *  // or use this shortcut
     *  cy.clock().invoke('restore')
     *
     * @see https://on.cypress.io/clock
     */
    clock(): Chainable<Clock>
    /**
     * Mocks global clock and sets current timestamp to the given value.
     * Overrides all functions that deal with time.
     *
     * @see https://on.cypress.io/clock
     * @example
     *    // in your app code
     *    $('#date').text(new Date().toJSON())
     *    // in the spec file
     *    // March 14, 2017 timestamp or Date object
     *    const now = new Date(2017, 2, 14).getTime()
     *    cy.clock(now)
     *    cy.visit('/index.html')
     *    cy.get('#date').contains('2017-03-14')
     *    // to restore the real clock
     *    cy.clock().then(clock => {
     *      clock.restore()
     *    })
     *    // or use this shortcut
     *    cy.clock().invoke('restore')
     */
    clock(now: number | Date, options?: Loggable): Chainable<Clock>
    /**
     * Mocks global clock but only overrides specific functions.
     *
     * @see https://on.cypress.io/clock
     * @example
     *    // keep current date but override "setTimeout" and "clearTimeout"
     *    cy.clock(null, ['setTimeout', 'clearTimeout'])
     */
    clock(now: number | Date, functions?: Array<'setTimeout' | 'clearTimeout' | 'setInterval' | 'clearInterval' | 'Date'>, options?: Loggable): Chainable<Clock>
    /**
     * Mocks global clock and all functions.
     *
     * @see https://on.cypress.io/clock
     * @example
     *    // mock clock but do not log this command
     *    cy.clock({ log: false })
     */
    clock(options: Loggable): Chainable<Clock>

    /**
     * Get the first DOM element that matches the selector (whether it be itself or one of its ancestors).
     *
     * @see https://on.cypress.io/closest
     */
    closest<K extends keyof HTMLElementTagNameMap>(selector: K, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<HTMLElementTagNameMap[K]>>
    closest<E extends Node = HTMLElement>(selector: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>

    /**
     * Get the DOM element containing the text.
     * DOM elements can contain more than the desired text and still match.
     * Additionally, Cypress prefers some DOM elements over the deepest element found.
     *
     * @see https://on.cypress.io/contains
     * @example
     *    // Yield el in .nav containing 'About'
     *    cy.get('.nav').contains('About')
     *    // Yield first el in document containing 'Hello'
     *    cy.contains('Hello')
     *    // you can use regular expression
     *    cy.contains(/^b\w+/)
     *    // yields <ul>...</ul>
     *    cy.contains('ul', 'apples')
     *    // tries to find the given text for up to 1 second
     *    cy.contains('my text to find', {timeout: 1000})
     */
    contains(content: string | number | RegExp, options?: Partial<Loggable & Timeoutable & CaseMatchable & Shadow>): Chainable<Subject>
    /**
     * Get the child DOM element that contains given text.
     *
     * @see https://on.cypress.io/contains
     * @example
     *    // Yield el in .nav containing 'About'
     *    cy.get('.nav').contains('About')
     */
    contains<E extends Node = HTMLElement>(content: string | number | RegExp): Chainable<JQuery<E>>
    /**
     * Get the DOM element with name "selector" containing the text or regular expression.
     *
     * @see https://on.cypress.io/contains
     * @example
     *    // yields <ul>...</ul>
     *    cy.contains('ul', 'apples')
     */
    contains<K extends keyof HTMLElementTagNameMap>(selector: K, text: string | number | RegExp, options?: Partial<Loggable & Timeoutable & CaseMatchable & Shadow>): Chainable<JQuery<HTMLElementTagNameMap[K]>>
    /**
     * Get the DOM element using CSS "selector" containing the text or regular expression.
     *
     * @see https://on.cypress.io/contains
     * @example
     *    // yields <... class="foo">... apples ...</...>
     *    cy.contains('.foo', 'apples')
     */
    contains<E extends Node = HTMLElement>(selector: string, text: string | number | RegExp, options?: Partial<Loggable & Timeoutable & CaseMatchable & Shadow>): Chainable<JQuery<E>>

    /**
     * Double-click a DOM element.
     *
     * @see https://on.cypress.io/dblclick
     */
    dblclick(options?: Partial<ClickOptions>): Chainable<Subject>
    /**
     * Double-click a DOM element at specific corner / side.
     *
     * @param {PositionType} position - The position where the click should be issued.
     * The `center` position is the default position.
     * @see https://on.cypress.io/dblclick
     * @example
     *    cy.get('button').dblclick('topRight')
     */
    dblclick(position: PositionType, options?: Partial<ClickOptions>): Chainable<Subject>
    /**
     * Double-click a DOM element at specific coordinates
     *
     * @param {number} x The distance in pixels from the element's left to issue the click.
     * @param {number} y The distance in pixels from the element's top to issue the click.
     * @see https://on.cypress.io/dblclick
     * @example
    ```
    // The click below will be issued inside of the element
    // (15px from the left and 40px from the top).
    cy.get('button').dblclick(15, 40)
    ```
     */
    dblclick(x: number, y: number, options?: Partial<ClickOptions>): Chainable<Subject>
    /**
     * Right-click a DOM element.
     *
     * @see https://on.cypress.io/rightclick
     */
    rightclick(options?: Partial<ClickOptions>): Chainable<Subject>
    /**
     * Right-click a DOM element at specific corner / side.
     *
     * @param {PositionType} position - The position where the click should be issued.
     * The `center` position is the default position.
     * @see https://on.cypress.io/click
     * @example
     *    cy.get('button').rightclick('topRight')
     */
    rightclick(position: PositionType, options?: Partial<ClickOptions>): Chainable<Subject>
    /**
     * Right-click a DOM element at specific coordinates
     *
     * @param {number} x The distance in pixels from the element's left to issue the click.
     * @param {number} y The distance in pixels from the element's top to issue the click.
     * @see https://on.cypress.io/rightclick
     * @example
    ```
    // The click below will be issued inside of the element
    // (15px from the left and 40px from the top).
    cy.get('button').rightclick(15, 40)
    ```
     */
    rightclick(x: number, y: number, options?: Partial<ClickOptions>): Chainable<Subject>

    /**
     * Set a debugger and log what the previous command yields.
     *
     * @see https://on.cypress.io/debug
     */
    debug(options?: Partial<Loggable>): Chainable<Subject>

    /**
      * Save/Restore browser Cookies, LocalStorage, and SessionStorage data resulting from the supplied `setup` function.
      *
      * @see https://on.cypress.io/session
      */
    session(id: string | object, setup: () => void, options?: SessionOptions): Chainable<null>

    /**
     * Get the window.document of the page that is currently active.
     *
     * @see https://on.cypress.io/document
     * @example
     *    cy.document()
     *      .its('contentType')
     *      .should('eq', 'text/html')
     */
    document(options?: Partial<Loggable & Timeoutable>): Chainable<Document>

    /**
     * Iterate through an array like structure (arrays or objects with a length property).
     *
     * @see https://on.cypress.io/each
     */
    each<E extends Node = HTMLElement>(fn: (element: JQuery<E>, index: number, $list: E[]) => void): Chainable<JQuery<E>> // Can't properly infer type without breaking down Chainable
    each(fn: (item: any, index: number, $list: any[]) => void): Chainable<Subject>

    /**
     * End a chain of commands
     *
     * @see https://on.cypress.io/end
     */
    end(): Chainable<null>

    /**
     * Get A DOM element at a specific index in an array of elements.
     *
     * @see https://on.cypress.io/eq
     * @param {Number} index A number indicating the index to find the element at within an array of elements. A negative number counts index from the end of the list.
     * @example
     *    cy.get('tbody>tr').eq(0)    // Yield first 'tr' in 'tbody'
     *    cy.get('ul>li').eq('4')     // Yield fifth 'li' in 'ul'
     *    cy.get('li').eq(-2) // Yields second from last 'li' element
     */
    eq<E extends Node = HTMLElement>(index: number, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>

    /**
     * Execute a system command.
     * @see https://on.cypress.io/exec
     */
    exec(command: string, options?: Partial<ExecOptions>): Chainable<Exec>

    /**
     * Get the DOM elements that match a specific selector. Opposite of `.not()`
     *
     * @see https://on.cypress.io/filter
     */
    filter<K extends keyof HTMLElementTagNameMap>(selector: K, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<HTMLElementTagNameMap[K]>> // automatically returns the correct HTMLElement type
    /**
     * Get the DOM elements that match a specific selector. Opposite of `.not()`
     *
     * @see https://on.cypress.io/filter
     */
    filter<E extends Node = HTMLElement>(selector: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>
    /**
     * Get the DOM elements that match a specific selector. Opposite of `.not()`
     *
     * @see https://on.cypress.io/filter
     */
    filter<E extends Node = HTMLElement>(fn: (index: number, element: E) => boolean, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>

    /**
     * Get the descendent DOM elements of a specific selector.
     *
     * @see https://on.cypress.io/find
     * @example
     *    cy.get('.article').find('footer') // Yield 'footer' within '.article'
     */
    find<K extends keyof HTMLElementTagNameMap>(selector: K, options?: Partial<Loggable & Timeoutable & Shadow>): Chainable<JQuery<HTMLElementTagNameMap[K]>>
    /**
     * Finds the descendent DOM elements with the given selector.
     *
     * @see https://on.cypress.io/find
     * @example
     *    // Find the li's within the nav
     *    cy.get('.left-nav>.nav').find('>li')
     */
    find<E extends Node = HTMLElement>(selector: string, options?: Partial<Loggable & Timeoutable & Shadow>): Chainable<JQuery<E>>

    /**
     * Get the first DOM element within a set of DOM elements.
     *
     * @see https://on.cypress.io/first
     */
    first(options?: Partial<Loggable & Timeoutable>): Chainable<Subject>

    /**
     * Load a fixed set of data located in a file.
     *
     * @see https://on.cypress.io/fixture
     */
    fixture<Contents = any>(path: string, options?: Partial<Timeoutable>): Chainable<Contents> // no log?
    /**
     * Load a fixed set of data located in a file with given encoding.
     *
     * @see https://on.cypress.io/fixture
     */
    fixture<Contents = any>(path: string, encoding: Encodings, options?: Partial<Timeoutable>): Chainable<Contents> // no log?

    /**
     * Focus on a DOM element.
     *
     * @see https://on.cypress.io/focus
     * @example
     * cy.get('input').first().focus() // Focus on the first input
     */
    focus(options?: Partial<Loggable & Timeoutable>): Chainable<Subject>

    /**
     * Get the DOM element that is currently focused.
     *
     * @see https://on.cypress.io/focused
     * @example
     *    // Get the element that is focused
     *    cy.focused().then(function($el) {
     *       // do something with $el
     *    })
     *    // Blur the element with focus
     *    cy.focused().blur()
     *    // Make an assertion on the focused element
     *    cy.focused().should('have.attr', 'name', 'username')
     */
    focused(options?: Partial<Loggable & Timeoutable>): Chainable<JQuery>

    /**
     * Get one or more DOM elements by node name: input, button, etc.
     * @see https://on.cypress.io/get
     * @example
     *    cy.get('input').should('be.disabled')
     *    cy.get('button').should('be.visible')
     */
    get<K extends keyof HTMLElementTagNameMap>(selector: K, options?: Partial<Loggable & Timeoutable & Withinable & Shadow>): Chainable<JQuery<HTMLElementTagNameMap[K]>>
    /**
     * Get one or more DOM elements by selector.
     * The querying behavior of this command matches exactly how $(…) works in jQuery.
     * @see https://on.cypress.io/get
     * @example
     *    cy.get('.list>li')    // Yield the <li>'s in <.list>
     *    cy.get('ul li:first').should('have.class', 'active')
     *    cy.get('.dropdown-menu').click()
     */
    get<E extends Node = HTMLElement>(selector: string, options?: Partial<Loggable & Timeoutable & Withinable & Shadow>): Chainable<JQuery<E>>
    /**
     * Get one or more DOM elements by alias.
     * @see https://on.cypress.io/get#Alias
     * @example
     *    // Get the aliased 'todos' elements
     *    cy.get('ul#todos').as('todos')
     *    //...hack hack hack...
     *    //later retrieve the todos
     *    cy.get('@todos')
     */
    get<S = any>(alias: string, options?: Partial<Loggable & Timeoutable & Withinable & Shadow>): Chainable<S>

    /**
     * Get a browser cookie by its name.
     *
     * @see https://on.cypress.io/getcookie
     */
    getCookie(name: string, options?: CookieOptions): Chainable<Cookie | null>

    /**
     * Get browser cookies for a domain.
     *
     * @see https://on.cypress.io/getcookies
     */
    getCookies(options?: CookieOptions): Chainable<Cookie[]>

    /**
     * Get all browser cookies.
     *
     * @see https://on.cypress.io/getallcookies
     */
    getAllCookies(options?: Partial<Loggable & Timeoutable>): Chainable<Cookie[]>

    /**
     * Navigate back or forward to the previous or next URL in the browser's history.
     *
     * @see https://on.cypress.io/go
     */
    go(direction: HistoryDirection | number, options?: Partial<Loggable & Timeoutable>): Chainable<AUTWindow>

    /**
     * Get the current URL hash of the page that is currently active.
     *
     * @see https://on.cypress.io/hash
     */
    hash(options?: Partial<Loggable & Timeoutable>): Chainable<string>

    /**
     * Invoke a function on the previously yielded subject.
     *
     * @see https://on.cypress.io/invoke
     */
    invoke<K extends keyof Subject, F extends ((...args: any[]) => any) & Subject[K], R = ReturnType<F>>(
      functionName: K,
      ...args: any[]
    ): Chainable<R>
    invoke<K extends keyof Subject, F extends ((...args: any[]) => any) & Subject[K], R = ReturnType<F>>(
      options: Partial<Loggable & Timeoutable>,
      functionName: K,
      ...args: any[]
    ): Chainable<R>

    /**
     * Invoke a function in an array of functions.
     * @see https://on.cypress.io/invoke
     */
    invoke<T extends (...args: any[]) => any, Subject extends T[]>(index: number): Chainable<ReturnType<T>>
    invoke<T extends (...args: any[]) => any, Subject extends T[]>(options: Partial<Loggable & Timeoutable>, index: number): Chainable<ReturnType<T>>

    /**
   * Invoke a function on the previously yielded subject by a property path.
   * Property path invocation cannot be strongly-typed.
   * Invoking by a property path will always result in any.
   *
   * @see https://on.cypress.io/invoke
   */
    invoke(propertyPath: string, ...args: any[]): Chainable

    /**
     * Get a property's value on the previously yielded subject.
     *
     * @see https://on.cypress.io/its
     * @example
     *    // Get the 'width' property
     *    cy.wrap({width: '50'}).its('width')
     *    // Drill into nested properties by using dot notation
     *    cy.wrap({foo: {bar: {baz: 1}}}).its('foo.bar.baz')
     */
    its<K extends keyof Subject>(propertyName: K, options?: Partial<Loggable & Timeoutable>): Chainable<NonNullable<Subject[K]>>
    its(propertyPath: string, options?: Partial<Loggable & Timeoutable>): Chainable

    /**
     * Get a value by index from an array yielded from the previous command.
     * @see https://on.cypress.io/its
     * @example
     *    cy.wrap(['a', 'b']).its(1).should('equal', 'b')
     */
    its<T, Subject extends T[]>(index: number, options?: Partial<Loggable & Timeoutable>): Chainable<T>

    /**
     * Get the last DOM element within a set of DOM elements.
     *
     * @see https://on.cypress.io/last
     */
    last<E extends Node = HTMLElement>(options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>

    /**
     * Get the global `window.location` object of the page that is currently active.
     *
     * @see https://on.cypress.io/location
     * @example
     *    cy.location() // Get location object
     */
    location(options?: Partial<Loggable & Timeoutable>): Chainable<Location>
    /**
     * Get a part of the global `window.location` object of the page that is currently active.
     *
     * @see https://on.cypress.io/location
     * @example
     *    cy.location('host') // Get the host of the location object
     *    cy.location('port') // Get the port of the location object
     *    // Assert on the href of the location
     *    cy.location('href').should('contain', '/tag/tutorials')
     */
    location<K extends keyof Location>(key: K, options?: Partial<Loggable & Timeoutable>): Chainable<Location[K]>

    /**
     * Print a message to the Cypress Command Log.
     *
     * @see https://on.cypress.io/log
     */
    log(message: string, ...args: any[]): Chainable<null>

    /**
     * Get the immediately following sibling of each DOM element within a set of DOM elements.
     *
     * @see https://on.cypress.io/next
     */
    next<K extends keyof HTMLElementTagNameMap>(selector: K, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<HTMLElementTagNameMap[K]>>
    /**
     * Get the immediately following sibling of each DOM element within a set of DOM elements.
     *
     * @see https://on.cypress.io/next
     * @example
     *    cy.get('nav a:first').next()
     */
    next<E extends Node = HTMLElement>(options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>
    /**
     * Get the immediately following sibling of each DOM element within a set of DOM elements that match selector
     *
     * @see https://on.cypress.io/next
     * @example
     *    cy.get('nav a:first').next('.menu-item)
     */
    next<E extends Node = HTMLElement>(selector: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>

    /**
     * Get all following siblings of each DOM element in a set of matched DOM elements.
     *
     * @see https://on.cypress.io/nextall
     */
    nextAll<K extends keyof HTMLElementTagNameMap>(selector: K, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<HTMLElementTagNameMap[K]>>
    /**
     * Get all following siblings of each DOM element in a set of matched DOM elements.
     *
     * @see https://on.cypress.io/nextall
     */
    nextAll<E extends HTMLElement = HTMLElement>(options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>
    /**
     * Get all following siblings of each DOM element in a set of matched DOM elements.
     *
     * @see https://on.cypress.io/nextall
     */
    nextAll<E extends HTMLElement = HTMLElement>(selector: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>

    /**
     * Get all following siblings of each DOM element in a set of matched DOM elements up to, but not including, the element provided.
     *
     * @see https://on.cypress.io/nextuntil
     */
    nextUntil<K extends keyof HTMLElementTagNameMap>(selector: K, filter?: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<HTMLElementTagNameMap[K]>>
    /**
     * Get all following siblings of each DOM element in a set of matched DOM elements up to, but not including, the element provided.
     *
     * @see https://on.cypress.io/nextuntil
     */
    nextUntil<E extends Node = HTMLElement>(selector: string, filter?: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>
    /**
     * Get all following siblings of each DOM element in a set of matched DOM elements up to, but not including, the element provided.
     *
     * @see https://on.cypress.io/nextuntil
     */
    nextUntil<E extends Node = HTMLElement>(element: E | JQuery<E>, filter?: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>

    /**
     * Filter DOM element(s) from a set of DOM elements. Opposite of `.filter()`
     *
     * @see https://on.cypress.io/not
     */
    not(selector: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery>

    /**
     * Invoke a command synchronously, without using the command queue.
     *
     * @see https://on.cypress.io/api/custom-queries
     */
    now(name: string, ...args: any[]): Promise<any> | ((subject: any) => any)

    /**
     * These events come from Cypress as it issues commands and reacts to their state. These are all useful to listen to for debugging purposes.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    on: Actions

    /**
     * These events come from Cypress as it issues commands and reacts to their state. These are all useful to listen to for debugging purposes.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    once: Actions

    /**
     * These events come from Cypress as it issues commands and reacts to their state. These are all useful to listen to for debugging purposes.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    off: Actions

    /**
     * Enables running Cypress commands in a secondary origin.
     * @see https://on.cypress.io/origin
     * @example
     *    cy.origin('example.com', () => {
     *      cy.get('h1').should('equal', 'Example Domain')
     *    })
     */
    origin<T>(urlOrDomain: string, fn: () => void): Chainable<T>

    /**
     * Enables running Cypress commands in a secondary origin.
     * @see https://on.cypress.io/origin
     * @example
     *    cy.origin('example.com', { args: { key: 'value', foo: 'foo' } }, ({ key, foo }) => {
     *      expect(key).to.equal('value')
     *      expect(foo).to.equal('foo')
     *    })
     */
    origin<T, S>(urlOrDomain: string, options: {
      args: T
    }, fn: (args: T) => void): Chainable<S>

    /**
     * Get the parent DOM element of a set of DOM elements.
     *
     * @see https://on.cypress.io/parent
     */
    parent<K extends keyof HTMLElementTagNameMap>(selector: K, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<HTMLElementTagNameMap[K]>>
    /**
     * Get the parent DOM element of a set of DOM elements.
     *
     * @see https://on.cypress.io/parent
     */
    parent<E extends Node = HTMLElement>(options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>
    /**
     * Get the parent DOM element of a set of DOM elements.
     *
     * @see https://on.cypress.io/parent
     */
    parent<E extends Node = HTMLElement>(selector: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>

    /**
     * Get the parent DOM elements of a set of DOM elements.
     *
     * @see https://on.cypress.io/parents
     */
    parents<K extends keyof HTMLElementTagNameMap>(selector: K, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<HTMLElementTagNameMap[K]>>
    /**
     * Get the parent DOM elements of a set of DOM elements.
     *
     * @see https://on.cypress.io/parents
     */
    parents<E extends Node = HTMLElement>(options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>
    /**
     * Get the parent DOM elements of a set of DOM elements.
     *
     * @see https://on.cypress.io/parents
     */
    parents<E extends Node = HTMLElement>(selector: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>

    /**
     * Get all ancestors of each DOM element in a set of matched DOM elements up to, but not including, the element provided.
     *
     * @see https://on.cypress.io/parentsuntil
     */
    parentsUntil<K extends keyof HTMLElementTagNameMap>(selector: K, filter?: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<HTMLElementTagNameMap[K]>>
    /**
     * Get all ancestors of each DOM element in a set of matched DOM elements up to, but not including, the element provided.
     *
     * @see https://on.cypress.io/parentsuntil
     */
    parentsUntil<E extends Node = HTMLElement>(selector: string, filter?: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>
    /**
     * Get all ancestors of each DOM element in a set of matched DOM elements up to, but not including, the element provided.
     *
     * @see https://on.cypress.io/parentsuntil
     */
    parentsUntil<E extends Node = HTMLElement>(element: E | JQuery<E>, filter?: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>

    /**
     * Stop cy commands from running and allow interaction with the application under test. You can then "resume" running all commands or choose to step through the "next" commands from the Command Log.
     * This does not set a `debugger` in your code, unlike `.debug()`
     *
     * @see https://on.cypress.io/pause
     */
    pause(options?: Partial<Loggable>): Chainable<Subject>

    /**
     * Send a native sequence of keyboard events: keydown & press, followed by keyup, for the provided key.
     * Supported keys index the Cypress.Keyboard.Keys record.
     *
     * @example
     *    cy.press(Cypress.Keyboard.Keys.TAB) // dispatches a keydown and press event to the browser, followed by a keyup event.
     * @see https://on.cypress.io/press
     */
    press(key: SupportedKey, options?: Partial<Loggable & Timeoutable>): Chainable<null>

    /**
     * Get the immediately preceding sibling of each element in a set of the elements.
     *
     * @example
     *    cy.get('nav').prev('a') // Yield previous 'a'
     * @see https://on.cypress.io/prev
     */
    prev<K extends keyof HTMLElementTagNameMap>(selector: K, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<HTMLElementTagNameMap[K]>>
    /**
     * Get the immediately preceding sibling of each element in a set of the elements.
     *
     * @example
     *    cy.get('li').prev() // Yield previous 'li'
     * @see https://on.cypress.io/prev
     */
    prev<E extends Node = HTMLElement>(options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>
    /**
     * Get the immediately preceding sibling of each element in a set of the elements that match selector.
     *
     * @example
     *    cy.get('nav').prev('.menu-item') // Yield previous '.menu-item'
     * @see https://on.cypress.io/prev
     */
    prev<E extends Node = HTMLElement>(selector: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>

    /**
     * Get all previous siblings of each DOM element in a set of matched DOM elements.
     * > The querying behavior of this command matches exactly how [.prevAll()](http://api.jquery.com/prevAll) works in jQuery.
     *
     * @see https://on.cypress.io/prevall
     */
    prevAll<K extends keyof HTMLElementTagNameMap>(selector: K, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<HTMLElementTagNameMap[K]>>
    /**
     * Get all previous siblings of each DOM element in a set of matched DOM elements.
     * > The querying behavior of this command matches exactly how [.prevAll()](http://api.jquery.com/prevAll) works in jQuery.
     *
     * @see https://on.cypress.io/prevall
     */
    prevAll<E extends Node = HTMLElement>(options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>
    /**
     * Get all previous siblings of each DOM element in a set of matched DOM elements.
     * > The querying behavior of this command matches exactly how [.prevAll()](http://api.jquery.com/prevAll) works in jQuery.
     *
     * @see https://on.cypress.io/prevall
     */
    prevAll<E extends Node = HTMLElement>(selector: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>

    /**
     * Get all previous siblings of each DOM element in a set of matched DOM elements up to, but not including, the element provided.
     * > The querying behavior of this command matches exactly how [.prevUntil()](http://api.jquery.com/prevUntil) works in jQuery.
     *
     * @see https://on.cypress.io/prevuntil
     */
    prevUntil<K extends keyof HTMLElementTagNameMap>(selector: K, filter?: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<HTMLElementTagNameMap[K]>>
    /**
     * Get all previous siblings of each DOM element in a set of matched DOM elements up to, but not including, the element provided.
     * > The querying behavior of this command matches exactly how [.prevUntil()](http://api.jquery.com/prevUntil) works in jQuery.
     *
     * @see https://on.cypress.io/prevuntil
     */
    prevUntil<E extends Node = HTMLElement>(selector: string, filter?: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>
    /**
     * Get all previous siblings of each DOM element in a set of matched DOM elements up to, but not including, the element provided.
     * > The querying behavior of this command matches exactly how [.prevUntil()](http://api.jquery.com/prevUntil) works in jQuery.
     *
     * @see https://on.cypress.io/prevuntil
     */
    prevUntil<E extends Node = HTMLElement>(element: E | JQuery<E>, filter?: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>
    /**
     * An AI-powered command that generates Cypress commands from natural language test steps.
     *
     * @see https://on.cypress.io/prompt
     */
    prompt<T>(steps: string[], options?: PromptOptions): Chainable<T>
    /**
     * Read a file and yield its contents.
     *
     * @see https://on.cypress.io/readfile
     */
    readFile<Contents = any>(filePath: string, options?: Partial<ReadFileOptions & Loggable & Timeoutable>): Chainable<Contents>
    /**
     * Read a file with given encoding and yield its contents.
     *
     * @see https://on.cypress.io/readfile
     * @example
     *    cy.readFile('foo.json', 'utf8')
     */
    readFile<Contents = any>(filePath: string, encoding: Encodings, options?: Partial<Loggable & Timeoutable>): Chainable<Contents>

    /**
     * Reload the page.
     *
     * @see https://on.cypress.io/reload
     * @example
     *    cy.visit('http://localhost:3000/admin')
     *    cy.reload()
     */
    reload(): Chainable<AUTWindow>
    /**
     * Reload the page.
     *
     * @see https://on.cypress.io/reload
     * @param {Partial<Loggable & Timeoutable>} options Pass in an options object to modify the default behavior of cy.reload()
     * @example
     *    // Reload the page, do not log it in the command log and timeout after 15s
     *    cy.visit('http://localhost:3000/admin')
     *    cy.reload({log: false, timeout: 15000})
     */
    reload(options: Partial<Loggable & Timeoutable>): Chainable<AUTWindow>
    /**
     * Reload the page without cache
     *
     * @see https://on.cypress.io/reload
     * @param {Boolean} forceReload Whether to reload the current page without using the cache. true forces the reload without cache.
     * @example
     *    // Reload the page without using the cache
     *    cy.visit('http://localhost:3000/admin')
     *    cy.reload(true)
     */
    reload(forceReload: boolean): Chainable<AUTWindow>
    /**
     * Reload the page without cache and with log and timeout options
     *
     * @see https://on.cypress.io/reload
     * @param {Boolean} forceReload Whether to reload the current page without using the cache. true forces the reload without cache.
     * @param {Partial<Loggable & Timeoutable>} options Pass in an options object to modify the default behavior of cy.reload()
     * @example
     *    // Reload the page without using the cache, do not log it in the command log and timeout after 15s
     *    cy.visit('http://localhost:3000/admin')
     *    cy.reload(true, {log: false, timeout: 15000})
     */
    reload(forceReload: boolean, options: Partial<Loggable & Timeoutable>): Chainable<AUTWindow>

    /**
     * Make an HTTP GET request.
     *
     * @see https://on.cypress.io/request
     * @example
     *    cy.request('http://dev.local/seed')
     */
    request<T = any>(url: string, body?: RequestBody): Chainable<Response<T>>
    /**
     * Make an HTTP request with specific method.
     *
     * @see https://on.cypress.io/request
     * @example
     *    cy.request('POST', 'http://localhost:8888/users', {name: 'Jane'})
     */
    request<T = any>(method: HttpMethod, url: string, body?: RequestBody): Chainable<Response<T>>
    /**
     * Make an HTTP request with specific behavior.
     *
     * @see https://on.cypress.io/request
     * @example
     *    cy.request({
     *      url: '/dashboard',
     *      followRedirect: false // turn off following redirects
     *    })
     */
    request<T = any>(options: Partial<RequestOptions>): Chainable<Response<T>>

    /**
     * Get the root DOM element.
     * The root element yielded is `<html>` by default.
     * However, when calling `.root()` from a `.within()` command,
     * the root element will point to the element you are "within".
     *
     * @see https://on.cypress.io/root
     */
    root<E extends Node = HTMLHtmlElement>(options?: Partial<LogTimeoutOptions>): Chainable<JQuery<E>> // can't do better typing unless we ignore the `.within()` case

    /**
     * Take a screenshot of the application under test and the Cypress Command Log.
     *
     * @see https://on.cypress.io/screenshot
     * @example
     *    cy.screenshot()
     *    cy.get(".post").screenshot()
     */
    screenshot(options?: Partial<Loggable & Timeoutable & ScreenshotOptions>): Chainable<Subject>

    /**
     * Take a screenshot of the application under test and the Cypress Command Log and save under given filename.
     *
     * @see https://on.cypress.io/screenshot
     * @example
     *    cy.screenshot("post-element")
     *    cy.get(".post").screenshot("post-element")
     */
    screenshot(fileName: string, options?: Partial<Loggable & Timeoutable & ScreenshotOptions>): Chainable<Subject>

    /**
     * Scroll an element into view.
     *
     * @see https://on.cypress.io/scrollintoview
     */
    scrollIntoView(options?: Partial<ScrollIntoViewOptions>): Chainable<Subject>

    /**
     * Scroll to a specific position.
     *
     * @see https://on.cypress.io/scrollto
     */
    scrollTo(positionOrX: PositionType | number | string, options?: Partial<ScrollToOptions>): Chainable<Subject>
    /**
     * Scroll to a specific X,Y position.
     *
     * @see https://on.cypress.io/scrollto
     */
    scrollTo(x: number | string, y: number | string, options?: Partial<ScrollToOptions>): Chainable<Subject>

    /**
     * Select an `<option>` with specific text, value, or index within a `<select>`.
     *
     * @see https://on.cypress.io/select
     */
    select(valueOrTextOrIndex: string | number | Array<string | number>, options?: Partial<SelectOptions>): Chainable<Subject>

    /**
     * Select a file with the given <input> element, or drag and drop a file over any DOM subject.
     *
     * @param {FileReference} files - The file(s) to select or drag onto this element.
     * @see https://on.cypress.io/selectfile
     * @example
     *    cy.get('input[type=file]').selectFile(Cypress.Buffer.from('text'))
     *    cy.get('input[type=file]').selectFile({
     *      fileName: 'users.json',
     *      contents: [{name: 'John Doe'}]
     *    })
     */
    selectFile(files: FileReference | FileReference[], options?: Partial<SelectFileOptions>): Chainable<Subject>

    /**
     * Set a browser cookie.
     *
     * @see https://on.cypress.io/setcookie
     */
    setCookie(name: string, value: string, options?: Partial<SetCookieOptions>): Chainable<Cookie>

    /**
     * Traverse into an element's shadow root.
     *
     * @example
     *    cy.get('my-component')
     *    .shadow()
     *    .find('.my-button')
     *    .click()
     * @see https://on.cypress.io/shadow
     */
    shadow(): Chainable<Subject>

      /**
     * Traverse into an element's shadow root.
     *
     * @example
     *    cy.get('my-component')
     *    .shadow({ timeout: 10000, log: false })
     *    .find('.my-button')
     *    .click()
     * @see https://on.cypress.io/shadow
     */
    shadow(options?: Partial<LogTimeoutOptions>): Chainable<Subject>

    /**
     * Create an assertion. Assertions are automatically retried until they pass or time out.
     *
     * @see https://on.cypress.io/should
     * @example
     *   // Assert on the href of the location
     *   cy.location('href').should('contain', '/tag/tutorials/')
     */
    should: Chainer<Subject>

    /**
     * Get sibling DOM elements.
     *
     * @see https://on.cypress.io/siblings
     * @example
     *    cy.get('td').siblings('a') // Yield all link siblings of "td"
     */
    siblings<K extends keyof HTMLElementTagNameMap>(selector: K, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<HTMLElementTagNameMap[K]>>
    /**
     * Get all sibling DOM elements.
     *
     * @see https://on.cypress.io/siblings
     * @example
     *    cy.get('td').siblings() // Yield all siblings of "td"
     */
    siblings<E extends Node = HTMLElement>(options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>
    /**
     * Get all sibling DOM elements that match given selector.
     *
     * @see https://on.cypress.io/siblings
     * @example
     *    // Yield all elements with class "foo" that are siblings of "td"
     *    cy.get('td').siblings('.foo')
     */
    siblings<E extends Node = HTMLElement>(selector: string, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>

    /**
     * Returns a new spy function.
     * > Note: `.spy()` assumes you are already familiar with our guide: [Stubs, Spies, and Clocks](https://on.cypress.io/stubs-spies-and-clocks)
     *
     * @see https://on.cypress.io/spy
     * @example
     *    const fn = cy.spy() // returns "dumb" spy function
     *    fn(42)
     *    expect(fn).to.have.been.calledOnce
     *    expect(fn).to.have.always.been.calledWithExactly(42)
     */
    spy(): Agent<sinon.SinonSpy>
    /**
     * Wraps existing function and spies on it, while passing arguments and results.
     * @see https://on.cypress.io/spy
     * @example
     *    const add = (a, b) => a + b
     *    const spy = cy.spy(add)
     *    expect(spy(2, 3)).to.equal(5)
     *    expect(spy).to.have.been.calledWithExactly(2, 3)
     */
    spy(func: (...args: any[]) => any): Agent<sinon.SinonSpy>
    /**
     * Spy on a method.
     * @see https://on.cypress.io/spy
     * @example
     *    // assume App.start calls util.addListeners
     *    cy.spy(util, 'addListeners')
     *    App.start()
     *    expect(util.addListeners).to.be.called
     */
    spy<T>(obj: T, method: keyof T): Agent<sinon.SinonSpy>

    /**
     * Replace a function, record its usage and control its behavior.
     * > Note: `.stub()` assumes you are already familiar with our guide:
     * [Stubs, Spies, and Clocks](https://on.cypress.io/stubs-spies-and-clocks)
     *
     * @see https://on.cypress.io/stub
     * @example
     *    const fn = cy.stub() // stub without any arguments acts like a spy
     *    fn(42)
     *    expect(fn).to.have.been.calledOnce
     *    expect(fn).to.have.always.been.calledWithExactly(42)
     */
    stub(): Agent<sinon.SinonStub>
    /**
     * Stubs all the object's methods.
     *
     * @see https://on.cypress.io/stub
     * @example
     * const o = {
     *  toString () {
     *    return 'foo'
     *  }
     * }
     * expect(o.toString()).to.equal('foo')
     * cy.stub(o)
     * // because stub does not call original function
     * expect(o.toString()).to.equal(undefined)
     * expect(o.toString).to.have.been.calledOnce
     */
    stub(obj: any): Agent<sinon.SinonStub>
    /**
     * Stubs single method of an object.
     *
     * @see https://on.cypress.io/stub
     * @example
     *    const o = {}
     *    expect(o.toString()).to.equal('[object Object]')
     *    cy.stub(o, 'toString').callsFake(() => 'foo')
     *    expect(o.toString()).to.equal('foo')
     *    expect(o.toString).to.have.been.calledOnce
     */
    stub<T>(obj: T, method: keyof T): Agent<sinon.SinonStub>

    /**
     * Submit a form.
     *
     * @see https://on.cypress.io/submit
     */
    submit(options?: Partial<Loggable & Timeoutable>): Chainable<Subject>

    /**
     * Expand an array into multiple arguments.
     * @see https://on.cypress.io/spread
     * @example
     *    cy.getCookies().spread((cookie1, cookie2, cookie3) => {
     *      // each cookie is now an individual argument
     *    })
     */
    spread<S extends object | any[] | string | number | boolean>(fn: (...args: any[]) => S): Chainable<S>
    /**
     * Expand an array into multiple arguments.
     * @see https://on.cypress.io/spread
     * @example
     *    cy.getCookies().spread((cookie1, cookie2, cookie3) => {
     *      // each cookie is now an individual argument
     *    })
     */
    spread(fn: (...args: any[]) => void): Chainable<Subject>

    /**
     * Run a task in Node via the plugins file.
     *
     * @see https://on.cypress.io/api/task
     */
    task<S = unknown>(event: string, arg?: any, options?: Partial<Loggable & Timeoutable>): Chainable<S>

    /**
     * Enables you to work with the subject yielded from the previous command.
     *
     * @see https://on.cypress.io/then
     */
    then<S>(fn: (this: ObjectLike, currentSubject: Subject) => Chainable<S>): Chainable<S>
    /**
     * Enables you to work with the subject yielded from the previous command.
     *
     * @see https://on.cypress.io/then
     */
    then<S>(options: Partial<Timeoutable>, fn: (this: ObjectLike, currentSubject: Subject) => Chainable<S>): Chainable<S>
    /**
     * Enables you to work with the subject yielded from the previous command / promise.
     *
     * @see https://on.cypress.io/then
     */
    then<S>(fn: (this: ObjectLike, currentSubject: Subject) => PromiseLike<S>): Chainable<S>
    /**
     * Enables you to work with the subject yielded from the previous command / promise.
     *
     * @see https://on.cypress.io/then
     */
    then<S>(options: Partial<Timeoutable>, fn: (this: ObjectLike, currentSubject: Subject) => PromiseLike<S>): Chainable<S>
    /**
     * Enables you to work with the subject yielded from the previous command / promise.
     *
     * @see https://on.cypress.io/then
     */
    then<S extends string | number | boolean>(fn: (this: ObjectLike, currentSubject: Subject) => S): Chainable<S>
    /**
     * Enables you to work with the subject yielded from the previous command / promise.
     *
     * @see https://on.cypress.io/then
     */
    then<S extends HTMLElement>(fn: (this: ObjectLike, currentSubject: Subject) => S): Chainable<JQuery<S>>
    /**
     * Enables you to work with the subject yielded from the previous command / promise.
     *
     * @see https://on.cypress.io/then
     */
    then<S extends ArrayLike<HTMLElement>>(fn: (this: ObjectLike, currentSubject: Subject) => S): Chainable<JQuery<S extends ArrayLike<infer T> ? T : never>>
    /**
     * Enables you to work with the subject yielded from the previous command / promise.
     *
     * @see https://on.cypress.io/then
     */
    then<S extends any[] | object>(fn: (this: ObjectLike, currentSubject: Subject) => S): Chainable<S>
    /**
     * Enables you to work with the subject yielded from the previous command / promise.
     *
     * @see https://on.cypress.io/then
     */
    then<S>(fn: (this: ObjectLike, currentSubject: Subject) => S): ThenReturn<Subject, S>
    /**
     * Enables you to work with the subject yielded from the previous command / promise.
     *
     * @see https://on.cypress.io/then
     */
    then<S extends HTMLElement>(options: Partial<Timeoutable>, fn: (this: ObjectLike, currentSubject: Subject) => S): Chainable<JQuery<S>>
    /**
     * Enables you to work with the subject yielded from the previous command / promise.
     *
     * @see https://on.cypress.io/then
     */
    then<S extends ArrayLike<HTMLElement>>(options: Partial<Timeoutable>, fn: (this: ObjectLike, currentSubject: Subject) => S): Chainable<JQuery<S extends ArrayLike<infer T> ? T : never>>
    /**
     * Enables you to work with the subject yielded from the previous command / promise.
     *
     * @see https://on.cypress.io/then
     */
    then<S extends object | any[] | string | number | boolean>(options: Partial<Timeoutable>, fn: (this: ObjectLike, currentSubject: Subject) => S): Chainable<S>
    /**
     * Enables you to work with the subject yielded from the previous command / promise.
     *
     * @see https://on.cypress.io/then
     */
    then<S>(options: Partial<Timeoutable>, fn: (this: ObjectLike, currentSubject: Subject) => S): ThenReturn<Subject, S>
    /**
     * Enables you to work with the subject yielded from the previous command.
     *
     * @see https://on.cypress.io/then
     * @example
     *    cy.get('.nav').then(($nav) => {})  // Yields .nav as first arg
     *    cy.location().then((loc) => {})   // Yields location object as first arg
     */
    then(fn: (this: ObjectLike, currentSubject: Subject) => void): Chainable<Subject>
    /**
     * Enables you to work with the subject yielded from the previous command.
     *
     * @see https://on.cypress.io/then
     * @example
     *    cy.get('.nav').then(($nav) => {})  // Yields .nav as first arg
     *    cy.location().then((loc) => {})   // Yields location object as first arg
     */
    then(options: Partial<Timeoutable>, fn: (this: ObjectLike, currentSubject: Subject) => void): Chainable<Subject>

    /**
     * Move time after overriding a native time function with [cy.clock()](https://on.cypress.io/clock).
     * `cy.clock()` must be called before `cy.tick()`
     *
     * @see https://on.cypress.io/clock
     * @example
     *  cy.clock()
     *  ...
     *  // advance time by 10 minutes
     *  cy.tick(600*1000)
     *  // you can restore the real clock
     *  cy.tick(1000).then(clock => {
     *    clock.restore()
     *  })
     *  // or use this shortcut
     *  cy.tick(5000).invoke('restore')
     */
    tick(milliseconds: number, options?: Partial<Loggable>): Chainable<Clock>

    /**
     * Get the `document.title` property of the page that is currently active.
     *
     * @see https://on.cypress.io/title
     */
    title(options?: Partial<Loggable & Timeoutable>): Chainable<string>

    /**
     * Trigger an event on a DOM element.
     *
     * @see https://on.cypress.io/trigger
     */
    trigger<K extends keyof DocumentEventMap>(eventName: K, options?: Partial<TriggerOptions & ObjectLike & DocumentEventMap[K]>): Chainable<Subject>
    /**
     * Trigger an event on a DOM element.
     *
     * @see https://on.cypress.io/trigger
     */
    trigger<K extends keyof DocumentEventMap>(eventName: K, position?: PositionType, options?: Partial<TriggerOptions & ObjectLike & DocumentEventMap[K]>): Chainable<Subject>
    /**
     * Trigger an event on a DOM element.
     *
     * @see https://on.cypress.io/trigger
     */
    trigger<K extends keyof DocumentEventMap>(eventName: K, x: number, y: number, options?: Partial<TriggerOptions & ObjectLike & DocumentEventMap[K]>): Chainable<Subject>
    /**
     * Trigger an event on a DOM element.
     * Custom events... If the following were `.triggerCustom`,
     * `.trigger` strongly typed with event data
     *
     * @see https://on.cypress.io/trigger
     * @example
     *    cy.get('a').trigger('mousedown')
     */
    trigger(eventName: string, position?: PositionType, options?: Partial<TriggerOptions & ObjectLike>): Chainable<Subject>
    /**
     * Trigger an event on a DOM element.
     * Custom events... If the following were `.triggerCustom`,
     * `.trigger` strongly typed with event data
     *
     * @see https://on.cypress.io/trigger
     * @example
     *    cy.get('a').trigger('mousedown')
     */
    trigger(eventName: string, options?: Partial<TriggerOptions & ObjectLike>): Chainable<Subject>
    /**
     * Trigger an event on a DOM element.
     * Custom events... If the following were `.triggerCustom`,
     * `.trigger` strongly typed with event data
     *
     * @see https://on.cypress.io/trigger
     * @example
     *    cy.get('a').trigger('mousedown')
     */
    trigger(eventName: string, x: number, y: number, options?: Partial<TriggerOptions & ObjectLike>): Chainable<Subject>

    /**
     * Type into a DOM element.
     *
     * @see https://on.cypress.io/type
     * @example
     *    cy.get('input').type('Hello, World')
     *    // type "hello" + press Enter
     *    cy.get('input').type('hello{enter}')
     */
    type(text: string, options?: Partial<TypeOptions>): Chainable<Subject>

    /**
     * Uncheck checkbox(es).
     *
     * @see https://on.cypress.io/uncheck
     * @example
     *    // Unchecks checkbox element
     *    cy.get('[type="checkbox"]').uncheck()
     *    // Uncheck element with the id 'saveUserName'
     *    cy.get('#saveUserName').uncheck()
     *    // Uncheck all checkboxes
     *    cy.get(':checkbox').uncheck()
     *    // Uncheck the checkbox with the value of 'ga'
     *    cy.get('input[type="checkbox"]').uncheck(['ga'])
     */
    uncheck(options?: Partial<CheckClearOptions>): Chainable<Subject>
    /**
     * Uncheck specific checkbox.
     *
     * @see https://on.cypress.io/uncheck
     * @example
     *    // Uncheck the checkbox with the value of 'ga'
     *    cy.get('input[type="checkbox"]').uncheck('ga')
     */
    uncheck(value: string, options?: Partial<CheckClearOptions>): Chainable<Subject>
    /**
     * Uncheck specific checkboxes.
     *
     * @see https://on.cypress.io/uncheck
     * @example
     *    // Uncheck the checkbox with the value of 'ga', 'ma'
     *    cy.get('input[type="checkbox"]').uncheck(['ga', 'ma'])
     */
    uncheck(values: string[], options?: Partial<CheckClearOptions>): Chainable<Subject>

    /**
     * Get the current URL of the page that is currently active.
     *
     * @alias cy.location('href')
     * @see https://on.cypress.io/url
     */
    url(options?: Partial<UrlOptions>): Chainable<string>

    /**
     * Control the size and orientation of the screen for your application.
     *
     * @see https://on.cypress.io/viewport
     * @example
     *    // Set viewport to 550px x 750px
     *    cy.viewport(550, 750)
     *    // Set viewport to 357px x 667px
     *    cy.viewport('iphone-6')
     */
    viewport(preset: ViewportPreset, orientation?: ViewportOrientation, options?: Partial<Loggable>): Chainable<null>
    /**
     * Set viewport to the given resolution.
     *
     * @see https://on.cypress.io/viewport
     * @example
     *    // Set viewport to 550px x 750px
     *    cy.viewport(550, 750)
     */
    viewport(width: number, height: number, options?: Partial<Loggable>): Chainable<null>

    /**
     * Visit the given url
     *
     * @param {string} url The URL to visit. If relative uses `baseUrl`
     * @param {VisitOptions} [options] Pass in an options object to change the default behavior of `cy.visit()`
     * @see https://on.cypress.io/visit
     * @example
     *    cy.visit('http://localhost:3000')
     *    cy.visit('/somewhere') // opens ${baseUrl}/somewhere
     *    cy.visit({
     *      url: 'http://google.com',
     *      method: 'POST'
     *    })
     *
     */
    visit(url: string, options?: Partial<VisitOptions>): Chainable<AUTWindow>
    visit(options: Partial<VisitOptions> & { url: string }): Chainable<AUTWindow>

    /**
     * Wait for a number of milliseconds.
     * You almost never need to wait for an arbitrary period of time.
     * There are always better ways to express this in Cypress, see the documentation.
     *
     * @see https://on.cypress.io/wait
     * @param {number} ms - Milliseconds to wait.
     * @example
     *    cy.wait(1000) // wait for 1 second
     */
    wait(ms: number, options?: Partial<Loggable & Timeoutable>): Chainable<Subject>

    /**
     * Get the window object of the page that is currently active.
     *
     * @see https://on.cypress.io/window
     * @example
    ```
    cy.visit('http://localhost:8080/app')
    cy.window().then(function(win){
      // win is the remote window
      // of the page at: http://localhost:8080/app
    })
    ```
     */
    window(options?: Partial<Loggable & Timeoutable>): Chainable<AUTWindow>

    /**
     * Scopes all subsequent cy commands to within this element.
     * Useful when working within a particular group of elements such as a `<form>`.
     * @see https://on.cypress.io/within
     * @example
    ```
    cy.get('form').within(($form) => {
      // cy.get() will only search for elements within form,
      // not within the entire document
      cy.get('input[name="username"]').type('john')
      cy.get('input[name="password"]').type('password')
      cy.root().submit()
    })
    ```
     */
    within(fn: (currentSubject: Subject) => void): Chainable<Subject>
    /**
     * Scopes all subsequent cy commands to within this element.
     * Useful when working within a particular group of elements such as a `<form>`.
     * @see https://on.cypress.io/within
     */
    within(options: Partial<Loggable>, fn: (currentSubject: Subject) => void): Chainable<Subject> // inconsistent argument order

    /**
     * Yield the element passed into `.wrap()`.
     *
     * @see https://on.cypress.io/wrap
     * @example
    ```
    // wraps DOM element
    cy.get('form').within(($form) => {
      // more commands
      cy.wrap($form).should('have.class', 'form-container')
    })
    ```
     */
    wrap<E extends Node = HTMLElement>(element: E | JQuery<E>, options?: Partial<Loggable & Timeoutable>): Chainable<JQuery<E>>
    /**
     * Yield the element passed into `.wrap()` to the next command in the Cypress chain.
     *
     * @see https://on.cypress.io/wrap
     * @example
    ```
    cy.wrap(new Promise((resolve, reject) => {
      setTimeout(resolve, 1000);
    }).then(result => {})
    ```
     */
    wrap<F extends Promise<S>, S>(promise: F, options?: Partial<Loggable & Timeoutable>): Chainable<S>
    /**
     * Yields whatever is passed into `.wrap()` to the next command in the Cypress chain.
     *
     * @see https://on.cypress.io/wrap
     * @example
    ```
    // Make assertions about object
    cy.wrap({ amount: 10 })
      .should('have.property', 'amount')
      .and('eq', 10)
    ```
     */
    wrap<S>(object: S, options?: Partial<Loggable & Timeoutable>): Chainable<S>

    /**
     * Write to a file with the specified contents.
     *
     * @see https://on.cypress.io/writefile
    ```
    cy.writeFile('path/to/message.txt', 'Hello World')
    ```
     */
    writeFile(filePath: string, contents: FileContents, encoding: Encodings): Chainable<null>
    /**
     * Write to a file with the specified encoding and contents.
     *
     * @see https://on.cypress.io/writefile
    ```
    cy.writeFile('path/to/ascii.txt', 'Hello World', {
      flag: 'a+',
      encoding: 'ascii'
    })
    ```
     */
    writeFile(filePath: string, contents: FileContents, options?: Partial<WriteFileOptions & Timeoutable>): Chainable<null>
    /**
     * Write to a file with the specified encoding and contents.
     *
     * An `encoding` option in `options` will override the `encoding` argument.
     *
     * @see https://on.cypress.io/writefile
    ```
    cy.writeFile('path/to/ascii.txt', 'Hello World', 'utf8', {
      flag: 'a+',
    })
    ```
     */
    writeFile(filePath: string, contents: FileContents, encoding: Encodings, options?: Partial<WriteFileOptions & Timeoutable>): Chainable<null>

    /**
     * jQuery library bound to the AUT
     *
     * @see https://on.cypress.io/$
     * @example
     *    cy.$$('p')
     */
    $$<TElement extends Element = HTMLElement>(selector: JQuery.Selector, context?: Element | Document | JQuery): JQuery<TElement>
  }

  type ChainableMethods<Subject = any> = {
    [P in keyof Chainable<Subject>]: Chainable<Subject>[P] extends ((...args: any[]) => any)
    ? Chainable<Subject>[P]
    : never
  }

  interface SinonSpyAgent<A extends sinon.SinonSpy> {
    log(shouldOutput?: boolean): Omit<A, 'withArgs'> & Agent<A>

    /**
     * Saves current spy / stub under an alias.
     * @see https://on.cypress.io/stubs-spies-and-clocks
     * @see https://on.cypress.io/as
     * @example
     *    cy.spy(win, 'fetch').as('winFetch') // Alias 'window.fetch' spy as "winFetch"
     */
    as(alias: string): Omit<A, 'withArgs'> & Agent<A>

    /**
     * Creates a spy / stub but only for calls with given arguments.
     * @see https://on.cypress.io/stubs-spies-and-clocks
     * @see https://on.cypress.io/as
     * @example
     *    const s = cy.stub(JSON, 'parse').withArgs('invalid').returns(42)
     *    expect(JSON.parse('invalid')).to.equal(42)
     *    expect(s).to.have.been.calledOnce
     */
    withArgs(...args: any[]): Omit<A, 'withArgs'> & Agent<A>

    callsFake(func: (...args: any[]) => any): Agent<A>

    callThroughWithNew(): Agent<A>
  }

  type Agent<T extends sinon.SinonSpy> = SinonSpyAgent<T> & T

  interface Failable {
    /**
     * Whether to fail on response codes other than 2xx and 3xx
     *
     * @default {true}
     */
    failOnStatusCode: boolean

    /**
     * Whether Cypress should automatically retry status code errors under the hood
     *
     * @default {false}
     */
    retryOnStatusCodeFailure: boolean

    /**
     * Whether Cypress should automatically retry transient network errors under the hood
     *
     * @default {true}
     */
    retryOnNetworkFailure: boolean
  }

  /**
   * Options that control how a command behaves in the `within` scope.
   * These options will determine how nodes are selected.
   */

  interface Withinable {
    /**
     * Element to search for children in. If null, search begins from root-level DOM element.
     *
     * @default depends on context, null if outside of within wrapper
     */
    withinSubject: JQuery | HTMLElement | null
  }

  /**
   * Element traversal options for dealing with Shadow DOM
   */
  interface Shadow {
    /**
     * Include shadow DOM in search
     *
     * @default: false
     */
    includeShadowDom: boolean
  }

  /**
   * Options that control how a command is logged in the Reporter
   */
  interface Loggable {
    /**
     * Displays the command in the Command Log
     *
     * @default true
     */
    log: boolean
  }

  /**
   * Options that control how long Test Runner is waiting for command to succeed
   */
  interface Timeoutable {
    /**
     * Time to wait (ms)
     *
     * @default defaultCommandTimeout
     * @see https://on.cypress.io/configuration#Timeouts
     */
    timeout: number
  }

  /**
   * Options that check case sensitivity
   */
  interface CaseMatchable {
    /**
     * Check case sensitivity
     *
     * @default true
     */
    matchCase: boolean
  }

  /**
   * Options that control how long the Test Runner waits for an XHR request and response to succeed
   */
  interface TimeoutableXHR {
    /**
     * Time to wait for the request (ms)
     *
     * @default {@link Timeoutable#timeout}
     * @see https://on.cypress.io/configuration#Timeouts
     */
    requestTimeout: number
    /**
     * Time to wait for the response (ms)
     *
     * @default {@link Timeoutable#timeout}
     * @see https://on.cypress.io/configuration#Timeouts
     */
    responseTimeout: number
  }

  /**
   * Options to force an event, skipping Actionability check
   * @see https://on.cypress.io/interacting-with-elements#Actionability
   */
  interface Forceable {
    /**
     * Forces the action, disables waiting for actionability
     *
     * @default false
     */
    force: boolean
  }

  type experimentalCspAllowedDirectives = 'default-src' | 'child-src' | 'frame-src' | 'script-src' | 'script-src-elem' | 'form-action'

  type scrollBehaviorOptions = false | 'center' | 'top' | 'bottom' | 'nearest'

  /**
   * Options to affect Actionability checks
   * @see https://on.cypress.io/interacting-with-elements#Actionability
   */
  interface ActionableOptions extends Forceable {
    /**
     * Whether to wait for elements to finish animating before executing commands
     *
     * @default true
     */
    waitForAnimations: boolean
    /**
     * The distance in pixels an element must exceed over time to be considered animating
     *
     * @default 5
     */
    animationDistanceThreshold: number
    /**
     * Viewport position to which an element should be scrolled prior to action commands. Setting `false` disables scrolling.
     *
     * @default 'top'
     */
    scrollBehavior: scrollBehaviorOptions
  }

  /**
   * Options to affect how an alias is stored
   *
   * @see https://on.cypress.io/as
   */
  interface AsOptions {
    /**
     * The type of alias to store, which impacts how the value is retrieved later in the test.
     * If an alias should be a 'query' (re-runs all queries leading up to the resulting value so it's alway up-to-date) or a
     * 'static' (read once when the alias is saved and is never updated). `type` has no effect when aliasing intercepts, spies, and stubs.
     *
     * @default 'query'
     */
    type: 'query' | 'static'
  }

  interface BlurOptions extends Loggable, Timeoutable, Forceable { }

  interface CheckClearOptions extends Loggable, Timeoutable, ActionableOptions { }

  interface LogTimeoutOptions extends Loggable, Timeoutable { }
  /**
   * Object to change the default behavior of .click().
   */
  interface ClickOptions extends Loggable, Timeoutable, ActionableOptions {
    /**
     * Serially click multiple elements
     *
     * @default false
     */
    multiple: boolean
    /**
     * Activates the control key during click
     *
     * @default false
     */
    ctrlKey: boolean
    /**
     * Activates the control key during click
     *
     * @default false
     */
    controlKey: boolean
    /**
     * Activates the alt key (option key for Mac) during click
     *
     * @default false
     */
    altKey: boolean
    /**
     * Activates the alt key (option key for Mac) during click
     *
     * @default false
     */
    optionKey: boolean
    /**
     * Activates the shift key during click
     *
     * @default false
     */
    shiftKey: boolean
    /**
     * Activates the meta key (Windows key or command key for Mac) during click
     *
     * @default false
     */
    metaKey: boolean
    /**
     * Activates the meta key (Windows key or command key for Mac) during click
     *
     * @default false
     */
    commandKey: boolean
    /**
     * Activates the meta key (Windows key or command key for Mac) during click
     *
     * @default false
     */
    cmdKey: boolean
  }

  interface CookieOptions extends Partial<Loggable & Timeoutable> {
    /**
     * Domain to set cookies on or get cookies from
     * @default hostname of the current app under test
     */
    domain?: string
  }

  interface PEMCert {
    /**
     * Path to the certificate file, relative to project root.
     */
    cert: string
    /**
     * Path to the private key file, relative to project root.
     */
    key: string
    /**
     * Path to a text file containing the passphrase, relative to project root.
     */
    passphrase?: string
  }

  interface PFXCert {
    /**
     * Path to the certificate container, relative to project root.
     */
    pfx: string
    /**
     * Path to a text file containing the passphrase, relative to project root.
     */
    passphrase?: string
  }

  interface ClientCertificate {
    /**
     * URL to match requests against. Wildcards following [minimatch](https://github.com/isaacs/minimatch) rules are supported.
     */
    url: string
    /**
     * Paths to one or more CA files to validate certs against, relative to project root.
     */
    ca?: string[]
    /**
     * A PEM format certificate/private key pair or PFX certificate container
     */
    certs: PEMCert[] | PFXCert[]
  }

  type RetryStrategyWithModeSpecs = RetryStrategy & {
    openMode: boolean // defaults to false
    runMode: boolean // defaults to true
  }

  type RetryStrategy =
    | RetryStrategyDetectFlakeAndPassOnThresholdType
    | RetryStrategyDetectFlakeButAlwaysFailType

  interface RetryStrategyDetectFlakeAndPassOnThresholdType {
    experimentalStrategy: 'detect-flake-and-pass-on-threshold'
    experimentalOptions?: {
      maxRetries: number // defaults to 2 if experimentalOptions is not provided, must be a whole number > 0
      passesRequired: number // defaults to 2 if experimentalOptions is not provided, must be a whole number > 0 and <= maxRetries
    }
  }

  interface RetryStrategyDetectFlakeButAlwaysFailType {
    experimentalStrategy: 'detect-flake-but-always-fail'
    experimentalOptions?: {
      maxRetries: number // defaults to 2 if experimentalOptions is not provided, must be a whole number > 0
      stopIfAnyPassed: boolean // defaults to false if experimentalOptions is not provided
    }
  }
  interface ResolvedConfigOptions<ComponentDevServerOpts = any> {
    /**
     * Url used as prefix for [cy.visit()](https://on.cypress.io/visit) or [cy.request()](https://on.cypress.io/request) command's url
     * @default null
     */
    baseUrl: string | null
    /**
     * Any values to be set as [environment variables](https://on.cypress.io/environment-variables)
     * @default {}
     */
    env: { [key: string]: any }
    /**
     * A String or Array of glob patterns used to ignore test files that would otherwise be shown in your list of tests. Cypress uses minimatch with the options: {dot: true, matchBase: true}. We suggest using a tool to test what files would match.
     * @default "*.hot-update.js"
     */
    excludeSpecPattern: string | string[]
    /**
     * The number of tests for which snapshots and command data are kept in memory. Reduce this number if you are experiencing high memory consumption in your browser during a test run.
     * @default 50
     */
    numTestsKeptInMemory: number
    /**
     * Port used to host Cypress. Normally this is a randomly generated port
     * @default null
     */
    port: number | null
    /**
     * The [reporter](https://on.cypress.io/reporters) used when running headlessly or in CI
     * @default "spec"
     */
    reporter: string
    /**
     * Some reporters accept [reporterOptions](https://on.cypress.io/reporters) that customize their behavior
     * @default "spec"
     */
    reporterOptions: { [key: string]: any }
    /**
     * Slow test threshold in milliseconds. Only affects the visual output of some reporters. For example, the spec reporter will display the test time in yellow if over the threshold.
     * @default 10000
     */
    slowTestThreshold: number
    /**
     * Whether Cypress will watch and restart tests on test file changes
     * @default true
     */
    watchForFileChanges: boolean
    /**
     * Time, in milliseconds, to wait until most DOM based commands are considered timed out
     * @default 4000
     */
    defaultCommandTimeout: number
    /**
     * Time, in milliseconds, to wait for a system command to finish executing during a [cy.exec()](https://on.cypress.io/exec) command
     * @default 60000
     */
    execTimeout: number
    /**
     * Time, in milliseconds, to wait for page transition events or [cy.visit()](https://on.cypress.io/visit), [cy.go()](https://on.cypress.io/go), [cy.reload()](https://on.cypress.io/reload) commands to fire their page load events
     * @default 60000
     */
    pageLoadTimeout: number
    /**
     * Whether Cypress will search for and replace
     * obstructive JS code in .js or .html files.
     *
     * @see https://on.cypress.io/configuration#modifyObstructiveCode
     */
    modifyObstructiveCode: boolean
    /**
     * Time, in milliseconds, to wait for an XHR request to go out in a [cy.wait()](https://on.cypress.io/wait) command
     * @default 5000
     */
    requestTimeout: number
    /**
     * Time, in milliseconds, to wait for a response in a [cy.request()](https://on.cypress.io/request), [cy.wait()](https://on.cypress.io/wait), [cy.fixture()](https://on.cypress.io/fixture), [cy.getCookie()](https://on.cypress.io/getcookie), [cy.getCookies()](https://on.cypress.io/getcookies), [cy.setCookie()](https://on.cypress.io/setcookie), [cy.clearCookie()](https://on.cypress.io/clearcookie), [cy.clearCookies()](https://on.cypress.io/clearcookies), and [cy.screenshot()](https://on.cypress.io/screenshot) commands
     * @default 30000
     */
    responseTimeout: number
    /**
     * Time, in milliseconds, to wait for a task to finish executing during a cy.task() command
     * @default 60000
     */
    taskTimeout: number
    /**
     * Path to folder where application files will attempt to be served from
     * @default root project folder
     */
    fileServerFolder: string
    /**
     * Path to folder containing fixture files (Pass false to disable)
     * @default "cypress/fixtures"
     */
    fixturesFolder: string | false
    /**
     * Path to folder where files downloaded during a test are saved
     * @default "cypress/downloads"
     */
    downloadsFolder: string
    /**
     * The application under test cannot redirect more than this limit.
     * @default 20
     */
    redirectionLimit: number
    /**
     * If a `node` executable is found, this will be the full filesystem path to that executable.
     * @default null
     */
    resolvedNodePath: string
    /**
     * The version of `node` that is being used to execute plugins.
     * @example 1.2.3
     */
    resolvedNodeVersion: string
    /**
     * Whether Cypress will take a screenshot when a test fails during cypress run.
     * @default true
     */
    screenshotOnRunFailure: boolean
    /**
     * Path to folder where screenshots will be saved from [cy.screenshot()](https://on.cypress.io/screenshot) command or after a headless or CI run's test failure
     * @default "cypress/screenshots"
     */
    screenshotsFolder: string | false
    /**
     * Path to file to load before test files load. This file is compiled and bundled. (Pass false to disable)
     * @default "cypress/support/{e2e|component}.js"
     */
    supportFile: string | false
    /**
     * The test isolation ensures a clean browser context between tests.
     *
     * Cypress will always reset/clear aliases, intercepts, clock, and viewport before each test
     * to ensure a clean test slate; i.e. this configuration only impacts the browser context.
     *
     * Note: the [`cy.session()`](https://on.cypress.io/session) command will inherent this value to determine whether
     * or not the page is cleared when the command executes. This command is only available in end-to-end testing.
     *
     *  - true - The page is cleared before each test. Cookies, local storage and session storage in all domains are cleared
     *         before each test. The `cy.session()` command will also clear the page and current browser context when creating
     *         or restoring the browser session.
     *  - false - The current browser state will persist between tests. The page does not clear before the test and cookies, local
     *          storage and session storage will be available in the next test. The `cy.session()` command will only clear the
     *          current browser context when creating or restoring the browser session - the current page will not clear.
     *
     * Tradeoffs:
     *      Turning test isolation off may improve performance of end-to-end tests, however, previous tests could impact the
     *      browser state of the next test and cause inconsistency when using .only(). Be mindful to write isolated tests when
     *      test isolation is false. If a test in the suite impacts the state of other tests and it were to fail, you could see
     *      misleading errors in later tests which makes debugging clunky. See the [documentation](https://on.cypress.io/test-isolation)
     *      for more information.
     *
     * @default true
     */
    testIsolation: boolean
    /**
     * Path to folder where videos will be saved after a headless or CI run
     * @default "cypress/videos"
     */
    videosFolder: string
    /**
     * Whether Cypress will trash assets within the screenshotsFolder and videosFolder before headless test runs.
     * @default true
     */
    trashAssetsBeforeRuns: boolean
    /**
     * The quality setting for the video compression, in Constant Rate Factor (CRF).
     * Enable compression by passing true to use the default CRF of 32.
     * Compress at custom CRF by passing a number between 1 and 51, where a lower value results in better quality (at the expense of a higher file size).
     * Disable compression by passing false or 0.
     * @default 32
     */
    videoCompression: number | boolean
    /**
     * Whether Cypress will record a video of the test run when executing in run mode.
     * @default false
     */
    video: boolean
    /**
     * Whether Chrome Web Security for same-origin policy and insecure mixed content is enabled. Read more about this [here](https://on.cypress.io/web-security#Disabling-Web-Security)
     * @default true
     */
    chromeWebSecurity: boolean
    /**
     * Default height in pixels for the application under tests' viewport (Override with [cy.viewport()](https://on.cypress.io/viewport) command)
     * @default 660
     */
    viewportHeight: number
    /**
     * Default width in pixels for the application under tests' viewport. (Override with [cy.viewport()](https://on.cypress.io/viewport) command)
     * @default 1000
     */
    viewportWidth: number
    /**
     * The distance in pixels an element must exceed over time to be considered animating
     * @default 5
     */
    animationDistanceThreshold: number
    /**
     * Whether to wait for elements to finish animating before executing commands
     * @default true
     */
    waitForAnimations: boolean
    /**
     * Viewport position to which an element should be scrolled prior to action commands. Setting `false` disables scrolling.
     * @default 'top'
     */
    scrollBehavior: scrollBehaviorOptions
    /**
     * Indicates whether Cypress should allow CSP header directives from the application under test.
     * - When this option is set to `false`, Cypress will strip the entire CSP header.
     * - When this option is set to `true`, Cypress will only to strip directives that would interfere
     * with or inhibit Cypress functionality.
     * - When this option to an array of allowable directives (`[ 'default-src', ... ]`), the directives
     * specified will remain in the response headers.
     *
     * Please see the documentation for more information.
     * @see https://on.cypress.io/experiments#Experimental-CSP-Allow-List
     * @default false
     */
    experimentalCspAllowList: boolean | experimentalCspAllowedDirectives[]
    /**
     * Allows listening to the `before:run`, `after:run`, `before:spec`, and `after:spec` events in the plugins file during interactive mode.
     * @default false
     */
    experimentalInteractiveRunEvents: boolean
    /**
     * Whether Cypress will search for and replace obstructive code in third party .js or .html files.
     * NOTE: Setting this flag to true removes Subresource Integrity (SRI).
     * Please see https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity.
     * This option has no impact on experimentalSourceRewriting and is only used with the
     * non-experimental source rewriter.
     * @see https://on.cypress.io/experiments#Configuration
     */
    experimentalModifyObstructiveThirdPartyCode: boolean
    /**
     * Enables setting document.domain to the superdomain on code injection. This option is
     * disabled by default. Enabling this option allows for navigating between subdomains in
     * the same test without the use of cy.origin(). Setting document.domain is deprecated in Chrome.
     * Enabling this may result in incompatibilities with sites that leverage origin-agent-cluster
     * headers. Enabling this when a browser does not support setting document.domain will not result
     * in the browser allowing document.domain to be set. In these cases, this configuration option
     * must be set to false, to allow cy.origin() to be used on subdomains.
     * @default false
     */
    injectDocumentDomain: boolean
    /**
     * Enables AST-based JS/HTML rewriting. This may fix issues caused by the existing regex-based JS/HTML replacement algorithm.
     * @default false
     */
    experimentalSourceRewriting: boolean
    /**
     * Generate and save commands directly to your test suite by interacting with your app as an end user would.
     * @default false
     */
    experimentalStudio: boolean
    /**
     * Adds support for testing in the WebKit browser engine used by Safari. See https://on.cypress.io/webkit-experiment for more information.
     * @default false
     */
    experimentalWebKitSupport: boolean
    /**
     * Enables support for improved memory management within Chromium-based browsers.
     * @default false
     */
    experimentalMemoryManagement: boolean
    /**
     * Allows for just-in-time compiling of a component test, which will only compile assets related to the component.
     * This results in a smaller bundle under test, reducing resource constraints on a given machine. This option is recommended
     * for users with large component testing projects and those who are running into webpack 'chunk load error' issues.
     * Supported for webpack-dev-server only. For component testing only.
     * @see https://on.cypress.io/experiments#Configuration
     */
    justInTimeCompile: boolean
    /**
     * Number of times to retry a failed test.
     * If a number is set, tests will retry in both runMode and openMode.
     * To enable test retries only in runMode, set e.g. `{ openMode: null, runMode: 2 }`
     * @default null
     */
    retries: Nullable<number | ({ runMode?: Nullable<number>, openMode?: Nullable<number> }) | RetryStrategyWithModeSpecs>
    /**
     * Enables including elements within the shadow DOM when using querying
     * commands (e.g. cy.get(), cy.find()). Can be set globally in cypress.config.{js,ts,mjs,cjs},
     * per-suite or per-test in the test configuration object, or programmatically
     * with Cypress.config()
     * @default false
     */
    includeShadowDom: boolean

    /**
     * The list of hosts to be blocked
     */
    blockHosts: null | string | string[]
    /**
     * A unique ID for the project used for recording
     */
    projectId: null | string
    /**
     * Path to the support folder.
     */
    supportFolder: string
    /**
     * Glob pattern to determine what test files to load.
     */
    specPattern: string | string[]
    /**
     * The user agent the browser sends in all request headers.
     */
    userAgent: null | string

    /**
     * Override default config options for Component Testing runner.
     * @default {}
     */
    component: ComponentConfigOptions<ComponentDevServerOpts>

    /**
     * Override default config options for E2E Testing runner.
     * @default {}
     */
    e2e: EndToEndConfigOptions

    /**
     * An array of objects defining the certificates
     */
    clientCertificates: ClientCertificate[]

    /**
     * Handle Cypress plugins
     */
    setupNodeEvents: (on: PluginEvents, config: PluginConfigOptions) => Promise<PluginConfigOptions | void> | PluginConfigOptions | void

    indexHtmlFile: string

    /**
     * The default browser to launch if the "--browser" command line option is not provided.
     */
    defaultBrowser: string
  }

  interface EndToEndConfigOptions extends Omit<CoreConfigOptions, 'indexHtmlFile'> {
    /**
     * Enables the "Run All Specs" UI feature, allowing the execution of multiple specs sequentially.
     * @default false
     */
    experimentalRunAllSpecs?: boolean
    /**
     * Enables support for `Cypress.require()` for including dependencies within the `cy.origin()` callback.
     * @default false
     */
    experimentalOriginDependencies?: boolean
    /**
     * Enables support for `cy.prompt`, an AI-powered command that turns natural language steps into executable Cypress test code.
     * @default false
     */
    experimentalPromptCommand?: boolean
  }

  /**
   * Options appended to config object on runtime.
   */
  interface RuntimeConfigOptions extends Partial<RuntimeServerConfigOptions> {
    /**
     * Absolute path to the config file (default: <projectRoot>/cypress.config.{js,ts,mjs,cjs})
     */
    configFile: string
    /**
     * CPU architecture, from Node `os.arch()`
     *
     * @see https://nodejs.org/api/os.html#os_os_arch
     */
    arch: string
    /**
     * Available browsers found on your system.
     */
    browsers: Browser[]
    /**
     * Hosts mappings to IP addresses.
     */
    hosts: null | { [key: string]: string }
    /**
     * Whether Cypress was launched via 'cypress open' (interactive mode)
     */
    isInteractive: boolean
    /**
     * The platform Cypress is running on.
     */
    platform: 'linux' | 'darwin' | 'win32'
    remote: RemoteState
    /**
     * The Cypress version being used.
     */
    version: string

    // Internal or Unlisted at server/lib/config_options
    namespace: string
    projectRoot: string
    repoRoot: string | null
    devServerPublicPathRoute: string
    cypressBinaryRoot: string
  }

  /**
   * Optional options added before the server starts
   */
  interface RuntimeServerConfigOptions {
    /**
     * The browser Cypress is running on.
     */
    browser: Browser
    // Internal or Unlisted at server/lib/config_options
    autoOpen: boolean
    browserUrl: string
    clientRoute: string
    cypressEnv: string
    isNewProject: boolean
    isTextTerminal: boolean
    morgan: boolean
    parentTestsFolder: string
    parentTestsFolderDisplay: string
    projectName: string
    proxyUrl: string
    remote: RemoteState
    report: boolean
    reporterRoute: string
    reporterUrl: string
    socketId: null | string
    socketIoCookie: string
    socketIoRoute: string
    spec: Cypress['spec'] | null
    specs: Array<Cypress['spec']>
    isDefaultProtocolEnabled: boolean
    hideCommandLog: boolean
    hideRunnerUi: boolean
  }

  interface SuiteConfigOverrides extends Partial<
    Pick<ConfigOptions, 'animationDistanceThreshold' | 'blockHosts' | 'defaultCommandTimeout' | 'env' | 'execTimeout' | 'includeShadowDom' | 'numTestsKeptInMemory' | 'pageLoadTimeout' | 'redirectionLimit' | 'requestTimeout' | 'responseTimeout' | 'retries' | 'screenshotOnRunFailure' | 'slowTestThreshold' | 'scrollBehavior' | 'taskTimeout' | 'viewportHeight' | 'viewportWidth' | 'waitForAnimations'>
  >, Partial<Pick<ResolvedConfigOptions, 'baseUrl' | 'testIsolation'>> {
    browser?: IsBrowserMatcher | IsBrowserMatcher[]
    keystrokeDelay?: number
  }

  interface TestConfigOverrides extends Partial<
    Pick<ConfigOptions, 'animationDistanceThreshold' | 'blockHosts' | 'defaultCommandTimeout' | 'env' | 'execTimeout' | 'includeShadowDom' | 'numTestsKeptInMemory' | 'pageLoadTimeout' | 'redirectionLimit' | 'requestTimeout' | 'responseTimeout' | 'retries' | 'screenshotOnRunFailure' | 'slowTestThreshold' | 'scrollBehavior' | 'taskTimeout' | 'viewportHeight' | 'viewportWidth' | 'waitForAnimations'>
  >, Partial<Pick<ResolvedConfigOptions, 'baseUrl'>> {
    browser?: IsBrowserMatcher | IsBrowserMatcher[]
    keystrokeDelay?: number
  }

  /**
   * All configuration items are optional.
   */
  type CoreConfigOptions = Partial<Omit<ResolvedConfigOptions, TestingType>>

  interface DefineDevServerConfig {
    // This interface can be extended by the user, to inject the types for their
    // preferred bundler: e.g.
    //
    // import type * as webpack from 'webpack'
    //
    // declare global {
    //   namespace Cypress {
    //     interface DefineDevServerConfig {
    //       webpackConfig?: webpack.Configuration
    //     }
    //   }
    // }
    [key: string]: any
  }

  type PickConfigOpt<T> = T extends keyof DefineDevServerConfig ? DefineDevServerConfig[T] : any

  interface DependencyToInstall {
    dependency: CypressComponentDependency
    satisfied: boolean
    detectedVersion: string | null
  }

  interface CypressComponentDependency {
    /**
     * Unique identifier.
     * @example 'react'
     */
    type: string

    /**
     * Name to display in the user interface.
     * @example "React.js"
     */
    name: string

    /**
     * Package name on npm.
     * @example react
     */
    package: string

    /**
     * Code to run when installing. Version is optional.
     *
     * Should be <package_name>@<version>.
     *
     * @example `react`
     * @example `react@18`
     */
    installer: string

    /**
     * Description shown in UI. It is recommended to use the same one the package uses on npm.
     * @example  'A JavaScript library for building user interfaces'
     */
    description: string

    /**
     * Minimum version supported. Should conform to Semantic Versioning as used in `package.json`.
     * @see https://docs.npmjs.com/cli/v9/configuring-npm/package-json#dependencies
     * @example '^=17.0.0 || ^=8.0.0'
     * @example '^4.0.0'
     */
    minVersion: string
  }

  interface ResolvedComponentFrameworkDefinition {
    /**
     * A semantic, unique identifier.
     * Must begin with `cypress-ct-` or `@org/cypress-ct-` for third party implementations.
     * @example 'react'
     * @example 'nextjs'
     * @example 'cypress-ct-solid-js'
     */
    type: string

    /**
     * Used as the flag for `getPreset` for meta frameworks, such as finding the webpack config for CRA, Angular, etc.
     * It is also the name of the string added to `cypress.config`
     *
     * @example
     *   export default {
     *     component: {
     *       devServer: {
     *         framework: 'react' // can be 'next', 'vue', etc etc.
     *       }
     *     }
     *   }
     */
    configFramework: string

    /**
     * Library (React, Vue) or template (aka "meta framework") (CRA, Next.js, Angular)
     */
    category: 'library' | 'template'

    /**
     * Name displayed in Launchpad when doing initial setup.
     * @example 'Solid.js'
     * @example 'React.js'
     */
    name: string

    /**
     * Supported bundlers.
     */
    supportedBundlers: Array<'webpack' | 'vite'>

    /**
     * Used to attempt to automatically select the correct framework/bundler from the dropdown.
     *
     * @example
     *   const SOLID_DETECTOR: Dependency = {
     *     type: 'solid',
     *     name: 'Solid.js',
     *     package: 'solid-js',
     *     installer: 'solid-js',
     *     description: 'Solid is a declarative JavaScript library for creating user interfaces',
     *     minVersion: '^1.0.0',
     *   }
     */
    detectors: CypressComponentDependency[]

    /**
     * Array of required dependencies. This could be the bundler and JavaScript library.
     */
    dependencies: (bundler: 'webpack' | 'vite', projectPath: string) => Promise<DependencyToInstall[]>

    /**
     * This is used internally by Cypress for the "Create From Component" feature.
     */
    codeGenFramework?: 'react' | 'vue' | 'svelte' | 'angular'

    /**
     * This is used internally by Cypress for the "Create From Component" feature.
     * @example '*.{js,jsx,tsx}'
     */
    glob?: string

    /**
     * This is the path to get mount, eg `import { mount } from <mount_module>,
     * @example: `cypress-ct-solidjs/src/mount`
     */
    mountModule: (projectPath: string) => Promise<string>

    /**
     * Support status. Internally alpha | beta | full.
     * Community integrations are "community".
     */
    supportStatus: 'alpha' | 'beta' | 'full' | 'community'

    /**
     * Function returning string for used for the component-index.html file.
     * Cypress provides a default if one isn't specified for third party integrations.
     */
    componentIndexHtml?: () => string

    /**
     * Used for the Create From Component feature.
     * This is currently not supported for third party frameworks.
     */
    specPattern?: '**/*.cy.ts'
  }

  type ComponentFrameworkDefinition = Omit<ResolvedComponentFrameworkDefinition, 'dependencies'> & {
    dependencies: (bundler: 'webpack' | 'vite') => CypressComponentDependency[]
  }

  /**
   * Certain properties are not supported for third party frameworks right now,
   * such as ones related to the "Create From" feature. This is a subset of
   * properties that are exposed for public usage.
   */

  type ThirdPartyComponentFrameworkDefinition = Pick<ComponentFrameworkDefinition, 'type' | 'name' | 'supportedBundlers' | 'detectors' | 'dependencies'> & {
    /**
     * @example `cypress-ct-${string} for third parties. Any string is valid internally.
     */
    type: string

    /**
     * Raw SVG icon that will be displayed in the Project Setup Wizard. Used for third parties that
     * want to render a custom icon.
     */
    icon?: string
  }

  interface AngularDevServerProjectConfig {
    root: string
    sourceRoot: string
    buildOptions: Record<string, any>
  }

  type DevServerFn<ComponentDevServerOpts = any> = (cypressDevServerConfig: DevServerConfig, devServerConfig: ComponentDevServerOpts) => ResolvedDevServerConfig | Promise<ResolvedDevServerConfig>

  type ConfigHandler<T> = T
    | (() => T | Promise<T>)

  type DevServerConfigOptions = {
    bundler: 'webpack'
    framework: 'react' | 'vue' | 'next' | 'svelte'
    webpackConfig?: ConfigHandler<PickConfigOpt<'webpackConfig'>>
  } | {
    bundler: 'vite'
    framework: 'react' | 'vue' | 'svelte'
    viteConfig?: ConfigHandler<Omit<Exclude<PickConfigOpt<'viteConfig'>, undefined>, 'base' | 'root'>>
  } | {
    bundler: 'webpack'
    framework: 'angular'
    webpackConfig?: ConfigHandler<PickConfigOpt<'webpackConfig'>>
    options?: {
      projectConfig: AngularDevServerProjectConfig
    }
  }

  interface ComponentConfigOptions<ComponentDevServerOpts = any> extends Omit<CoreConfigOptions, 'baseUrl' | 'experimentalStudio'> {
    devServer: DevServerFn<ComponentDevServerOpts> | DevServerConfigOptions
    devServerConfig?: ComponentDevServerOpts
    /**
     * Runs all component specs in a single tab, trading spec isolation for faster run mode execution.
     * @default false
     */
    experimentalSingleTabRunMode?: boolean
  }

  /**
   * Config options that can be assigned on cypress.config.{js,ts,mjs,cjs} file
   */
  type UserConfigOptions<ComponentDevServerOpts = any> = Omit<ResolvedConfigOptions<ComponentDevServerOpts>, 'baseUrl' | 'excludeSpecPattern' | 'supportFile' | 'specPattern' | 'indexHtmlFile'>

  /**
   * Takes ComponentDevServerOpts to track the signature of the devServerConfig for the provided `devServer`,
   * so we have proper completion for `devServerConfig`
   */
  type ConfigOptions<ComponentDevServerOpts = any> = Partial<UserConfigOptions<ComponentDevServerOpts>> & {
    /**
     * Hosts mappings to IP addresses.
     */
    hosts?: null | { [key: string]: string }
  }

  interface PluginConfigOptions extends ResolvedConfigOptions, RuntimeConfigOptions {
    /**
    * Absolute path to the root of the project
    */
    projectRoot: string
    /**
     * Type of test and associated runner that was launched.
     */
    testingType: TestingType
    /**
     * Cypress version.
     */
    version: string
  }

  interface DebugOptions {
    verbose: boolean
  }

  /**
   * Options object to change the default behavior of cy.exec().
   */
  interface ExecOptions extends Loggable, Timeoutable {
    /**
     * Whether to fail if the command exits with a non-zero code
     *
     * @default true
     */
    failOnNonZeroExit: boolean
    /**
     * Object of environment variables to set before the command executes
     * (e.g. {USERNAME: 'johndoe'}). Will be merged with existing
     * system environment variables
     *
     * @default {}
     */
    env: object
  }

  /**
   * Options for Cypress.Keyboard.defaults()
   */
  interface KeyboardDefaultsOptions {
    /**
    * Time, in milliseconds, between each keystroke when typing. (Pass 0 to disable)
    *
    * @default 10
    */
    keystrokeDelay: number
  }

  /**
   * Full set of possible options for cy.request call
   */
  interface RequestOptions extends Loggable, Timeoutable, Failable {
    auth: object
    body: RequestBody
    encoding: Encodings
    followRedirect: boolean
    form: boolean
    gzip: boolean
    headers: object
    method: HttpMethod
    qs: object
    url: string
  }

  interface RouteOptions {
    method: HttpMethod
    url: string | RegExp
    response: any
    status: number
    delay: number
    headers: object | null
    force404: boolean
    onRequest(...args: any[]): void
    onResponse(...args: any[]): void
    onAbort(...args: any[]): void
  }

  interface Dimensions {
    x: number
    y: number
    width: number
    height: number
  }

  type Padding =
    | number
    | [number]
    | [number, number]
    | [number, number, number]
    | [number, number, number, number]

  interface ScreenshotOptions {
    blackout: string[]
    capture: 'runner' | 'viewport' | 'fullPage'
    clip: Dimensions
    disableTimersAndAnimations: boolean
    padding: Padding
    scale: boolean
    overwrite: boolean
    onBeforeScreenshot: ($el: JQuery) => void
    onAfterScreenshot: ($el: JQuery, props: {
      path: string
      size: number
      dimensions: {
        width: number
        height: number
      }
      multipart: boolean
      pixelRatio: number
      takenAt: string
      name: string
      blackout: string[]
      duration: number
      testAttemptIndex: number
    }) => void
  }

  interface ScreenshotDefaultsOptions extends ScreenshotOptions {
    screenshotOnRunFailure: boolean
  }

  type SelectorPriority =
    | `attribute:${string}`
    | 'attributes'
    | 'class'
    | `data-${string}`
    | 'id'
    | 'name'
    | 'nth-child'
    | 'tag'

  interface ElementSelectorDefaultsOptions {
    selectorPriority?: SelectorPriority[]
  }

  interface ScrollToOptions extends Loggable, Timeoutable {
    /**
     * Scrolls over the duration (in ms)
     *
     * @default 0
     */
    duration: number | string
    /**
     * Will scroll with the easing animation
     *
     * @default 'swing'
     */
    easing: 'swing' | 'linear'
    /**
     * Ensure element is scrollable. Error if element is not scrollable
     *
     * @default true
     */
    ensureScrollable: boolean
  }

  interface ScrollIntoViewOptions extends ScrollToOptions {
    /**
     * Amount to scroll after the element has been scrolled into view
     *
     * @default {top: 0, left: 0}
     */
    offset: Offset
  }

  interface SelectOptions extends Loggable, Timeoutable, Forceable {
    interval: number
  }

  interface Session {
    /**
     * Clear all sessions saved on the backend, including cached global sessions.
     */
    clearAllSavedSessions: () => Promise<void>
    /**
     * Clear all storage and cookie data across all origins associated with the current session.
     */
    clearCurrentSessionData: () => Promise<void>
    /**
     * Get all storage and cookie data across all origins associated with the current session.
     */
    getCurrentSessionData: () => Promise<SessionData>
    /**
     * Get all storage and cookie data saved on the backend associated with the provided session id.
     */
    getSession: (id: string) => Promise<ServerSessionData>
  }

  type ActiveSessions = Record<string, SessionData>

  interface SessionData {
    id: string
    hydrated: boolean
    cacheAcrossSpecs: SessionOptions['cacheAcrossSpecs']
    cookies?: Cookie[] | null
    localStorage?: OriginStorage[] | null
    sessionStorage?: OriginStorage[] | null
    setup: () => void
    validate?: SessionOptions['validate']
  }

  interface ServerSessionData extends Omit<SessionData, 'setup' | 'validate'> {
    setup: string
    validate?: string
  }

  interface SessionOptions {
    /**
     * Whether or not to persist the session across all specs in the run.
     * @default {false}
     */
    cacheAcrossSpecs?: boolean
    /**
     * Function to run immediately after the session is created and `setup` function runs or
     * after a session is restored and the page is cleared. If this returns `false`, throws an
     * exception, returns a Promise which resolves to `false` or rejects or contains any failing
     * Cypress command, the session is considered invalid.
     *
     * If validation fails immediately after `setup`, the test will fail.
     * If validation fails after restoring a session, `setup` will re-run.
     * @default {false}
     */
    validate?: () => Promise<false | void> | void
  }

  type SameSiteStatus = 'no_restriction' | 'strict' | 'lax' | 'unspecified'

  interface SelectFileOptions extends Loggable, Timeoutable, ActionableOptions {
    /**
     * Which user action to perform. `select` matches selecting a file while
     * `drag-drop` matches dragging files from the operating system into the
     * document.
     *
     * @default 'select'
     */
    action: 'select' | 'drag-drop'
  }

  /**
   * Options that control how the `cy.setCookie` command
   * sets the cookie in the browser.
   * @see https://on.cypress.io/setcookie#Arguments
   */
  interface SetCookieOptions extends Loggable, Timeoutable {
    /**
     * The path of the cookie.
     * @default "/"
     */
    path: string
    /**
     * Represents the domain the cookie belongs to (e.g. "docs.cypress.io", "github.com").
     * @default location.hostname
     */
    domain: string
    /**
     * Whether a cookie's scope is limited to secure channels, such as HTTPS.
     * @default false
     */
    secure: boolean
    /**
     * Whether or not the cookie is HttpOnly, meaning the cookie is inaccessible to client-side scripts.
     * The Cypress cookie API has access to HttpOnly cookies.
     * @default false
     */
    httpOnly: boolean
    /**
     * Whether or not the cookie is a host-only cookie, meaning the request's host must exactly match the domain of the cookie.
     * @default false
     */
    hostOnly: boolean
    /**
     * The cookie's expiry time, specified in seconds since Unix Epoch.
     * The default is expiry is 20 years in the future from current time.
     */
    expiry: number
    /**
     * The cookie's SameSite value. If set, should be one of `lax`, `strict`, `no_restriction`, or `unspecified`.
     * `no_restriction` is the equivalent of `SameSite=None`. Pass `undefined` to use the browser's default ('unspecified' is the default for Firefox 140 and up).
     * Note: `no_restriction` can only be used if the secure flag is set to `true`.
     * @default undefined
     */
    sameSite: SameSiteStatus
  }

  interface ShadowDomOptions {
    includeShadowDom?: boolean
  }

  /**
   * Options that control `cy.type` command
   *
   * @see https://on.cypress.io/type
   */
  interface TypeOptions extends Loggable, Timeoutable, ActionableOptions {
    /**
     * Delay after each keypress (ms)
     *
     * @default 10
     */
    delay: number
    /**
     * Parse special characters for strings surrounded by `{}`,
     * such as `{esc}`. Set to `false` to type the literal characters instead
     *
     * @default true
     */
    parseSpecialCharSequences: boolean
    /**
     * Keep a modifier activated between commands
     *
     * @default true
     */
    release: boolean
  }

  /**
   * Visit website options
   *
   * @see https://on.cypress.io/visit
   */
  interface VisitOptions extends Loggable, Timeoutable, Failable {
    /**
     * The URL to visit. Behaves the same as the `url` argument.
     */
    url: string

    /**
     * The HTTP method to use in the visit. Can be `GET` or `POST`.
     *
     * @default "GET"
     */
    method: 'GET' | 'POST'

    /**
     * An optional body to send along with a `POST` request. If it is a string, it will be passed along unmodified. If it is an object, it will be URL encoded to a string and sent with a `Content-Type: application/x-www-urlencoded` header.
     *
     * @example
     *    cy.visit({
     *      url: 'http://www.example.com/form.html',
     *      method: 'POST',
     *      body: {
     *        "field1": "foo",
     *        "field2": "bar"
     *      }
     *    })
     */
    body: RequestBody

    /**
     * An object that maps HTTP header names to values to be sent along with the request.
     *
     * @example
     *    cy.visit({
     *      url: 'http://www.example.com',
     *      headers: {
     *        'Accept-Language': 'en-US'
     *      }
     *    })
     */
    headers: { [header: string]: string }

    /**
     * Called before your page has loaded all of its resources.
     *
     * @param {AUTWindow} contentWindow the remote page's window object
     */
    onBeforeLoad(win: AUTWindow): void

    /**
     * Called once your page has fired its load event.
     *
     * @param {AUTWindow} contentWindow the remote page's window object
     */
    onLoad(win: AUTWindow): void

    /**
     * Cypress will automatically apply the right authorization headers
     * if you're attempting to visit an application that requires
     * Basic Authentication.
     *
     * @example
     *    cy.visit('https://www.acme.com/', {
     *      auth: {
     *        username: 'wile',
     *        password: 'coyote'
     *      }
     *    })
     */
    auth: Auth

    /**
     * Query parameters to append to the `url` of the request.
     */
    qs: object
  }

  /**
   * Options to change the default behavior of .trigger()
   */
  interface TriggerOptions extends Loggable, Timeoutable, ActionableOptions {
    /**
     * Whether the event bubbles
     *
     * @default true
     */
    bubbles: boolean
    /**
     * Whether the event is cancelable
     *
     * @default true
     */
    cancelable: boolean
    /**
     * The type of the event you want to trigger
     *
     * @default 'Event'
     */
    eventConstructor: string
  }

  /**
   * Options to change the default behavior of .url()
   */
  interface UrlOptions extends Loggable, Timeoutable {
    /**
     * Whether the url is decoded
     *
     * @default false
     */
    decode: boolean
  }

  /** Options to change the default behavior of .readFile */
  interface ReadFileOptions extends Loggable {
    encoding: Encodings
  }

  /** Options to change the default behavior of .writeFile */
  interface WriteFileOptions extends Loggable {
    flag: string
    encoding: Encodings
  }

  // Kind of onerous, but has a nice auto-complete.
  /**
   * @see https://on.cypress.io/should
   *
   * @interface Chainer
   * @template Subject
   */
  interface Chainer<Subject> {
    // chai
    /**
     * Asserts that the target's `type` is equal to the given string type.
     * Types are case insensitive. See the `type-detect` project page for info on the type detection algorithm:
     * https://github.com/chaijs/type-detect.
     * @example
     *    cy.wrap('foo').should('be.a', 'string')
     * @see http://chaijs.com/api/bdd/#method_a
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.a', type: string): Chainable<Subject>
    /**
     * Asserts that the target is a number or a date greater than the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(6).should('be.above', 5)
     * @see http://chaijs.com/api/bdd/#method_above
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.above', value: number | Date): Chainable<Subject>
    /**
     * Asserts that the target's `type` is equal to the given string type.
     * Types are case insensitive. See the `type-detect` project page for info on the type detection algorithm:
     * https://github.com/chaijs/type-detect.
     * @example
     *    cy.wrap({ foo: 'bar' }).should('be.an', 'object')
     * @alias a
     * @see http://chaijs.com/api/bdd/#method_a
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.an', value: string): Chainable<Subject>
    /**
     * Asserts that the target is a number or a `n` date greater than or equal to the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(6).should('be.at.least', 5)
     * @see http://chaijs.com/api/bdd/#method_least
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.at.least', value: number | Date): Chainable<Subject>
    /**
     * Asserts that the target is a number or a `n` date less than or equal to the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(4).should('be.below', 5)
     * @see http://chaijs.com/api/bdd/#method_below
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.below', value: number): Chainable<Subject>
    /**
     * Asserts that the target is an `arguments` object.
     * @example
     *    cy.wrap(arguments).should('be.arguments')
     * @see http://chaijs.com/api/bdd/#method_arguments
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.arguments'): Chainable<Subject>
    /**
     * Asserts that the target is a number that's within a given +/- `delta` range of the given number `expected`. However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(5.1).should('be.approximately', 5, 0.5)
     * @alias closeTo
     * @see http://chaijs.com/api/bdd/#method_closeto
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.approximately', value: number, delta: number): Chainable<Subject>
    /**
     * Asserts that the target is a number that's within a given +/- `delta` range of the given number `expected`. However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(5.1).should('be.closeTo', 5, 0.5)
     * @see http://chaijs.com/api/bdd/#method_closeto
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.closeTo', value: number, delta: number): Chainable<Subject>
    /**
     * When the target is a string or array, .empty asserts that the target's length property is strictly (===) equal to 0
     * @example
     *    cy.wrap([]).should('be.empty')
     *    cy.wrap('').should('be.empty')
     * @see http://chaijs.com/api/bdd/#method_empty
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.empty'): Chainable<Subject>
    /**
     * Asserts that the target is an instance of the given `constructor`.
     * @example
     *    cy.wrap([1, 2]).should('be.instanceOf', Array)
     * @see http://chaijs.com/api/bdd/#method_instanceof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.instanceOf', value: any): Chainable<Subject>
    /**
     * Asserts that the target is strictly (`===`) equal to `false`.
     * @example
     *    cy.wrap(false).should('be.false')
     * @see http://chaijs.com/api/bdd/#method_false
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.false'): Chainable<Subject>
    /**
     * Asserts that the target is a number or a date greater than the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(6).should('be.greaterThan', 5)
     * @alias above
     * @see http://chaijs.com/api/bdd/#method_above
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.greaterThan', value: number): Chainable<Subject>
    /**
     * Asserts that the target is a number or a date greater than the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(6).should('be.gt', 5)
     * @alias above
     * @see http://chaijs.com/api/bdd/#method_above
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.gt', value: number): Chainable<Subject>
    /**
     * Asserts that the target is a number or a `n` date greater than or equal to the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(6).should('be.gte', 5)
     * @alias least
     * @see http://chaijs.com/api/bdd/#method_least
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.gte', value: number): Chainable<Subject>
    /**
     * Asserts that the target is a number or a `n` date less than or equal to the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(4).should('be.lessThan', 5)
     * @alias below
     * @see http://chaijs.com/api/bdd/#method_below
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.lessThan', value: number): Chainable<Subject>
    /**
     * Asserts that the target is a number or a `n` date less than or equal to the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(4).should('be.lt', 5)
     * @alias below
     * @see http://chaijs.com/api/bdd/#method_below
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.lt', value: number): Chainable<Subject>
    /**
     * Asserts that the target is a number or a date less than or equal to the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(4).should('be.lte', 5)
     * @alias most
     * @see http://chaijs.com/api/bdd/#method_most
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.lte', value: number): Chainable<Subject>
    /**
     * Asserts that the target is loosely (`==`) equal to `true`. However, it's often best to assert that the target is strictly (`===`) or deeply equal to its expected value.
     * @example
     *    cy.wrap(1).should('be.ok')
     * @see http://chaijs.com/api/bdd/#method_ok
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.ok'): Chainable<Subject>
    /**
     * Asserts that the target is strictly (`===`) equal to true.
     * @example
     *    cy.wrap(true).should('be.true')
     * @see http://chaijs.com/api/bdd/#method_true
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.true'): Chainable<Subject>
    /**
     * Asserts that the target is strictly (`===`) equal to undefined.
     * @example
     *    cy.wrap(undefined).should('be.undefined')
     * @see http://chaijs.com/api/bdd/#method_undefined
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.undefined'): Chainable<Subject>
    /**
     * Asserts that the target is strictly (`===`) equal to null.
     * @example
     *    cy.wrap(null).should('be.null')
     * @see http://chaijs.com/api/bdd/#method_null
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.null'): Chainable<Subject>
    /**
     * Asserts that the target is strictly (`===`) equal to NaN.
     * @example
     *    cy.wrap(NaN).should('be.NaN')
     * @see http://chaijs.com/api/bdd/#method_null
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.NaN'): Chainable<Subject>
    /**
     * Asserts that the target is a number or a date greater than or equal to the given number or date `start`, and less than or equal to the given number or date `finish` respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(6).should('be.within', 5, 10)
     * @see http://chaijs.com/api/bdd/#method_within
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.within', start: number, end: number): Chainable<Subject>
    (chainer: 'be.within', start: Date, end: Date): Chainable<Subject>
    /**
     * When one argument is provided, `.change` asserts that the given function `subject` returns a different value when it's invoked before the target function compared to when it's invoked afterward.
     * However, it's often best to assert that `subject` is equal to its expected value.
     * @example
     *    let dots = ''
     *    function addDot() { dots += '.' }
     *    function getDots() { return dots }
     *    cy.wrap(addDot).should('change', getDots)
     * @see http://chaijs.com/api/bdd/#method_change
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'change', fn: (...args: any[]) => any): Chainable<Subject>
    /**
     * When two arguments are provided, `.change` asserts that the value of the given object `subject`'s `prop` property is different before invoking the target function compared to afterward.
     * @example
     *    const myObj = { dots: '' }
     *    function addDot() { myObj.dots += '.' }
     *    cy.wrap(addDot).should('change', myObj, 'dots')
     * @see http://chaijs.com/api/bdd/#method_change
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'change', obj: object, prop: string): Chainable<Subject>
    /**
     * When the target is a string, `.include` asserts that the given string val is a substring of the target.
     * @example
     *    cy.wrap('tester').should('contain', 'test')
     * @alias include
     * @see http://chaijs.com/api/bdd/#method_include
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'contain', value: any): Chainable<Subject>
    /**
     * When one argument is provided, `.decrease` asserts that the given function `subject` returns a lesser number when it's invoked after invoking the target function compared to when it's invoked beforehand.
     * `.decrease` also causes all `.by` assertions that follow in the chain to assert how much lesser of a number is returned. It's often best to assert that the return value decreased by the expected amount, rather than asserting it decreased by any amount.
     * @example
     *    let val = 1
     *    function subtractTwo() { val -= 2 }
     *    function getVal() { return val }
     *    cy.wrap(subtractTwo).should('decrease', getVal)
     * @see http://chaijs.com/api/bdd/#method_decrease
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'decrease', fn: (...args: any[]) => any): Chainable<Subject>
    /**
     * When two arguments are provided, `.decrease` asserts that the value of the given object `subject`'s `prop` property is lesser after invoking the target function compared to beforehand.
     * @example
     *    let val = 1
     *    function subtractTwo() { val -= 2 }
     *    function getVal() { return val }
     *    cy.wrap(subtractTwo).should('decrease', getVal)
     * @see http://chaijs.com/api/bdd/#method_decrease
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'decrease', obj: object, prop: string): Chainable<Subject>
    /**
     * Causes all `.equal`, `.include`, `.members`, `.keys`, and `.property` assertions that follow in the chain to use deep equality instead of strict (`===`) equality. See the `deep-eql` project page for info on the deep equality algorithm: https://github.com/chaijs/deep-eql.
     * @example
     *    cy.wrap({ a: 1 }).should('deep.equal', { a: 1 })
     * @see http://chaijs.com/api/bdd/#method_deep
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'deep.equal', value: Subject): Chainable<Subject>
    /**
     * Asserts that the target is not strictly (`===`) equal to either `null` or `undefined`. However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(1).should('exist')
     * @see http://chaijs.com/api/bdd/#method_exist
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'exist'): Chainable<Subject>
    /**
     * Asserts that the target is strictly (`===`) equal to the given `val`.
     * @example
     *    cy.wrap(1).should('eq', 1)
     * @alias equal
     * @see http://chaijs.com/api/bdd/#method_equal
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'eq', value: any): Chainable<Subject>
    /**
     * Asserts that the target is deeply equal to the given `obj`. See the `deep-eql` project page for info on the deep equality algorithm: https://github.com/chaijs/deep-eql.
     * @example
     *    cy.wrap({a: 1}).should('eql', {a: 1}).and('not.equal', {a: 1})
     * @see http://chaijs.com/api/bdd/#method_eql
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'eql', value: any): Chainable<Subject>
    /**
     * Asserts that the target is strictly (`===`) equal to the given `val`.
     * @example
     *    cy.wrap(1).should('equal', 1)
     * @see http://chaijs.com/api/bdd/#method_equal
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'equal', value: any): Chainable<Subject>
    /**
   * Causes all `.key` assertions that follow in the chain to require that the target have all of the given keys. This is the opposite of `.any`, which only requires that the target have at least one of the given keys.
   * @example
   *    cy.wrap({ a: 1, b: 2 }).should('have.all.key', 'a', 'b')
   * @see http://chaijs.com/api/bdd/#method_all
   * @see https://on.cypress.io/assertions
   */
    (chainer: 'have.all.key', ...value: string[]): Chainable<Subject>
    /**
     * Causes all `.key` assertions that follow in the chain to only require that the target have at least one of the given keys. This is the opposite of `.all`, which requires that the target have all of the given keys.
     * @example
     *    cy.wrap({ a: 1, b: 2 }).should('have.any.key', 'a')
     * @see http://chaijs.com/api/bdd/#method_any
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.any.key', ...value: string[]): Chainable<Subject>
    /**
     * Causes all `.keys` assertions that follow in the chain to require that the target have all of the given keys. This is the opposite of `.any`, which only requires that the target have at least one of the given keys.
     * @example
     *    cy.wrap({ a: 1, b: 2 }).should('have.all.keys', 'a', 'b')
     * @see http://chaijs.com/api/bdd/#method_all
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.all.keys' | 'have.keys' | 'have.deep.keys' | 'have.all.deep.keys', ...value: string[]): Chainable<Subject>
    /**
     * Causes all `.keys` assertions that follow in the chain to only require that the target have at least one of the given keys. This is the opposite of `.all`, which requires that the target have all of the given keys.
     * @example
     *    cy.wrap({ a: 1, b: 2 }).should('have.any.keys', 'a')
     * @see http://chaijs.com/api/bdd/#method_any
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.any.keys' | 'include.any.keys', ...value: string[]): Chainable<Subject>
    /**
     * Causes all `.keys` assertions that follow in the chain to require the target to be a superset of the expected set, rather than an identical set.
     * @example
     *    cy.wrap({ a: 1, b: 2 }).should('include.all.keys', 'a', 'b')
     * @see http://chaijs.com/api/bdd/#method_keys
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'include.all.keys', ...value: string[]): Chainable<Subject>
    /**
     * Asserts that the target has a property with the given key `name`. See the `deep-eql` project page for info on the deep equality algorithm: https://github.com/chaijs/deep-eql.
     * @example
     *    cy.wrap({ x: {a: 1 }}).should('have.deep.property', 'x', { a: 1 })
     * @see http://chaijs.com/api/bdd/#method_property
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.deep.property', value: string, obj: object): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is equal to the given number `n`.
     * @example
     *    cy.wrap([1, 2, 3]).should('have.length', 3)
     *    cy.wrap('foo').should('have.length', 3)
     * @alias lengthOf
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.length' | 'have.lengthOf', value: number): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is greater than to the given number `n`.
     * @example
     *    cy.wrap([1, 2, 3]).should('have.length.greaterThan', 2)
     *    cy.wrap('foo').should('have.length.greaterThan', 2)
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.length.greaterThan' | 'have.lengthOf.greaterThan', value: number): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is greater than to the given number `n`.
     * @example
     *    cy.wrap([1, 2, 3]).should('have.length.gt', 2)
     *    cy.wrap('foo').should('have.length.gt', 2)
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.length.gt' | 'have.lengthOf.gt' | 'have.length.above' | 'have.lengthOf.above', value: number): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is greater than or equal to the given number `n`.
     * @example
     *    cy.wrap([1, 2, 3]).should('have.length.gte', 2)
     *    cy.wrap('foo').should('have.length.gte', 2)
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.length.gte' | 'have.lengthOf.gte' | 'have.length.at.least' | 'have.lengthOf.at.least', value: number): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is less than to the given number `n`.
     * @example
     *    cy.wrap([1, 2, 3]).should('have.length.lessThan', 4)
     *    cy.wrap('foo').should('have.length.lessThan', 4)
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.length.lessThan' | 'have.lengthOf.lessThan', value: number): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is less than to the given number `n`.
     * @example
     *    cy.wrap([1, 2, 3]).should('have.length.lt', 4)
     *    cy.wrap('foo').should('have.length.lt', 4)
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.length.lt' | 'have.lengthOf.lt' | 'have.length.below' | 'have.lengthOf.below', value: number): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is less than or equal to the given number `n`.
     * @example
     *    cy.wrap([1, 2, 3]).should('have.length.lte', 4)
     *    cy.wrap('foo').should('have.length.lte', 4)
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.length.lte' | 'have.lengthOf.lte' | 'have.length.at.most' | 'have.lengthOf.at.most', value: number): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is within `start` and `finish`.
     * @example
     *    cy.wrap([1, 2, 3]).should('have.length.within', 1, 5)
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.length.within' | 'have.lengthOf.within', start: number, finish: number): Chainable<Subject>
    /**
     * Asserts that the target array has the same members as the given array `set`.
     * @example
     *    cy.wrap([1, 2, 3]).should('have.members', [2, 1, 3])
     * @see http://chaijs.com/api/bdd/#method_members
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.members' | 'have.deep.members', values: any[]): Chainable<Subject>
    /**
     * Asserts that the target array has the same members as the given array where order matters.
     * @example
     *    cy.wrap([1, 2, 3]).should('have.ordered.members', [1, 2, 3])
     * @see http://chaijs.com/api/bdd/#method_members
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.ordered.members', values: any[]): Chainable<Subject>
    /**
     * Causes all `.property` and `.include` assertions that follow in the chain to ignore inherited properties.
     * @example
     *    Object.prototype.b = 2
     *    cy.wrap({ a: 1 }).should('have.property', 'a').and('not.have.ownProperty', 'b')
     * @see http://chaijs.com/api/bdd/#method_ownproperty
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.ownProperty', property: string): Chainable<Subject>
    /**
     * Asserts that the target has a property with the given key `name`.
     * @example
     *    cy.wrap({ a: 1 }).should('have.property', 'a')
     *    cy.wrap({ a: 1 }).should('have.property', 'a', 1)
     * @see http://chaijs.com/api/bdd/#method_property
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.property' | 'have.nested.property' | 'have.own.property' | 'have.a.property' | 'have.deep.property' | 'have.deep.own.property' | 'have.deep.nested.property', property: string, value?: any): Chainable<Subject>
    /**
     * Asserts that the target has its own property descriptor with the given key name.
     * @example
     *    cy.wrap({a: 1}).should('have.ownPropertyDescriptor', 'a', { value: 1 })
     * @see http://chaijs.com/api/bdd/#method_ownpropertydescriptor
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.ownPropertyDescriptor' | 'haveOwnPropertyDescriptor', name: string, descriptor?: PropertyDescriptor): Chainable<Subject>
    /**
     * Asserts that the target string contains the given substring `str`.
     * @example
     *    cy.wrap('foobar').should('have.string', 'bar')
     * @see http://chaijs.com/api/bdd/#method_string
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.string', match: string | RegExp): Chainable<Subject>
    /**
     * When the target is a string, `.include` asserts that the given string `val` is a substring of the target.
     * @example
     *    cy.wrap('foobar').should('include', 'foo')
     * @see http://chaijs.com/api/bdd/#method_include
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'include' | 'deep.include' | 'nested.include' | 'own.include' | 'deep.own.include' | 'deep.nested.include', value: any): Chainable<Subject>
    /**
     * When the target is a string, `.include` asserts that the given string `val` is a substring of the target.
     * @example
     *    cy.wrap([1, 2, 3]).should('include.members', [1, 2])
     * @see http://chaijs.com/api/bdd/#method_members
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'include.members' | 'include.ordered.members' | 'include.deep.ordered.members', value: any[]): Chainable<Subject>
    /**
     * When one argument is provided, `.increase` asserts that the given function `subject` returns a greater number when it's
     * invoked after invoking the target function compared to when it's invoked beforehand.
     * `.increase` also causes all `.by` assertions that follow in the chain to assert how much greater of a number is returned.
     * It's often best to assert that the return value increased by the expected amount, rather than asserting it increased by any amount.
     *
     * When two arguments are provided, `.increase` asserts that the value of the given object `subject`'s `prop` property is greater after
     * invoking the target function compared to beforehand.
     *
     * @example
     *    let val = 1
     *    function addTwo() { val += 2 }
     *    function getVal() { return val }
     *    cy.wrap(addTwo).should('increase', getVal)
     *
     *    const myObj = { val: 1 }
     *    function addTwo() { myObj.val += 2 }
     *    cy.wrap(addTwo).should('increase', myObj, 'val')
     * @see http://chaijs.com/api/bdd/#method_increase
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'increase', value: object, property?: string): Chainable<Subject>
    /**
     * Asserts that the target matches the given regular expression `re`.
     * @example
     *    cy.wrap('foobar').should('match', /^foo/)
     * @see http://chaijs.com/api/bdd/#method_match
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'match', value: RegExp): Chainable<Subject>
    /**
     * When the target is a non-function object, `.respondTo` asserts that the target has a `method` with the given name method. The method can be own or inherited, and it can be enumerable or non-enumerable.
     * @example
     *    class Cat {
     *      meow() {}
     *    }
     *    cy.wrap(new Cat()).should('respondTo', 'meow')
     * @see http://chaijs.com/api/bdd/#method_respondto
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'respondTo', value: string): Chainable<Subject>
    /**
     * Invokes the given `matcher` function with the target being passed as the first argument, and asserts that the value returned is truthy.
     * @example
     *    cy.wrap(1).should('satisfy', (num) => num > 0)
     * @see http://chaijs.com/api/bdd/#method_satisfy
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'satisfy', fn: (val: any) => boolean): Chainable<Subject>
    /**
     * When no arguments are provided, `.throw` invokes the target function and asserts that an error is thrown.
     * When one argument is provided, and it's a string, `.throw` invokes the target function and asserts that an error is thrown with a message that contains that string.
     * @example
     *    function badFn() { throw new TypeError('Illegal salmon!') }
     *    cy.wrap(badFn).should('throw')
     *    cy.wrap(badFn).should('throw', 'salmon')
     *    cy.wrap(badFn).should('throw', /salmon/)
     * @see http://chaijs.com/api/bdd/#method_throw
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'throw', value?: string | RegExp): Chainable<Subject>
    /**
     * When no arguments are provided, `.throw` invokes the target function and asserts that an error is thrown.
     * When one argument is provided, and it's a string, `.throw` invokes the target function and asserts that an error is thrown with a message that contains that string.
     * @example
     *    function badFn() { throw new TypeError('Illegal salmon!') }
     *    cy.wrap(badFn).should('throw')
     *    cy.wrap(badFn).should('throw', 'salmon')
     *    cy.wrap(badFn).should('throw', /salmon/)
     * @see http://chaijs.com/api/bdd/#method_throw
     * @see https://on.cypress.io/assertions
     */
    // tslint:disable-next-line ban-types
    (chainer: 'throw', error: Error | Function, expected?: string | RegExp): Chainable<Subject>
    /**
     * Asserts that the target is a member of the given array list.
     * @example
     *    cy.wrap(1).should('be.oneOf', [1, 2, 3])
     * @see http://chaijs.com/api/bdd/#method_oneof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.oneOf', list: ReadonlyArray<any>): Chainable<Subject>
    /**
     * Asserts that the target is extensible, which means that new properties can be added to it.
     * @example
     *    cy.wrap({a: 1}).should('be.extensible')
     * @see http://chaijs.com/api/bdd/#method_extensible
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.extensible'): Chainable<Subject>
    /**
     * Asserts that the target is sealed, which means that new properties can't be added to it, and its existing properties can't be reconfigured or deleted.
     * @example
     *    let sealedObject = Object.seal({})
     *    let frozenObject = Object.freeze({})
     *    cy.wrap(sealedObject).should('be.sealed')
     *    cy.wrap(frozenObject).should('be.sealed')
     * @see http://chaijs.com/api/bdd/#method_sealed
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.sealed'): Chainable<Subject>
    /**
     * Asserts that the target is frozen, which means that new properties can't be added to it, and its existing properties can't be reassigned to different values, reconfigured, or deleted.
     * @example
     *    let frozenObject = Object.freeze({})
     *    cy.wrap(frozenObject).should('be.frozen')
     * @see http://chaijs.com/api/bdd/#method_frozen
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.frozen'): Chainable<Subject>
    /**
     * Asserts that the target is a number, and isn't `NaN` or positive/negative `Infinity`.
     * @example
     *    cy.wrap(1).should('be.finite')
     * @see http://chaijs.com/api/bdd/#method_finite
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.finite'): Chainable<Subject>

    // chai.not
    /**
     * Asserts that the target's `type` is not equal to the given string type.
     * Types are case insensitive. See the `type-detect` project page for info on the type detection algorithm:
     * https://github.com/chaijs/type-detect.
     * @example
     *    cy.wrap('foo').should('not.be.a', 'number')
     * @see http://chaijs.com/api/bdd/#method_a
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.a', type: string): Chainable<Subject>
    /**
     * Asserts that the target is a not number or not a date greater than the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(6).should('not.be.above', 10)
     * @see http://chaijs.com/api/bdd/#method_above
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.above', value: number | Date): Chainable<Subject>
    /**
     * Asserts that the target's `type` is not equal to the given string type.
     * Types are case insensitive. See the `type-detect` project page for info on the type detection algorithm:
     * https://github.com/chaijs/type-detect.
     * @example
     *    cy.wrap('foo').should('not.be.an', 'object')
     * @alias a
     * @see http://chaijs.com/api/bdd/#method_a
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.an', value: string): Chainable<Subject>
    /**
     * Asserts that the target is not a number or not a `n` date greater than or equal to the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(6).should('not.be.at.least', 10)
     * @see http://chaijs.com/api/bdd/#method_least
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.at.least', value: number | Date): Chainable<Subject>
    /**
     * Asserts that the target is not a number or not a `n` date less than or equal to the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(4).should('not.be.below', 1)
     * @see http://chaijs.com/api/bdd/#method_below
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.below', value: number): Chainable<Subject>
    /**
     * Asserts that the target is not an `arguments` object.
     * @example
     *    cy.wrap(1).should('not.be.arguments')
     * @see http://chaijs.com/api/bdd/#method_arguments
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.arguments'): Chainable<Subject>
    /**
     * Asserts that the target is a not number that's within a given +/- `delta` range of the given number `expected`. However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(5.1).should('not.be.approximately', 6, 0.5)
     * @alias closeTo
     * @see http://chaijs.com/api/bdd/#method_closeto
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.approximately', value: number, delta: number): Chainable<Subject>
    /**
     * Asserts that the target is not a number that's within a given +/- `delta` range of the given number `expected`. However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(5.1).should('not.be.closeTo', 6, 0.5)
     * @see http://chaijs.com/api/bdd/#method_closeto
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.closeTo', value: number, delta: number): Chainable<Subject>
    /**
     * When the target is a not string or array, .empty asserts that the target's length property is strictly (===) equal to 0
     * @example
     *    cy.wrap([1]).should('not.be.empty')
     *    cy.wrap('foo').should('not.be.empty')
     * @see http://chaijs.com/api/bdd/#method_empty
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.empty'): Chainable<Subject>
    /**
     * Asserts that the target is not an instance of the given `constructor`.
     * @example
     *    cy.wrap([1, 2]).should('not.be.instanceOf', String)
     * @see http://chaijs.com/api/bdd/#method_instanceof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.instanceOf', value: any): Chainable<Subject>
    /**
     * Asserts that the target is not strictly (`===`) equal to `false`.
     * @example
     *    cy.wrap(true).should('not.be.false')
     * @see http://chaijs.com/api/bdd/#method_false
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.false'): Chainable<Subject>
    /**
     * Asserts that the target is a not number or a date greater than the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(6).should('be.greaterThan', 7)
     * @alias above
     * @see http://chaijs.com/api/bdd/#method_above
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.greaterThan', value: number): Chainable<Subject>
    /**
     * Asserts that the target is a not number or a date greater than the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(6).should('not.be.gt', 7)
     * @alias above
     * @see http://chaijs.com/api/bdd/#method_above
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.gt', value: number): Chainable<Subject>
    /**
     * Asserts that the target is a not number or a `n` date greater than or equal to the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(6).should('not.be.gte', 7)
     * @alias least
     * @see http://chaijs.com/api/bdd/#method_least
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.gte', value: number): Chainable<Subject>
    /**
     * Asserts that the target is not a number or a `n` date less than or equal to the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(4).should('not.be.lessThan', 3)
     * @alias below
     * @see http://chaijs.com/api/bdd/#method_below
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.lessThan', value: number): Chainable<Subject>
    /**
     * Asserts that the target is not a number or a `n` date less than or equal to the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(4).should('not.be.lt', 3)
     * @alias below
     * @see http://chaijs.com/api/bdd/#method_below
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.lt', value: number): Chainable<Subject>
    /**
     * Asserts that the target is not a number or a date less than or equal to the given number or date n respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(4).should('not.be.lte', 3)
     * @alias most
     * @see http://chaijs.com/api/bdd/#method_most
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.lte', value: number): Chainable<Subject>
    /**
     * Asserts that the target is not loosely (`==`) equal to `true`. However, it's often best to assert that the target is strictly (`===`) or deeply equal to its expected value.
     * @example
     *    cy.wrap(0).should('not.be.ok')
     * @see http://chaijs.com/api/bdd/#method_ok
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.ok'): Chainable<Subject>
    /**
     * Asserts that the target is not strictly (`===`) equal to true.
     * @example
     *    cy.wrap(false).should('not.be.true')
     * @see http://chaijs.com/api/bdd/#method_true
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.true'): Chainable<Subject>
    /**
     * Asserts that the target is not strictly (`===`) equal to undefined.
     * @example
     *    cy.wrap(true).should('not.be.undefined')
     * @see http://chaijs.com/api/bdd/#method_undefined
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.undefined'): Chainable<Subject>
    /**
     * Asserts that the target is strictly (`===`) equal to null.
     * @example
     *    cy.wrap(null).should('not.be.null')
     * @see http://chaijs.com/api/bdd/#method_null
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.null'): Chainable<Subject>
    /**
     * Asserts that the target is strictly (`===`) equal to NaN.
     * @example
     *    cy.wrap(NaN).should('not.be.NaN')
     * @see http://chaijs.com/api/bdd/#method_nan
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.NaN'): Chainable<Subject>
    /**
     * Asserts that the target is not a number or a date greater than or equal to the given number or date `start`, and less than or equal to the given number or date `finish` respectively.
     * However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(3).should('not.be.within', 5, 10)
     * @see http://chaijs.com/api/bdd/#method_within
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.within', start: number, end: number): Chainable<Subject>
    (chainer: 'not.be.within', start: Date, end: Date): Chainable<Subject>
    /**
     * When one argument is provided, `.change` asserts that the given function `subject` returns a different value when it's invoked before the target function compared to when it's invoked afterward.
     * However, it's often best to assert that `subject` is equal to its expected value.
     * @example
     *    let dots = ''
     *    function addDot() { dots += '.' }
     *    function getDots() { return dots }
     *    cy.wrap(() => {}).should('not.change', getDots)
     * @see http://chaijs.com/api/bdd/#method_change
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.change', fn: (...args: any[]) => any): Chainable<Subject>
    /**
     * When two arguments are provided, `.change` asserts that the value of the given object `subject`'s `prop` property is different before invoking the target function compared to afterward.
     * @example
     *    const myObj = { dots: '' }
     *    function addDot() { myObj.dots += '.' }
     *    cy.wrap(() => {}).should('not.change', myObj, 'dots')
     * @see http://chaijs.com/api/bdd/#method_change
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.change', obj: object, prop: string): Chainable<Subject>
    /**
     * When the target is a string, `.include` asserts that the given string val is a substring of the target.
     * @example
     *    cy.wrap('tester').should('not.contain', 'foo')
     * @alias include
     * @see http://chaijs.com/api/bdd/#method_include
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.contain', value: any): Chainable<Subject>
    /**
     * When one argument is provided, `.decrease` asserts that the given function `subject` does not returns a lesser number when it's invoked after invoking the target function compared to when it's invoked beforehand.
     * `.decrease` also causes all `.by` assertions that follow in the chain to assert how much lesser of a number is returned. It's often best to assert that the return value decreased by the expected amount, rather than asserting it decreased by any amount.
     * @example
     *    let val = 1
     *    function subtractTwo() { val -= 2 }
     *    function getVal() { return val }
     *    cy.wrap(() => {}).should('not.decrease', getVal)
     * @see http://chaijs.com/api/bdd/#method_decrease
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.decrease', fn: (...args: any[]) => any): Chainable<Subject>
    /**
     * When two arguments are provided, `.decrease` asserts that the value of the given object `subject`'s `prop` property is not lesser after invoking the target function compared to beforehand.
     * @example
     *    const myObj = { val: 1 }
     *    function subtractTwo() { myObj.val -= 2 }
     *    cy.wrap(() => {}).should('not.decrease', myObj, 'val')
     * @see http://chaijs.com/api/bdd/#method_decrease
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.decrease', obj: object, prop: string): Chainable<Subject>
    /**
     * Causes all `.equal`, `.include`, `.members`, `.keys`, and `.property` assertions that follow in the chain to not use deep equality instead of strict (`===`) equality. See the `deep-eql` project page for info on the deep equality algorithm: https://github.com/chaijs/deep-eql.
     * @example
     *    cy.wrap({ a: 1 }).should('not.deep.equal', { b: 1 })
     * @see http://chaijs.com/api/bdd/#method_deep
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.deep.equal', value: Subject): Chainable<Subject>
    /**
     * Asserts that the target is not strictly (`===`) equal to either `null` or `undefined`. However, it's often best to assert that the target is equal to its expected value.
     * @example
     *    cy.wrap(null).should('not.exist')
     * @see http://chaijs.com/api/bdd/#method_exist
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.exist'): Chainable<Subject>
    /**
     * Asserts that the target is not strictly (`===`) equal to the given `val`.
     * @example
     *    cy.wrap(1).should('not.eq', 2)
     * @alias equal
     * @see http://chaijs.com/api/bdd/#method_equal
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.eq', value: any): Chainable<Subject>
    /**
     * Asserts that the target is not deeply equal to the given `obj`. See the `deep-eql` project page for info on the deep equality algorithm: https://github.com/chaijs/deep-eql.
     * @example
     *    cy.wrap({a: 1}).should('not.eql', {c: 1}).and('not.equal', {a: 1})
     * @see http://chaijs.com/api/bdd/#method_eql
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.eql', value: any): Chainable<Subject>
    /**
     * Asserts that the target is not strictly (`===`) equal to the given `val`.
     * @example
     *    cy.wrap(1).should('not.equal', 2)
     * @see http://chaijs.com/api/bdd/#method_equal
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.equal', value: any): Chainable<Subject>
    /**
     * Causes all `.keys` assertions that follow in the chain to not require that the target have all of the given keys. This is the opposite of `.any`, which only requires that the target have at least one of the given keys.
     * @example
     *    cy.wrap({ a: 1, b: 2 }).should('not.have.all.keys', 'c', 'd')
     * @see http://chaijs.com/api/bdd/#method_all
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.all.keys' | 'not.have.keys' | 'not.have.deep.keys' | 'not.have.all.deep.keys', ...value: string[]): Chainable<Subject>
    /**
     * Causes all `.keys` assertions that follow in the chain to only require that the target not have at least one of the given keys. This is the opposite of `.all`, which requires that the target have all of the given keys.
     * @example
     *    cy.wrap({ a: 1, b: 2 }).should('not.have.any.keys', 'c')
     * @see http://chaijs.com/api/bdd/#method_any
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.any.keys' | 'not.include.any.keys', ...value: string[]): Chainable<Subject>
    /**
     * Asserts that the target does not have a property with the given key `name`. See the `deep-eql` project page for info on the deep equality algorithm: https://github.com/chaijs/deep-eql.
     * @example
     *    cy.wrap({ x: {a: 1 }}).should('not.have.deep.property', 'y', { a: 1 })
     * @see http://chaijs.com/api/bdd/#method_property
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.deep.property', value: string, obj: object): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is not equal to the given number `n`.
     * @example
     *    cy.wrap([1, 2, 3]).should('not.have.length', 2)
     * cy.wrap('foo').should('not.have.length', 2)
     * @alias lengthOf
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.length' | 'not.have.lengthOf', value: number): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is not greater than to the given number `n`.
     * @example
     *    cy.wrap([1, 2, 3]).should('not.have.length.greaterThan', 4)
     *    cy.wrap('foo').should('not.have.length.greaterThan', 4)
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.length.greaterThan' | 'not.have.lengthOf.greaterThan', value: number): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is not greater than to the given number `n`.
     * @example
     *    cy.wrap([1, 2, 3]).should('not.have.length.gt', 4)
     *    cy.wrap('foo').should('not.have.length.gt', 4)
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.length.gt' | 'not.have.lengthOf.gt' | 'not.have.length.above' | 'not.have.lengthOf.above', value: number): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is not greater than or equal to the given number `n`.
     * @example
     *    cy.wrap([1, 2, 3]).should('not.have.length.gte', 4)
     *    cy.wrap('foo').should('not.have.length.gte', 4)
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.length.gte' | 'not.have.lengthOf.gte' | 'not.have.length.at.least' | 'not.have.lengthOf.at.least', value: number): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is less than to the given number `n`.
     * @example
     *    cy.wrap([1, 2, 3]).should('have.length.lessThan', 2)
     *    cy.wrap('foo').should('have.length.lessThan', 2)
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.length.lessThan' | 'not.have.lengthOf.lessThan', value: number): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is not less than to the given number `n`.
     * @example
     *    cy.wrap([1, 2, 3]).should('not.have.length.lt', 2)
     *    cy.wrap('foo').should('not.have.length.lt', 2)
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.length.lt' | 'not.have.lengthOf.lt' | 'not.have.length.below' | 'not.have.lengthOf.below', value: number): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is not less than or equal to the given number `n`.
     * @example
     *    cy.wrap([1, 2, 3]).should('not.have.length.lte', 2)
     *    cy.wrap('foo').should('not.have.length.lte', 2)
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.length.lte' | 'not.have.lengthOf.lte' | 'not.have.length.at.most' | 'not.have.lengthOf.at.most', value: number): Chainable<Subject>
    /**
     * Asserts that the target's `length` property is within `start` and `finish`.
     * @example
     *    cy.wrap([1, 2, 3]).should('not.have.length.within', 6, 12)
     * @see http://chaijs.com/api/bdd/#method_lengthof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.length.within' | 'not.have.lengthOf.within', start: number, finish: number): Chainable<Subject>
    /**
     * Asserts that the target array does not have the same members as the given array `set`.
     * @example
     *    cy.wrap([1, 2, 3]).should('not.have.members', [4, 5, 6])
     * @see http://chaijs.com/api/bdd/#method_members
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.members' | 'not.have.deep.members', values: any[]): Chainable<Subject>
    /**
     * Asserts that the target array does not have the same members as the given array where order matters.
     * @example
     *    cy.wrap([1, 2, 3]).should('not. have.ordered.members', [4, 5, 6])
     * @see http://chaijs.com/api/bdd/#method_members
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.ordered.members', values: any[]): Chainable<Subject>
    /**
     * Causes all `.property` and `.include` assertions that follow in the chain to ignore inherited properties.
     * @example
     *    Object.prototype.b = 2
     *    cy.wrap({ a: 1 }).should('have.property', 'a').and('not.have.ownProperty', 'b')
     * @see http://chaijs.com/api/bdd/#method_ownproperty
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.ownProperty', property: string): Chainable<Subject>
    /**
     * Asserts that the target has a property with the given key `name`.
     * @example
     *    cy.wrap({ a: 1 }).should('not.have.property', 'b')
     *    cy.wrap({ a: 1 }).should('not.have.property', 'b', 1)
     * @see http://chaijs.com/api/bdd/#method_property
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.property' | 'not.have.nested.property' | 'not.have.own.property' | 'not.have.a.property' | 'not.have.deep.property' | 'not.have.deep.own.property' | 'not.have.deep.nested.property', property: string, value?: any): Chainable<Subject>
    /**
     * Asserts that the target has its own property descriptor with the given key name.
     * @example
     *    cy.wrap({a: 1}).should('not.have.ownPropertyDescriptor', 'a', { value: 2 })
     * @see http://chaijs.com/api/bdd/#method_ownpropertydescriptor
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.ownPropertyDescriptor' | 'not.haveOwnPropertyDescriptor', name: string, descriptor?: PropertyDescriptor): Chainable<Subject>
    /**
     * Asserts that the target string does not contains the given substring `str`.
     * @example
     *    cy.wrap('foobar').should('not.have.string', 'baz')
     * @see http://chaijs.com/api/bdd/#method_string
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.string', match: string | RegExp): Chainable<Subject>
    /**
     * When the target is a string, `.include` asserts that the given string `val` is not a substring of the target.
     * @example
     *    cy.wrap('foobar').should('not.include', 'baz')
     * @see http://chaijs.com/api/bdd/#method_include
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.include' | 'not.deep.include' | 'not.nested.include' | 'not.own.include' | 'not.deep.own.include' | 'not.deep.nested.include', value: any): Chainable<Subject>
    /**
     * When the target is a string, `.include` asserts that the given string `val` is not a substring of the target.
     * @example
     *    cy.wrap([1, 2, 3]).should('not.include.members', [4, 5])
     * @see http://chaijs.com/api/bdd/#method_members
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.include.members' | 'not.include.ordered.members' | 'not.include.deep.ordered.members', value: any[]): Chainable<Subject>
    /**
     * When one argument is provided, `.increase` asserts that the given function `subject` returns a greater number when it's
     * invoked after invoking the target function compared to when it's invoked beforehand.
     * `.increase` also causes all `.by` assertions that follow in the chain to assert how much greater of a number is returned.
     * It's often best to assert that the return value increased by the expected amount, rather than asserting it increased by any amount.
     *
     * When two arguments are provided, `.increase` asserts that the value of the given object `subject`'s `prop` property is greater after
     * invoking the target function compared to beforehand.
     *
     * @example
     *    let val = 1
     *    function addTwo() { val += 2 }
     *    function getVal() { return val }
     *    cy.wrap(() => {}).should('not.increase', getVal)
     *
     *    const myObj = { val: 1 }
     *    function addTwo() { myObj.val += 2 }
     *    cy.wrap(addTwo).should('increase', myObj, 'val')
     * @see http://chaijs.com/api/bdd/#method_increase
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.increase', value: object, property?: string): Chainable<Subject>
    /**
     * Asserts that the target does not match the given regular expression `re`.
     * @example
     *    cy.wrap('foobar').should('not.match', /baz$/)
     * @see http://chaijs.com/api/bdd/#method_match
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.match', value: RegExp): Chainable<Subject>
    /**
     * When the target is a non-function object, `.respondTo` asserts that the target does not have a `method` with the given name method. The method can be own or inherited, and it can be enumerable or non-enumerable.
     * @example
     *    class Cat {
     *      meow() {}
     *    }
     *    cy.wrap(new Cat()).should('not.respondTo', 'bark')
     * @see http://chaijs.com/api/bdd/#method_respondto
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.respondTo', value: string): Chainable<Subject>
    /**
     * Invokes the given `matcher` function with the target being passed as the first argument, and asserts that the value returned is falsy.
     * @example
     *    cy.wrap(1).should('not.satisfy', (num) => num < 0)
     * @see http://chaijs.com/api/bdd/#method_satisfy
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.satisfy', fn: (val: any) => boolean): Chainable<Subject>
    /**
     * When no arguments are provided, `.throw` invokes the target function and asserts that no error is thrown.
     * When one argument is provided, and it's a string, `.throw` invokes the target function and asserts that no error is thrown with a message that contains that string.
     * @example
     *    function badFn() { console.log('Illegal salmon!') }
     *    cy.wrap(badFn).should('not.throw')
     *    cy.wrap(badFn).should('not.throw', 'salmon')
     *    cy.wrap(badFn).should('not.throw', /salmon/)
     * @see http://chaijs.com/api/bdd/#method_throw
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.throw', value?: string | RegExp): Chainable<Subject>
    /**
     * When no arguments are provided, `.throw` invokes the target function and asserts that no error is thrown.
     * When one argument is provided, and it's a string, `.throw` invokes the target function and asserts that no error is thrown with a message that contains that string.
     * @example
     *    function badFn() { console.log('Illegal salmon!') }
     *    cy.wrap(badFn).should('not.throw')
     *    cy.wrap(badFn).should('not.throw', 'salmon')
     *    cy.wrap(badFn).should('not.throw', /salmon/)
     * @see http://chaijs.com/api/bdd/#method_throw
     * @see https://on.cypress.io/assertions
     */
    // tslint:disable-next-line ban-types
    (chainer: 'not.throw', error: Error | Function, expected?: string | RegExp): Chainable<Subject>
    /**
     * Asserts that the target is a member of the given array list.
     * @example
     *    cy.wrap(42).should('not.be.oneOf', [1, 2, 3])
     * @see http://chaijs.com/api/bdd/#method_oneof
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.oneOf', list: ReadonlyArray<any>): Chainable<Subject>
    /**
     * Asserts that the target is extensible, which means that new properties can be added to it.
     * @example
     *    let o = Object.seal({})
     *    cy.wrap(o).should('not.be.extensible')
     * @see http://chaijs.com/api/bdd/#method_extensible
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.extensible'): Chainable<Subject>
    /**
     * Asserts that the target is sealed, which means that new properties can't be added to it, and its existing properties can't be reconfigured or deleted.
     * @example
     *    cy.wrap({a: 1}).should('be.sealed')
     *    cy.wrap({a: 1}).should('be.sealed')
     * @see http://chaijs.com/api/bdd/#method_sealed
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.sealed'): Chainable<Subject>
    /**
     * Asserts that the target is frozen, which means that new properties can't be added to it, and its existing properties can't be reassigned to different values, reconfigured, or deleted.
     * @example
     *    cy.wrap({a: 1}).should('not.be.frozen')
     * @see http://chaijs.com/api/bdd/#method_frozen
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.frozen'): Chainable<Subject>
    /**
     * Asserts that the target is a number, and isn't `NaN` or positive/negative `Infinity`.
     * @example
     *    cy.wrap(NaN).should('not.be.finite')
     *    cy.wrap(Infinity).should('not.be.finite')
     * @see http://chaijs.com/api/bdd/#method_finite
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.finite'): Chainable<Subject>

    // sinon-chai
    /**
     * Assert spy/stub was called the `new` operator.
     * Beware that this is inferred based on the value of the this object and the spy function's prototype, so it may give false positives if you actively return the right kind of object.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledwithnew
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.always.calledWithNew' | 'always.have.been.calledWithNew'): Chainable<Subject>
    /**
     * Assert if spy was always called with matching arguments (and possibly others).
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spyalwayscalledwithmatcharg1-arg2-
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.always.calledWithMatch' | 'always.have.been.calledWithMatch', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy always returned the provided value.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spyalwaysreturnedobj
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'always.returned' | 'have.always.returned', value: any): Chainable<Subject>
    /**
     * `true` if the spy was called at least once
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalled
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.called' | 'have.been.called'): Chainable<Subject>
    /**
     * Assert spy was called after `anotherSpy`
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledafteranotherspy
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.calledAfter' | 'have.been.calledAfter', spy: sinon.SinonSpy): Chainable<Subject>
    /**
     * Assert spy was called before `anotherSpy`
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledbeforeanotherspy
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.calledBefore' | 'have.been.calledBefore', spy: sinon.SinonSpy): Chainable<Subject>
    /**
     * Assert spy was called at least once with `obj` as `this`. `calledOn` also accepts a matcher (see [matchers](http://sinonjs.org/releases/v4.1.3/spies/#matchers)).
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledonobj
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.calledOn' | 'have.been.calledOn', context: any): Chainable<Subject>
    /**
     * Assert spy was called exactly once
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledonce
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.calledOnce' | 'have.been.calledOnce'): Chainable<Subject>
    /**
     * Assert spy was called exactly three times
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledthrice
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.calledThrice' | 'have.been.calledThrice'): Chainable<Subject>
    /**
     * Assert spy was called exactly twice
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledtwice
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.calledTwice' | 'have.been.calledTwice'): Chainable<Subject>
    /**
     * Assert spy was called at least once with the provided arguments and no others.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledwithexactlyarg1-arg2-
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.calledWithExactly' | 'have.been.calledWithExactly', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy was called with matching arguments (and possibly others).
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledwithmatcharg1-arg2-
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.calledWithMatch' | 'have.been.calledWithMatch', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy/stub was called the `new` operator.
     * Beware that this is inferred based on the value of the this object and the spy function's prototype, so it may give false positives if you actively return the right kind of object.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledwithnew
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.calledWithNew' | 'have.been.calledWithNew'): Chainable<Subject>
    /**
     * Assert spy always threw an exception.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spyalwaysthrew
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.always.thrown', value?: Error | typeof Error | string): Chainable<Subject>
    /**
     * Assert the number of calls.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycallcount
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.callCount', value: number): Chainable<Subject>
    /**
     * Assert spy threw an exception at least once.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spythrew
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.thrown', value?: Error | typeof Error | string): Chainable<Subject>
    /**
     * Assert spy returned the provided value at least once. (see [matchers](http://sinonjs.org/releases/v4.1.3/spies/#matchers))
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spyreturnedobj
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'returned' | 'have.returned', value: any): Chainable<Subject>
    /**
     * Assert spy was called before anotherSpy, and no spy calls occurred between spy and anotherSpy.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledimmediatelybeforeanotherspy
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.calledImmediatelyBefore' | 'have.been.calledImmediatelyBefore', anotherSpy: sinon.SinonSpy): Chainable<Subject>
    /**
     * Assert spy was called after anotherSpy, and no spy calls occurred between anotherSpy and spy.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledimmediatelyafteranotherspy
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.calledImmediatelyAfter' | 'have.been.calledImmediatelyAfter', anotherSpy: sinon.SinonSpy): Chainable<Subject>
    /**
     * Assert the spy was always called with obj as this
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spyalwayscalledonobj
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.always.calledOn' | 'always.have.been.calledOn', obj: any): Chainable<Subject>
    /**
     * Assert spy was called at least once with the provided arguments.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledwitharg1-arg2-
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.calledWith' | 'have.been.calledWith', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy was always called with the provided arguments (and possibly others).
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spyalwayscalledwitharg1-arg2-
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.always.calledWith' | 'always.have.been.calledWith', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy was called at exactly once with the provided arguments.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledwitharg1-arg2-
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.calledOnceWith' | 'have.been.calledOnceWith', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy was always called with the exact provided arguments.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spyalwayscalledwithexactlyarg1-arg2-
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.always.calledWithExactly' | 'have.been.calledWithExactly', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy was called at exactly once with the provided arguments.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.calledOnceWithExactly' | 'have.been.calledOnceWithExactly', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy always returned the provided value.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.always.returned', obj: any): Chainable<Subject>

    // sinon-chai.not
    /**
     * Assert spy/stub was not called the `new` operator.
     * Beware that this is inferred based on the value of the this object and the spy function's prototype, so it may give false positives if you actively return the right kind of object.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledwithnew
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.always.calledWithNew' | 'not.always.have.been.calledWithNew'): Chainable<Subject>
    /**
     * Assert if spy was not always called with matching arguments (and possibly others).
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spyalwayscalledwithmatcharg1-arg2-
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.always.calledWithMatch' | 'not.always.have.been.calledWithMatch', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy not always returned the provided value.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spyalwaysreturnedobj
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.always.returned' | 'not.have.always.returned', value: any): Chainable<Subject>
    /**
     * `true` if the spy was not called at least once
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalled
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.called' | 'not.have.been.called'): Chainable<Subject>
    /**
     * Assert spy was not.called after `anotherSpy`
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledafteranotherspy
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.calledAfter' | 'not.have.been.calledAfter', spy: sinon.SinonSpy): Chainable<Subject>
    /**
     * Assert spy was not called before `anotherSpy`
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledbeforeanotherspy
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.calledBefore' | 'not.have.been.calledBefore', spy: sinon.SinonSpy): Chainable<Subject>
    /**
     * Assert spy was not called at least once with `obj` as `this`. `calledOn` also accepts a matcher (see [matchers](http://sinonjs.org/releases/v4.1.3/spies/#matchers)).
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledonobj
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.calledOn' | 'not.have.been.calledOn', context: any): Chainable<Subject>
    /**
     * Assert spy was not called exactly once
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledonce
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.calledOnce' | 'not.have.been.calledOnce'): Chainable<Subject>
    /**
     * Assert spy was not called exactly three times
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledthrice
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.calledThrice' | 'not.have.been.calledThrice'): Chainable<Subject>
    /**
     * Assert spy was not called exactly twice
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledtwice
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.calledTwice' | 'not.have.been.calledTwice'): Chainable<Subject>
    /**
     * Assert spy was not called at least once with the provided arguments and no others.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledwithexactlyarg1-arg2-
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.calledWithExactly' | 'not.have.been.calledWithExactly', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy was not called with matching arguments (and possibly others).
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledwithmatcharg1-arg2-
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.calledWithMatch' | 'not.have.been.calledWithMatch', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy/stub was not called the `new` operator.
     * Beware that this is inferred based on the value of the this object and the spy function's prototype, so it may give false positives if you actively return the right kind of object.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledwithnew
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.calledWithNew' | 'not.have.been.calledWithNew'): Chainable<Subject>
    /**
     * Assert spy did not always throw an exception.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spyalwaysthrew
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.always.thrown', value?: Error | typeof Error | string): Chainable<Subject>
    /**
     * Assert not the number of calls.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycallcount
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.callCount', value: number): Chainable<Subject>
    /**
     * Assert spy did not throw an exception at least once.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spythrew
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.thrown', value?: Error | typeof Error | string): Chainable<Subject>
    /**
     * Assert spy did not return the provided value at least once. (see [matchers](http://sinonjs.org/releases/v4.1.3/spies/#matchers))
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spyreturnedobj
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.returned' | 'not.have.returned', value: any): Chainable<Subject>
    /**
     * Assert spy was called before anotherSpy, and no spy calls occurred between spy and anotherSpy.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledimmediatelybeforeanotherspy
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.calledImmediatelyBefore' | 'not.have.been.calledImmediatelyBefore', anotherSpy: sinon.SinonSpy): Chainable<Subject>
    /**
     * Assert spy was called after anotherSpy, and no spy calls occurred between anotherSpy and spy.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledimmediatelyafteranotherspy
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.calledImmediatelyAfter' | 'not.have.been.calledImmediatelyAfter', anotherSpy: sinon.SinonSpy): Chainable<Subject>
    /**
     * Assert the spy was always called with obj as this
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spyalwayscalledonobj
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.always.calledOn' | 'not.always.have.been.calledOn', obj: any): Chainable<Subject>
    /**
     * Assert spy was called at least once with the provided arguments.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledwitharg1-arg2-
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.calledWith' | 'not.have.been.calledWith', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy was always called with the provided arguments (and possibly others).
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spyalwayscalledwitharg1-arg2-
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.always.calledWith' | 'not.always.have.been.calledWith', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy was called at exactly once with the provided arguments.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spycalledwitharg1-arg2-
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.calledOnceWith' | 'not.have.been.calledOnceWith', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy was always called with the exact provided arguments.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#spyalwayscalledwithexactlyarg1-arg2-
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.always.calledWithExactly' | 'not.have.been.calledWithExactly', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy was called at exactly once with the provided arguments.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.calledOnceWithExactly' | 'not.have.been.calledOnceWithExactly', ...args: any[]): Chainable<Subject>
    /**
     * Assert spy always returned the provided value.
     * @see http://sinonjs.org/releases/v4.1.3/spies/#
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.always.returned', obj: any): Chainable<Subject>

    // jquery-chai
    /**
     * Assert that at least one element of the selection is checked, using `.is(':checked')`.
     * @example
     *    cy.get('#result').should('be.checked')
     * @see http://chaijs.com/plugins/chai-jquery/#checked
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.checked'): Chainable<Subject>
    /**
     * Assert that at least one element of the selection is disabled, using `.is(':disabled')`.
     * @example
     *    cy.get('#result').should('be.disabled')
     * @see http://chaijs.com/plugins/chai-jquery/#disabled
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.disabled'): Chainable<Subject>
    /**
     * Assert that at least one element of the selection is empty, using `.is(':empty')`. If the object asserted against is not a jQuery object, the original implementation will be called.
     * @example
     *    cy.get('#result').should('be.empty')
     * @see http://chaijs.com/plugins/chai-jquery/#empty
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.empty'): Chainable<Subject>
    /**
     * Assert that at least one element of the selection is enabled, using `.is(':enabled')`.
     * @example
     *    cy.get('#result').should('be.enabled')
     * @see http://chaijs.com/plugins/chai-jquery/#enabled
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.enabled'): Chainable<Subject>
    /**
     * Assert that at least one element of the selection is hidden, using `.is(':hidden')`.
     * @example
     *    cy.get('#result').should('be.hidden')
     * @see http://chaijs.com/plugins/chai-jquery/#hidden
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.hidden'): Chainable<Subject>
    /**
     * Assert that at least one element of the selection is selected, using `.is(':selected')`.
     * @example
     *    cy.get('#result').should('be.selected')
     * @see http://chaijs.com/plugins/chai-jquery/#selected
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.selected'): Chainable<Subject>
    /**
     * Assert that at least one element of the selection is visible, using `.is(':visible')`.
     * @example
     *    cy.get('#result').should('be.visible')
     * @see http://chaijs.com/plugins/chai-jquery/#visible
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.visible'): Chainable<Subject>
    /**
     * Assert that the selection contains the given text, using `:contains()`. If the object asserted against is not a jQuery object, or if `contain` is not called as a function, the original implementation will be called.
     * @example
     *    cy.get('#result').should('contain', 'text')
     * @see http://chaijs.com/plugins/chai-jquery/#containtext
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'contain', value: string): Chainable<Subject>
    /**
     * Assert that at least one element of the selection is focused.
     * @example
     *    cy.get('#result').should('have.focus')
     *    cy.get('#result').should('be.focused')
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.focus'): Chainable<Subject>
    /**
     * Assert that at least one element of the selection is focused.
     * @example
     *    cy.get('#result').should('be.focused')
     *    cy.get('#result').should('have.focus')
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'be.focused'): Chainable<Subject>
    /**
     * Assert that the selection is not empty. Note that this overrides the built-in chai assertion. If the object asserted against is not a jQuery object, the original implementation will be called.
     * @example
     *    cy.get('#result').should('exist')
     * @see http://chaijs.com/plugins/chai-jquery/#exist
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'exist'): Chainable<Subject>
    /**
     * Assert that the first element of the selection has the given attribute, using `.attr()`. Optionally, assert a particular value as well. The return value is available for chaining.
     * @example
     *    cy.get('#result').should('have.attr', 'role')
     *    cy.get('#result').should('have.attr', 'role', 'menu')
     * @see http://chaijs.com/plugins/chai-jquery/#attrname-value
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.attr', value: string, match?: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection has the given attribute, using `.attr()`. Optionally, assert a particular value as well. The return value is available for chaining.
     * @example
     *    cy.get('#result').should('have.class', 'success')
     * @see http://chaijs.com/plugins/chai-jquery/#classclassname
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.class', value: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection has the given CSS property, using `.css()`. Optionally, assert a particular value as well. The return value is available for chaining.
     * @example
     *    cy.get('#result').should('have.css', 'display', 'none')
     * @see http://chaijs.com/plugins/chai-jquery/#cssname-value
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.css', value: string, match?: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection has the given data value, using `.data()`. Optionally, assert a particular value as well. The return value is available for chaining.
     * @example
     *    cy.get('#result').should('have.data', 'foo', 'bar')
     * @see http://chaijs.com/plugins/chai-jquery/#dataname-value
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.data', value: string, match?: string): Chainable<Subject>
    /**
     * Assert that the selection contains at least one element which has a descendant matching the given selector, using `.has()`.
     * @example
     *    cy.get('#result').should('have.descendants', 'h1')
     * @see http://chaijs.com/plugins/chai-jquery/#descendantsselector
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.descendants', selector: string): Chainable<Subject>
    /**
     * Assert that the html of the first element of the selection is equal to the given html, using `.html()`.
     * @example
     *    cy.get('#result').should('have.html', '<em>John Doe</em>')
     * @see http://chaijs.com/plugins/chai-jquery/#htmlhtml
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.html', value: string): Chainable<Subject>
    /**
     * Assert that the html of the first element of the selection partially contains the given html, using `.html()`.
     * @example
     *    cy.get('#result').should('contain.html', '<em>John Doe</em>')
     * @see http://chaijs.com/plugins/chai-jquery/#htmlhtml
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'contain.html', value: string): Chainable<Subject>
    /**
     * Assert that the html of the first element of the selection partially contains the given html, using `.html()`.
     * @example
     *    cy.get('#result').should('include.html', '<em>John Doe</em>')
     * @see http://chaijs.com/plugins/chai-jquery/#htmlhtml
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'include.html', value: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection has the given id, using `.attr('id')`.
     * @example
     *    cy.get('#result').should('have.id', 'result')
     * @see http://chaijs.com/plugins/chai-jquery/#idid
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.id', value: string, match?: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection has the given property, using `.prop()`. Optionally, assert a particular value as well. The return value is available for chaining.
     * @example
     *    cy.get('#result').should('have.prop', 'disabled')
     *    cy.get('#result').should('have.prop', 'disabled', false)
     * @see http://chaijs.com/plugins/chai-jquery/#propname-value
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.prop', value: string, match?: any): Chainable<Subject>
    /**
     * Assert that the text of the first element of the selection is equal to the given text, using `.text()`.
     * @example
     *    cy.get('#result').should('have.text', 'John Doe')
     * @see http://chaijs.com/plugins/chai-jquery/#texttext
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.text', value: string): Chainable<Subject>
    /**
     * Assert that the text of the first element of the selection partially contains the given text, using `.text()`.
     * @example
     *    cy.get('#result').should('contain.text', 'John Doe')
     * @see http://chaijs.com/plugins/chai-jquery/#texttext
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'contain.text', value: string): Chainable<Subject>
    /**
     * Assert that the text of the first element of the selection partially contains the given text, using `.text()`.
     * @example
     *    cy.get('#result').should('include.text', 'John Doe')
     * @see http://chaijs.com/plugins/chai-jquery/#texttext
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'include.text', value: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection has the given value, using `.val()`.
     * @example
     *    cy.get('textarea').should('have.value', 'foo bar baz')
     * @see http://chaijs.com/plugins/chai-jquery/#valuevalue
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'have.value', value: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection partially contains the given value, using `.val()`.
     * @example
     *    cy.get('textarea').should('contain.value', 'foo bar baz')
     * @see http://chaijs.com/plugins/chai-jquery/#valuevalue
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'contain.value', value: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection partially contains the given value, using `.val()`.
     * @example
     *    cy.get('textarea').should('include.value', 'foo bar baz')
     * @see http://chaijs.com/plugins/chai-jquery/#valuevalue
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'include.value', value: string): Chainable<Subject>
    /**
     * Assert that the selection matches a given selector, using `.is()`. Note that this overrides the built-in chai assertion. If the object asserted against is not a jQuery object, the original implementation will be called.
     * @example
     *    cy.get('#result').should('match', ':empty')
     * @see http://chaijs.com/plugins/chai-jquery/#matchselector
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'match', value: string): Chainable<Subject>

    // jquery-chai.not
    /**
     * Assert that at least one element of the selection is not checked, using `.is(':checked')`.
     * @example
     *    cy.get('#result').should('not.be.checked')
     * @see http://chaijs.com/plugins/chai-jquery/#checked
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.checked'): Chainable<Subject>
    /**
     * Assert that at least one element of the selection is not disabled, using `.is(':disabled')`.
     * @example
     *    cy.get('#result').should('not.be.disabled')
     * @see http://chaijs.com/plugins/chai-jquery/#disabled
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.disabled'): Chainable<Subject>
    /**
     * Assert that at least one element of the selection is not empty, using `.is(':empty')`. If the object asserted against is not a jQuery object, the original implementation will be called.
     * @example
     *    cy.get('#result').should('not.be.empty')
     * @see http://chaijs.com/plugins/chai-jquery/#empty
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.empty'): Chainable<Subject>
    /**
     * Assert that at least one element of the selection is not enabled, using `.is(':enabled')`.
     * @example
     *    cy.get('#result').should('not.be.enabled')
     * @see http://chaijs.com/plugins/chai-jquery/#enabled
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.enabled'): Chainable<Subject>
    /**
     * Assert that at least one element of the selection is not hidden, using `.is(':hidden')`.
     * @example
     *    cy.get('#result').should('not.be.hidden')
     * @see http://chaijs.com/plugins/chai-jquery/#hidden
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.hidden'): Chainable<Subject>
    /**
     * Assert that at least one element of the selection is not selected, using `.is(':selected')`.
     * @example
     *    cy.get('#result').should('not.be.selected')
     * @see http://chaijs.com/plugins/chai-jquery/#selected
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.selected'): Chainable<Subject>
    /**
     * Assert that at least one element of the selection is not visible, using `.is(':visible')`.
     * @example
     *    cy.get('#result').should('not.be.visible')
     * @see http://chaijs.com/plugins/chai-jquery/#visible
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.visible'): Chainable<Subject>
    /**
     * Assert that no element of the selection is focused.
     * @example
     *    cy.get('#result').should('not.have.focus')
     *    cy.get('#result').should('not.be.focused')
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.focus'): Chainable<Subject>
    /**
     * Assert that no element of the selection is focused.
     * @example
     *    cy.get('#result').should('not.be.focused')
     *    cy.get('#result').should('not.have.focus')
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.be.focused'): Chainable<Subject>
    /**
     * Assert that the selection does not contain the given text, using `:contains()`. If the object asserted against is not a jQuery object, or if `contain` is not called as a function, the original implementation will be called.
     * @example
     *    cy.get('#result').should('not.contain', 'text')
     * @see http://chaijs.com/plugins/chai-jquery/#containtext
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.contain', value: string): Chainable<Subject>
    /**
     * Assert that the selection is empty. Note that this overrides the built-in chai assertion. If the object asserted against is not a jQuery object, the original implementation will be called.
     * @example
     *    cy.get('#result').should('not.exist')
     * @see http://chaijs.com/plugins/chai-jquery/#exist
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.exist'): Chainable<Subject>
    /**
     * Assert that the first element of the selection does not have the given attribute, using `.attr()`. Optionally, assert a particular value as well. The return value is available for chaining.
     * @example
     *    cy.get('#result').should('not.have.attr', 'role')
     *    cy.get('#result').should('not.have.attr', 'role', 'menu')
     * @see http://chaijs.com/plugins/chai-jquery/#attrname-value
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.attr', value: string, match?: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection does not have the given attribute, using `.attr()`. Optionally, assert a particular value as well. The return value is available for chaining.
     * @example
     *    cy.get('#result').should('not.have.class', 'success')
     * @see http://chaijs.com/plugins/chai-jquery/#classclassname
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.class', value: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection does not have the given CSS property, using `.css()`. Optionally, assert a particular value as well. The return value is available for chaining.
     * @example
     *    cy.get('#result').should('not.have.css', 'display', 'none')
     * @see http://chaijs.com/plugins/chai-jquery/#cssname-value
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.css', value: string, match?: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection does not have the given data value, using `.data()`. Optionally, assert a particular value as well. The return value is available for chaining.
     * @example
     *    cy.get('#result').should('not.have.data', 'foo', 'bar')
     * @see http://chaijs.com/plugins/chai-jquery/#dataname-value
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.data', value: string, match?: string): Chainable<Subject>
    /**
     * Assert that the selection does not contain at least one element which has a descendant matching the given selector, using `.has()`.
     * @example
     *    cy.get('#result').should('not.have.descendants', 'h1')
     * @see http://chaijs.com/plugins/chai-jquery/#descendantsselector
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.descendants', selector: string): Chainable<Subject>
    /**
     * Assert that the html of the first element of the selection is not equal to the given html, using `.html()`.
     * @example
     *    cy.get('#result').should('not.have.html', '<em>John Doe</em>')
     * @see http://chaijs.com/plugins/chai-jquery/#htmlhtml
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.html', value: string): Chainable<Subject>
    /**
     * Assert that the html of the first element of the selection does not contain the given html, using `.html()`.
     * @example
     *    cy.get('#result').should('not.contain.html', '<em>John Doe</em>')
     * @see http://chaijs.com/plugins/chai-jquery/#htmlhtml
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.contain.html', value: string): Chainable<Subject>
    /**
     * Assert that the html of the first element of the selection does not contain the given html, using `.html()`.
     * @example
     *    cy.get('#result').should('not.include.html', '<em>John Doe</em>')
     * @see http://chaijs.com/plugins/chai-jquery/#htmlhtml
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.include.html', value: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection does not have the given id, using `.attr('id')`.
     * @example
     *    cy.get('#result').should('not.have.id', 'result')
     * @see http://chaijs.com/plugins/chai-jquery/#idid
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.id', value: string, match?: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection does not have the given property, using `.prop()`. Optionally, assert a particular value as well. The return value is available for chaining.
     * @example
     *    cy.get('#result').should('not.have.prop', 'disabled')
     *    cy.get('#result').should('not.have.prop', 'disabled', false)
     * @see http://chaijs.com/plugins/chai-jquery/#propname-value
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.prop', value: string, match?: any): Chainable<Subject>
    /**
     * Assert that the text of the first element of the selection is not equal to the given text, using `.text()`.
     * @example
     *    cy.get('#result').should('not.have.text', 'John Doe')
     * @see http://chaijs.com/plugins/chai-jquery/#texttext
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.text', value: string): Chainable<Subject>
    /**
     * Assert that the text of the first element of the selection does not contain the given text, using `.text()`.
     * @example
     *    cy.get('#result').should('not.contain.text', 'John Doe')
     * @see http://chaijs.com/plugins/chai-jquery/#texttext
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.contain.text', value: string): Chainable<Subject>
    /**
     * Assert that the text of the first element of the selection does not contain the given text, using `.text()`.
     * @example
     *    cy.get('#result').should('not.include.text', 'John Doe')
     * @see http://chaijs.com/plugins/chai-jquery/#texttext
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.include.text', value: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection does not have the given value, using `.val()`.
     * @example
     *    cy.get('textarea').should('not.have.value', 'foo bar baz')
     * @see http://chaijs.com/plugins/chai-jquery/#valuevalue
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.have.value', value: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection does not contain the given value, using `.val()`.
     * @example
     *    cy.get('textarea').should('not.contain.value', 'foo bar baz')
     * @see http://chaijs.com/plugins/chai-jquery/#valuevalue
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.contain.value', value: string): Chainable<Subject>
    /**
     * Assert that the first element of the selection does not contain the given value, using `.val()`.
     * @example
     *    cy.get('textarea').should('not.include.value', 'foo bar baz')
     * @see http://chaijs.com/plugins/chai-jquery/#valuevalue
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.include.value', value: string): Chainable<Subject>
    /**
     * Assert that the selection does not match a given selector, using `.is()`. Note that this overrides the built-in chai assertion. If the object asserted against is not a jQuery object, the original implementation will be called.
     * @example
     *    cy.get('#result').should('not.match', ':empty')
     * @see http://chaijs.com/plugins/chai-jquery/#matchselector
     * @see https://on.cypress.io/assertions
     */
    (chainer: 'not.match', value: string): Chainable<Subject>

    // fallback
    /**
     * Create an assertion. Assertions are automatically retried until they pass or time out.
     * Ctrl+Space will invoke auto-complete in most editors.
     * @see https://on.cypress.io/should
     */
    (chainers: string, value?: any): Chainable<Subject>
    (chainers: string, value: any, match: any): Chainable<Subject>

    /**
     * Create an assertion. Assertions are automatically retried until they pass or time out.
     * Passing a function to `.should()` enables you to make multiple assertions on the yielded subject. This also gives you the opportunity to massage what you'd like to assert on.
     * Just be sure _not_ to include any code that has side effects in your callback function. The callback function will be retried over and over again until no assertions within it throw.
     * @example
     *    cy
     *      .get('p')
     *      .should(($p) => {
     *        // should have found 3 elements
     *        expect($p).to.have.length(3)
     *
     *        // make sure the first contains some text content
     *        expect($p.first()).to.contain('Hello World')
     *
     *        // use jquery's map to grab all of their classes
     *        // jquery's map returns a new jquery object
     *        const classes = $p.map((i, el) => {
     *          return Cypress.$(el).attr('class')
     *        })
     *
     *        // call classes.get() to make this a plain array
     *        expect(classes.get()).to.deep.eq([
     *          'text-primary',
     *          'text-danger',
     *          'text-default'
     *        ])
     *      })
     * @see https://on.cypress.io/should
     */
    (fn: (currentSubject: Subject) => void): Chainable<Subject>
  }

  interface AfterBrowserLaunchDetails {
    webSocketDebuggerUrl: string
  }

  interface BeforeBrowserLaunchOptions {
    extensions: string[]
    preferences: { [key: string]: any }
    args: string[]
    env: { [key: string]: any }
  }

  interface Dimensions {
    width: number
    height: number
  }

  interface ScreenshotDetails {
    size: number
    takenAt: string
    duration: number
    dimensions: Dimensions
    multipart: boolean
    pixelRatio: number
    name: string
    specName: string
    testFailure: boolean
    path: string
    scaled: boolean
    blackout: string[]
  }

  interface AfterScreenshotReturnObject {
    path?: string
    size?: number
    dimensions?: Dimensions
  }

  interface FileObject extends NodeEventEmitter {
    filePath: string
    outputPath: string
    shouldWatch: boolean
  }

  /**
   * Individual task callback. Receives a single argument and _should_ return
   * anything but `undefined` or a promise that resolves anything but `undefined`
   * TODO: find a way to express "anything but undefined" in TypeScript
   */
  type Task = (value: any) => any

  interface Tasks {
    [key: string]: Task
  }

  interface SystemDetails {
    osName: string
    osVersion: string
  }

  interface BeforeRunDetails {
    browser?: Browser
    config: ConfigOptions
    cypressVersion: string
    group?: string
    parallel?: boolean
    runUrl?: string
    specs?: Spec[]
    specPattern?: string[]
    system: SystemDetails
    tag?: string
    autoCancelAfterFailures?: number | false
  }

  interface DevServerConfig {
    specs: Spec[]
    cypressConfig: PluginConfigOptions
    devServerEvents: NodeJS.EventEmitter
  }

  interface ResolvedDevServerConfig {
    port: number
    close: (done?: (err?: Error) => any) => void
  }

  interface PluginEvents {
    (action: 'after:browser:launch', fn: (browser: Browser, browserLaunchDetails: AfterBrowserLaunchDetails) => void | Promise<void>): void
    (action: 'after:run', fn: (results: CypressCommandLine.CypressRunResult | CypressCommandLine.CypressFailedRunResult) => void | Promise<void>): void
    (action: 'after:screenshot', fn: (details: ScreenshotDetails) => void | AfterScreenshotReturnObject | Promise<AfterScreenshotReturnObject>): void
    (action: 'after:spec', fn: (spec: Spec, results: CypressCommandLine.RunResult) => void | Promise<void>): void
    (action: 'before:run', fn: (runDetails: BeforeRunDetails) => void | Promise<void>): void
    (action: 'before:spec', fn: (spec: Spec) => void | Promise<void>): void
    (action: 'before:browser:launch', fn: (browser: Browser, afterBrowserLaunchOptions: BeforeBrowserLaunchOptions) => void | Promise<void> | BeforeBrowserLaunchOptions | Promise<BeforeBrowserLaunchOptions>): void
    (action: 'file:preprocessor', fn: (file: FileObject) => string | Promise<string>): void
    (action: 'dev-server:start', fn: (file: DevServerConfig) => Promise<ResolvedDevServerConfig>): void
    (action: 'task', tasks: Tasks): void
  }

  interface CodeFrame {
    frame: string
    language: string
    line: number
    column: number
    absoluteFile: string
    originalFile: string
    relativeFile: string
  }

  interface CypressError extends Error {
    docsUrl?: string
    codeFrame?: CodeFrame
  }

  // for just a few events like "window:alert" it makes sense to allow passing cy.stub() or
  // a user callback function. Others probably only need a callback function.

  /**
   * These events come from the application currently under test (your application).
   * These are the most useful events for you to listen to.
   * @see https://on.cypress.io/catalog-of-events#App-Events
   */
  interface Actions {
    /**
     * Fires when an uncaught exception or unhandled rejection occurs in your application. If it's an unhandled rejection, the rejected promise will be the 3rd argument.
     * Cypress will fail the test when this fires.
     * Return `false` from this event and Cypress will not fail the test. Also useful for debugging purposes because the actual `error` instance is provided to you.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     * @example
    ```
      // likely want to do this in a support file
      // so it's applied to all spec files
      // cypress/support/{e2e|component}.js

      Cypress.on('uncaught:exception', (err, runnable) => {
        // returning false here prevents Cypress from
        // failing the test
        return false
      })
      // stub "window.alert" in a single test
      it('shows alert', () => {
        const stub = cy.stub()
        cy.on('window:alert', stub)
        // trigger application code that calls alert(...)
        .then(() => {
          expect(stub).to.have.been.calledOnce
        })
      })
    ```
     */
    (action: 'uncaught:exception', fn: (error: Error, runnable: Mocha.Runnable, promise?: Promise<any>) => false | void): Cypress
    /**
     * Fires when your app calls the global `window.confirm()` method.
     * Cypress will auto accept confirmations. Return `false` from this event and the confirmation will be canceled.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     * @example
    ```
    cy.on('window:confirm', (str) => {
      console.log(str)
      return false // simulate "Cancel"
    })
    ```
     */
    (action: 'window:confirm', fn: ((text: string) => false | void) | SinonSpyAgent<sinon.SinonSpy> | SinonSpyAgent<sinon.SinonStub>): Cypress
    /**
     * Fires when your app calls the global `window.alert()` method.
     * Cypress will auto accept alerts. You cannot change this behavior.
     * @example
    ```
    const stub = cy.stub()
    cy.on('window:alert', stub)
    // assume the button calls window.alert()
    cy.get('.my-button')
      .click()
      .then(() => {
        expect(stub).to.have.been.calledOnce
      })
    ```
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'window:alert', fn: ((text: string) => void) | SinonSpyAgent<sinon.SinonSpy> | SinonSpyAgent<sinon.SinonStub>): Cypress
    /**
     * Fires as the page begins to load, but before any of your applications JavaScript has executed.
     * This fires at the exact same time as `cy.visit()` `onBeforeLoad` callback.
     * Useful to modify the window on a page transition.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'window:before:load', fn: (win: AUTWindow) => void): Cypress
    /**
     * Fires after all your resources have finished loading after a page transition.
     * This fires at the exact same time as a `cy.visit()` `onLoad` callback.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'window:load', fn: (win: AUTWindow) => void): Cypress
    /**
     * Fires when your application is about to navigate away.
     * The real event object is provided to you.
     * Your app may have set a `returnValue` on the event, which is useful to assert on.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'window:before:unload', fn: (event: BeforeUnloadEvent) => void): Cypress
    /**
     * Fires when your application is has unloaded and is navigating away.
     * The real event object is provided to you. This event is not cancelable.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'window:unload', fn: (event: Event) => void): Cypress
    /**
     * Fires whenever Cypress detects that your application's URL has changed.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'url:changed', fn: (url: string) => void): Cypress
    /**
     * Fires when the test has failed. It is technically possible to prevent the test
     * from actually failing by binding to this event and invoking an async `done` callback.
     * However this is **strongly discouraged**. Tests should never legitimately fail.
     *  This event exists because it's extremely useful for debugging purposes.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'fail', fn: (error: CypressError, mocha: Mocha.Runnable) => void): Cypress
    /**
     * Fires whenever the viewport changes via a `cy.viewport()` or naturally when
     * Cypress resets the viewport to the default between tests. Useful for debugging purposes.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'viewport:changed', fn: (viewport: Viewport) => void): Cypress
    /**
     * Fires whenever **Cypress** is scrolling your application.
     * This event is fired when Cypress is {% url 'waiting for and calculating
     * actionability' interacting-with-elements %}. It will scroll to 'uncover'
     * elements currently being covered. This event is extremely useful to debug why
     * Cypress may think an element is not interactive.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'scrolled', fn: ($el: JQuery) => void): Cypress
    /**
     * Fires when a cy command is first invoked and enqueued to be run later.
     * Useful for debugging purposes if you're confused about the order in which commands will execute.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'command:enqueued', fn: (command: EnqueuedCommandAttributes) => void): Cypress
    /**
     * Fires when cy begins actually running and executing your command.
     * Useful for debugging and understanding how the command queue is async.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'command:start', fn: (command: CommandQueue) => void): Cypress
    /**
     * Fires when cy finishes running and executing your command.
     * Useful for debugging and understanding how commands are handled.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'command:end', fn: (command: CommandQueue) => void): Cypress
    /**
     * Fires when a command is skipped, namely the `should` command.
     * Useful for debugging and understanding how commands are handled.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'skipped:command:end', fn: (command: CommandQueue) => void): Cypress
    /**
     * Fires whenever a command begins its retrying routines.
     * This is called on the trailing edge after Cypress has internally
     * waited for the retry interval. Useful to understand **why** a command is retrying,
     * and generally includes the actual error causing the retry to happen.
     * When commands fail the final error is the one that actually bubbles up to fail the test.
     * This event is essentially to debug why Cypress is failing.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'command:retry', fn: (command: CommandQueue) => void): Cypress
    /**
     * Fires whenever a command emits this event so it can be displayed in the Command Log.
     * Useful to see how internal cypress commands utilize the {% url 'Cypress.log()' cypress-log %} API.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'log:added', fn: (attributes: ObjectLike, log: any) => void): Cypress
    /**
     * Fires whenever a command's attributes changes.
     * This event is debounced to prevent it from firing too quickly and too often.
     * Useful to see how internal cypress commands utilize the {% url 'Cypress.log()' cypress-log %} API.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'log:changed', fn: (attributes: ObjectLike, log: any) => void): Cypress
    /**
     * Fires before the test and all **before** and **beforeEach** hooks run.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'test:before:run', fn: (attributes: ObjectLike, test: Mocha.Test) => void): Cypress
    /**
     * Fires before the test and all **before** and **beforeEach** hooks run.
     * If a `Promise` is returned, it will be awaited before proceeding.
     */
    (action: 'test:before:run:async', fn: (attributes: ObjectLike, test: Mocha.Test) => void | Promise<any>): Cypress
    /**
     * Fires after the test and all **afterEach** and **after** hooks run.
     * @see https://on.cypress.io/catalog-of-events#App-Events
     */
    (action: 'test:after:run', fn: (attributes: ObjectLike, test: Mocha.Test) => void): Cypress
  }

  // $CommandQueue from `command_queue.coffee` - a lot to type. Might be more useful if it was written in TS
  interface CommandQueue extends ObjectLike {
    logs(filters: any): any
    add(obj: any): any
    get(): any
    get<K extends keyof CommandQueue>(key: string): CommandQueue[K]
    toJSON(): string[]
    create(): CommandQueue
  }

  /**
   * The clock starts at the unix epoch (timestamp of 0). This means that when you instantiate new Date in your application, it will have a time of January 1st, 1970.
   */
  interface Clock {
    /**
     * Move the clock the specified number of `milliseconds`.
     * Any timers within the affected range of time will be called.
     * @param time Number in ms to advance the clock
     * @see https://on.cypress.io/tick
     */
    tick(time: number): void
    /**
     * Restore all overridden native functions.
     * This is automatically called between tests, so should not generally be needed.
     * @see https://on.cypress.io/clock
     * @example
     *   cy.clock()
     *   cy.visit('/')
     *   ...
     *   cy.clock().then(clock => {
     *     clock.restore()
     *   })
     *   // or use this shortcut
     *   cy.clock().invoke('restore')
     */
    restore(): void
    /**
     * Change the time without invoking any timers.
     *
     * Default value with no argument or undefined is 0.
     *
     * This can be useful if you need to change the time by an hour
     * while there is a setInterval registered that may otherwise run thousands
     * of times.
     * @see https://on.cypress.io/clock
     * @example
     *   cy.clock()
     *   cy.visit('/')
     *   ...
     *   cy.clock().then(clock => {
     *     clock.setSystemTime(60 * 60 * 1000)
     *   })
     *   // or use this shortcut
     *   cy.clock().invoke('setSystemTime', 60 * 60 * 1000)
     */
    setSystemTime(now?: number | Date): void
  }

  interface Cookie {
    name: string
    value: string
    path: string
    domain: string
    hostOnly?: boolean
    httpOnly: boolean
    secure: boolean
    expiry?: number
    sameSite?: SameSiteStatus
  }

  interface EnqueuedCommandAttributes {
    id: string
    name: string
    args: any[]
    type: string
    chainerId: string
    injected: boolean
    userInvocationStack?: string
    query?: boolean
    fn(...args: any[]): any
  }

  interface Command {
    get<K extends keyof EnqueuedCommandAttributes>(attr: K): EnqueuedCommandAttributes[K]
    get(): EnqueuedCommandAttributes
    set<K extends keyof EnqueuedCommandAttributes>(key: K, value: EnqueuedCommandAttributes[K]): Log
    set(options: Partial<EnqueuedCommandAttributes>): Log
  }

  interface Exec {
    code: number
    stdout: string
    stderr: string
  }

  type TypedArray =
    | Int8Array
    | Uint8Array
    | Uint8ClampedArray
    | Int16Array
    | Uint16Array
    | Int32Array
    | Uint32Array
    | Float32Array
    | Float64Array

  type FileReference = string | BufferType | FileReferenceObject | TypedArray
  interface FileReferenceObject {
    /*
     * Buffers will be used as-is, while strings will be interpreted as an alias or a file path.
     * All other types will have `Buffer.from(JSON.stringify())` applied.
     */
    contents: any
    fileName?: string
    mimeType?: string
    lastModified?: number
  }

  interface LogAttrs {
    url: string
    consoleProps: ObjectLike
  }

  interface Log {
    id: string
    end(): Log
    error(error: Error): Log
    finish(): void
    get<K extends keyof LogConfig>(attr: K): LogConfig[K]
    get(): LogConfig
    set<K extends keyof LogConfig>(key: K, value: LogConfig[K]): Log
    set(options: Partial<LogConfig>): Log
    snapshot(name?: string, options?: { at?: number, next: string }): Log
  }

  interface LogConfig extends Timeoutable {
    /** Unique id for the log, in the form of '<origin>-<number>' */
    id: string
    /** The JQuery element for the command. This will highlight the command in the main window when debugging */
    $el: JQuery
    /** The scope of the log entry. If child, will appear nested below parents, prefixed with '-' */
    type: 'parent' | 'child'
    /** Allows the name of the command to be overwritten */
    name: string
    /** Override *name* for display purposes only */
    displayName: string
    /** additional information to include in the log */
    message: any
    /** Set to false if you want to control the finishing of the command in the log yourself */
    autoEnd: boolean
    /** Set to true to immediately finish the log  */
    end: boolean
    /** Return an object that will be printed in the dev tools console */
    consoleProps(): ObjectLike
  }

  interface Response<T> {
    allRequestResponses: any[]
    body: T
    duration: number
    headers: { [key: string]: string | string[] }
    isOkStatusCode: boolean
    redirects?: string[]
    redirectedToUrl?: string
    requestHeaders: { [key: string]: string }
    status: number
    statusText: string
  }

  interface Server extends RouteOptions {
    enable: boolean
    ignore: (xhr: any) => boolean
  }

  interface Viewport {
    viewportWidth: number
    viewportHeight: number
  }

  type Encodings = 'ascii' | 'base64' | 'binary' | 'hex' | 'latin1' | 'utf8' | 'utf-8' | 'ucs2' | 'ucs-2' | 'utf16le' | 'utf-16le' | null
  type PositionType = 'topLeft' | 'top' | 'topRight' | 'left' | 'center' | 'right' | 'bottomLeft' | 'bottom' | 'bottomRight'
  type ViewportPreset = 'macbook-16' | 'macbook-15' | 'macbook-13' | 'macbook-11' | 'ipad-2' | 'ipad-mini' | 'iphone-xr' | 'iphone-x' | 'iphone-6+' | 'iphone-se2' | 'iphone-8' | 'iphone-7' | 'iphone-6' | 'iphone-5' | 'iphone-4' | 'iphone-3' | 'samsung-s10' | 'samsung-note9'
  interface Offset {
    top: number
    left: number
  }

  // Diff taken from https://github.com/Microsoft/TypeScript/issues/12215#issuecomment-311923766
  type Diff<T extends string, U extends string> = ({ [P in T]: P } & { [P in U]: never } & { [x: string]: never })[T]
  type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>

  /**
   * Public interface for the global "cy" object. If you want to add
   * a custom property to this object, you should extend this interface.
   * @see https://on.cypress.io/typescript#Types-for-custom-commands
   *
  ```
  // in your TS file
  declare namespace Cypress {
    interface cy {
      // declare additional properties on "cy" object, like
      // label: string
    }
    interface Chainable {
      // declare additional custom commands as methods, like
      // login(username: string, password: string)
    }
  }
  ```
   */
  interface cy extends Chainable<undefined> { }
}

declare namespace Mocha {
  interface TestFunction {
    /**
     * Describe a specification or test-case with the given `title`, TestOptions, and callback `fn` acting
     * as a thunk.
     */
    (title: string, config: Cypress.TestConfigOverrides, fn?: Func): Test

    /**
     * Describe a specification or test-case with the given `title`, TestOptions, and callback `fn` acting
     * as a thunk.
     */
    (title: string, config: Cypress.TestConfigOverrides, fn?: AsyncFunc): Test
  }
  interface ExclusiveTestFunction {
    /**
     * Describe a specification or test-case with the given `title`, TestOptions, and callback `fn` acting
     * as a thunk.
     */
    (title: string, config: Cypress.TestConfigOverrides, fn?: Func): Test

    /**
     * Describe a specification or test-case with the given `title`, TestOptions, and callback `fn` acting
     * as a thunk.
     */
    (title: string, config: Cypress.TestConfigOverrides, fn?: AsyncFunc): Test
  }
  interface PendingTestFunction {
    /**
     * Describe a specification or test-case with the given `title`, TestOptions, and callback `fn` acting
     * as a thunk.
     */
    (title: string, config: Cypress.TestConfigOverrides, fn?: Func): Test

    /**
     * Describe a specification or test-case with the given `title`, TestOptions, and callback `fn` acting
     * as a thunk.
     */
    (title: string, config: Cypress.TestConfigOverrides, fn?: AsyncFunc): Test
  }

  interface SuiteFunction {
    /**
     * Describe a "suite" with the given `title`, TestOptions, and callback `fn` containing
     * nested suites.
     */
    (title: string, config: Cypress.SuiteConfigOverrides, fn: (this: Suite) => void): Suite
  }

  interface ExclusiveSuiteFunction {
    /**
     * Describe a "suite" with the given `title`, TestOptions, and callback `fn` containing
     * nested suites. Indicates this suite should be executed exclusively.
     */
    (title: string, config: Cypress.SuiteConfigOverrides, fn: (this: Suite) => void): Suite
  }

  interface PendingSuiteFunction {
    (title: string, config: Cypress.SuiteConfigOverrides, fn: (this: Suite) => void): Suite | void
  }
}
