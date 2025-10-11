/**
 *  An environment's implementation of ``getUrl`` must return this type.
 */
export type GetUrlResponse = {
    statusCode: number;
    statusMessage: string;
    headers: Record<string, string>;
    body: null | Uint8Array;
};
/**
 *  This can be used to control how throttling is handled in
 *  [[FetchRequest-setThrottleParams]].
 */
export type FetchThrottleParams = {
    maxAttempts?: number;
    slotInterval?: number;
};
/**
 *  Called before any network request, allowing updated headers (e.g. Bearer tokens), etc.
 */
export type FetchPreflightFunc = (req: FetchRequest) => Promise<FetchRequest>;
/**
 *  Called on the response, allowing client-based throttling logic or post-processing.
 */
export type FetchProcessFunc = (req: FetchRequest, resp: FetchResponse) => Promise<FetchResponse>;
/**
 *  Called prior to each retry; return true to retry, false to abort.
 */
export type FetchRetryFunc = (req: FetchRequest, resp: FetchResponse, attempt: number) => Promise<boolean>;
/**
 *  Called on Gateway URLs.
 */
export type FetchGatewayFunc = (url: string, signal?: FetchCancelSignal) => Promise<FetchRequest | FetchResponse>;
/**
 *  Used to perform a fetch; use this to override the underlying network
 *  fetch layer. In NodeJS, the default uses the "http" and "https" libraries
 *  and in the browser ``fetch`` is used. If you wish to use Axios, this is
 *  how you would register it.
 */
export type FetchGetUrlFunc = (req: FetchRequest, signal?: FetchCancelSignal) => Promise<GetUrlResponse>;
/**
 *  @_ignore
 */
export declare class FetchCancelSignal {
    #private;
    constructor(request: FetchRequest);
    addListener(listener: () => void): void;
    get cancelled(): boolean;
    checkSignal(): void;
}
/**
 *  Represents a request for a resource using a URI.
 *
 *  By default, the supported schemes are ``HTTP``, ``HTTPS``, ``data:``,
 *  and ``IPFS:``.
 *
 *  Additional schemes can be added globally using [[registerGateway]].
 *
 *  @example:
 *    req = new FetchRequest("https://www.ricmoo.com")
 *    resp = await req.send()
 *    resp.body.length
 *    //_result:
 */
