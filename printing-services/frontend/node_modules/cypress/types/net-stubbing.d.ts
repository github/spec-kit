// Copied from https://github.com/DefinitelyTyped/DefinitelyTyped/blob/master/types/methods/index.d.ts
type Method =
  | 'ACL'
  | 'BIND'
  | 'CHECKOUT'
  | 'CONNECT'
  | 'COPY'
  | 'DELETE'
  | 'GET'
  | 'HEAD'
  | 'LINK'
  | 'LOCK'
  | 'M-SEARCH'
  | 'MERGE'
  | 'MKACTIVITY'
  | 'MKCALENDAR'
  | 'MKCOL'
  | 'MOVE'
  | 'NOTIFY'
  | 'OPTIONS'
  | 'PATCH'
  | 'POST'
  | 'PROPFIND'
  | 'PROPPATCH'
  | 'PURGE'
  | 'PUT'
  | 'REBIND'
  | 'REPORT'
  | 'SEARCH'
  | 'SOURCE'
  | 'SUBSCRIBE'
  | 'TRACE'
  | 'UNBIND'
  | 'UNLINK'
  | 'UNLOCK'
  | 'UNSUBSCRIBE'
  | 'acl'
  | 'bind'
  | 'checkout'
  | 'connect'
  | 'copy'
  | 'delete'
  | 'get'
  | 'head'
  | 'link'
  | 'lock'
  | 'm-search'
  | 'merge'
  | 'mkactivity'
  | 'mkcalendar'
  | 'mkcol'
  | 'move'
  | 'notify'
  | 'options'
  | 'patch'
  | 'post'
  | 'propfind'
  | 'proppatch'
  | 'purge'
  | 'put'
  | 'rebind'
  | 'report'
  | 'search'
  | 'source'
  | 'subscribe'
  | 'trace'
  | 'unbind'
  | 'unlink'
  | 'unlock'
  | 'unsubscribe'

export type ResourceType = 'document' | 'fetch' | 'xhr' | 'websocket' | 'stylesheet' | 'script' | 'image' | 'font' | 'cspviolationreport' | 'ping' | 'manifest' | 'other'

export namespace CyHttpMessages {
  export interface BaseMessage<T = any> {
    /**
     * The body of the HTTP message.
     * If a JSON Content-Type was used and the body was valid JSON, this will be an object.
     * If the body was binary content, this will be a buffer.
     */
    body: T
    /**
     * The headers of the HTTP message.
     */
    headers: { [key: string]: string | string[] }
  }

  export type IncomingResponse<T = any> = BaseMessage<T> & {
    /**
     * The HTTP status code of the response.
     */
    statusCode: number
    /**
     * The HTTP status message.
     */
    statusMessage: string
    /**
     * Kilobytes per second to send 'body'.
     */
    throttleKbps?: number
    /**
     * Milliseconds to delay before the response is sent.
     */
    delay?: number
  }

  export type IncomingHttpResponse<T = any> = IncomingResponse<T> & {
    /**
     * Continue the HTTP response, merging the supplied values with the real response.
     */
    send(status: number, body?: string | number | object, headers?: { [key: string]: string }): void
    send(body: string | object, headers?: { [key: string]: string }): void
    send(staticResponse: StaticResponse): void
    /**
     * Continue the HTTP response to the browser, including any modifications made to `res`.
     */
    send(): void
    /**
     * Wait for `delay` milliseconds before sending the response to the client.
     */
    setDelay: (delay: number) => IncomingHttpResponse<T>
    /**
     * Serve the response at `throttleKbps` kilobytes per second.
     */
    setThrottle: (throttleKbps: number) => IncomingHttpResponse<T>
  }

  export type IncomingRequest<T = any> = BaseMessage<T> & {
    /**
     * Request HTTP method (GET, POST, ...).
     */
    method: string
    /**
     * Request URL.
     */
    url: string
    /**
     * URL query string as object.
     */
    query: Record<string, string | number>
    /**
     * The HTTP version used in the request. Read only.
     */
    httpVersion: string
    /**
     * The resource type that is being requested, according to the browser.
     * @deprecated the resource types may change or be completely removed in a future version of Cypress
     */
    resourceType: ResourceType
    /**
     * If provided, the number of milliseconds before an upstream response to this request
     * will time out and cause an error. By default, `responseTimeout` from config is used.
     */
    responseTimeout?: number
    /**
     * Set if redirects should be followed when this request is made. By default, requests will
     * not follow redirects before yielding the response (the 3xx redirect is yielded)
     */
    followRedirect?: boolean
    /**
     * If set, `cy.wait` can be used to await the request/response cycle to complete for this
     * request via `cy.wait('@alias')`.
     */
    alias?: string
  }