export declare class FetchRequest implements Iterable<[key: string, value: string]> {
    #private;
    /**
     *  The fetch URL to request.
     */
    get url(): string;
    set url(url: string);
    /**
     *  The fetch body, if any, to send as the request body. //(default: null)//
     *
     *  When setting a body, the intrinsic ``Content-Type`` is automatically
     *  set and will be used if **not overridden** by setting a custom
     *  header.
     *
     *  If %%body%% is null, the body is cleared (along with the
     *  intrinsic ``Content-Type``).
     *
     *  If %%body%% is a string, the intrinsic ``Content-Type`` is set to
     *  ``text/plain``.
     *
     *  If %%body%% is a Uint8Array, the intrinsic ``Content-Type`` is set to
     *  ``application/octet-stream``.
     *
     *  If %%body%% is any other object, the intrinsic ``Content-Type`` is
     *  set to ``application/json``.
     */
    get body(): null | Uint8Array;
    set body(body: null | string | Readonly<object> | Readonly<Uint8Array>);
    /**
     *  Returns true if the request has a body.
     */
    hasBody(): this is (FetchRequest & {
        body: Uint8Array;
    });
    /**
     *  The HTTP method to use when requesting the URI. If no method
     *  has been explicitly set, then ``GET`` is used if the body is
     *  null and ``POST`` otherwise.
     */
    get method(): string;
    set method(method: null | string);
    /**
     *  The headers that will be used when requesting the URI. All
     *  keys are lower-case.
     *
     *  This object is a copy, so any changes will **NOT** be reflected
     *  in the ``FetchRequest``.
     *
     *  To set a header entry, use the ``setHeader`` method.
     */
    get headers(): Record<string, string>;
    /**
     *  Get the header for %%key%%, ignoring case.
     */
    getHeader(key: string): string;
    /**
     *  Set the header for %%key%% to %%value%%. All values are coerced
     *  to a string.
     */
    setHeader(key: string, value: string | number): void;
    /**
     *  Clear all headers, resetting all intrinsic headers.
     */
    clearHeaders(): void;
    [Symbol.iterator](): Iterator<[key: string, value: string]>;
    /**
     *  The value that will be sent for the ``Authorization`` header.
     *
     *  To set the credentials, use the ``setCredentials`` method.
     */
    get credentials(): null | string;
    /**
     *  Sets an ``Authorization`` for %%username%% with %%password%%.
     */
    setCredentials(username: string, password: string): void;
    /**
     *  Enable and request gzip-encoded responses. The response will
     *  automatically be decompressed. //(default: true)//
     */
    get allowGzip(): boolean;
    set allowGzip(value: boolean);
    /**
     *  Allow ``Authentication`` credentials to be sent over insecure
     *  channels. //(default: false)//
     */
    get allowInsecureAuthentication(): boolean;
    set allowInsecureAuthentication(value: boolean);
    /**
     *  The timeout (in milliseconds) to wait for a complete response.
     *  //(default: 5 minutes)//
     */
    get timeout(): number;
    set timeout(timeout: number);
    /**
     *  This function is called prior to each request, for example
     *  during a redirection or retry in case of server throttling.
     *
     *  This offers an opportunity to populate headers or update
     *  content before sending a request.
     */
    get preflightFunc(): null | FetchPreflightFunc;
    set preflightFunc(preflight: null | FetchPreflightFunc);
    /**
     *  This function is called after each response, offering an
     *  opportunity to provide client-level throttling or updating
     *  response data.
     *
     *  Any error thrown in this causes the ``send()`` to throw.
     *
     *  To schedule a retry attempt (assuming the maximum retry limit
     *  has not been reached), use [[response.throwThrottleError]].
     */
    get processFunc(): null | FetchProcessFunc;
    set processFunc(process: null | FetchProcessFunc);
    /**
     *  This function is called on each retry attempt.
     */
    get retryFunc(): null | FetchRetryFunc;
    set retryFunc(retry: null | FetchRetryFunc);
    /**
     *  This function is called to fetch content from HTTP and
     *  HTTPS URLs and is platform specific (e.g. nodejs vs
     *  browsers).
     *
     *  This is by default the currently registered global getUrl
     *  function, which can be changed using [[registerGetUrl]].
     *  If this has been set, setting is to ``null`` will cause
     *  this FetchRequest (and any future clones) to revert back to
     *  using the currently registered global getUrl function.
     *
     *  Setting this is generally not necessary, but may be useful
     *  for developers that wish to intercept requests or to
     *  configurege a proxy or other agent.
     */
    get getUrlFunc(): FetchGetUrlFunc;
    set getUrlFunc(value: null | FetchGetUrlFunc);
    /**
     *  Create a new FetchRequest instance with default values.
     *
     *  Once created, each property may be set before issuing a
     *  ``.send()`` to make the request.
     */
    constructor(url: string);
    toString(): string;
    /**
     *  Update the throttle parameters used to determine maximum
     *  attempts and exponential-backoff properties.
     */
    setThrottleParams(params: FetchThrottleParams): void;
    /**
     *  Resolves to the response by sending the request.
     */
    send(): Promise<FetchResponse>;
    /**
     *  Cancels the inflight response, causing a ``CANCELLED``
     *  error to be rejected from the [[send]].
     */
    cancel(): void;
    /**
     *  Returns a new [[FetchRequest]] that represents the redirection
     *  to %%location%%.
     */
    redirect(location: string): FetchRequest;
    /**
     *  Create a new copy of this request.
     */
    clone(): FetchRequest;
    /**
     *  Locks all static configuration for gateways and FetchGetUrlFunc
     *  registration.
     */
    static lockConfig(): void;
    /**
     *  Get the current Gateway function for %%scheme%%.
     */
    static getGateway(scheme: string): null | FetchGatewayFunc;
    /**
     *  Use the %%func%% when fetching URIs using %%scheme%%.
     *
     *  This method affects all requests globally.
     *
     *  If [[lockConfig]] has been called, no change is made and this
     *  throws.
     */
    static registerGateway(scheme: string, func: FetchGatewayFunc): void;
    /**
     *  Use %%getUrl%% when fetching URIs over HTTP and HTTPS requests.
     *
     *  This method affects all requests globally.
     *
     *  If [[lockConfig]] has been called, no change is made and this
     *  throws.
     */
    static registerGetUrl(getUrl: FetchGetUrlFunc): void;
    /**
     *  Creates a getUrl function that fetches content from HTTP and
     *  HTTPS URLs.
     *
     *  The available %%options%% are dependent on the platform
     *  implementation of the default getUrl function.
     *
     *  This is not generally something that is needed, but is useful
     *  when trying to customize simple behaviour when fetching HTTP
     *  content.
     */
    static createGetUrlFunc(options?: Record<string, any>): FetchGetUrlFunc;
    /**
     *  Creates a function that can "fetch" data URIs.
     *
     *  Note that this is automatically done internally to support
     *  data URIs, so it is not necessary to register it.
     *
     *  This is not generally something that is needed, but may
     *  be useful in a wrapper to perfom custom data URI functionality.
     */
    static createDataGateway(): FetchGatewayFunc;
    /**
     *  Creates a function that will fetch IPFS (unvalidated) from
     *  a custom gateway baseUrl.
     *
     *  The default IPFS gateway used internally is
     *  ``"https:/\/gateway.ipfs.io/ipfs/"``.
     */
    static createIpfsGatewayFunc(baseUrl: string): FetchGatewayFunc;
}
/**
 *  The response for a FetchRequest.
 */