  export interface IncomingHttpRequest<TRequest = any, TResponse = any> extends IncomingRequest<TRequest>, RequestEvents<TResponse> {
    /**
     * Destroy the request and respond with a network error.
     */
    destroy(): void
    /**
     * Send the request outgoing, skipping any other request handlers.
     * If a function is passed, the request will be sent outgoing, and the function will be called
     * with the response from the upstream server.
     */
    continue(interceptor?: HttpResponseInterceptor<TResponse>): void
    /**
     * Control the response to this request.
     * If a function is passed, the request will be sent outgoing, and the function will be called
     * with the response from the upstream server.
     * If a `StaticResponse` is passed, it will be used as the response, and no request will be made
     * to the upstream server.
     */
    reply(interceptor?: StaticResponse | HttpResponseInterceptor<TResponse>): void
    /**
     * Shortcut to reply to the request with a body and optional headers.
     */
    reply(body: string | object, headers?: { [key: string]: string }): void
    /**
     * Shortcut to reply to the request with an HTTP status code and optional body and headers.
     */
    reply(status: number, body?: string | object, headers?: { [key: string]: string }): void
    /**
     * Respond to this request with a redirect to a new `location`.
     * @param statusCode HTTP status code to redirect with. Default: 302
     */
    redirect(location: string, statusCode?: number): void
  }

  export interface ResponseComplete<T = any> {
    finalResBody?: BaseMessage<T>['body']
  }

  export interface NetworkError {
    error: any
  }
}

export interface DictMatcher<T> {
  [key: string]: T
}

/**
 * Matches a string using glob (`*`) matching.
 */
export type GlobPattern = string

/**
 * Interceptor for an HTTP request. If a Promise is returned, it will be awaited before passing the
 * request to the next handler (if there is one), otherwise the request will be passed to the next
 * handler synchronously.
 */
export type HttpRequestInterceptor<TRequest = any, TResponse = any> = (req: CyHttpMessages.IncomingHttpRequest<TRequest, TResponse>) => void | Promise<void>

/**
 * Interceptor for an HTTP response. If a Promise is returned, it will be awaited before passing the
 * request to the next handler (if there is one), otherwise the request will be passed to the next
 * handler synchronously.
 */
export type HttpResponseInterceptor<T = any> = (res: CyHttpMessages.IncomingHttpResponse<T>) => void | Promise<void>

/**
 * Matches a single number or any of an array of acceptable numbers.
 */
export type NumberMatcher = number | number[]

/**
 * Metadata for a subscription for an interception event.
 */
export interface Subscription {
  /**
   * If not defined, this is a default subscription.
   */
  id?: string
  routeId: string
  eventName: string
  await: boolean
  skip?: boolean
}

interface RequestEvents<T> {
  /**
   * Emitted before `response` and before any `req.continue` handlers.
   * Modifications to `res` will be applied to the incoming response.
   * If a promise is returned from `cb`, it will be awaited before processing other event handlers.
   */
  on(eventName: 'before:response', cb: HttpResponseInterceptor<T>): this
  /**
   * Emitted after `before:response` and after any `req.continue` handlers - before the response is sent to the browser.
   * Modifications to `res` will be applied to the incoming response.
   * If a promise is returned from `cb`, it will be awaited before processing other event handlers.
   */
  on(eventName: 'response', cb: HttpResponseInterceptor<T>): this
  /**
   * Emitted once the response to a request has finished sending to the browser.
   * Modifications to `res` have no impact.
   * If a promise is returned from `cb`, it will be awaited before processing other event handlers.
   */
  on(eventName: 'after:response', cb: (res: CyHttpMessages.IncomingResponse<T>) => void | Promise<void>): this
}

/**
 * Request/response cycle.
 */
export interface Interception<TRequest = any, TResponse = any> {
  id: string
  /* @internal */
  browserRequestId?: string
  routeId: string
  /* @internal */
  setLogFlag: (flag: 'spied' | 'stubbed' | 'reqModified' | 'resModified') => void
  request: CyHttpMessages.IncomingRequest<TRequest>
  /**
   * Was `cy.wait()` used to wait on this request?
   * @internal
   */
  requestWaited: boolean
  response?: CyHttpMessages.IncomingResponse<TResponse>
  /**
   * The error that occurred during this request.
   */
  error?: Error
  /**
   * Was `cy.wait()` used to wait on the response to this request?
   * @internal
   */
  responseWaited: boolean
  /* @internal */
  state: InterceptionState
  /* @internal */
  subscriptions: Array<{
    subscription: Subscription
    handler: (data: any) => Promise<void> | void
  }>
}

export type InterceptionState =
  'Received' |
  'Intercepted' |
  'ResponseReceived' |
  'ResponseIntercepted' |
  'Complete' |
  'Errored'

export interface Route<TRequest = any, TResponse = any> {
  alias?: string
  log: any
  options: RouteMatcherOptions
  handler: RouteHandler<TRequest, TResponse>
  hitCount: number
  requests: { [key: string]: Interception<TRequest, TResponse> }
  command: any
}

export interface RouteMap<TRequest = any, TResponse = any> { [key: string]: Route<TRequest, TResponse> }

/**
 * A `RouteMatcher` describes a filter for HTTP requests.
 */
export type RouteMatcher = StringMatcher | RouteMatcherOptions

export type RouteMatcherOptions = RouteMatcherOptionsGeneric<StringMatcher>

export interface RouteMatcherOptionsGeneric<S> {
  /**
   * Match against the username and password used in HTTP Basic authentication.
   */
  auth?: { username: S, password: S }
  /**
   * Match against HTTP headers on the request.
   */
  headers?: DictMatcher<S>
  /**
   * Match against the requested HTTP hostname.
   */
  hostname?: S
  /**
   * If 'true', only HTTPS requests will be matched.
   * If 'false', only HTTP requests will be matched.
   */
  https?: boolean
  /**
   * Match against the request's HTTP method.
   * @default '*'
   */
  method?: S
  /**
   * If `true`, this handler will be called before any non-`middleware` handlers, in the order it was defined.
   * Can only be used with a dynamic request handler.
   * @default false
   */
  middleware?: boolean
  /**
   * Match on request path after the hostname, including query params.
   */
  path?: S
  /**
   * Matches like `path`, but without query params.
   */
  pathname?: S
  /**
   * Match based on requested port, or pass an array of ports
   * to match against any in that array.
   */
  port?: NumberMatcher
  /**
   * Match on parsed querystring parameters.
   */
  query?: DictMatcher<S>
  /**
   * Match on the request's resource type, according to the browser.
   */
  resourceType?: ResourceType | S
  /**
   * If set, this `RouteMatcher` will only match the first `times` requests.
   */
  times?: number
  /**
   * Match against the full request URL.
   * If a string is passed, it will be used as a substring match,
   * not an equality match.
   */
  url?: S
}

export type RouteHandlerController<TRequest = any, TResponse = any> = HttpRequestInterceptor<TRequest, TResponse>

export type RouteHandler<TRequest = any, TResponse = any> = string | StaticResponseWithOptions | RouteHandlerController<TRequest, TResponse> | object

export type InterceptOptions = {
  /**
   * If set to `false`, matching requests will not be shown in the Command Log.
   * @default true
   */
  log?: boolean
}

export type StaticResponseWithOptions = StaticResponse & InterceptOptions

/**
 * Describes a response that will be sent back to the browser to fulfill the request.
 */
export type StaticResponse = GenericStaticResponse<string, string | object | boolean | ArrayBuffer | null>