export declare class FetchResponse implements Iterable<[key: string, value: string]> {
    #private;
    toString(): string;
    /**
     *  The response status code.
     */
    get statusCode(): number;
    /**
     *  The response status message.
     */
    get statusMessage(): string;
    /**
     *  The response headers. All keys are lower-case.
     */
    get headers(): Record<string, string>;
    /**
     *  The response body, or ``null`` if there was no body.
     */
    get body(): null | Readonly<Uint8Array>;
    /**
     *  The response body as a UTF-8 encoded string, or the empty
     *  string (i.e. ``""``) if there was no body.
     *
     *  An error is thrown if the body is invalid UTF-8 data.
     */
    get bodyText(): string;
    /**
     *  The response body, decoded as JSON.
     *
     *  An error is thrown if the body is invalid JSON-encoded data
     *  or if there was no body.
     */
    get bodyJson(): any;
    [Symbol.iterator](): Iterator<[key: string, value: string]>;
    constructor(statusCode: number, statusMessage: string, headers: Readonly<Record<string, string>>, body: null | Uint8Array, request?: FetchRequest);
    /**
     *  Return a Response with matching headers and body, but with
     *  an error status code (i.e. 599) and %%message%% with an
     *  optional %%error%%.
     */
    makeServerError(message?: string, error?: Error): FetchResponse;
    /**
     *  If called within a [request.processFunc](FetchRequest-processFunc)
     *  call, causes the request to retry as if throttled for %%stall%%
     *  milliseconds.
     */
    throwThrottleError(message?: string, stall?: number): never;
    /**
     *  Get the header value for %%key%%, ignoring case.
     */
    getHeader(key: string): string;
    /**
     *  Returns true if the response has a body.
     */
    hasBody(): this is (FetchResponse & {
        body: Uint8Array;
    });
    /**
     *  The request made for this response.
     */
    get request(): null | FetchRequest;
    /**
     *  Returns true if this response was a success statusCode.
     */
    ok(): boolean;
    /**
     *  Throws a ``SERVER_ERROR`` if this response is not ok.
     */
    assertOk(): void;
}
//# sourceMappingURL=fetch.d.ts.map