export interface GenericStaticResponse<Fixture, Body> {
  /**
   * Serve a fixture as the response body.
   */
  fixture?: Fixture
  /**
   * Serve a static string/JSON object as the response body.
   */
  body?: Body
  /**
   * HTTP headers to accompany the response.
   * @default {}
   */
  headers?: { [key: string]: string }
  /**
   * The HTTP status code to send.
   * @default 200
   */
  statusCode?: number
  /**
   * If 'forceNetworkError' is truthy, Cypress will destroy the browser connection
   * and send no response. Useful for simulating a server that is not reachable.
   * Must not be set in combination with other options.
   */
  forceNetworkError?: boolean
  /**
   * Kilobytes per second to send 'body'.
   */
  throttleKbps?: number
  /**
   * Milliseconds to delay before the response is sent.
   */
  delay?: number
}

/**
 * Either a `GlobPattern` string or a `RegExp`.
 */
export type StringMatcher = GlobPattern | RegExp

interface WaitOptions {
  /**
   * Displays the command in the Command Log
   *
   * @default true
   */
  log: boolean
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
  /**
   * Time to wait (ms)
   *
   * @default defaultCommandTimeout
   * @see https://on.cypress.io/configuration#Timeouts
   */
  timeout: number
}

declare global {
  namespace Cypress {
    // TODO: Why is Subject unused?
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    interface Chainable<Subject = any> {
      /**
       * Use `cy.intercept()` to stub and intercept HTTP requests and responses.
       *
       * @see https://on.cypress.io/intercept
       * @example
       *    cy.intercept('https://localhost:7777/users', [{id: 1, name: 'Pat'}])
       * @example
       *    cy.intercept('https://localhost:7777/protected-endpoint', (req) => {
       *      req.headers['authorization'] = 'basic fooabc123'
       *    })
       * @example
       *    cy.intercept('https://localhost:7777/some-response', (req) => {
       *      req.continue(res => {
       *        res.body = 'some new body'
       *      })
       *    })
       */
      intercept<TRequest = any, TResponse = any>(url: RouteMatcher, response?: RouteHandler<TRequest, TResponse>): Chainable<null>
      /**
       * Use `cy.intercept()` to stub and intercept HTTP requests and responses.
       *
       * @see https://on.cypress.io/intercept
       * @example
       *    cy.intercept('GET', 'http://foo.com/fruits', ['apple', 'banana', 'cherry'])
       */
      intercept<TRequest = any, TResponse = any>(method: Method, url: RouteMatcher, response?: RouteHandler<TRequest, TResponse>): Chainable<null>
      /**
       * Use `cy.intercept()` to stub and intercept HTTP requests and responses.
       *
       * @see https://on.cypress.io/intercept
       *
       * @example
       *    cy.intercept('/fruits', { middleware: true }, (req) => { ... })
       *
       * @param mergeRouteMatcher Additional route matcher options to merge with `url`. Typically used for middleware.
       */
      intercept<TRequest = any, TResponse = any>(url: StringMatcher, mergeRouteMatcher: Omit<RouteMatcherOptions, 'url'>, response: RouteHandler<TRequest, TResponse>): Chainable<null>
      /**
       * Wait for a specific request to complete.
       *
       * @see https://on.cypress.io/wait
       * @param {string} alias - Name of the alias to wait for.
       *
      ```
      // Wait for the route aliased as 'getAccount' to respond
      // without changing or stubbing its response
      cy.intercept('https://api.example.com/accounts/*').as('getAccount')
      cy.visit('/accounts/123')
      cy.wait('@getAccount').then((interception) => {
        // we can now access the low level request
        // that contains the request body,
        // response body, status, etc
      })
      ```
      */
      wait<TRequest = any, TResponse = any>(alias: string, options?: Partial<WaitOptions>): Chainable<Interception<TRequest, TResponse>>
      /**
       * Wait for list of requests to complete.
       *
       * @see https://on.cypress.io/wait
       * @param {string[]} aliases - An array of aliased routes as defined using the `.as()` command.
       *
      ```
      // wait for 3 XHR requests to complete
      cy.intercept('users/*').as('getUsers')
      cy.intercept('activities/*').as('getActivities')
      cy.intercept('comments/*').as('getComments')
      cy.visit('/dashboard')

      cy.wait(['@getUsers', '@getActivities', '@getComments'])
        .then((interceptions) => {
          // intercepts will now be an array of matching HTTP requests
        })
      ```
      */
      wait(aliases: string[], options?: Partial<WaitOptions>): Chainable<Interception[]>
    }
  }
}
