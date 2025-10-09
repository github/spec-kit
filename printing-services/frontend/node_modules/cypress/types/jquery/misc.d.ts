// tslint:disable:jsdoc-format
// tslint:disable:max-line-length
// tslint:disable:no-irregular-whitespace

declare namespace JQuery {
    type TypeOrArray<T> = T | T[];
    type Node = Element | Text | Comment | DocumentFragment;

    /**
     * A string is designated htmlString in jQuery documentation when it is used to represent one or more DOM elements, typically to be created and inserted in the document. When passed as an argument of the jQuery() function, the string is identified as HTML if it starts with <tag ... >) and is parsed as such until the final > character. Prior to jQuery 1.9, a string was considered to be HTML if it contained <tag ... > anywhere within the string.
     */
    type htmlString = string;
    /**
     * A selector is used in jQuery to select DOM elements from a DOM document. That document is, in most cases, the DOM document present in all browsers, but can also be an XML document received via Ajax.
     */
    type Selector = string;

    /**
     * The PlainObject type is a JavaScript object containing zero or more key-value pairs. The plain object is, in other words, an Object object. It is designated "plain" in jQuery documentation to distinguish it from other kinds of JavaScript objects: for example, null, user-defined arrays, and host objects such as document, all of which have a typeof value of "object."
     *
     * **Note**: The type declaration of PlainObject is imprecise. It includes host objects and user-defined arrays which do not match jQuery's definition.
     */
    interface PlainObject<T = any> {
        [key: string]: T;
    }

    interface Selectors extends Sizzle.Selectors {
        /**
         * @deprecated ​ Deprecated since 3.0. Use \`{@link Selectors#pseudos }\`.
         *
         * **Cause**: The standard way to add new custom selectors through jQuery is `jQuery.expr.pseudos`. These two other aliases are deprecated, although they still work as of jQuery 3.0.
         *
         * **Solution**: Rename any of the older usage to `jQuery.expr.pseudos`. The functionality is identical.
         */
        ':': Sizzle.Selectors.PseudoFunctions;
        /**
         * @deprecated ​ Deprecated since 3.0. Use \`{@link Selectors#pseudos }\`.
         *
         * **Cause**: The standard way to add new custom selectors through jQuery is `jQuery.expr.pseudos`. These two other aliases are deprecated, although they still work as of jQuery 3.0.
         *
         * **Solution**: Rename any of the older usage to `jQuery.expr.pseudos`. The functionality is identical.
         */
        filter: Sizzle.Selectors.FilterFunctions;
    }

    // region Ajax
    // #region Ajax

    interface AjaxSettings<TContext = any> extends Ajax.AjaxSettingsBase<TContext> {
        /**
         * A string containing the URL to which the request is sent.
         */
        url?: string;
    }

    interface UrlAjaxSettings<TContext = any> extends Ajax.AjaxSettingsBase<TContext> {
        /**
         * A string containing the URL to which the request is sent.
         */
        url: string;
    }

    namespace Ajax {
        type SuccessTextStatus = 'success' | 'notmodified' | 'nocontent';
        type ErrorTextStatus = 'timeout' | 'error' | 'abort' | 'parsererror';
        type TextStatus = SuccessTextStatus | ErrorTextStatus;

        type SuccessCallback<TContext> = (this: TContext, data: any, textStatus: SuccessTextStatus, jqXHR: jqXHR) => void;

        type ErrorCallback<TContext> = (this: TContext, jqXHR: jqXHR, textStatus: ErrorTextStatus, errorThrown: string) => void;

        type CompleteCallback<TContext> = (this: TContext, jqXHR: jqXHR, textStatus: TextStatus) => void;

        /**
         * @see \`{@link https://api.jquery.com/jquery.ajax/#jQuery-ajax-settings }\`
         */
        interface AjaxSettingsBase<TContext> {
            /**
             * A set of key/value pairs that map a given dataType to its MIME type, which gets sent in the Accept request header. This header tells the server what kind of response it will accept in return.
             */
            accepts?: PlainObject<string>;
            /**
             * By default, all requests are sent asynchronously (i.e. this is set to true by default). If you need synchronous requests, set this option to false. Cross-domain requests and dataType: "jsonp" requests do not support synchronous operation. Note that synchronous requests may temporarily lock the browser, disabling any actions while the request is active. As of jQuery 1.8, the use of async: false with jqXHR ($.Deferred) is deprecated; you must use the success/error/complete callback options instead of the corresponding methods of the jqXHR object such as jqXHR.done().
             */
            async?: boolean;
            /**
             * A pre-request callback function that can be used to modify the jqXHR (in jQuery 1.4.x, XMLHTTPRequest) object before it is sent. Use this to set custom headers, etc. The jqXHR and settings objects are passed as arguments. This is an Ajax Event. Returning false in the beforeSend function will cancel the request. As of jQuery 1.5, the beforeSend option will be called regardless of the type of request.
             */
            beforeSend?(this: TContext, jqXHR: jqXHR, settings: this): false | void;
            /**
             * If set to false, it will force requested pages not to be cached by the browser. Note: Setting cache to false will only work correctly with HEAD and GET requests. It works by appending "_={timestamp}" to the GET parameters. The parameter is not needed for other types of requests, except in IE8 when a POST is made to a URL that has already been requested by a GET.
             */
            cache?: boolean;
            /**
             * A function to be called when the request finishes (after success and error callbacks are executed). The function gets passed two arguments: The jqXHR (in jQuery 1.4.x, XMLHTTPRequest) object and a string categorizing the status of the request ("success", "notmodified", "nocontent", "error", "timeout", "abort", or "parsererror"). As of jQuery 1.5, the complete setting can accept an array of functions. Each function will be called in turn. This is an Ajax Event.
             */
            complete?: TypeOrArray<CompleteCallback<TContext>>;
            /**
             * An object of string/regular-expression pairs that determine how jQuery will parse the response, given its content type.
             */
            contents?: PlainObject<RegExp>;
            /**
             * When sending data to the server, use this content type. Default is "application/x-www-form-urlencoded; charset=UTF-8", which is fine for most cases. If you explicitly pass in a content-type to $.ajax(), then it is always sent to the server (even if no data is sent). As of jQuery 1.6 you can pass false to tell jQuery to not set any content type header. Note: The W3C XMLHttpRequest specification dictates that the charset is always UTF-8; specifying another charset will not force the browser to change the encoding. Note: For cross-domain requests, setting the content type to anything other than application/x-www-form-urlencoded, multipart/form-data, or text/plain will trigger the browser to send a preflight OPTIONS request to the server.
             */
            contentType?: string | false;
            /**
             * This object will be the context of all Ajax-related callbacks. By default, the context is an object that represents the Ajax settings used in the call ($.ajaxSettings merged with the settings passed to $.ajax).
             */
            context?: TContext;
            /**
             * An object containing dataType-to-dataType converters. Each converter's value is a function that returns the transformed value of the response.
             */
            converters?: PlainObject<((value: any) => any) | true>;
            /**
             * If you wish to force a crossDomain request (such as JSONP) on the same domain, set the value of crossDomain to true. This allows, for example, server-side redirection to another domain.
             */
            crossDomain?: boolean;
            /**
             * Data to be sent to the server. It is converted to a query string, if not already a string. It's appended to the url for GET-requests. See processData option to prevent this automatic processing. Object must be Key/Value pairs. If value is an Array, jQuery serializes multiple values with same key based on the value of the traditional setting (described below).
             */
            data?: PlainObject | string;
            /**
             * A function to be used to handle the raw response data of XMLHttpRequest. This is a pre-filtering function to sanitize the response. You should return the sanitized data. The function accepts two arguments: The raw data returned from the server and the 'dataType' parameter.
             */
            dataFilter?(data: string, type: string): any;
            /**
             * The type of data that you're expecting back from the server. If none is specified, jQuery will try to infer it based on the MIME type of the response (an XML MIME type will yield XML, in 1.4 JSON will yield a JavaScript object, in 1.4 script will execute the script, and anything else will be returned as a string). The available types (and the result passed as the first argument to your success callback) are:
             *
             * "xml": Returns a XML document that can be processed via jQuery.
             *
             * "html": Returns HTML as plain text; included script tags are evaluated when inserted in the DOM.
             *
             * "script": Evaluates the response as JavaScript and returns it as plain text. Disables caching by appending a query string parameter, _=[TIMESTAMP], to the URL unless the cache option is set to true. Note: This will turn POSTs into GETs for remote-domain requests.
             *
             * "json": Evaluates the response as JSON and returns a JavaScript object. Cross-domain "json" requests are converted to "jsonp" unless the request includes jsonp: false in its request options. The JSON data is parsed in a strict manner; any malformed JSON is rejected and a parse error is thrown. As of jQuery 1.9, an empty response is also rejected; the server should return a response of null or {} instead. (See json.org for more information on proper JSON formatting.)
             *
             * "jsonp": Loads in a JSON block using JSONP. Adds an extra "?callback=?" to the end of your URL to specify the callback. Disables caching by appending a query string parameter, "_=[TIMESTAMP]", to the URL unless the cache option is set to true.
             *
             * "text": A plain text string.
             *
             * multiple, space-separated values: As of jQuery 1.5, jQuery can convert a dataType from what it received in the Content-Type header to what you require. For example, if you want a text response to be treated as XML, use "text xml" for the dataType. You can also make a JSONP request, have it received as text, and interpreted by jQuery as XML: "jsonp text xml". Similarly, a shorthand string such as "jsonp xml" will first attempt to convert from jsonp to xml, and, failing that, convert from jsonp to text, and then from text to xml.
             */
            dataType?: 'xml' | 'html' | 'script' | 'json' | 'jsonp' | 'text' | string;
            /**
             * A function to be called if the request fails. The function receives three arguments: The jqXHR (in jQuery 1.4.x, XMLHttpRequest) object, a string describing the type of error that occurred and an optional exception object, if one occurred. Possible values for the second argument (besides null) are "timeout", "error", "abort", and "parsererror". When an HTTP error occurs, errorThrown receives the textual portion of the HTTP status, such as "Not Found" or "Internal Server Error." As of jQuery 1.5, the error setting can accept an array of functions. Each function will be called in turn. Note: This handler is not called for cross-domain script and cross-domain JSONP requests. This is an Ajax Event.
             */
            error?: TypeOrArray<ErrorCallback<TContext>>;
            /**
             * Whether to trigger global Ajax event handlers for this request. The default is true. Set to false to prevent the global handlers like ajaxStart or ajaxStop from being triggered. This can be used to control various Ajax Events.
             */
            global?: boolean;
            /**
             * An object of additional header key/value pairs to send along with requests using the XMLHttpRequest transport. The header X-Requested-With: XMLHttpRequest is always added, but its default XMLHttpRequest value can be changed here. Values in the headers setting can also be overwritten from within the beforeSend function.
             */
            headers?: PlainObject<string | null | undefined>;
            /**
             * Allow the request to be successful only if the response has changed since the last request. This is done by checking the Last-Modified header. Default value is false, ignoring the header. In jQuery 1.4 this technique also checks the 'etag' specified by the server to catch unmodified data.
             */
            ifModified?: boolean;
            /**
             * Allow the current environment to be recognized as "local," (e.g. the filesystem), even if jQuery does not recognize it as such by default. The following protocols are currently recognized as local: file, *-extension, and widget. If the isLocal setting needs modification, it is recommended to do so once in the $.ajaxSetup() method.
             */
            isLocal?: boolean;
            /**
             * Override the callback function name in a JSONP request. This value will be used instead of 'callback' in the 'callback=?' part of the query string in the url. So {jsonp:'onJSONPLoad'} would result in 'onJSONPLoad=?' passed to the server. As of jQuery 1.5, setting the jsonp option to false prevents jQuery from adding the "?callback" string to the URL or attempting to use "=?" for transformation. In this case, you should also explicitly set the jsonpCallback setting. For example, { jsonp: false, jsonpCallback: "callbackName" }. If you don't trust the target of your Ajax requests, consider setting the jsonp property to false for security reasons.
             */
            jsonp?: string | false;
            /**
             * Specify the callback function name for a JSONP request. This value will be used instead of the random name automatically generated by jQuery. It is preferable to let jQuery generate a unique name as it'll make it easier to manage the requests and provide callbacks and error handling. You may want to specify the callback when you want to enable better browser caching of GET requests. As of jQuery 1.5, you can also use a function for this setting, in which case the value of jsonpCallback is set to the return value of that function.
             */
            jsonpCallback?: string | ((this: TContext) => string);
            /**
             * The HTTP method to use for the request (e.g. "POST", "GET", "PUT").
             */
            method?: string;
            /**
             * A mime type to override the XHR mime type.
             */
            mimeType?: string;
            /**
             * A password to be used with XMLHttpRequest in response to an HTTP access authentication request.
             */
            password?: string;
            /**
             * By default, data passed in to the data option as an object (technically, anything other than a string) will be processed and transformed into a query string, fitting to the default content-type "application/x-www-form-urlencoded". If you want to send a DOMDocument, or other non-processed data, set this option to false.
             */
            processData?: boolean;
            /**
             * Only applies when the "script" transport is used (e.g., cross-domain requests with "jsonp" or "script" dataType and "GET" type). Sets the charset attribute on the script tag used in the request. Used when the character set on the local page is not the same as the one on the remote script.
             */
            scriptCharset?: string;
            /**
             * An object of numeric HTTP codes and functions to be called when the response has the corresponding code.
             *
             * If the request is successful, the status code functions take the same parameters as the success callback; if it results in an error (including 3xx redirect), they take the same parameters as the error callback.
             */
            statusCode?: StatusCodeCallbacks<TContext>;
            /**
             * A function to be called if the request succeeds. The function gets passed three arguments: The data returned from the server, formatted according to the dataType parameter or the dataFilter callback function, if specified; a string describing the status; and the jqXHR (in jQuery 1.4.x, XMLHttpRequest) object. As of jQuery 1.5, the success setting can accept an array of functions. Each function will be called in turn. This is an Ajax Event.
             */
            success?: TypeOrArray<SuccessCallback<TContext>>;
            /**
             * Set a timeout (in milliseconds) for the request. A value of 0 means there will be no timeout. This will override any global timeout set with $.ajaxSetup(). The timeout period starts at the point the $.ajax call is made; if several other requests are in progress and the browser has no connections available, it is possible for a request to time out before it can be sent. In jQuery 1.4.x and below, the XMLHttpRequest object will be in an invalid state if the request times out; accessing any object members may throw an exception. In Firefox 3.0+ only, script and JSONP requests cannot be cancelled by a timeout; the script will run even if it arrives after the timeout period.
             */
            timeout?: number;
            /**
             * Set this to true if you wish to use the traditional style of param serialization.
             */
            traditional?: boolean;
            /**
             * An alias for method. You should use type if you're using versions of jQuery prior to 1.9.0.
             */
            type?: string;
            /**
             * A username to be used with XMLHttpRequest in response to an HTTP access authentication request.
             */
            username?: string;
            // ActiveXObject requires "lib": ["scripthost"] which consumers would also require
            /**
             * Callback for creating the XMLHttpRequest object. Defaults to the ActiveXObject when available (IE), the XMLHttpRequest otherwise. Override to provide your own implementation for XMLHttpRequest or enhancements to the factory.
             */
            xhr?(): XMLHttpRequest;
            /**
             * An object of fieldName-fieldValue pairs to set on the native XHR object.
             *
             * In jQuery 1.5, the withCredentials property was not propagated to the native XHR and thus CORS requests requiring it would ignore this flag. For this reason, we recommend using jQuery 1.5.1+ should you require the use of it.
             */
            xhrFields?: XHRFields;
        }

        // region StatusCodeCallbacks
        // #region StatusCodeCallbacks

        type StatusCodeCallbacks<TContext> = {
            // region Success Status Codes
            // #region Success Status Codes

            // jQuery treats 2xx and 304 status codes as a success

            200?: SuccessCallback<TContext>;
            201?: SuccessCallback<TContext>;
            202?: SuccessCallback<TContext>;
            203?: SuccessCallback<TContext>;
            204?: SuccessCallback<TContext>;
            205?: SuccessCallback<TContext>;
            206?: SuccessCallback<TContext>;
            207?: SuccessCallback<TContext>;
            208?: SuccessCallback<TContext>;
            209?: SuccessCallback<TContext>;
            210?: SuccessCallback<TContext>;
            211?: SuccessCallback<TContext>;
            212?: SuccessCallback<TContext>;
            213?: SuccessCallback<TContext>;
            214?: SuccessCallback<TContext>;
            215?: SuccessCallback<TContext>;
            216?: SuccessCallback<TContext>;
            217?: SuccessCallback<TContext>;
            218?: SuccessCallback<TContext>;
            219?: SuccessCallback<TContext>;
            220?: SuccessCallback<TContext>;
            221?: SuccessCallback<TContext>;
            222?: SuccessCallback<TContext>;
            223?: SuccessCallback<TContext>;
            224?: SuccessCallback<TContext>;
            225?: SuccessCallback<TContext>;
            226?: SuccessCallback<TContext>;
            227?: SuccessCallback<TContext>;
            228?: SuccessCallback<TContext>;
            229?: SuccessCallback<TContext>;
            230?: SuccessCallback<TContext>;
            231?: SuccessCallback<TContext>;
            232?: SuccessCallback<TContext>;
            233?: SuccessCallback<TContext>;
            234?: SuccessCallback<TContext>;
            235?: SuccessCallback<TContext>;
            236?: SuccessCallback<TContext>;
            237?: SuccessCallback<TContext>;
            238?: SuccessCallback<TContext>;
            239?: SuccessCallback<TContext>;
            240?: SuccessCallback<TContext>;
            241?: SuccessCallback<TContext>;
            242?: SuccessCallback<TContext>;
            243?: SuccessCallback<TContext>;
            244?: SuccessCallback<TContext>;
            245?: SuccessCallback<TContext>;
            246?: SuccessCallback<TContext>;
            247?: SuccessCallback<TContext>;
            248?: SuccessCallback<TContext>;
            249?: SuccessCallback<TContext>;
            250?: SuccessCallback<TContext>;
            251?: SuccessCallback<TContext>;
            252?: SuccessCallback<TContext>;
            253?: SuccessCallback<TContext>;
            254?: SuccessCallback<TContext>;
            255?: SuccessCallback<TContext>;
            256?: SuccessCallback<TContext>;
            257?: SuccessCallback<TContext>;
            258?: SuccessCallback<TContext>;
            259?: SuccessCallback<TContext>;
            260?: SuccessCallback<TContext>;
            261?: SuccessCallback<TContext>;
            262?: SuccessCallback<TContext>;
            263?: SuccessCallback<TContext>;
            264?: SuccessCallback<TContext>;
            265?: SuccessCallback<TContext>;
            266?: SuccessCallback<TContext>;
            267?: SuccessCallback<TContext>;
            268?: SuccessCallback<TContext>;
            269?: SuccessCallback<TContext>;
            270?: SuccessCallback<TContext>;
            271?: SuccessCallback<TContext>;
            272?: SuccessCallback<TContext>;
            273?: SuccessCallback<TContext>;
            274?: SuccessCallback<TContext>;
            275?: SuccessCallback<TContext>;
            276?: SuccessCallback<TContext>;
            277?: SuccessCallback<TContext>;
            278?: SuccessCallback<TContext>;
            279?: SuccessCallback<TContext>;
            280?: SuccessCallback<TContext>;
            281?: SuccessCallback<TContext>;
            282?: SuccessCallback<TContext>;
            283?: SuccessCallback<TContext>;
            284?: SuccessCallback<TContext>;
            285?: SuccessCallback<TContext>;
            286?: SuccessCallback<TContext>;
            287?: SuccessCallback<TContext>;
            288?: SuccessCallback<TContext>;
            289?: SuccessCallback<TContext>;
            290?: SuccessCallback<TContext>;
            291?: SuccessCallback<TContext>;
            292?: SuccessCallback<TContext>;
            293?: SuccessCallback<TContext>;
            294?: SuccessCallback<TContext>;
            295?: SuccessCallback<TContext>;
            296?: SuccessCallback<TContext>;
            297?: SuccessCallback<TContext>;
            298?: SuccessCallback<TContext>;
            299?: SuccessCallback<TContext>;
            304?: SuccessCallback<TContext>;

            // #endregion

            // region Error Status Codes
            // #region Error Status Codes

            300?: ErrorCallback<TContext>;
            301?: ErrorCallback<TContext>;
            302?: ErrorCallback<TContext>;
            303?: ErrorCallback<TContext>;
            305?: ErrorCallback<TContext>;
            306?: ErrorCallback<TContext>;
            307?: ErrorCallback<TContext>;
            308?: ErrorCallback<TContext>;
            309?: ErrorCallback<TContext>;
            310?: ErrorCallback<TContext>;
            311?: ErrorCallback<TContext>;
            312?: ErrorCallback<TContext>;
            313?: ErrorCallback<TContext>;
            314?: ErrorCallback<TContext>;
            315?: ErrorCallback<TContext>;
            316?: ErrorCallback<TContext>;
            317?: ErrorCallback<TContext>;
            318?: ErrorCallback<TContext>;
            319?: ErrorCallback<TContext>;
            320?: ErrorCallback<TContext>;
            321?: ErrorCallback<TContext>;
            322?: ErrorCallback<TContext>;
            323?: ErrorCallback<TContext>;
            324?: ErrorCallback<TContext>;
            325?: ErrorCallback<TContext>;
            326?: ErrorCallback<TContext>;
            327?: ErrorCallback<TContext>;
            328?: ErrorCallback<TContext>;
            329?: ErrorCallback<TContext>;
            330?: ErrorCallback<TContext>;
            331?: ErrorCallback<TContext>;
            332?: ErrorCallback<TContext>;
            333?: ErrorCallback<TContext>;
            334?: ErrorCallback<TContext>;
            335?: ErrorCallback<TContext>;
            336?: ErrorCallback<TContext>;
            337?: ErrorCallback<TContext>;
            338?: ErrorCallback<TContext>;
            339?: ErrorCallback<TContext>;
            340?: ErrorCallback<TContext>;
            341?: ErrorCallback<TContext>;
            342?: ErrorCallback<TContext>;
            343?: ErrorCallback<TContext>;
            344?: ErrorCallback<TContext>;
            345?: ErrorCallback<TContext>;
            346?: ErrorCallback<TContext>;
            347?: ErrorCallback<TContext>;
            348?: ErrorCallback<TContext>;
            349?: ErrorCallback<TContext>;
            350?: ErrorCallback<TContext>;
            351?: ErrorCallback<TContext>;
            352?: ErrorCallback<TContext>;
            353?: ErrorCallback<TContext>;
            354?: ErrorCallback<TContext>;
            355?: ErrorCallback<TContext>;
            356?: ErrorCallback<TContext>;
            357?: ErrorCallback<TContext>;
            358?: ErrorCallback<TContext>;
            359?: ErrorCallback<TContext>;
            360?: ErrorCallback<TContext>;
            361?: ErrorCallback<TContext>;
            362?: ErrorCallback<TContext>;
            363?: ErrorCallback<TContext>;
            364?: ErrorCallback<TContext>;
            365?: ErrorCallback<TContext>;
            366?: ErrorCallback<TContext>;
            367?: ErrorCallback<TContext>;
            368?: ErrorCallback<TContext>;
            369?: ErrorCallback<TContext>;
            370?: ErrorCallback<TContext>;
            371?: ErrorCallback<TContext>;
            372?: ErrorCallback<TContext>;
            373?: ErrorCallback<TContext>;
            374?: ErrorCallback<TContext>;
            375?: ErrorCallback<TContext>;
            376?: ErrorCallback<TContext>;
            377?: ErrorCallback<TContext>;
            378?: ErrorCallback<TContext>;
            379?: ErrorCallback<TContext>;
            380?: ErrorCallback<TContext>;
            381?: ErrorCallback<TContext>;
            382?: ErrorCallback<TContext>;
            383?: ErrorCallback<TContext>;
            384?: ErrorCallback<TContext>;
            385?: ErrorCallback<TContext>;
            386?: ErrorCallback<TContext>;
            387?: ErrorCallback<TContext>;
            388?: ErrorCallback<TContext>;
            389?: ErrorCallback<TContext>;
            390?: ErrorCallback<TContext>;
            391?: ErrorCallback<TContext>;
            392?: ErrorCallback<TContext>;
            393?: ErrorCallback<TContext>;
            394?: ErrorCallback<TContext>;
            395?: ErrorCallback<TContext>;
            396?: ErrorCallback<TContext>;
            397?: ErrorCallback<TContext>;
            398?: ErrorCallback<TContext>;
            399?: ErrorCallback<TContext>;
            400?: ErrorCallback<TContext>;
            401?: ErrorCallback<TContext>;
            402?: ErrorCallback<TContext>;
            403?: ErrorCallback<TContext>;
            404?: ErrorCallback<TContext>;
            405?: ErrorCallback<TContext>;
            406?: ErrorCallback<TContext>;
            407?: ErrorCallback<TContext>;
            408?: ErrorCallback<TContext>;
            409?: ErrorCallback<TContext>;
            410?: ErrorCallback<TContext>;
            411?: ErrorCallback<TContext>;
            412?: ErrorCallback<TContext>;
            413?: ErrorCallback<TContext>;
            414?: ErrorCallback<TContext>;
            415?: ErrorCallback<TContext>;
            416?: ErrorCallback<TContext>;
            417?: ErrorCallback<TContext>;
            418?: ErrorCallback<TContext>;
            419?: ErrorCallback<TContext>;
            420?: ErrorCallback<TContext>;
            421?: ErrorCallback<TContext>;
            422?: ErrorCallback<TContext>;
            423?: ErrorCallback<TContext>;
            424?: ErrorCallback<TContext>;
            425?: ErrorCallback<TContext>;
            426?: ErrorCallback<TContext>;
            427?: ErrorCallback<TContext>;
            428?: ErrorCallback<TContext>;
            429?: ErrorCallback<TContext>;
            430?: ErrorCallback<TContext>;
            431?: ErrorCallback<TContext>;
            432?: ErrorCallback<TContext>;
            433?: ErrorCallback<TContext>;
            434?: ErrorCallback<TContext>;
            435?: ErrorCallback<TContext>;
            436?: ErrorCallback<TContext>;
            437?: ErrorCallback<TContext>;
            438?: ErrorCallback<TContext>;
            439?: ErrorCallback<TContext>;
            440?: ErrorCallback<TContext>;
            441?: ErrorCallback<TContext>;
            442?: ErrorCallback<TContext>;
            443?: ErrorCallback<TContext>;
            444?: ErrorCallback<TContext>;
            445?: ErrorCallback<TContext>;
            446?: ErrorCallback<TContext>;
            447?: ErrorCallback<TContext>;
            448?: ErrorCallback<TContext>;
            449?: ErrorCallback<TContext>;
            450?: ErrorCallback<TContext>;
            451?: ErrorCallback<TContext>;
            452?: ErrorCallback<TContext>;
            453?: ErrorCallback<TContext>;
            454?: ErrorCallback<TContext>;
            455?: ErrorCallback<TContext>;
            456?: ErrorCallback<TContext>;
            457?: ErrorCallback<TContext>;
            458?: ErrorCallback<TContext>;
            459?: ErrorCallback<TContext>;
            460?: ErrorCallback<TContext>;
            461?: ErrorCallback<TContext>;
            462?: ErrorCallback<TContext>;
            463?: ErrorCallback<TContext>;
            464?: ErrorCallback<TContext>;
            465?: ErrorCallback<TContext>;
            466?: ErrorCallback<TContext>;
            467?: ErrorCallback<TContext>;
            468?: ErrorCallback<TContext>;
            469?: ErrorCallback<TContext>;
            470?: ErrorCallback<TContext>;
            471?: ErrorCallback<TContext>;
            472?: ErrorCallback<TContext>;
            473?: ErrorCallback<TContext>;
            474?: ErrorCallback<TContext>;
            475?: ErrorCallback<TContext>;
            476?: ErrorCallback<TContext>;
            477?: ErrorCallback<TContext>;
            478?: ErrorCallback<TContext>;
            479?: ErrorCallback<TContext>;
            480?: ErrorCallback<TContext>;
            481?: ErrorCallback<TContext>;
            482?: ErrorCallback<TContext>;
            483?: ErrorCallback<TContext>;
            484?: ErrorCallback<TContext>;
            485?: ErrorCallback<TContext>;
            486?: ErrorCallback<TContext>;
            487?: ErrorCallback<TContext>;
            488?: ErrorCallback<TContext>;
            489?: ErrorCallback<TContext>;
            490?: ErrorCallback<TContext>;
            491?: ErrorCallback<TContext>;
            492?: ErrorCallback<TContext>;
            493?: ErrorCallback<TContext>;
            494?: ErrorCallback<TContext>;
            495?: ErrorCallback<TContext>;
            496?: ErrorCallback<TContext>;
            497?: ErrorCallback<TContext>;
            498?: ErrorCallback<TContext>;
            499?: ErrorCallback<TContext>;
            500?: ErrorCallback<TContext>;
            501?: ErrorCallback<TContext>;
            502?: ErrorCallback<TContext>;
            503?: ErrorCallback<TContext>;
            504?: ErrorCallback<TContext>;
            505?: ErrorCallback<TContext>;
            506?: ErrorCallback<TContext>;
            507?: ErrorCallback<TContext>;
            508?: ErrorCallback<TContext>;
            509?: ErrorCallback<TContext>;
            510?: ErrorCallback<TContext>;
            511?: ErrorCallback<TContext>;
            512?: ErrorCallback<TContext>;
            513?: ErrorCallback<TContext>;
            514?: ErrorCallback<TContext>;
            515?: ErrorCallback<TContext>;
            516?: ErrorCallback<TContext>;
            517?: ErrorCallback<TContext>;
            518?: ErrorCallback<TContext>;
            519?: ErrorCallback<TContext>;
            520?: ErrorCallback<TContext>;
            521?: ErrorCallback<TContext>;
            522?: ErrorCallback<TContext>;
            523?: ErrorCallback<TContext>;
            524?: ErrorCallback<TContext>;
            525?: ErrorCallback<TContext>;
            526?: ErrorCallback<TContext>;
            527?: ErrorCallback<TContext>;
            528?: ErrorCallback<TContext>;
            529?: ErrorCallback<TContext>;
            530?: ErrorCallback<TContext>;
            531?: ErrorCallback<TContext>;
            532?: ErrorCallback<TContext>;
            533?: ErrorCallback<TContext>;
            534?: ErrorCallback<TContext>;
            535?: ErrorCallback<TContext>;
            536?: ErrorCallback<TContext>;
            537?: ErrorCallback<TContext>;
            538?: ErrorCallback<TContext>;
            539?: ErrorCallback<TContext>;
            540?: ErrorCallback<TContext>;
            541?: ErrorCallback<TContext>;
            542?: ErrorCallback<TContext>;
            543?: ErrorCallback<TContext>;
            544?: ErrorCallback<TContext>;
            545?: ErrorCallback<TContext>;
            546?: ErrorCallback<TContext>;
            547?: ErrorCallback<TContext>;
            548?: ErrorCallback<TContext>;
            549?: ErrorCallback<TContext>;
            550?: ErrorCallback<TContext>;
            551?: ErrorCallback<TContext>;
            552?: ErrorCallback<TContext>;
            553?: ErrorCallback<TContext>;
            554?: ErrorCallback<TContext>;
            555?: ErrorCallback<TContext>;
            556?: ErrorCallback<TContext>;
            557?: ErrorCallback<TContext>;
            558?: ErrorCallback<TContext>;
            559?: ErrorCallback<TContext>;
            560?: ErrorCallback<TContext>;
            561?: ErrorCallback<TContext>;
            562?: ErrorCallback<TContext>;
            563?: ErrorCallback<TContext>;
            564?: ErrorCallback<TContext>;
            565?: ErrorCallback<TContext>;
            566?: ErrorCallback<TContext>;
            567?: ErrorCallback<TContext>;
            568?: ErrorCallback<TContext>;
            569?: ErrorCallback<TContext>;
            570?: ErrorCallback<TContext>;
            571?: ErrorCallback<TContext>;
            572?: ErrorCallback<TContext>;
            573?: ErrorCallback<TContext>;
            574?: ErrorCallback<TContext>;
            575?: ErrorCallback<TContext>;
            576?: ErrorCallback<TContext>;
            577?: ErrorCallback<TContext>;
            578?: ErrorCallback<TContext>;
            579?: ErrorCallback<TContext>;
            580?: ErrorCallback<TContext>;
            581?: ErrorCallback<TContext>;
            582?: ErrorCallback<TContext>;
            583?: ErrorCallback<TContext>;
            584?: ErrorCallback<TContext>;
            585?: ErrorCallback<TContext>;
            586?: ErrorCallback<TContext>;
            587?: ErrorCallback<TContext>;
            588?: ErrorCallback<TContext>;
            589?: ErrorCallback<TContext>;
            590?: ErrorCallback<TContext>;
            591?: ErrorCallback<TContext>;
            592?: ErrorCallback<TContext>;
            593?: ErrorCallback<TContext>;
            594?: ErrorCallback<TContext>;
            595?: ErrorCallback<TContext>;
            596?: ErrorCallback<TContext>;
            597?: ErrorCallback<TContext>;
            598?: ErrorCallback<TContext>;
            599?: ErrorCallback<TContext>;

            // #endregion
        } & {
            // Status codes not listed require type annotations when defining the callback
            [index: number]: SuccessCallback<TContext> | ErrorCallback<TContext>;
        };

        // #endregion

        // Writable properties on XMLHttpRequest
        interface XHRFields extends Partial<Pick<XMLHttpRequest, 'onreadystatechange' | 'responseType' | 'timeout' | 'withCredentials'>> {
            msCaching?: string;
        }
    }

    interface Transport {
        send(headers: PlainObject, completeCallback: Transport.SuccessCallback): void;
        abort(): void;
    }

    namespace Transport {
        type SuccessCallback = (status: number, statusText: Ajax.TextStatus, responses?: PlainObject, headers?: string) => void;
    }

    /**
     * @see \`{@link https://api.jquery.com/jquery.ajax/#jqXHR }\`
     */
    interface jqXHR<TResolve = any> extends Promise3<TResolve, jqXHR<TResolve>, never,
        Ajax.SuccessTextStatus, Ajax.ErrorTextStatus, never,
        jqXHR<TResolve>, string, never>,
        Pick<XMLHttpRequest, 'abort' | 'getAllResponseHeaders' | 'getResponseHeader' | 'overrideMimeType' | 'readyState' | 'responseText' |
            'setRequestHeader' | 'status' | 'statusText'>,
        Partial<Pick<XMLHttpRequest, 'responseXML'>> {
        responseJSON?: any;
        abort(statusText?: string): void;

        /**
         * Determine the current state of a Deferred object.
         * @see \`{@link https://api.jquery.com/deferred.state/ }\`
         * @since 1.7
         */
        state(): 'pending' | 'resolved' | 'rejected';
        statusCode(map: Ajax.StatusCodeCallbacks<any>): void;
    }

    namespace jqXHR {
        interface DoneCallback<TResolve = any, TjqXHR = jqXHR<TResolve>> extends Deferred.Callback3<TResolve, Ajax.SuccessTextStatus, TjqXHR> { }

        interface FailCallback<TjqXHR> extends Deferred.Callback3<TjqXHR, Ajax.ErrorTextStatus, string> { }

        interface AlwaysCallback<TResolve = any, TjqXHR = jqXHR<TResolve>> extends Deferred.Callback3<TResolve | TjqXHR, Ajax.TextStatus, TjqXHR | string> { }
    }

    // #endregion

    // region Callbacks
    // #region Callbacks

    interface CallbacksStatic {
        /**
         * A multi-purpose callbacks list object that provides a powerful way to manage callback lists.
         * @param flags An optional list of space-separated flags that change how the callback list behaves.
         * @see \`{@link https://api.jquery.com/jQuery.Callbacks/ }\`
         * @since 1.7
         */
        // tslint:disable-next-line:ban-types callable-types no-unnecessary-generics
        <T extends Function>(flags?: string): Callbacks<T>;
    }

    // tslint:disable-next-line:ban-types
    interface Callbacks<T extends Function = Function> {
        /**
         * Add a callback or a collection of callbacks to a callback list.
         * @param callback A function, or array of functions, that are to be added to the callback list.
         * @param callbacks A function, or array of functions, that are to be added to the callback list.
         * @see \`{@link https://api.jquery.com/callbacks.add/ }\`
         * @since 1.7
         * @example ​ ````Use callbacks.add() to add new callbacks to a callback list:
```javascript
// A sample logging function to be added to a callbacks list
var foo = function( value ) {
  console.log( "foo: " + value );
};
​
// Another function to also be added to the list
var bar = function( value ) {
  console.log( "bar: " + value );
};
​
var callbacks = $.Callbacks();
​
// Add the function "foo" to the list
callbacks.add( foo );
​
// Fire the items on the list
callbacks.fire( "hello" );
// Outputs: "foo: hello"
​
// Add the function "bar" to the list
callbacks.add( bar );
​
// Fire the items on the list again
callbacks.fire( "world" );
​
// Outputs:
// "foo: world"
// "bar: world"
```
         */
        add(callback: TypeOrArray<T>, ...callbacks: Array<TypeOrArray<T>>): this;
        /**
         * Disable a callback list from doing anything more.
         * @see \`{@link https://api.jquery.com/callbacks.disable/ }\`
         * @since 1.7
         * @example ​ ````Use callbacks.disable() to disable further calls to a callback list:
```javascript
// A sample logging function to be added to a callbacks list
var foo = function( value ) {
  console.log( value );
};
​
var callbacks = $.Callbacks();
​
// Add the above function to the list
callbacks.add( foo );
​
// Fire the items on the list
callbacks.fire( "foo" );
// Outputs: foo
​
// Disable further calls being possible
callbacks.disable();
​
// Attempt to fire with "foobar" as an argument
callbacks.fire( "foobar" );
// foobar isn't output
```
         */
        disable(): this;
        /**
         * Determine if the callbacks list has been disabled.
         * @see \`{@link https://api.jquery.com/callbacks.disabled/ }\`
         * @since 1.7
         * @example ​ ````Use callbacks.disabled() to determine if the callbacks list has been disabled:
```javascript
// A sample logging function to be added to a callbacks list
var foo = function( value ) {
  console.log( "foo:" + value );
};
​
var callbacks = $.Callbacks();
​
// Add the logging function to the callback list
callbacks.add( foo );
​
// Fire the items on the list, passing an argument
callbacks.fire( "hello" );
// Outputs "foo: hello"
​
// Disable the callbacks list
callbacks.disable();
​
// Test the disabled state of the list
console.log ( callbacks.disabled() );
// Outputs: true
```
         */
        disabled(): boolean;
        /**
         * Remove all of the callbacks from a list.
         * @see \`{@link https://api.jquery.com/callbacks.empty/ }\`
         * @since 1.7
         * @example ​ ````Use callbacks.empty() to empty a list of callbacks:
```javascript
// A sample logging function to be added to a callbacks list
var foo = function( value1, value2 ) {
  console.log( "foo: " + value1 + "," + value2 );
};
​
// Another function to also be added to the list
var bar = function( value1, value2 ) {
  console.log( "bar: " + value1 + "," + value2 );
};
​
var callbacks = $.Callbacks();
​
// Add the two functions
callbacks.add( foo );
callbacks.add( bar );
​
// Empty the callbacks list
callbacks.empty();
​
// Check to ensure all callbacks have been removed
console.log( callbacks.has( foo ) );
// false
console.log( callbacks.has( bar ) );
// false
```
         */
        empty(): this;
        /**
         * Call all of the callbacks with the given arguments.
         * @param args The argument or list of arguments to pass back to the callback list.
         * @see \`{@link https://api.jquery.com/callbacks.fire/ }\`
         * @since 1.7
         * @example ​ ````Use callbacks.fire() to invoke the callbacks in a list with any arguments that have been passed:
```javascript
// A sample logging function to be added to a callbacks list
var foo = function( value ) {
  console.log( "foo:" + value );
};
​
var callbacks = $.Callbacks();
​
// Add the function "foo" to the list
callbacks.add( foo );
​
// Fire the items on the list
callbacks.fire( "hello" ); // Outputs: "foo: hello"
callbacks.fire( "world" ); // Outputs: "foo: world"
​
// Add another function to the list
var bar = function( value ){
  console.log( "bar:" + value );
};
​
// Add this function to the list
callbacks.add( bar );
​
// Fire the items on the list again
callbacks.fire( "hello again" );
// Outputs:
// "foo: hello again"
// "bar: hello again"
```
         */
        fire(...args: any[]): this;
        /**
         * Determine if the callbacks have already been called at least once.
         * @see \`{@link https://api.jquery.com/callbacks.fired/ }\`
         * @since 1.7
         * @example ​ ````Use callbacks.fired() to determine if the callbacks in a list have been called at least once:
```javascript
// A sample logging function to be added to a callbacks list
var foo = function( value ) {
  console.log( "foo:" + value );
};
​
var callbacks = $.Callbacks();
​
// Add the function "foo" to the list
callbacks.add( foo );
​
// Fire the items on the list
callbacks.fire( "hello" ); // Outputs: "foo: hello"
callbacks.fire( "world" ); // Outputs: "foo: world"
​
// Test to establish if the callbacks have been called
console.log( callbacks.fired() );
```
         */
        fired(): boolean;
        /**
         * Call all callbacks in a list with the given context and arguments.
         * @param context A reference to the context in which the callbacks in the list should be fired.
         * @param args An argument, or array of arguments, to pass to the callbacks in the list.
         * @see \`{@link https://api.jquery.com/callbacks.fireWith/ }\`
         * @since 1.7
         * @example ​ ````Use callbacks.fireWith() to fire a list of callbacks with a specific context and an array of arguments:
```javascript
// A sample logging function to be added to a callbacks list
var log = function( value1, value2 ) {
  console.log( "Received: " + value1 + "," + value2 );
};
​
var callbacks = $.Callbacks();
​
// Add the log method to the callbacks list
callbacks.add( log );
​
// Fire the callbacks on the list using the context "window"
// and an arguments array
​
callbacks.fireWith( window, [ "foo","bar" ] );
// Outputs: "Received: foo, bar"
```
         */
        fireWith(context: object, args?: ArrayLike<any>): this;
        /**
         * Determine whether or not the list has any callbacks attached. If a callback is provided as an argument, determine whether it is in a list.
         * @param callback The callback to search for.
         * @see \`{@link https://api.jquery.com/callbacks.has/ }\`
         * @since 1.7
         * @example ​ ````Use callbacks.has() to check if a callback list contains a specific callback:
```javascript
// A sample logging function to be added to a callbacks list
var foo = function( value1, value2 ) {
  console.log( "Received: " + value1 + "," + value2 );
};
​
// A second function which will not be added to the list
var bar = function( value1, value2 ) {
  console.log( "foobar" );
};
​
var callbacks = $.Callbacks();
​
// Add the log method to the callbacks list
callbacks.add( foo );
​
// Determine which callbacks are in the list
console.log( callbacks.has( foo ) );
// true
console.log( callbacks.has( bar ) );
// false
```
         */
        has(callback?: T): boolean;
        /**
         * Lock a callback list in its current state.
         * @see \`{@link https://api.jquery.com/callbacks.lock/ }\`
         * @since 1.7
         * @example ​ ````Use callbacks.lock() to lock a callback list to avoid further changes being made to the list state:
```javascript
// A sample logging function to be added to a callbacks list
var foo = function( value ) {
  console.log( "foo:" + value );
};
​
var callbacks = $.Callbacks();
​
// Add the logging function to the callback list
callbacks.add( foo );
​
// Fire the items on the list, passing an argument
callbacks.fire( "hello" );
// Outputs "foo: hello"
​
// Lock the callbacks list
callbacks.lock();
​
// Try firing the items again
callbacks.fire( "world" );
​
// As the list was locked, no items were called,
// so "world" isn't logged
```
         * @example ​ ````Use callbacks.lock() to lock a callback list with &quot;memory,&quot; and then resume using the list:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>callbacks.lock demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
// Simple function for logging results
var log = function( value ) {
  $( "#log" ).append( "<p>" + value + "</p>" );
};
​
// Two sample functions to be added to a callbacks list
var foo = function( value ) {
  log( "foo: " + value );
};
var bar = function( value ) {
  log( "bar: " + value );
};
​
// Create the callbacks object with the "memory" flag
var callbacks = $.Callbacks( "memory" );
​
// Add the foo logging function to the callback list
callbacks.add( foo );
​
// Fire the items on the list, passing an argument
callbacks.fire( "hello" );
// Outputs "foo: hello"
​
// Lock the callbacks list
callbacks.lock();
​
// Try firing the items again
callbacks.fire( "world" );
// As the list was locked, no items were called,
// so "foo: world" isn't logged
​
// Add the foo function to the callback list again
callbacks.add( foo );
​
// Try firing the items again
callbacks.fire( "silentArgument" );
// Outputs "foo: hello" because the argument value was stored in memory
​
// Add the bar function to the callback list
callbacks.add( bar );
​
callbacks.fire( "youHadMeAtHello" );
// Outputs "bar: hello" because the list is still locked,
// and the argument value is still stored in memory
</script>
​
</body>
</html>
```
         */
        lock(): this;
        /**
         * Determine if the callbacks list has been locked.
         * @see \`{@link https://api.jquery.com/callbacks.locked/ }\`
         * @since 1.7
         * @example ​ ````Use callbacks.locked() to determine the lock-state of a callback list:
```javascript
// A sample logging function to be added to a callbacks list
var foo = function( value ) {
  console.log( "foo: " + value );
};
​
var callbacks = $.Callbacks();
​
// Add the logging function to the callback list
callbacks.add( foo );
​
// Fire the items on the list, passing an argument
callbacks.fire( "hello" );
// Outputs "foo: hello"
​
// Lock the callbacks list
callbacks.lock();
​
// Test the lock-state of the list
console.log ( callbacks.locked() );
// true
```
         */
        locked(): boolean;
        /**
         * Remove a callback or a collection of callbacks from a callback list.
         * @param callbacks A function, or array of functions, that are to be removed from the callback list.
         * @see \`{@link https://api.jquery.com/callbacks.remove/ }\`
         * @since 1.7
         * @example ​ ````Use callbacks.remove() to remove callbacks from a callback list:
```javascript
// A sample logging function to be added to a callbacks list
var foo = function( value ) {
  console.log( "foo: " + value );
};
​
var callbacks = $.Callbacks();
​
// Add the function "foo" to the list
callbacks.add( foo );
​
// Fire the items on the list
callbacks.fire( "hello" );
// Outputs: "foo: hello"
​
// Remove "foo" from the callback list
callbacks.remove( foo );
​
// Fire the items on the list again
callbacks.fire( "world" );
​
// Nothing output as "foo" is no longer in the list
```
         */
        remove(...callbacks: T[]): this;
    }

    // #endregion

    // region CSS hooks
    // #region CSS hooks

    // Workaround for TypeScript 2.3 which does not have support for weak types handling.
    type CSSHook<TElement> =
        Partial<_CSSHook<TElement>> & (
            Pick<_CSSHook<TElement>, 'get'> |
            Pick<_CSSHook<TElement>, 'set'>
        );

    interface _CSSHook<TElement> {
        get(elem: TElement, computed: any, extra: any): any;
        set(elem: TElement, value: any): void;
    }

    interface CSSHooks {
        // Set to HTMLElement to minimize breaks but should probably be Element.
        [propertyName: string]: CSSHook<HTMLElement>;
    }

    // #endregion

    // region Deferred
    // #region Deferred

    /**
     * Any object that has a then method.
     */
    interface Thenable<T> extends PromiseLike<T> { }

    // NOTE: This is a private copy of the global Promise interface. It is used by JQuery.PromiseBase to indicate compatibility with other Promise implementations.
    //       The global Promise interface cannot be used directly as it may be modified, as in the case of @types/bluebird-global.
    /**
     * Represents the completion of an asynchronous operation
     */
    interface _Promise<T> {
        readonly [Symbol.toStringTag]: "Promise";
        /**
         * Attaches callbacks for the resolution and/or rejection of the Promise.
         * @param onfulfilled The callback to execute when the Promise is resolved.
         * @param onrejected The callback to execute when the Promise is rejected.
         * @returns A Promise for the completion of which ever callback is executed.
         */
        then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | null,
                                             onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | null): _Promise<TResult1 | TResult2>;
        /**
         * Attaches a callback for only the rejection of the Promise.
         * @param onrejected The callback to execute when the Promise is rejected.
         * @returns A Promise for the completion of the callback.
         */
        catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | null): _Promise<T | TResult>;
    }

    // Type parameter guide
    // --------------------
    // Each type parameter represents a parameter in one of the three possible callbacks.
    //
    // The first letter indicates which position the parameter is in.
    //
    // T = A = 1st position
    // U = B = 2nd position
    // V = C = 3rd position
    // S = R = rest position
    //
    // The second letter indicates which whether it is a [R]esolve, Re[J]ect, or [N]otify value.
    //
    // The third letter indicates whether the value is returned in the [D]one filter, [F]ail filter, or [P]rogress filter.

    /**
     * This object provides a subset of the methods of the Deferred object (then, done, fail, always, pipe, progress, state and promise) to prevent users from changing the state of the Deferred.
     * @see \`{@link https://api.jquery.com/Types/#Promise }\`
     */
    interface PromiseBase<TR, TJ, TN,
        UR, UJ, UN,
        VR, VJ, VN,
        SR, SJ, SN> extends _Promise<TR>, PromiseLike<TR> {
        /**
         * Add handlers to be called when the Deferred object is either resolved or rejected.
         * @param alwaysCallback A function, or array of functions, that is called when the Deferred is resolved or rejected.
         * @param alwaysCallbacks Optional additional functions, or arrays of functions, that are called when the Deferred is resolved or rejected.
         * @see \`{@link https://api.jquery.com/deferred.always/ }\`
         * @since 1.6
         * @example ​ ````Since the jQuery.get() method returns a jqXHR object, which is derived from a Deferred object, we can attach a callback for both success and error using the deferred.always() method.
```javascript
$.get( "test.php" ).always(function() {
  alert( "$.get completed with success or error callback arguments" );
});
```
         */
        always(alwaysCallback: TypeOrArray<Deferred.CallbackBase<TR | TJ, UR | UJ, VR | VJ, SR | SJ>>,
               ...alwaysCallbacks: Array<TypeOrArray<Deferred.CallbackBase<TR | TJ, UR | UJ, VR | VJ, SR | SJ>>>): this;
        /**
         * Add handlers to be called when the Deferred object is resolved.
         * @param doneCallback A function, or array of functions, that are called when the Deferred is resolved.
         * @param doneCallbacks Optional additional functions, or arrays of functions, that are called when the Deferred is resolved.
         * @see \`{@link https://api.jquery.com/deferred.done/ }\`
         * @since 1.5
         * @example ​ ````Since the jQuery.get method returns a jqXHR object, which is derived from a Deferred object, we can attach a success callback using the .done() method.
```javascript
$.get( "test.php" ).done(function() {
  alert( "$.get succeeded" );
});
```
         * @example ​ ````Resolve a Deferred object when the user clicks a button, triggering a number of callback functions:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>deferred.done demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Go</button>
<p>Ready...</p>
​
<script>
// 3 functions to call when the Deferred object is resolved
function fn1() {
  $( "p" ).append( " 1 " );
}
function fn2() {
  $( "p" ).append( " 2 " );
}
function fn3( n ) {
  $( "p" ).append( n + " 3 " + n );
}
​
// Create a deferred object
var dfd = $.Deferred();
​
// Add handlers to be called when dfd is resolved
dfd
// .done() can take any number of functions or arrays of functions
  .done( [ fn1, fn2 ], fn3, [ fn2, fn1 ] )
// We can chain done methods, too
  .done(function( n ) {
    $( "p" ).append( n + " we're done." );
  });
​
// Resolve the Deferred object when the button is clicked
$( "button" ).on( "click", function() {
  dfd.resolve( "and" );
});
</script>
​
</body>
</html>
```
         */
        done(doneCallback: TypeOrArray<Deferred.CallbackBase<TR, UR, VR, SR>>,
             ...doneCallbacks: Array<TypeOrArray<Deferred.CallbackBase<TR, UR, VR, SR>>>): this;
        /**
         * Add handlers to be called when the Deferred object is rejected.
         * @param failCallback A function, or array of functions, that are called when the Deferred is rejected.
         * @param failCallbacks Optional additional functions, or arrays of functions, that are called when the Deferred is rejected.
         * @see \`{@link https://api.jquery.com/deferred.fail/ }\`
         * @since 1.5
         * @example ​ ````Since the jQuery.get method returns a jqXHR object, which is derived from a Deferred, you can attach a success and failure callback using the deferred.done() and deferred.fail() methods.
```javascript
$.get( "test.php" )
  .done(function() {
    alert( "$.get succeeded" );
  })
  .fail(function() {
    alert( "$.get failed!" );
  });
```
         */
        fail(failCallback: TypeOrArray<Deferred.CallbackBase<TJ, UJ, VJ, SJ>>,
             ...failCallbacks: Array<TypeOrArray<Deferred.CallbackBase<TJ, UJ, VJ, SJ>>>): this;
        /**
         * Add handlers to be called when the Deferred object generates progress notifications.
         * @param progressCallback A function, or array of functions, to be called when the Deferred generates progress notifications.
         * @param progressCallbacks Optional additional functions, or arrays of functions, to be called when the Deferred generates
         *                          progress notifications.
         * @see \`{@link https://api.jquery.com/deferred.progress/ }\`
         * @since 1.7
         */
        progress(progressCallback: TypeOrArray<Deferred.CallbackBase<TN, UN, VN, SN>>,
                 ...progressCallbacks: Array<TypeOrArray<Deferred.CallbackBase<TN, UN, VN, SN>>>): this;
        /**
         * Return a Deferred's Promise object.
         * @param target Object onto which the promise methods have to be attached
         * @see \`{@link https://api.jquery.com/deferred.promise/ }\`
         * @since 1.5
         * @example ​ ````Create a Deferred and set two timer-based functions to either resolve or reject the Deferred after a random interval. Whichever one fires first &quot;wins&quot; and will call one of the callbacks. The second timeout has no effect since the Deferred is already complete (in a resolved or rejected state) from the first timeout action. Also set a timer-based progress notification function, and call a progress handler that adds &quot;working...&quot; to the document body.
```javascript
function asyncEvent() {
  var dfd = jQuery.Deferred();
​
  // Resolve after a random interval
  setTimeout(function() {
    dfd.resolve( "hurray" );
  }, Math.floor( 400 + Math.random() * 2000 ) );
​
  // Reject after a random interval
  setTimeout(function() {
    dfd.reject( "sorry" );
  }, Math.floor( 400 + Math.random() * 2000 ) );
​
  // Show a "working..." message every half-second
  setTimeout(function working() {
    if ( dfd.state() === "pending" ) {
      dfd.notify( "working... " );
      setTimeout( working, 500 );
    }
  }, 1 );
​
  // Return the Promise so caller can't change the Deferred
  return dfd.promise();
}
​
// Attach a done, fail, and progress handler for the asyncEvent
$.when( asyncEvent() ).then(
  function( status ) {
    alert( status + ", things are going well" );
  },
  function( status ) {
    alert( status + ", you fail this time" );
  },
  function( status ) {
    $( "body" ).append( status );
  }
);
```
         */
        promise<TTarget extends object>(target: TTarget): this & TTarget;
        /**
         * Return a Deferred's Promise object.
         * @see \`{@link https://api.jquery.com/deferred.promise/ }\`
         * @since 1.5
         * @example ​ ````Use the target argument to promote an existing object to a Promise:
```javascript
// Existing object
var obj = {
    hello: function( name ) {
      alert( "Hello " + name );
    }
  },
  // Create a Deferred
  defer = $.Deferred();
​
// Set object as a promise
defer.promise( obj );
​
// Resolve the deferred
defer.resolve( "John" );
​
// Use the object as a Promise
obj.done(function( name ) {
  obj.hello( name ); // Will alert "Hello John"
}).hello( "Karl" ); // Will alert "Hello Karl"
```
         */
        promise(): this;
        /**
         * Determine the current state of a Deferred object.
         * @see \`{@link https://api.jquery.com/deferred.state/ }\`
         * @since 1.7
         */
        state(): 'pending' | 'resolved' | 'rejected';

        // region pipe
        // #region pipe

        /**
         * Utility method to filter and/or chain Deferreds.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.pipe/ }\`
         * @since 1.6
         * @since 1.7
         * @deprecated ​ Deprecated since 1.8. Use \`{@link then }\`.
         *
         * **Cause**: The `.pipe()` method on a `jQuery.Deferred` object was deprecated as of jQuery 1.8, when the `.then()` method was changed to perform the same function.
         *
         * **Solution**: In most cases it is sufficient to change all occurrences of `.pipe()` to `.then()`. Ensure that you aren't relying on context/state propagation (e.g., using `this`) or synchronous callback invocation, which were dropped from `.then()` for Promises/A+ interoperability as of jQuery 3.0.
         * @example ​ ````Filter resolve value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe(function( value ) {
    return value * 2;
  });
​
defer.resolve( 5 );
filtered.done(function( value ) {
  alert( "Value is ( 2*5 = ) 10: " + value );
});
```
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.pipe(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        pipe<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never,
            ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never,
            ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: (t: TR, u: UR, v: VR, ...s: SR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter: (t: TJ, u: UJ, v: VJ, ...s: SJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<AJF> | AJF,
                progressFilter: (t: TN, u: UN, v: VN, ...s: SN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARD | ARF | ARP, AJD | AJF | AJP, AND | ANF | ANP,
            BRD | BRF | BRP, BJD | BJF | BJP, BND | BNF | BNP,
            CRD | CRF | CRP, CJD | CJF | CJP, CND | CNF | CNP,
            RRD | RRF | RRP, RJD | RJF | RJP, RND | RNF | RNP>;
        /**
         * Utility method to filter and/or chain Deferreds.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.pipe/ }\`
         * @since 1.6
         * @since 1.7
         * @deprecated ​ Deprecated since 1.8. Use \`{@link then }\`.
         *
         * **Cause**: The `.pipe()` method on a `jQuery.Deferred` object was deprecated as of jQuery 1.8, when the `.then()` method was changed to perform the same function.
         *
         * **Solution**: In most cases it is sufficient to change all occurrences of `.pipe()` to `.then()`. Ensure that you aren't relying on context/state propagation (e.g., using `this`) or synchronous callback invocation, which were dropped from `.then()` for Promises/A+ interoperability as of jQuery 3.0.
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.pipe(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        pipe<ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never,
            ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: null,
                failFilter: (t: TJ, u: UJ, v: VJ, ...s: SJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<AJF> | AJF,
                progressFilter: (t: TN, u: UN, v: VN, ...s: SN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARF | ARP, AJF | AJP, ANF | ANP,
            BRF | BRP, BJF | BJP, BNF | BNP,
            CRF | CRP, CJF | CJP, CNF | CNP,
            RRF | RRP, RJF | RJP, RNF | RNP>;
        /**
         * Utility method to filter and/or chain Deferreds.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.pipe/ }\`
         * @since 1.6
         * @since 1.7
         * @deprecated ​ Deprecated since 1.8. Use \`{@link then }\`.
         *
         * **Cause**: The `.pipe()` method on a `jQuery.Deferred` object was deprecated as of jQuery 1.8, when the `.then()` method was changed to perform the same function.
         *
         * **Solution**: In most cases it is sufficient to change all occurrences of `.pipe()` to `.then()`. Ensure that you aren't relying on context/state propagation (e.g., using `this`) or synchronous callback invocation, which were dropped from `.then()` for Promises/A+ interoperability as of jQuery 3.0.
         * @example ​ ````Filter resolve value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe(function( value ) {
    return value * 2;
  });
​
defer.resolve( 5 );
filtered.done(function( value ) {
  alert( "Value is ( 2*5 = ) 10: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.pipe(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        pipe<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never,
            ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: (t: TR, u: UR, v: VR, ...s: SR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter: null,
                progressFilter: (t: TN, u: UN, v: VN, ...s: SN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARD | ARP, AJD | AJP, AND | ANP,
            BRD | BRP, BJD | BJP, BND | BNP,
            CRD | CRP, CJD | CJP, CND | CNP,
            RRD | RRP, RJD | RJP, RND | RNP>;
        /**
         * Utility method to filter and/or chain Deferreds.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.pipe/ }\`
         * @since 1.6
         * @since 1.7
         * @deprecated ​ Deprecated since 1.8. Use \`{@link then }\`.
         *
         * **Cause**: The `.pipe()` method on a `jQuery.Deferred` object was deprecated as of jQuery 1.8, when the `.then()` method was changed to perform the same function.
         *
         * **Solution**: In most cases it is sufficient to change all occurrences of `.pipe()` to `.then()`. Ensure that you aren't relying on context/state propagation (e.g., using `this`) or synchronous callback invocation, which were dropped from `.then()` for Promises/A+ interoperability as of jQuery 3.0.
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.pipe(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        pipe<ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: null,
                failFilter: null,
                progressFilter?: (t: TN, u: UN, v: VN, ...s: SN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARP, AJP, ANP,
            BRP, BJP, BNP,
            CRP, CJP, CNP,
            RRP, RJP, RNP>;
        /**
         * Utility method to filter and/or chain Deferreds.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.pipe/ }\`
         * @since 1.6
         * @since 1.7
         * @deprecated ​ Deprecated since 1.8. Use \`{@link then }\`.
         *
         * **Cause**: The `.pipe()` method on a `jQuery.Deferred` object was deprecated as of jQuery 1.8, when the `.then()` method was changed to perform the same function.
         *
         * **Solution**: In most cases it is sufficient to change all occurrences of `.pipe()` to `.then()`. Ensure that you aren't relying on context/state propagation (e.g., using `this`) or synchronous callback invocation, which were dropped from `.then()` for Promises/A+ interoperability as of jQuery 3.0.
         * @example ​ ````Filter resolve value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe(function( value ) {
    return value * 2;
  });
​
defer.resolve( 5 );
filtered.done(function( value ) {
  alert( "Value is ( 2*5 = ) 10: " + value );
});
```
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.pipe(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        pipe<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never,
            ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never>(
                doneFilter: (t: TR, u: UR, v: VR, ...s: SR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter: (t: TJ, u: UJ, v: VJ, ...s: SJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<AJF> | AJF,
                progressFilter?: null): PromiseBase<ARD | ARF, AJD | AJF, AND | ANF,
            BRD | BRF, BJD | BJF, BND | BNF,
            CRD | CRF, CJD | CJF, CND | CNF,
            RRD | RRF, RJD | RJF, RND | RNF>;
        /**
         * Utility method to filter and/or chain Deferreds.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.pipe/ }\`
         * @since 1.6
         * @since 1.7
         * @deprecated ​ Deprecated since 1.8. Use \`{@link then }\`.
         *
         * **Cause**: The `.pipe()` method on a `jQuery.Deferred` object was deprecated as of jQuery 1.8, when the `.then()` method was changed to perform the same function.
         *
         * **Solution**: In most cases it is sufficient to change all occurrences of `.pipe()` to `.then()`. Ensure that you aren't relying on context/state propagation (e.g., using `this`) or synchronous callback invocation, which were dropped from `.then()` for Promises/A+ interoperability as of jQuery 3.0.
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.pipe(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        pipe<ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never>(
                doneFilter: null,
                failFilter: (t: TJ, u: UJ, v: VJ, ...s: SJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<AJF> | AJF,
                progressFilter?: null): PromiseBase<ARF, AJF, ANF,
            BRF, BJF, BNF,
            CRF, CJF, CNF,
            RRF, RJF, RNF>;
        /**
         * Utility method to filter and/or chain Deferreds.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.pipe/ }\`
         * @since 1.6
         * @since 1.7
         * @deprecated ​ Deprecated since 1.8. Use \`{@link then }\`.
         *
         * **Cause**: The `.pipe()` method on a `jQuery.Deferred` object was deprecated as of jQuery 1.8, when the `.then()` method was changed to perform the same function.
         *
         * **Solution**: In most cases it is sufficient to change all occurrences of `.pipe()` to `.then()`. Ensure that you aren't relying on context/state propagation (e.g., using `this`) or synchronous callback invocation, which were dropped from `.then()` for Promises/A+ interoperability as of jQuery 3.0.
         * @example ​ ````Filter resolve value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe(function( value ) {
    return value * 2;
  });
​
defer.resolve( 5 );
filtered.done(function( value ) {
  alert( "Value is ( 2*5 = ) 10: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.pipe(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        pipe<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never>(
                doneFilter: (t: TR, u: UR, v: VR, ...s: SR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter?: null,
                progressFilter?: null): PromiseBase<ARD, AJD, AND,
            BRD, BJD, BND,
            CRD, CJD, CND,
            RRD, RJD, RND>;

        // #endregion

        // region then
        // #region then

        /**
         * Add handlers to be called when the Deferred object is resolved, rejected, or still in progress.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.then/ }\`
         * @since 1.8
         * @example ​ ````Since the jQuery.get method returns a jqXHR object, which is derived from a Deferred object, we can attach handlers using the .then method.
```javascript
$.get( "test.php" ).then(
  function() {
    alert( "$.get succeeded" );
  }, function() {
    alert( "$.get failed!" );
  }
);
```
         * @example ​ ````Filter the resolve value:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>deferred.then demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Filter Resolve</button>
<p></p>
​
<script>
var filterResolve = function() {
  var defer = $.Deferred(),
    filtered = defer.then(function( value ) {
      return value * 2;
    });
​
  defer.resolve( 5 );
  filtered.done(function( value ) {
    $( "p" ).html( "Value is ( 2*5 = ) 10: " + value );
  });
};
​
$( "button" ).on( "click", filterResolve );
</script>
​
</body>
</html>
```
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.then( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.then(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        then<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never,
            ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never,
            ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: (t: TR, u: UR, v: VR, ...s: SR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter: (t: TJ, u: UJ, v: VJ, ...s: SJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<ARF> | ARF,
                progressFilter: (t: TN, u: UN, v: VN, ...s: SN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARD | ARF | ARP, AJD | AJF | AJP, AND | ANF | ANP,
            BRD | BRF | BRP, BJD | BJF | BJP, BND | BNF | BNP,
            CRD | CRF | CRP, CJD | CJF | CJP, CND | CNF | CNP,
            RRD | RRF | RRP, RJD | RJF | RJP, RND | RNF | RNP>;
        /**
         * Add handlers to be called when the Deferred object is resolved, rejected, or still in progress.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.then/ }\`
         * @since 1.8
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.then( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.then(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        then<ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never,
            ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: null,
                failFilter: (t: TJ, u: UJ, v: VJ, ...s: SJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<ARF> | ARF,
                progressFilter: (t: TN, u: UN, v: VN, ...s: SN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARF | ARP, AJF | AJP, ANF | ANP,
            BRF | BRP, BJF | BJP, BNF | BNP,
            CRF | CRP, CJF | CJP, CNF | CNP,
            RRF | RRP, RJF | RJP, RNF | RNP>;
        /**
         * Add handlers to be called when the Deferred object is resolved, rejected, or still in progress.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.then/ }\`
         * @since 1.8
         * @example ​ ````Filter the resolve value:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>deferred.then demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Filter Resolve</button>
<p></p>
​
<script>
var filterResolve = function() {
  var defer = $.Deferred(),
    filtered = defer.then(function( value ) {
      return value * 2;
    });
​
  defer.resolve( 5 );
  filtered.done(function( value ) {
    $( "p" ).html( "Value is ( 2*5 = ) 10: " + value );
  });
};
​
$( "button" ).on( "click", filterResolve );
</script>
​
</body>
</html>
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.then(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        then<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never,
            ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: (t: TR, u: UR, v: VR, ...s: SR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter: null,
                progressFilter: (t: TN, u: UN, v: VN, ...s: SN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARD | ARP, AJD | AJP, AND | ANP,
            BRD | BRP, BJD | BJP, BND | BNP,
            CRD | CRP, CJD | CJP, CND | CNP,
            RRD | RRP, RJD | RJP, RND | RNP>;
        /**
         * Add handlers to be called when the Deferred object is resolved, rejected, or still in progress.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.then/ }\`
         * @since 1.8
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.then(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        then<ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: null,
                failFilter: null,
                progressFilter?: (t: TN, u: UN, v: VN, ...s: SN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARP, AJP, ANP,
            BRP, BJP, BNP,
            CRP, CJP, CNP,
            RRP, RJP, RNP>;
        /**
         * Add handlers to be called when the Deferred object is resolved, rejected, or still in progress.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.then/ }\`
         * @since 1.8
         * @example ​ ````Since the jQuery.get method returns a jqXHR object, which is derived from a Deferred object, we can attach handlers using the .then method.
```javascript
$.get( "test.php" ).then(
  function() {
    alert( "$.get succeeded" );
  }, function() {
    alert( "$.get failed!" );
  }
);
```
         * @example ​ ````Filter the resolve value:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>deferred.then demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Filter Resolve</button>
<p></p>
​
<script>
var filterResolve = function() {
  var defer = $.Deferred(),
    filtered = defer.then(function( value ) {
      return value * 2;
    });
​
  defer.resolve( 5 );
  filtered.done(function( value ) {
    $( "p" ).html( "Value is ( 2*5 = ) 10: " + value );
  });
};
​
$( "button" ).on( "click", filterResolve );
</script>
​
</body>
</html>
```
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.then( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.then(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        then<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never,
            ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never>(
                doneFilter: (t: TR, u: UR, v: VR, ...s: SR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter: (t: TJ, u: UJ, v: VJ, ...s: SJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<ARF> | ARF,
                progressFilter?: null): PromiseBase<ARD | ARF, AJD | AJF, AND | ANF,
            BRD | BRF, BJD | BJF, BND | BNF,
            CRD | CRF, CJD | CJF, CND | CNF,
            RRD | RRF, RJD | RJF, RND | RNF>;
        /**
         * Add handlers to be called when the Deferred object is resolved, rejected, or still in progress.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.then/ }\`
         * @since 1.8
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.then( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.then(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        then<ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never>(
                doneFilter: null,
                failFilter: (t: TJ, u: UJ, v: VJ, ...s: SJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<ARF> | ARF,
                progressFilter?: null): PromiseBase<ARF, AJF, ANF,
            BRF, BJF, BNF,
            CRF, CJF, CNF,
            RRF, RJF, RNF>;
        /**
         * Add handlers to be called when the Deferred object is resolved, rejected, or still in progress.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.then/ }\`
         * @since 1.8
         * @example ​ ````Filter the resolve value:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>deferred.then demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Filter Resolve</button>
<p></p>
​
<script>
var filterResolve = function() {
  var defer = $.Deferred(),
    filtered = defer.then(function( value ) {
      return value * 2;
    });
​
  defer.resolve( 5 );
  filtered.done(function( value ) {
    $( "p" ).html( "Value is ( 2*5 = ) 10: " + value );
  });
};
​
$( "button" ).on( "click", filterResolve );
</script>
​
</body>
</html>
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.then(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        then<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never>(
                doneFilter: (t: TR, u: UR, v: VR, ...s: SR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter?: null,
                progressFilter?: null): PromiseBase<ARD, AJD, AND,
            BRD, BJD, BND,
            CRD, CJD, CND,
            RRD, RJD, RND>;

        // #endregion

        /**
         * Add handlers to be called when the Deferred object is rejected.
         * @param failFilter A function that is called when the Deferred is rejected.
         * @see \`{@link https://api.jquery.com/deferred.catch/ }\`
         * @since 3.0
         * @example ​ ````Since the jQuery.get method returns a jqXHR object, which is derived from a Deferred object, we can rejection handlers using the .catch method.
```javascript
$.get( "test.php" )
  .then( function() {
    alert( "$.get succeeded" );
  } )
  .catch( function() {
    alert( "$.get failed!" );
  } );
```
         */
        catch<ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never>(
                failFilter?: ((t: TJ, u: UJ, v: VJ, ...s: SJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<ARF> | ARF) | null): PromiseBase<ARF, AJF, ANF,
            BRF, BJF, BNF,
            CRF, CJF, CNF,
            RRF, RJF, RNF>;
    }

    /**
     * This object provides a subset of the methods of the Deferred object (then, done, fail, always, pipe, progress, state and promise) to prevent users from changing the state of the Deferred.
     * @see \`{@link https://api.jquery.com/Types/#Promise }\`
     */
    interface Promise3<TR, TJ, TN,
        UR, UJ, UN,
        VR, VJ, VN> extends PromiseBase<TR, TJ, TN,
        UR, UJ, UN,
        VR, VJ, VN,
        never, never, never> { }

    /**
     * This object provides a subset of the methods of the Deferred object (then, done, fail, always, pipe, progress, state and promise) to prevent users from changing the state of the Deferred.
     * @see \`{@link https://api.jquery.com/Types/#Promise }\`
     */
    interface Promise2<TR, TJ, TN,
        UR, UJ, UN> extends PromiseBase<TR, TJ, TN,
        UR, UJ, UN,
        never, never, never,
        never, never, never> { }

    /**
     * This object provides a subset of the methods of the Deferred object (then, done, fail, always, pipe, progress, state and promise) to prevent users from changing the state of the Deferred.
     * @see \`{@link https://api.jquery.com/Types/#Promise }\`
     */
    interface Promise<TR, TJ = any, TN = any> extends PromiseBase<TR, TJ, TN,
        TR, TJ, TN,
        TR, TJ, TN,
        TR, TJ, TN> { }

    interface DeferredStatic {
        // https://jquery.com/upgrade-guide/3.0/#callback-exit
        exceptionHook: any;
        /**
         * A factory function that returns a chainable utility object with methods to register multiple callbacks into callback queues, invoke callback queues, and relay the success or failure state of any synchronous or asynchronous function.
         * @param beforeStart A function that is called just before the constructor returns.
         * @see \`{@link https://api.jquery.com/jQuery.Deferred/ }\`
         * @since 1.5
         */
        <TR = any, TJ = any, TN = any>(beforeStart?: (this: Deferred<TR, TJ, TN>, deferred: Deferred<TR, TJ, TN>) => void): Deferred<TR, TJ, TN>;
    }

    interface Deferred<TR, TJ = any, TN = any> {
        /**
         * Call the progressCallbacks on a Deferred object with the given args.
         * @param args Optional arguments that are passed to the progressCallbacks.
         * @see \`{@link https://api.jquery.com/deferred.notify/ }\`
         * @since 1.7
         */
        notify(...args: TN[]): this;
        /**
         * Call the progressCallbacks on a Deferred object with the given context and args.
         * @param context Context passed to the progressCallbacks as the this object.
         * @param args An optional array of arguments that are passed to the progressCallbacks.
         * @see \`{@link https://api.jquery.com/deferred.notifyWith/ }\`
         * @since 1.7
         */
        notifyWith(context: object, args?: ArrayLike<TN>): this;
        /**
         * Reject a Deferred object and call any failCallbacks with the given args.
         * @param args Optional arguments that are passed to the failCallbacks.
         * @see \`{@link https://api.jquery.com/deferred.reject/ }\`
         * @since 1.5
         */
        reject(...args: TJ[]): this;
        /**
         * Reject a Deferred object and call any failCallbacks with the given context and args.
         * @param context Context passed to the failCallbacks as the this object.
         * @param args An optional array of arguments that are passed to the failCallbacks.
         * @see \`{@link https://api.jquery.com/deferred.rejectWith/ }\`
         * @since 1.5
         */
        rejectWith(context: object, args?: ArrayLike<TJ>): this;
        /**
         * Resolve a Deferred object and call any doneCallbacks with the given args.
         * @param args Optional arguments that are passed to the doneCallbacks.
         * @see \`{@link https://api.jquery.com/deferred.resolve/ }\`
         * @since 1.5
         */
        resolve(...args: TR[]): this;
        /**
         * Resolve a Deferred object and call any doneCallbacks with the given context and args.
         * @param context Context passed to the doneCallbacks as the this object.
         * @param args An optional array of arguments that are passed to the doneCallbacks.
         * @see \`{@link https://api.jquery.com/deferred.resolveWith/ }\`
         * @since 1.5
         */
        resolveWith(context: object, args?: ArrayLike<TR>): this;

        /**
         * Add handlers to be called when the Deferred object is either resolved or rejected.
         * @param alwaysCallback A function, or array of functions, that is called when the Deferred is resolved or rejected.
         * @param alwaysCallbacks Optional additional functions, or arrays of functions, that are called when the Deferred is resolved or rejected.
         * @see \`{@link https://api.jquery.com/deferred.always/ }\`
         * @since 1.6
         * @example ​ ````Since the jQuery.get() method returns a jqXHR object, which is derived from a Deferred object, we can attach a callback for both success and error using the deferred.always() method.
```javascript
$.get( "test.php" ).always(function() {
  alert( "$.get completed with success or error callback arguments" );
});
```
         */
        always(alwaysCallback: TypeOrArray<Deferred.Callback<TR | TJ>>,
               ...alwaysCallbacks: Array<TypeOrArray<Deferred.Callback<TR | TJ>>>): this;
        /**
         * Add handlers to be called when the Deferred object is resolved.
         * @param doneCallback A function, or array of functions, that are called when the Deferred is resolved.
         * @param doneCallbacks Optional additional functions, or arrays of functions, that are called when the Deferred is resolved.
         * @see \`{@link https://api.jquery.com/deferred.done/ }\`
         * @since 1.5
         * @example ​ ````Since the jQuery.get method returns a jqXHR object, which is derived from a Deferred object, we can attach a success callback using the .done() method.
```javascript
$.get( "test.php" ).done(function() {
  alert( "$.get succeeded" );
});
```
         * @example ​ ````Resolve a Deferred object when the user clicks a button, triggering a number of callback functions:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>deferred.done demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Go</button>
<p>Ready...</p>
​
<script>
// 3 functions to call when the Deferred object is resolved
function fn1() {
  $( "p" ).append( " 1 " );
}
function fn2() {
  $( "p" ).append( " 2 " );
}
function fn3( n ) {
  $( "p" ).append( n + " 3 " + n );
}
​
// Create a deferred object
var dfd = $.Deferred();
​
// Add handlers to be called when dfd is resolved
dfd
// .done() can take any number of functions or arrays of functions
  .done( [ fn1, fn2 ], fn3, [ fn2, fn1 ] )
// We can chain done methods, too
  .done(function( n ) {
    $( "p" ).append( n + " we're done." );
  });
​
// Resolve the Deferred object when the button is clicked
$( "button" ).on( "click", function() {
  dfd.resolve( "and" );
});
</script>
​
</body>
</html>
```
         */
        done(doneCallback: TypeOrArray<Deferred.Callback<TR>>,
             ...doneCallbacks: Array<TypeOrArray<Deferred.Callback<TR>>>): this;
        /**
         * Add handlers to be called when the Deferred object is rejected.
         * @param failCallback A function, or array of functions, that are called when the Deferred is rejected.
         * @param failCallbacks Optional additional functions, or arrays of functions, that are called when the Deferred is rejected.
         * @see \`{@link https://api.jquery.com/deferred.fail/ }\`
         * @since 1.5
         * @example ​ ````Since the jQuery.get method returns a jqXHR object, which is derived from a Deferred, you can attach a success and failure callback using the deferred.done() and deferred.fail() methods.
```javascript
$.get( "test.php" )
  .done(function() {
    alert( "$.get succeeded" );
  })
  .fail(function() {
    alert( "$.get failed!" );
  });
```
         */
        fail(failCallback: TypeOrArray<Deferred.Callback<TJ>>,
             ...failCallbacks: Array<TypeOrArray<Deferred.Callback<TJ>>>): this;
        /**
         * Add handlers to be called when the Deferred object generates progress notifications.
         * @param progressCallback A function, or array of functions, to be called when the Deferred generates progress notifications.
         * @param progressCallbacks Optional additional functions, or arrays of functions, to be called when the Deferred generates
         *                          progress notifications.
         * @see \`{@link https://api.jquery.com/deferred.progress/ }\`
         * @since 1.7
         */
        progress(progressCallback: TypeOrArray<Deferred.Callback<TN>>,
                 ...progressCallbacks: Array<TypeOrArray<Deferred.Callback<TN>>>): this;
        /**
         * Return a Deferred's Promise object.
         * @param target Object onto which the promise methods have to be attached
         * @see \`{@link https://api.jquery.com/deferred.promise/ }\`
         * @since 1.5
         * @example ​ ````Use the target argument to promote an existing object to a Promise:
```javascript
// Existing object
var obj = {
    hello: function( name ) {
      alert( "Hello " + name );
    }
  },
  // Create a Deferred
  defer = $.Deferred();
​
// Set object as a promise
defer.promise( obj );
​
// Resolve the deferred
defer.resolve( "John" );
​
// Use the object as a Promise
obj.done(function( name ) {
  obj.hello( name ); // Will alert "Hello John"
}).hello( "Karl" ); // Will alert "Hello Karl"
```
         */
        promise<TTarget extends object>(target: TTarget): Promise<TR, TJ, TN> & TTarget;
        /**
         * Return a Deferred's Promise object.
         * @see \`{@link https://api.jquery.com/deferred.promise/ }\`
         * @since 1.5
         * @example ​ ````Create a Deferred and set two timer-based functions to either resolve or reject the Deferred after a random interval. Whichever one fires first &quot;wins&quot; and will call one of the callbacks. The second timeout has no effect since the Deferred is already complete (in a resolved or rejected state) from the first timeout action. Also set a timer-based progress notification function, and call a progress handler that adds &quot;working...&quot; to the document body.
```javascript
function asyncEvent() {
  var dfd = jQuery.Deferred();
​
  // Resolve after a random interval
  setTimeout(function() {
    dfd.resolve( "hurray" );
  }, Math.floor( 400 + Math.random() * 2000 ) );
​
  // Reject after a random interval
  setTimeout(function() {
    dfd.reject( "sorry" );
  }, Math.floor( 400 + Math.random() * 2000 ) );
​
  // Show a "working..." message every half-second
  setTimeout(function working() {
    if ( dfd.state() === "pending" ) {
      dfd.notify( "working... " );
      setTimeout( working, 500 );
    }
  }, 1 );
​
  // Return the Promise so caller can't change the Deferred
  return dfd.promise();
}
​
// Attach a done, fail, and progress handler for the asyncEvent
$.when( asyncEvent() ).then(
  function( status ) {
    alert( status + ", things are going well" );
  },
  function( status ) {
    alert( status + ", you fail this time" );
  },
  function( status ) {
    $( "body" ).append( status );
  }
);
```
         */
        promise(): Promise<TR, TJ, TN>;
        /**
         * Determine the current state of a Deferred object.
         * @see \`{@link https://api.jquery.com/deferred.state/ }\`
         * @since 1.7
         */
        state(): 'pending' | 'resolved' | 'rejected';

        // region pipe
        // #region pipe

        /**
         * Utility method to filter and/or chain Deferreds.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.pipe/ }\`
         * @since 1.6
         * @since 1.7
         * @deprecated ​ Deprecated since 1.8. Use \`{@link then }\`.
         *
         * **Cause**: The `.pipe()` method on a `jQuery.Deferred` object was deprecated as of jQuery 1.8, when the `.then()` method was changed to perform the same function.
         *
         * **Solution**: In most cases it is sufficient to change all occurrences of `.pipe()` to `.then()`. Ensure that you aren't relying on context/state propagation (e.g., using `this`) or synchronous callback invocation, which were dropped from `.then()` for Promises/A+ interoperability as of jQuery 3.0.
         * @example ​ ````Filter resolve value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe(function( value ) {
    return value * 2;
  });
​
defer.resolve( 5 );
filtered.done(function( value ) {
  alert( "Value is ( 2*5 = ) 10: " + value );
});
```
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.pipe(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        pipe<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never,
            ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never,
            ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: (...t: TR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter: (...t: TJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<AJF> | AJF,
                progressFilter: (...t: TN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARD | ARF | ARP, AJD | AJF | AJP, AND | ANF | ANP,
            BRD | BRF | BRP, BJD | BJF | BJP, BND | BNF | BNP,
            CRD | CRF | CRP, CJD | CJF | CJP, CND | CNF | CNP,
            RRD | RRF | RRP, RJD | RJF | RJP, RND | RNF | RNP>;
        /**
         * Utility method to filter and/or chain Deferreds.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.pipe/ }\`
         * @since 1.6
         * @since 1.7
         * @deprecated ​ Deprecated since 1.8. Use \`{@link then }\`.
         *
         * **Cause**: The `.pipe()` method on a `jQuery.Deferred` object was deprecated as of jQuery 1.8, when the `.then()` method was changed to perform the same function.
         *
         * **Solution**: In most cases it is sufficient to change all occurrences of `.pipe()` to `.then()`. Ensure that you aren't relying on context/state propagation (e.g., using `this`) or synchronous callback invocation, which were dropped from `.then()` for Promises/A+ interoperability as of jQuery 3.0.
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.pipe(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        pipe<ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never,
            ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: null,
                failFilter: (...t: TJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<AJF> | AJF,
                progressFilter: (...t: TN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARF | ARP, AJF | AJP, ANF | ANP,
            BRF | BRP, BJF | BJP, BNF | BNP,
            CRF | CRP, CJF | CJP, CNF | CNP,
            RRF | RRP, RJF | RJP, RNF | RNP>;
        /**
         * Utility method to filter and/or chain Deferreds.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.pipe/ }\`
         * @since 1.6
         * @since 1.7
         * @deprecated ​ Deprecated since 1.8. Use \`{@link then }\`.
         *
         * **Cause**: The `.pipe()` method on a `jQuery.Deferred` object was deprecated as of jQuery 1.8, when the `.then()` method was changed to perform the same function.
         *
         * **Solution**: In most cases it is sufficient to change all occurrences of `.pipe()` to `.then()`. Ensure that you aren't relying on context/state propagation (e.g., using `this`) or synchronous callback invocation, which were dropped from `.then()` for Promises/A+ interoperability as of jQuery 3.0.
         * @example ​ ````Filter resolve value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe(function( value ) {
    return value * 2;
  });
​
defer.resolve( 5 );
filtered.done(function( value ) {
  alert( "Value is ( 2*5 = ) 10: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.pipe(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        pipe<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never,
            ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: (...t: TR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter: null,
                progressFilter: (...t: TN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARD | ARP, AJD | AJP, AND | ANP,
            BRD | BRP, BJD | BJP, BND | BNP,
            CRD | CRP, CJD | CJP, CND | CNP,
            RRD | RRP, RJD | RJP, RND | RNP>;
        /**
         * Utility method to filter and/or chain Deferreds.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.pipe/ }\`
         * @since 1.6
         * @since 1.7
         * @deprecated ​ Deprecated since 1.8. Use \`{@link then }\`.
         *
         * **Cause**: The `.pipe()` method on a `jQuery.Deferred` object was deprecated as of jQuery 1.8, when the `.then()` method was changed to perform the same function.
         *
         * **Solution**: In most cases it is sufficient to change all occurrences of `.pipe()` to `.then()`. Ensure that you aren't relying on context/state propagation (e.g., using `this`) or synchronous callback invocation, which were dropped from `.then()` for Promises/A+ interoperability as of jQuery 3.0.
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.pipe(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        pipe<ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: null,
                failFilter: null,
                progressFilter?: (...t: TN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARP, AJP, ANP,
            BRP, BJP, BNP,
            CRP, CJP, CNP,
            RRP, RJP, RNP>;
        /**
         * Utility method to filter and/or chain Deferreds.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.pipe/ }\`
         * @since 1.6
         * @since 1.7
         * @deprecated ​ Deprecated since 1.8. Use \`{@link then }\`.
         *
         * **Cause**: The `.pipe()` method on a `jQuery.Deferred` object was deprecated as of jQuery 1.8, when the `.then()` method was changed to perform the same function.
         *
         * **Solution**: In most cases it is sufficient to change all occurrences of `.pipe()` to `.then()`. Ensure that you aren't relying on context/state propagation (e.g., using `this`) or synchronous callback invocation, which were dropped from `.then()` for Promises/A+ interoperability as of jQuery 3.0.
         * @example ​ ````Filter resolve value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe(function( value ) {
    return value * 2;
  });
​
defer.resolve( 5 );
filtered.done(function( value ) {
  alert( "Value is ( 2*5 = ) 10: " + value );
});
```
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.pipe(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        pipe<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never,
            ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never>(
                doneFilter: (...t: TR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter: (...t: TJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<AJF> | AJF,
                progressFilter?: null): PromiseBase<ARD | ARF, AJD | AJF, AND | ANF,
            BRD | BRF, BJD | BJF, BND | BNF,
            CRD | CRF, CJD | CJF, CND | CNF,
            RRD | RRF, RJD | RJF, RND | RNF>;
        /**
         * Utility method to filter and/or chain Deferreds.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.pipe/ }\`
         * @since 1.6
         * @since 1.7
         * @deprecated ​ Deprecated since 1.8. Use \`{@link then }\`.
         *
         * **Cause**: The `.pipe()` method on a `jQuery.Deferred` object was deprecated as of jQuery 1.8, when the `.then()` method was changed to perform the same function.
         *
         * **Solution**: In most cases it is sufficient to change all occurrences of `.pipe()` to `.then()`. Ensure that you aren't relying on context/state propagation (e.g., using `this`) or synchronous callback invocation, which were dropped from `.then()` for Promises/A+ interoperability as of jQuery 3.0.
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.pipe(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        pipe<ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never>(
                doneFilter: null,
                failFilter: (...t: TJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<AJF> | AJF,
                progressFilter?: null): PromiseBase<ARF, AJF, ANF,
            BRF, BJF, BNF,
            CRF, CJF, CNF,
            RRF, RJF, RNF>;
        /**
         * Utility method to filter and/or chain Deferreds.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.pipe/ }\`
         * @since 1.6
         * @since 1.7
         * @deprecated ​ Deprecated since 1.8. Use \`{@link then }\`.
         *
         * **Cause**: The `.pipe()` method on a `jQuery.Deferred` object was deprecated as of jQuery 1.8, when the `.then()` method was changed to perform the same function.
         *
         * **Solution**: In most cases it is sufficient to change all occurrences of `.pipe()` to `.then()`. Ensure that you aren't relying on context/state propagation (e.g., using `this`) or synchronous callback invocation, which were dropped from `.then()` for Promises/A+ interoperability as of jQuery 3.0.
         * @example ​ ````Filter resolve value:
```javascript
var defer = $.Deferred(),
  filtered = defer.pipe(function( value ) {
    return value * 2;
  });
​
defer.resolve( 5 );
filtered.done(function( value ) {
  alert( "Value is ( 2*5 = ) 10: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.pipe(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        pipe<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never>(
                doneFilter: (...t: TR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter?: null,
                progressFilter?: null): PromiseBase<ARD, AJD, AND,
            BRD, BJD, BND,
            CRD, CJD, CND,
            RRD, RJD, RND>;

        // #endregion

        // region then
        // #region then

        /**
         * Add handlers to be called when the Deferred object is resolved, rejected, or still in progress.
         * @param doneFilter A function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.then/ }\`
         * @since 1.8
         * @example ​ ````Since the jQuery.get method returns a jqXHR object, which is derived from a Deferred object, we can attach handlers using the .then method.
```javascript
$.get( "test.php" ).then(
  function() {
    alert( "$.get succeeded" );
  }, function() {
    alert( "$.get failed!" );
  }
);
```
         * @example ​ ````Filter the resolve value:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>deferred.then demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Filter Resolve</button>
<p></p>
​
<script>
var filterResolve = function() {
  var defer = $.Deferred(),
    filtered = defer.then(function( value ) {
      return value * 2;
    });
​
  defer.resolve( 5 );
  filtered.done(function( value ) {
    $( "p" ).html( "Value is ( 2*5 = ) 10: " + value );
  });
};
​
$( "button" ).on( "click", filterResolve );
</script>
​
</body>
</html>
```
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.then( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.then(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        then<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never,
            ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never,
            ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: (...t: TR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter: (...t: TJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<ARF> | ARF,
                progressFilter: (...t: TN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARD | ARF | ARP, AJD | AJF | AJP, AND | ANF | ANP,
            BRD | BRF | BRP, BJD | BJF | BJP, BND | BNF | BNP,
            CRD | CRF | CRP, CJD | CJF | CJP, CND | CNF | CNP,
            RRD | RRF | RRP, RJD | RJF | RJP, RND | RNF | RNP>;
        /**
         * Add handlers to be called when the Deferred object is resolved, rejected, or still in progress.
         * @param doneFilter A function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.then/ }\`
         * @since 1.8
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.then( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.then(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        then<ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never,
            ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: null,
                failFilter: (...t: TJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<ARF> | ARF,
                progressFilter: (...t: TN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARF | ARP, AJF | AJP, ANF | ANP,
            BRF | BRP, BJF | BJP, BNF | BNP,
            CRF | CRP, CJF | CJP, CNF | CNP,
            RRF | RRP, RJF | RJP, RNF | RNP>;
        /**
         * Add handlers to be called when the Deferred object is resolved, rejected, or still in progress.
         * @param doneFilter A function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.then/ }\`
         * @since 1.8
         * @example ​ ````Filter the resolve value:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>deferred.then demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Filter Resolve</button>
<p></p>
​
<script>
var filterResolve = function() {
  var defer = $.Deferred(),
    filtered = defer.then(function( value ) {
      return value * 2;
    });
​
  defer.resolve( 5 );
  filtered.done(function( value ) {
    $( "p" ).html( "Value is ( 2*5 = ) 10: " + value );
  });
};
​
$( "button" ).on( "click", filterResolve );
</script>
​
</body>
</html>
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.then(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        then<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never,
            ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: (...t: TR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter: null,
                progressFilter: (...t: TN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARD | ARP, AJD | AJP, AND | ANP,
            BRD | BRP, BJD | BJP, BND | BNP,
            CRD | CRP, CJD | CJP, CND | CNP,
            RRD | RRP, RJD | RJP, RND | RNP>;
        /**
         * Add handlers to be called when the Deferred object is resolved, rejected, or still in progress.
         * @param doneFilter A function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.then/ }\`
         * @since 1.8
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.then(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        then<ARP = never, AJP = never, ANP = never,
            BRP = never, BJP = never, BNP = never,
            CRP = never, CJP = never, CNP = never,
            RRP = never, RJP = never, RNP = never>(
                doneFilter: null,
                failFilter: null,
                progressFilter?: (...t: TN[]) => PromiseBase<ARP, AJP, ANP,
                    BRP, BJP, BNP,
                    CRP, CJP, CNP,
                    RRP, RJP, RNP> | Thenable<ANP> | ANP): PromiseBase<ARP, AJP, ANP,
            BRP, BJP, BNP,
            CRP, CJP, CNP,
            RRP, RJP, RNP>;
        /**
         * Add handlers to be called when the Deferred object is resolved, rejected, or still in progress.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.then/ }\`
         * @since 1.8
         * @example ​ ````Since the jQuery.get method returns a jqXHR object, which is derived from a Deferred object, we can attach handlers using the .then method.
```javascript
$.get( "test.php" ).then(
  function() {
    alert( "$.get succeeded" );
  }, function() {
    alert( "$.get failed!" );
  }
);
```
         * @example ​ ````Filter the resolve value:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>deferred.then demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Filter Resolve</button>
<p></p>
​
<script>
var filterResolve = function() {
  var defer = $.Deferred(),
    filtered = defer.then(function( value ) {
      return value * 2;
    });
​
  defer.resolve( 5 );
  filtered.done(function( value ) {
    $( "p" ).html( "Value is ( 2*5 = ) 10: " + value );
  });
};
​
$( "button" ).on( "click", filterResolve );
</script>
​
</body>
</html>
```
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.then( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.then(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        then<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never,
            ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never>(
                doneFilter: (...t: TR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter: (...t: TJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<ARF> | ARF,
                progressFilter?: null): PromiseBase<ARD | ARF, AJD | AJF, AND | ANF,
            BRD | BRF, BJD | BJF, BND | BNF,
            CRD | CRF, CJD | CJF, CND | CNF,
            RRD | RRF, RJD | RJF, RND | RNF>;
        /**
         * Add handlers to be called when the Deferred object is resolved, rejected, or still in progress.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.then/ }\`
         * @since 1.8
         * @example ​ ````Filter reject value:
```javascript
var defer = $.Deferred(),
  filtered = defer.then( null, function( value ) {
    return value * 3;
  });
​
defer.reject( 6 );
filtered.fail(function( value ) {
  alert( "Value is ( 3*6 = ) 18: " + value );
});
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.then(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        then<ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never>(
                doneFilter: null,
                failFilter: (...t: TJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<ARF> | ARF,
                progressFilter?: null): PromiseBase<ARF, AJF, ANF,
            BRF, BJF, BNF,
            CRF, CJF, CNF,
            RRF, RJF, RNF>;
        /**
         * Add handlers to be called when the Deferred object is resolved, rejected, or still in progress.
         * @param doneFilter An optional function that is called when the Deferred is resolved.
         * @param failFilter An optional function that is called when the Deferred is rejected.
         * @param progressFilter An optional function that is called when progress notifications are sent to the Deferred.
         * @see \`{@link https://api.jquery.com/deferred.then/ }\`
         * @since 1.8
         * @example ​ ````Filter the resolve value:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>deferred.then demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>Filter Resolve</button>
<p></p>
​
<script>
var filterResolve = function() {
  var defer = $.Deferred(),
    filtered = defer.then(function( value ) {
      return value * 2;
    });
​
  defer.resolve( 5 );
  filtered.done(function( value ) {
    $( "p" ).html( "Value is ( 2*5 = ) 10: " + value );
  });
};
​
$( "button" ).on( "click", filterResolve );
</script>
​
</body>
</html>
```
         * @example ​ ````Chain tasks:
```javascript
var request = $.ajax( url, { dataType: "json" } ),
  chained = request.then(function( data ) {
    return $.ajax( url2, { data: { user: data.userId } } );
  });
​
chained.done(function( data ) {
  // data retrieved from url2 as provided by the first request
});
```
         */
        then<ARD = never, AJD = never, AND = never,
            BRD = never, BJD = never, BND = never,
            CRD = never, CJD = never, CND = never,
            RRD = never, RJD = never, RND = never>(
                doneFilter: (...t: TR[]) => PromiseBase<ARD, AJD, AND,
                    BRD, BJD, BND,
                    CRD, CJD, CND,
                    RRD, RJD, RND> | Thenable<ARD> | ARD,
                failFilter?: null,
                progressFilter?: null): PromiseBase<ARD, AJD, AND,
            BRD, BJD, BND,
            CRD, CJD, CND,
            RRD, RJD, RND>;

        // #endregion

        /**
         * Add handlers to be called when the Deferred object is rejected.
         * @param failFilter A function that is called when the Deferred is rejected.
         * @see \`{@link https://api.jquery.com/deferred.catch/ }\`
         * @since 3.0
         * @example ​ ````Since the jQuery.get method returns a jqXHR object, which is derived from a Deferred object, we can rejection handlers using the .catch method.
```javascript
$.get( "test.php" )
  .then( function() {
    alert( "$.get succeeded" );
  } )
  .catch( function() {
    alert( "$.get failed!" );
  } );
```
         */
        catch<ARF = never, AJF = never, ANF = never,
            BRF = never, BJF = never, BNF = never,
            CRF = never, CJF = never, CNF = never,
            RRF = never, RJF = never, RNF = never>(
                failFilter?: ((...t: TJ[]) => PromiseBase<ARF, AJF, ANF,
                    BRF, BJF, BNF,
                    CRF, CJF, CNF,
                    RRF, RJF, RNF> | Thenable<ARF> | ARF) | null): PromiseBase<ARF, AJF, ANF,
            BRF, BJF, BNF,
            CRF, CJF, CNF,
            RRF, RJF, RNF>;
    }

    namespace Deferred {
        type CallbackBase<T, U, V, R> = (t: T, u: U, v: V, ...r: R[]) => void;

        interface Callback3<T, U, V> extends CallbackBase<T, U, V, never> { }

        type Callback<T> = (...args: T[]) => void;

        /**
         * @deprecated ​ Deprecated. Use \`{@link Callback }\`.
         */
        interface DoneCallback<TResolve> extends Callback<TResolve> { }

        /**
         * @deprecated ​ Deprecated. Use \`{@link Callback }\`.
         */
        interface FailCallback<TReject> extends Callback<TReject> { }

        /**
         * @deprecated ​ Deprecated. Use \`{@link Callback }\`.
         */
        interface AlwaysCallback<TResolve, TReject> extends Callback<TResolve | TReject> { }

        /**
         * @deprecated ​ Deprecated. Use \`{@link Callback }\`.
         */
        interface ProgressCallback<TNotify> extends Callback<TNotify> { }
    }

    // #endregion

    // region Effects
    // #region Effects

    type Duration = number | 'fast' | 'slow';

    /**
     * @see \`{@link https://api.jquery.com/animate/#animate-properties-options }\`
     */
    interface EffectsOptions<TElement> extends PlainObject {
        /**
         * A function to be called when the animation on an element completes or stops without completing (its Promise object is either resolved or rejected).
         */
        always?(this: TElement, animation: Animation<TElement>, jumpedToEnd: boolean): void;
        /**
         * A function that is called once the animation on an element is complete.
         */
        complete?(this: TElement): void;
        /**
         * A function to be called when the animation on an element completes (its Promise object is resolved).
         */
        done?(this: TElement, animation: Animation<TElement>, jumpedToEnd: boolean): void;
        /**
         * A string or number determining how long the animation will run.
         */
        duration?: Duration;
        /**
         * A string indicating which easing function to use for the transition.
         */
        easing?: string;
        /**
         * A function to be called when the animation on an element fails to complete (its Promise object is rejected).
         */
        fail?(this: TElement, animation: Animation<TElement>, jumpedToEnd: boolean): void;
        /**
         * A function to be called after each step of the animation, only once per animated element regardless of the number of animated properties.
         */
        progress?(this: TElement, animation: Animation<TElement>, progress: number, remainingMs: number): void;
        /**
         * A Boolean indicating whether to place the animation in the effects queue. If false, the animation will begin immediately. As of jQuery 1.7, the queue option can also accept a string, in which case the animation is added to the queue represented by that string. When a custom queue name is used the animation does not automatically start; you must call .dequeue("queuename") to start it.
         */
        queue?: boolean | string;
        /**
         * An object containing one or more of the CSS properties defined by the properties argument and their corresponding easing functions.
         */
        specialEasing?: PlainObject<string>;
        /**
         * A function to call when the animation on an element begins.
         */
        start?(this: TElement, animation: Animation<TElement>): void;
        /**
         * A function to be called for each animated property of each animated element. This function provides an opportunity to modify the Tween object to change the value of the property before it is set.
         */
        step?(this: TElement, now: number, tween: Tween<TElement>): void;
    }

    // region Animation
    // #region Animation

    /**
     * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#animation-factory }\`
     * @since 1.8
     */
    interface AnimationStatic {
        /**
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#animation-factory }\`
         * @since 1.8
         */
        <TElement>(element: TElement, props: PlainObject, opts: EffectsOptions<TElement>): Animation<TElement>;
        /**
         * During the initial setup, `jQuery.Animation` will call any callbacks that have been registered through `jQuery.Animation.prefilter( function( element, props, opts ) )`.
         * @param callback The prefilter will have `this` set to an animation object, and you can modify any of the `props` or
         *                 `opts` however you need. The prefilter _may_ return its own promise which also implements `stop()`,
         *                 in which case, processing of prefilters stops. If the prefilter is not trying to override the animation
         *                 entirely, it should return `undefined` or some other falsy value.
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#prefilters }\`
         * @since 1.8
         */
        prefilter<TElement>(
            callback: (this: Animation<TElement>, element: TElement, props: PlainObject, opts: EffectsOptions<TElement>) => Animation<TElement> | _Falsy | void,
            prepend?: boolean
        ): void;
        /**
         * A "Tweener" is a function responsible for creating a tween object, and you might want to override these if you want to implement complex values ( like a clip/transform array matrix ) in a single property.
         *
         * You can override the default process for creating a tween in order to provide your own tween object by using `jQuery.Animation.tweener( props, callback( prop, value ) )`.
         * @param props A space separated list of properties to be passed to your tweener, or `"*"` if it should be called
         *              for all properties.
         * @param callback The callback will be called with `this` being an `Animation` object. The tweener function will
         *                 generally start with `var tween = this.createTween( prop, value );`, but doesn't nessecarily need to
         *                 use the `jQuery.Tween()` factory.
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tweeners }\`
         * @since 1.8
         */
        tweener(props: string, callback: Tweener<any>): void;
    }

    /**
     * The promise will be resolved when the animation reaches its end, and rejected when terminated early. The context of callbacks attached to the promise will be the element, and the arguments will be the `Animation` object and a boolean `jumpedToEnd` which when true means the animation was stopped with `gotoEnd`, when `undefined` the animation completed naturally.
     * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#animation-factory }\`
     * @since 1.8
     */
    interface Animation<TElement> extends Promise3<
        Animation<TElement>, Animation<TElement>, Animation<TElement>,
        true | undefined, false, number,
        never, never, number
    > {
        /**
         * The duration specified in ms
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#animation-factory }\`
         * @since 1.8
         */
        duration: number;
        /**
         * The element being animatied
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#animation-factory }\`
         * @since 1.8
         */
        elem: TElement;
        /**
         * The final value of each property animating
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#animation-factory }\`
         * @since 1.8
         */
        props: PlainObject;
        /**
         * The animation options
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#animation-factory }\`
         * @since 1.8
         */
        opts: EffectsOptions<TElement>;
        /**
         * The original properties before being filtered
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#animation-factory }\`
         * @since 1.8
         */
        originalProps: PlainObject;
        /**
         * The original options before being filtered
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#animation-factory }\`
         * @since 1.8
         */
        originalOpts: EffectsOptions<TElement>;
        /**
         * The numeric value of `new Date()` when the animation began
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#animation-factory }\`
         * @since 1.8
         */
        startTime: number;
        /**
         * The animations tweens.
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#animation-factory }\`
         * @since 1.8
         */
        tweens: Array<Tween<TElement>>;
        /**
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#animation-factory }\`
         * @since 1.8
         */
        createTween(propName: string, finalValue: number): Tween<TElement>;
        /**
         * Stops the animation early, optionally going to the end.
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#animation-factory }\`
         * @since 1.8
         */
        stop(gotoEnd: boolean): this;
    }

    /**
     * A "Tweener" is a function responsible for creating a tween object, and you might want to override these if you want to implement complex values ( like a clip/transform array matrix ) in a single property.
     * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tweeners }\`
     * @since 1.8
     */
    type Tweener<TElement> = (this: Animation<TElement>, propName: string, finalValue: number) => Tween<TElement>;

    /**
     * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tweens }\`
     * @since 1.8
     */
    interface TweenStatic {
        /**
         * `jQuery.Tween.propHooks[ prop ]` is a hook point that replaces `jQuery.fx.step[ prop ]` (which is being deprecated.) These hooks are used by the tween to get and set values on elements.
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tween-hooks }\`
         * @since 1.8
         * @example
```javascript
jQuery.Tween.propHooks[ property ] = {
    get: function( tween ) {
         // get tween.prop from tween.elem and return it
    },
    set: function( tween ) {
         // set tween.prop on tween.elem to tween.now + tween.unit
    }
}
```
         */
        propHooks: PropHooks;
        /**
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tweens }\`
         * @since 1.8
         */
        <TElement>(elem: TElement, options: EffectsOptions<TElement>, prop: string, end: number, easing?: string, unit?: string): Tween<TElement>;
    }

    /**
     * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tweens }\`
     * @since 1.8
     */
    // This should be a class but doesn't work correctly under the JQuery namespace. Tween should be an inner class of jQuery.
    interface Tween<TElement> {
        /**
         * The easing used
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tweens }\`
         * @since 1.8
         */
        easing: string;
        /**
         * The element being animated
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tweens }\`
         * @since 1.8
         */
        elem: TElement;
        /**
         * The ending value of the tween
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tweens }\`
         * @since 1.8
         */
        end: number;
        /**
         * The current value of the tween
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tweens }\`
         * @since 1.8
         */
        now: number;
        /**
         * A reference to the animation options
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tweens }\`
         * @since 1.8
         */
        options: EffectsOptions<TElement>;
        // Undocumented. Is this intended to be public?
        pos?: number;
        /**
         * The property being animated
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tweens }\`
         * @since 1.8
         */
        prop: string;
        /**
         * The starting value of the tween
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tweens }\`
         * @since 1.8
         */
        start: number;
        /**
         * The CSS unit for the tween
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tweens }\`
         * @since 1.8
         */
        unit: string;
        /**
         * Reads the current value for property from the element
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tweens }\`
         * @since 1.8
         */
        cur(): any;
        /**
         * Updates the value for the property on the animated elemd.
         * @param progress A number from 0 to 1.
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tweens }\`
         * @since 1.8
         */
        run(progress: number): this;
    }

    /**
     * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tween-hooks }\`
     * @since 1.8
     */
    // Workaround for TypeScript 2.3 which does not have support for weak types handling.
    type PropHook<TElement> = {
        /**
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tween-hooks }\`
         * @since 1.8
         */
        get(tween: Tween<TElement>): any;
    } | {
        /**
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tween-hooks }\`
         * @since 1.8
         */
        set(tween: Tween<TElement>): void;
    } | {
        [key: string]: never;
    };

    /**
     * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#tween-hooks }\`
     * @since 1.8
     */
    interface PropHooks {
        [property: string]: PropHook<Node>;
    }

    // #endregion

    // region Easing
    // #region Easing

    type EasingMethod = (percent: number) => number;

    interface Easings {
        [name: string]: EasingMethod;
    }

    // #endregion

    // region Effects (fx)
    // #region Effects (fx)

    interface Effects {
        /**
         * The rate (in milliseconds) at which animations fire.
         * @see \`{@link https://api.jquery.com/jQuery.fx.interval/ }\`
         * @since 1.4.3
         * @deprecated ​ Deprecated since 3.0. See \`{@link https://api.jquery.com/jQuery.fx.interval/ }\`.
         *
         * **Cause**: As of jQuery 3.0 the `jQuery.fx.interval` property can be used to change the animation interval only on browsers that do not support the `window.requestAnimationFrame()` method. That is currently only Internet Explorer 9 and the Android Browser. Once support is dropped for these browsers, the property will serve no purpose and it will be removed.
         *
         * **Solution**: Find and remove code that changes or uses `jQuery.fx.interval`. If the value is being used by code in your page or a plugin, the code may be making assumptions that are no longer valid. The default value of `jQuery.fx.interval` is `13` (milliseconds), which could be used instead of accessing this property.
         * @example ​ ````Cause all animations to run with less frames.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.fx.interval demo</title>
  <style>
  div {
    width: 50px;
    height: 30px;
    margin: 5px;
    float: left;
    background: green;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p><input type="button" value="Run"></p>
<div></div>
​
<script>
jQuery.fx.interval = 100;
$( "input" ).click(function() {
  $( "div" ).toggle( 3000 );
});
</script>
</body>
</html>
```
        */
        interval: number;
        /**
         * Globally disable all animations.
         * @see \`{@link https://api.jquery.com/jQuery.fx.off/ }\`
         * @since 1.3
         * @example ​ ````Toggle animation on and off
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>jQuery.fx.off demo</title>
  <style>
  div {
    width: 50px;
    height: 30px;
    margin: 5px;
    float: left;
    background: green;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input type="button" value="Run">
<button>Toggle fx</button>
<div></div>
​
<script>
var toggleFx = function() {
  $.fx.off = !$.fx.off;
};
toggleFx();
$( "button" ).click( toggleFx );
$( "input" ).click(function() {
  $( "div" ).toggle( "slow" );
});
</script>
</body>
</html>
```
        */
        off: boolean;
        /**
         * @deprecated ​ Deprecated since 1.8. Use \`{@link Tween.propHooks jQuery.Tween.propHooks}\`.
         *
         * `jQuery.fx.step` functions are being replaced by `jQuery.Tween.propHooks` and may eventually be removed, but are still supported via the default tween propHook.
         */
        step: PlainObject<AnimationHook<Node>>;
        /**
         * _overridable_ Clears up the `setInterval`
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#plugging-in-a-different-timer-loop }\`
         * @since 1.8
         */
        stop(): void;
        /**
         * Calls `.run()` on each object in the `jQuery.timers` array, removing it from the array if `.run()` returns a falsy value. Calls `jQuery.fx.stop()` whenever there are no timers remaining.
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#plugging-in-a-different-timer-loop }\`
         * @since 1.8
         */
        tick(): void;
        /**
         * _overridable_ Creates a `setInterval` if one doesn't already exist, and pushes `tickFunction` to the `jQuery.timers` array. `tickFunction` should also have `anim`, `elem`, and `queue` properties that reference the animation object, animated element, and queue option to facilitate `jQuery.fn.stop()`
         *
         * By overriding `fx.timer` and `fx.stop` you should be able to implement any animation tick behaviour you desire. (like using `requestAnimationFrame` instead of `setTimeout`.)
         *
         * There is an example of overriding the timer loop in \`{@link https://github.com/gnarf37/jquery-requestAnimationFrame jquery.requestAnimationFrame}\`
         * @see \`{@link https://gist.github.com/gnarf/54829d408993526fe475#plugging-in-a-different-timer-loop }\`
         * @since 1.8
         */
        timer(tickFunction: TickFunction<any>): void;
    }

    /**
     * @deprecated ​ Deprecated since 1.8. Use \`{@link Tween.propHooks jQuery.Tween.propHooks}\`.
     *
     * `jQuery.fx.step` functions are being replaced by `jQuery.Tween.propHooks` and may eventually be removed, but are still supported via the default tween propHook.
     */
    type AnimationHook<TElement> = (fx: Tween<TElement>) => void;

    interface TickFunction<TElement> {
        anim: Animation<TElement>;
        elem: TElement;
        queue: boolean | string;
        (): any;
    }

    // #endregion

    // region Queue
    // #region Queue

    // TODO: Is the first element always a string or is that specific to the 'fx' queue?
    type Queue<TElement> = { 0: string; } & Array<QueueFunction<TElement>>;

    type QueueFunction<TElement> = (this: TElement, next: () => void) => void;

    // #endregion

    // region Speed
    // #region Speed

    // Workaround for TypeScript 2.3 which does not have support for weak types handling.
    type SpeedSettings<TElement> = {
        /**
         * A string or number determining how long the animation will run.
         */
        duration: Duration;
    } | {
        /**
         * A string indicating which easing function to use for the transition.
         */
        easing: string;
    } | {
        /**
         * A function to call once the animation is complete.
         */
        complete(this: TElement): void;
    } | {
        [key: string]: never;
    };

    // #endregion

    // #endregion

    // region Events
    // #region Events

    // region Event
    // #region Event

    // This should be a class but doesn't work correctly under the JQuery namespace. Event should be an inner class of jQuery.

    /**
     * jQuery's event system normalizes the event object according to W3C standards. The event object is guaranteed to be passed to the event handler (no checks for window.event required). It normalizes the target, relatedTarget, which, metaKey and pageX/Y properties and provides both stopPropagation() and preventDefault() methods.
     *
     * Those properties are all documented, and accompanied by examples, on the \`{@link http://api.jquery.com/category/events/event-object/ Event object}\` page.
     *
     * The standard events in the Document Object Model are: `blur`, `focus`, `load`, `resize`, `scroll`, `unload`, `beforeunload`, `click`, `dblclick`, `mousedown`, `mouseup`, `mousemove`, `mouseover`, `mouseout`, `mouseenter`, `mouseleave`, `change`, `select`, `submit`, `keydown`, `keypress`, and `keyup`. Since the DOM event names have predefined meanings for some elements, using them for other purposes is not recommended. jQuery's event model can trigger an event by any name on an element, and it is propagated up the DOM tree to which that element belongs, if any.
     * @see \`{@link https://api.jquery.com/category/events/event-object/ }\`
     */
    interface EventStatic {
        /**
         * The jQuery.Event constructor is exposed and can be used when calling trigger. The new operator is optional.
         *
         * Check \`{@link https://api.jquery.com/trigger/ trigger}\`'s documentation to see how to combine it with your own event object.
         * @see \`{@link https://api.jquery.com/category/events/event-object/ }\`
         * @since 1.6
         * @example
```javascript
//Create a new jQuery.Event object without the "new" operator.
var e = jQuery.Event( "click" );
​
// trigger an artificial click event
jQuery( "body" ).trigger( e );
```
         * @example
```javascript
// Create a new jQuery.Event object with specified event properties.
var e = jQuery.Event( "keydown", { keyCode: 64 } );
​
// trigger an artificial keydown event with keyCode 64
jQuery( "body" ).trigger( e );
```
         */
        <T extends object>(event: string, properties?: T): Event & T;
        /**
         * The jQuery.Event constructor is exposed and can be used when calling trigger. The new operator is optional.
         *
         * Check \`{@link https://api.jquery.com/trigger/ trigger}\`'s documentation to see how to combine it with your own event object.
         * @see \`{@link https://api.jquery.com/category/events/event-object/ }\`
         * @since 1.6
         * @example
```javascript
//Create a new jQuery.Event object without the "new" operator.
var e = jQuery.Event( "click" );
​
// trigger an artificial click event
jQuery( "body" ).trigger( e );
```
         * @example
```javascript
// Create a new jQuery.Event object with specified event properties.
var e = jQuery.Event( "keydown", { keyCode: 64 } );
​
// trigger an artificial keydown event with keyCode 64
jQuery( "body" ).trigger( e );
```
         */
        new <T extends object>(event: string, properties?: T): Event & T;
    }

    /**
     * jQuery's event system normalizes the event object according to W3C standards. The event object is guaranteed to be passed to the event handler (no checks for window.event required). It normalizes the target, relatedTarget, which, metaKey and pageX/Y properties and provides both stopPropagation() and preventDefault() methods.
     *
     * Those properties are all documented, and accompanied by examples, on the \`{@link http://api.jquery.com/category/events/event-object/ Event object}\` page.
     *
     * The standard events in the Document Object Model are: `blur`, `focus`, `load`, `resize`, `scroll`, `unload`, `beforeunload`, `click`, `dblclick`, `mousedown`, `mouseup`, `mousemove`, `mouseover`, `mouseout`, `mouseenter`, `mouseleave`, `change`, `select`, `submit`, `keydown`, `keypress`, and `keyup`. Since the DOM event names have predefined meanings for some elements, using them for other purposes is not recommended. jQuery's event model can trigger an event by any name on an element, and it is propagated up the DOM tree to which that element belongs, if any.
     * @see \`{@link https://api.jquery.com/category/events/event-object/ }\`
     * @see \`{@link TriggeredEvent }\`
     */
    interface Event {
        // region Copied properties
        // #region Copied properties

        // Event

        bubbles: boolean | undefined;
        cancelable: boolean | undefined;
        eventPhase: number | undefined;

        // UIEvent

        detail: number | undefined;
        view: Window | undefined;

        // MouseEvent

        button: number | undefined;
        buttons: number | undefined;
        clientX: number | undefined;
        clientY: number | undefined;
        offsetX: number | undefined;
        offsetY: number | undefined;
        /**
         * The mouse position relative to the left edge of the document.
         * @see \`{@link https://api.jquery.com/event.pageX/ }\`
         * @since 1.0.4
         * @example ​ ````Show the mouse position relative to the left and top edges of the document (within this iframe).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.pageX demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
$( document ).on( "mousemove", function( event ) {
  $( "#log" ).text( "pageX: " + event.pageX + ", pageY: " + event.pageY );
});
</script>
​
</body>
</html>
```
         */
        pageX: number | undefined;
        /**
         * The mouse position relative to the top edge of the document.
         * @see \`{@link https://api.jquery.com/event.pageY/ }\`
         * @since 1.0.4
         * @example ​ ````Show the mouse position relative to the left and top edges of the document (within this iframe).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.pageY demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
$( document ).on( "mousemove", function( event ) {
  $( "#log" ).text( "pageX: " + event.pageX + ", pageY: " + event.pageY );
});
</script>
​
</body>
</html>
```
         */
        pageY: number | undefined;
        screenX: number | undefined;
        screenY: number | undefined;
        /** @deprecated */
        toElement: Element | undefined;

        // PointerEvent

        pointerId: number | undefined;
        pointerType: string | undefined;

        // KeyboardEvent

        /** @deprecated */
        char: string | undefined;
        /** @deprecated */
        charCode: number | undefined;
        key: string | undefined;
        /** @deprecated */
        keyCode: number | undefined;

        // TouchEvent

        changedTouches: TouchList | undefined;
        targetTouches: TouchList | undefined;
        touches: TouchList | undefined;

        // MouseEvent, KeyboardEvent

        /**
         * For key or mouse events, this property indicates the specific key or button that was pressed.
         * @see \`{@link https://api.jquery.com/event.which/ }\`
         * @since 1.1.3
         * @deprecated ​ Deprecated since 3.3. See \`{@link https://github.com/jquery/api.jquery.com/issues/821 }\`.
         * @example ​ ````Log which key was depressed.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.which demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input id="whichkey" value="type something">
<div id="log"></div>
​
<script>
$( "#whichkey" ).on( "keydown", function( event ) {
  $( "#log" ).html( event.type + ": " +  event.which );
});
</script>
​
</body>
</html>
```
         * @example ​ ````Log which mouse button was depressed.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.which demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input id="whichkey" value="click here">
<div id="log"></div>
​
<script>
$( "#whichkey" ).on( "mousedown", function( event ) {
  $( "#log" ).html( event.type + ": " +  event.which );
});
</script>
​
</body>
</html>
```
         */
        which: number | undefined;

        // MouseEvent, KeyboardEvent, TouchEvent

        altKey: boolean | undefined;
        ctrlKey: boolean | undefined;
        /**
         * Indicates whether the META key was pressed when the event fired.
         * @see \`{@link https://api.jquery.com/event.metaKey/ }\`
         * @since 1.0.4
         * @example ​ ````Determine whether the META key was pressed when the event fired.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.metaKey demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button value="Test" name="Test" id="checkMetaKey">Click me!</button>
<div id="display"></div>
​
<script>
$( "#checkMetaKey" ).click(function( event ) {
  $( "#display" ).text( event.metaKey );
});
</script>
​
</body>
</html>
```
         */
        metaKey: boolean | undefined;
        shiftKey: boolean | undefined;

        // #endregion

        /**
         * The difference in milliseconds between the time the browser created the event and January 1, 1970.
         * @see \`{@link https://api.jquery.com/event.timeStamp/ }\`
         * @since 1.2.6
         * @example ​ ````Display the time since the click handler last executed.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.timeStamp demo</title>
  <style>
  div {
    height: 100px;
    width: 300px;
    margin: 10px;
    background-color: #ffd;
    overflow: auto;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div>Click.</div>
​
<script>
var last, diff;
$( "div" ).click(function( event ) {
  if ( last ) {
    diff = event.timeStamp - last;
    $( "div" ).append( "time since last event: " + diff + "<br>" );
  } else {
    $( "div" ).append( "Click again.<br>" );
  }
  last = event.timeStamp;
});
</script>
​
</body>
</html>
```
         */
        timeStamp: number;
        /**
         * Describes the nature of the event.
         * @see \`{@link https://api.jquery.com/event.type/ }\`
         * @since 1.0
         * @example ​ ````On all anchor clicks, alert the event type.
```javascript
$( "a" ).click(function( event ) {
  alert( event.type ); // "click"
});
```
         */
        type: string;
        /**
         * Returns whether event.preventDefault() was ever called on this event object.
         * @see \`{@link https://api.jquery.com/event.isDefaultPrevented/ }\`
         * @since 1.3
         * @example ​ ````Checks whether event.preventDefault() was called.
```javascript
$( "a" ).click(function( event ) {
  alert( event.isDefaultPrevented() ); // false
  event.preventDefault();
  alert( event.isDefaultPrevented() ); // true
});
```
         */
        isDefaultPrevented(): boolean;
        /**
         * Returns whether event.stopImmediatePropagation() was ever called on this event object.
         * @see \`{@link https://api.jquery.com/event.isImmediatePropagationStopped/ }\`
         * @since 1.3
         * @example ​ ````Checks whether event.stopImmediatePropagation() was called.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.isImmediatePropagationStopped demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>click me</button>
<div id="stop-log"></div>
  ​
<script>
function immediatePropStopped( event ) {
  var msg = "";
  if ( event.isImmediatePropagationStopped() ) {
    msg = "called";
  } else {
    msg = "not called";
  }
  $( "#stop-log" ).append( "<div>" + msg + "</div>" );
}
​
$( "button" ).click(function( event ) {
  immediatePropStopped( event );
  event.stopImmediatePropagation();
  immediatePropStopped( event );
});
</script>
​
</body>
</html>
```
         */
        isImmediatePropagationStopped(): boolean;
        /**
         * Returns whether event.stopPropagation() was ever called on this event object.
         * @see \`{@link https://api.jquery.com/event.isPropagationStopped/ }\`
         * @since 1.3
         * @example ​ ````Checks whether event.stopPropagation() was called
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.isPropagationStopped demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>click me</button>
<div id="stop-log"></div>
  ​
<script>
function propStopped( event ) {
  var msg = "";
  if ( event.isPropagationStopped() ) {
    msg = "called";
  } else {
    msg = "not called";
  }
  $( "#stop-log" ).append( "<div>" + msg + "</div>" );
}
​
$( "button" ).click(function(event) {
  propStopped( event );
  event.stopPropagation();
  propStopped( event );
});
</script>
​
</body>
</html>
```
         */
        isPropagationStopped(): boolean;
        /**
         * If this method is called, the default action of the event will not be triggered.
         * @see \`{@link https://api.jquery.com/event.preventDefault/ }\`
         * @since 1.0
         * @example ​ ````Cancel the default action (navigation) of the click.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.preventDefault demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<a href="https://jquery.com">default click action is prevented</a>
<div id="log"></div>
​
<script>
$( "a" ).click(function( event ) {
  event.preventDefault();
  $( "<div>" )
    .append( "default " + event.type + " prevented" )
    .appendTo( "#log" );
});
</script>
​
</body>
</html>
```
         */
        preventDefault(): void;
        /**
         * Keeps the rest of the handlers from being executed and prevents the event from bubbling up the DOM tree.
         * @see \`{@link https://api.jquery.com/event.stopImmediatePropagation/ }\`
         * @since 1.3
         * @example ​ ````Prevents other event handlers from being called.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.stopImmediatePropagation demo</title>
  <style>
  p {
    height: 30px;
    width: 150px;
    background-color: #ccf;
  }
  div {
    height: 30px;
    width: 150px;
    background-color: #cfc;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<p>paragraph</p>
<div>division</div>
​
<script>
$( "p" ).click(function( event ) {
  event.stopImmediatePropagation();
});
$( "p" ).click(function( event ) {
  // This function won't be executed
  $( this ).css( "background-color", "#f00" );
});
$( "div" ).click(function( event ) {
  // This function will be executed
  $( this ).css( "background-color", "#f00" );
});
</script>
​
</body>
</html>
```
         */
        stopImmediatePropagation(): void;
        /**
         * Prevents the event from bubbling up the DOM tree, preventing any parent handlers from being notified of the event.
         * @see \`{@link https://api.jquery.com/event.stopPropagation/ }\`
         * @since 1.0
         * @example ​ ````Kill the bubbling on the click event.
```javascript
$( "p" ).click(function( event ) {
  event.stopPropagation();
  // Do something
});
```
         */
        stopPropagation(): void;
    }

    // #endregion

    /**
     * Base type for jQuery events that have been triggered (including events triggered on plain objects).
     */
    interface TriggeredEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends Event {
        /**
         * The current DOM element within the event bubbling phase.
         * @see \`{@link https://api.jquery.com/event.currentTarget/ }\`
         * @since 1.3
         * @example ​ ````Alert that currentTarget matches the `this` keyword.
```javascript
$( "p" ).click(function( event ) {
  alert( event.currentTarget === this ); // true
});
```
        */
        currentTarget: TCurrentTarget;
        /**
         * The element where the currently-called jQuery event handler was attached.
         * @see \`{@link https://api.jquery.com/event.delegateTarget/ }\`
         * @since 1.7
         * @example ​ ````When a button in any box class is clicked, change the box&#39;s background color to red.
```javascript
$( ".box" ).on( "click", "button", function( event ) {
  $( event.delegateTarget ).css( "background-color", "red" );
});
```
        */
        delegateTarget: TDelegateTarget;
        /**
         * The DOM element that initiated the event.
         * @see \`{@link https://api.jquery.com/event.target/ }\`
         * @since 1.0
         * @example ​ ````Display the tag&#39;s name on click
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.target demo</title>
  <style>
  span, strong, p {
    padding: 8px;
    display: block;
    border: 1px solid #999;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
<div>
  <p>
    <strong><span>click</span></strong>
  </p>
</div>
​
<script>
$( "body" ).click(function( event ) {
  $( "#log" ).html( "clicked: " + event.target.nodeName );
});
</script>
​
</body>
</html>
```
         * @example ​ ````Implements a simple event delegation: The click handler is added to an unordered list, and the children of its li children are hidden. Clicking one of the li children toggles (see toggle()) their children.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.target demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<ul>
  <li>item 1
    <ul>
      <li>sub item 1-a</li>
      <li>sub item 1-b</li>
    </ul>
  </li>
  <li>item 2
    <ul>
      <li>sub item 2-a</li>
      <li>sub item 2-b</li>
    </ul>
  </li>
</ul>
​
<script>
function handler( event ) {
  var target = $( event.target );
  if ( target.is( "li" ) ) {
    target.children().toggle();
  }
}
$( "ul" ).click( handler ).find( "ul" ).hide();
</script>
​
</body>
</html>
```
        */
        target: TTarget;

        /**
         * An optional object of data passed to an event method when the current executing handler is bound.
         * @see \`{@link https://api.jquery.com/event.data/ }\`
         * @since 1.1
         * @example ​ ````Within a for loop, pass the value of i to the .on() method so that the current iteration&#39;s value is preserved.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.data demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button> 0 </button>
<button> 1 </button>
<button> 2 </button>
<button> 3 </button>
<button> 4 </button>
​
<div id="log"></div>
​
<script>
var logDiv = $( "#log" );
​
for ( var i = 0; i < 5; i++ ) {
  $( "button" ).eq( i ).on( "click", { value: i }, function( event ) {
    var msgs = [
      "button = " + $( this ).index(),
      "event.data.value = " + event.data.value,
      "i = " + i
    ];
    logDiv.append( msgs.join( ", " ) + "<br>" );
  });
}
</script>
​
</body>
</html>
```
        */
        data: TData;

        /**
         * The namespace specified when the event was triggered.
         * @see \`{@link https://api.jquery.com/event.namespace/ }\`
         * @since 1.4.3
         * @example ​ ````Determine the event namespace used.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.namespace demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>display event.namespace</button>
<p></p>
​
<script>
$( "p" ).on( "test.something", function( event ) {
  alert( event.namespace );
});
$( "button" ).click(function( event ) {
  $( "p" ).trigger( "test.something" );
});
</script>
​
</body>
</html>
```
         */
        namespace?: string;
        originalEvent?: _Event;
        /**
         * The last value returned by an event handler that was triggered by this event, unless the value was undefined.
         * @see \`{@link https://api.jquery.com/event.result/ }\`
         * @since 1.3
         * @example ​ ````Display previous handler&#39;s return value
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.result demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button>display event.result</button>
<p></p>
​
<script>
$( "button" ).click(function( event ) {
  return "hey";
});
$( "button" ).click(function( event ) {
  $( "p" ).html( event.result );
});
</script>
​
</body>
</html>
```
         */
        result?: any;
    }

    // region Event
    // #region Event

    interface EventBase<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends TriggeredEvent<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        /**
         * The other DOM element involved in the event, if any.
         * @see \`{@link https://api.jquery.com/event.relatedTarget/ }\`
         * @since 1.1.4
         * @example ​ ````On mouseout of anchors, alert the element type being entered.
```javascript
$( "a" ).mouseout(function( event ) {
  alert( event.relatedTarget.nodeName ); // "DIV"
});
```
        */
        relatedTarget?: undefined;

        // Event

        bubbles: boolean;
        cancelable: boolean;
        eventPhase: number;

        // UIEvent

        detail: undefined;
        view: undefined;

        // MouseEvent

        button: undefined;
        buttons: undefined;
        clientX: undefined;
        clientY: undefined;
        offsetX: undefined;
        offsetY: undefined;
        /**
         * The mouse position relative to the left edge of the document.
         * @see \`{@link https://api.jquery.com/event.pageX/ }\`
         * @since 1.0.4
         * @example ​ ````Show the mouse position relative to the left and top edges of the document (within this iframe).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.pageX demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
$( document ).on( "mousemove", function( event ) {
  $( "#log" ).text( "pageX: " + event.pageX + ", pageY: " + event.pageY );
});
</script>
​
</body>
</html>
```
         */
        pageX: undefined;
        /**
         * The mouse position relative to the top edge of the document.
         * @see \`{@link https://api.jquery.com/event.pageY/ }\`
         * @since 1.0.4
         * @example ​ ````Show the mouse position relative to the left and top edges of the document (within this iframe).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.pageY demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
$( document ).on( "mousemove", function( event ) {
  $( "#log" ).text( "pageX: " + event.pageX + ", pageY: " + event.pageY );
});
</script>
​
</body>
</html>
```
         */
        pageY: undefined;
        screenX: undefined;
        screenY: undefined;
        /** @deprecated */
        toElement: undefined;

        // PointerEvent

        pointerId: undefined;
        pointerType: undefined;

        // KeyboardEvent

        /** @deprecated */
        char: undefined;
        /** @deprecated */
        charCode: undefined;
        key: undefined;
        /** @deprecated */
        keyCode: undefined;

        // TouchEvent

        changedTouches: undefined;
        targetTouches: undefined;
        touches: undefined;

        // MouseEvent, KeyboardEvent

        /**
         * For key or mouse events, this property indicates the specific key or button that was pressed.
         * @see \`{@link https://api.jquery.com/event.which/ }\`
         * @since 1.1.3
         * @deprecated ​ Deprecated since 3.3. See \`{@link https://github.com/jquery/api.jquery.com/issues/821 }\`.
         * @example ​ ````Log which key was depressed.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.which demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input id="whichkey" value="type something">
<div id="log"></div>
​
<script>
$( "#whichkey" ).on( "keydown", function( event ) {
  $( "#log" ).html( event.type + ": " +  event.which );
});
</script>
​
</body>
</html>
```
         * @example ​ ````Log which mouse button was depressed.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.which demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input id="whichkey" value="click here">
<div id="log"></div>
​
<script>
$( "#whichkey" ).on( "mousedown", function( event ) {
  $( "#log" ).html( event.type + ": " +  event.which );
});
</script>
​
</body>
</html>
```
         */
        which: undefined;

        // MouseEvent, KeyboardEvent, TouchEvent

        altKey: undefined;
        ctrlKey: undefined;
        /**
         * Indicates whether the META key was pressed when the event fired.
         * @see \`{@link https://api.jquery.com/event.metaKey/ }\`
         * @since 1.0.4
         * @example ​ ````Determine whether the META key was pressed when the event fired.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.metaKey demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button value="Test" name="Test" id="checkMetaKey">Click me!</button>
<div id="display"></div>
​
<script>
$( "#checkMetaKey" ).click(function( event ) {
  $( "#display" ).text( event.metaKey );
});
</script>
​
</body>
</html>
```
         */
        metaKey: undefined;
        shiftKey: undefined;

        originalEvent?: _Event;
    }

    interface ChangeEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends EventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'change';
    }

    interface ResizeEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends EventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'resize';
    }

    interface ScrollEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends EventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'scroll';
    }

    interface SelectEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends EventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'select';
    }

    interface SubmitEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends EventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'submit';
    }

    // #endregion

    // region UIEvent
    // #region UIEvent

    interface UIEventBase<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends TriggeredEvent<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        // Event

        bubbles: boolean;
        cancelable: boolean;
        eventPhase: number;

        // UIEvent

        detail: number;
        view: Window;

        originalEvent?: _UIEvent;
    }

    // region MouseEvent
    // #region MouseEvent

    interface MouseEventBase<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends UIEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        /**
         * The other DOM element involved in the event, if any.
         * @see \`{@link https://api.jquery.com/event.relatedTarget/ }\`
         * @since 1.1.4
         * @example ​ ````On mouseout of anchors, alert the element type being entered.
```javascript
$( "a" ).mouseout(function( event ) {
  alert( event.relatedTarget.nodeName ); // "DIV"
});
```
        */
        relatedTarget?: EventTarget | null;

        // MouseEvent

        button: number;
        buttons: number;
        clientX: number;
        clientY: number;
        offsetX: number;
        offsetY: number;
        /**
         * The mouse position relative to the left edge of the document.
         * @see \`{@link https://api.jquery.com/event.pageX/ }\`
         * @since 1.0.4
         * @example ​ ````Show the mouse position relative to the left and top edges of the document (within this iframe).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.pageX demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
$( document ).on( "mousemove", function( event ) {
  $( "#log" ).text( "pageX: " + event.pageX + ", pageY: " + event.pageY );
});
</script>
​
</body>
</html>
```
         */
        pageX: number;
        /**
         * The mouse position relative to the top edge of the document.
         * @see \`{@link https://api.jquery.com/event.pageY/ }\`
         * @since 1.0.4
         * @example ​ ````Show the mouse position relative to the left and top edges of the document (within this iframe).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.pageY demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
$( document ).on( "mousemove", function( event ) {
  $( "#log" ).text( "pageX: " + event.pageX + ", pageY: " + event.pageY );
});
</script>
​
</body>
</html>
```
         */
        pageY: number;
        screenX: number;
        screenY: number;
        /** @deprecated */
        toElement: Element;

        // PointerEvent

        pointerId: undefined;
        pointerType: undefined;

        // KeyboardEvent

        /** @deprecated */
        char: undefined;
        /** @deprecated */
        charCode: undefined;
        key: undefined;
        /** @deprecated */
        keyCode: undefined;

        // TouchEvent

        changedTouches: undefined;
        targetTouches: undefined;
        touches: undefined;

        // MouseEvent, KeyboardEvent

        /**
         * For key or mouse events, this property indicates the specific key or button that was pressed.
         * @see \`{@link https://api.jquery.com/event.which/ }\`
         * @since 1.1.3
         * @deprecated ​ Deprecated since 3.3. See \`{@link https://github.com/jquery/api.jquery.com/issues/821 }\`.
         * @example ​ ````Log which key was depressed.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.which demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input id="whichkey" value="type something">
<div id="log"></div>
​
<script>
$( "#whichkey" ).on( "keydown", function( event ) {
  $( "#log" ).html( event.type + ": " +  event.which );
});
</script>
​
</body>
</html>
```
         * @example ​ ````Log which mouse button was depressed.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.which demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input id="whichkey" value="click here">
<div id="log"></div>
​
<script>
$( "#whichkey" ).on( "mousedown", function( event ) {
  $( "#log" ).html( event.type + ": " +  event.which );
});
</script>
​
</body>
</html>
```
         */
        which: number;

        // MouseEvent, KeyboardEvent, TouchEvent

        altKey: boolean;
        ctrlKey: boolean;
        /**
         * Indicates whether the META key was pressed when the event fired.
         * @see \`{@link https://api.jquery.com/event.metaKey/ }\`
         * @since 1.0.4
         * @example ​ ````Determine whether the META key was pressed when the event fired.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.metaKey demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button value="Test" name="Test" id="checkMetaKey">Click me!</button>
<div id="display"></div>
​
<script>
$( "#checkMetaKey" ).click(function( event ) {
  $( "#display" ).text( event.metaKey );
});
</script>
​
</body>
</html>
```
         */
        metaKey: boolean;
        shiftKey: boolean;

        originalEvent?: _MouseEvent;
    }

    interface ClickEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends MouseEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        /**
         * The other DOM element involved in the event, if any.
         * @see \`{@link https://api.jquery.com/event.relatedTarget/ }\`
         * @since 1.1.4
         * @example ​ ````On mouseout of anchors, alert the element type being entered.
 ```javascript
 $( "a" ).mouseout(function( event ) {
  alert( event.relatedTarget.nodeName ); // "DIV"
 });
 ```
        */
        relatedTarget?: null;

        type: 'click';
    }

    interface ContextMenuEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends MouseEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        /**
         * The other DOM element involved in the event, if any.
         * @see \`{@link https://api.jquery.com/event.relatedTarget/ }\`
         * @since 1.1.4
         * @example ​ ````On mouseout of anchors, alert the element type being entered.
 ```javascript
 $( "a" ).mouseout(function( event ) {
  alert( event.relatedTarget.nodeName ); // "DIV"
 });
 ```
        */
        relatedTarget?: null;

        type: 'contextmenu';
    }

    interface DoubleClickEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends MouseEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        /**
         * The other DOM element involved in the event, if any.
         * @see \`{@link https://api.jquery.com/event.relatedTarget/ }\`
         * @since 1.1.4
         * @example ​ ````On mouseout of anchors, alert the element type being entered.
 ```javascript
 $( "a" ).mouseout(function( event ) {
  alert( event.relatedTarget.nodeName ); // "DIV"
 });
 ```
        */
        relatedTarget?: null;

        type: 'dblclick';
    }

    interface MouseDownEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends MouseEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        /**
         * The other DOM element involved in the event, if any.
         * @see \`{@link https://api.jquery.com/event.relatedTarget/ }\`
         * @since 1.1.4
         * @example ​ ````On mouseout of anchors, alert the element type being entered.
 ```javascript
 $( "a" ).mouseout(function( event ) {
  alert( event.relatedTarget.nodeName ); // "DIV"
 });
 ```
        */
        relatedTarget?: null;

        type: 'mousedown';
    }

    interface MouseEnterEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends MouseEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        // Special handling by jQuery.
        type: 'mouseover';
    }

    interface MouseLeaveEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends MouseEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        // Special handling by jQuery.
        type: 'mouseout';
    }

    interface MouseMoveEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends MouseEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        /**
         * The other DOM element involved in the event, if any.
         * @see \`{@link https://api.jquery.com/event.relatedTarget/ }\`
         * @since 1.1.4
         * @example ​ ````On mouseout of anchors, alert the element type being entered.
 ```javascript
 $( "a" ).mouseout(function( event ) {
  alert( event.relatedTarget.nodeName ); // "DIV"
 });
 ```
        */
        relatedTarget?: null;

        type: 'mousemove';
    }

    interface MouseOutEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends MouseEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'mouseout';
    }

    interface MouseOverEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends MouseEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'mouseover';
    }

    interface MouseUpEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends MouseEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        /**
         * The other DOM element involved in the event, if any.
         * @see \`{@link https://api.jquery.com/event.relatedTarget/ }\`
         * @since 1.1.4
         * @example ​ ````On mouseout of anchors, alert the element type being entered.
 ```javascript
 $( "a" ).mouseout(function( event ) {
  alert( event.relatedTarget.nodeName ); // "DIV"
 });
 ```
        */
        relatedTarget?: null;

        type: 'mouseup';
    }

    // region DragEvent
    // #region DragEvent

    interface DragEventBase<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends UIEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        originalEvent?: _DragEvent;
    }

    interface DragEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends DragEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'drag';
    }

    interface DragEndEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends DragEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'dragend';
    }

    interface DragEnterEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends DragEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'dragenter';
    }

    interface DragExitEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends DragEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'dragexit';
    }

    interface DragLeaveEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends DragEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'dragleave';
    }

    interface DragOverEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends DragEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'dragover';
    }

    interface DragStartEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends DragEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'dragstart';
    }

    interface DropEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends DragEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'drop';
    }

    // #endregion

    // #endregion

    // region KeyboardEvent
    // #region KeyboardEvent

    interface KeyboardEventBase<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends UIEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        /**
         * The other DOM element involved in the event, if any.
         * @see \`{@link https://api.jquery.com/event.relatedTarget/ }\`
         * @since 1.1.4
         * @example ​ ````On mouseout of anchors, alert the element type being entered.
```javascript
$( "a" ).mouseout(function( event ) {
  alert( event.relatedTarget.nodeName ); // "DIV"
});
```
        */
        relatedTarget?: undefined;

        // MouseEvent

        button: undefined;
        buttons: undefined;
        clientX: undefined;
        clientY: undefined;
        offsetX: undefined;
        offsetY: undefined;
        /**
         * The mouse position relative to the left edge of the document.
         * @see \`{@link https://api.jquery.com/event.pageX/ }\`
         * @since 1.0.4
         * @example ​ ````Show the mouse position relative to the left and top edges of the document (within this iframe).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.pageX demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
$( document ).on( "mousemove", function( event ) {
  $( "#log" ).text( "pageX: " + event.pageX + ", pageY: " + event.pageY );
});
</script>
​
</body>
</html>
```
         */
        pageX: undefined;
        /**
         * The mouse position relative to the top edge of the document.
         * @see \`{@link https://api.jquery.com/event.pageY/ }\`
         * @since 1.0.4
         * @example ​ ````Show the mouse position relative to the left and top edges of the document (within this iframe).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.pageY demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
$( document ).on( "mousemove", function( event ) {
  $( "#log" ).text( "pageX: " + event.pageX + ", pageY: " + event.pageY );
});
</script>
​
</body>
</html>
```
         */
        pageY: undefined;
        screenX: undefined;
        screenY: undefined;
        /** @deprecated */
        toElement: undefined;

        // PointerEvent

        pointerId: undefined;
        pointerType: undefined;

        // KeyboardEvent

        /** @deprecated */
        char: string | undefined;
        /** @deprecated */
        charCode: number;
        key: string;
        /** @deprecated */
        keyCode: number;

        // TouchEvent

        changedTouches: undefined;
        targetTouches: undefined;
        touches: undefined;

        // MouseEvent, KeyboardEvent

        /**
         * For key or mouse events, this property indicates the specific key or button that was pressed.
         * @see \`{@link https://api.jquery.com/event.which/ }\`
         * @since 1.1.3
         * @deprecated ​ Deprecated since 3.3. See \`{@link https://github.com/jquery/api.jquery.com/issues/821 }\`.
         * @example ​ ````Log which key was depressed.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.which demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input id="whichkey" value="type something">
<div id="log"></div>
​
<script>
$( "#whichkey" ).on( "keydown", function( event ) {
  $( "#log" ).html( event.type + ": " +  event.which );
});
</script>
​
</body>
</html>
```
         * @example ​ ````Log which mouse button was depressed.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.which demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input id="whichkey" value="click here">
<div id="log"></div>
​
<script>
$( "#whichkey" ).on( "mousedown", function( event ) {
  $( "#log" ).html( event.type + ": " +  event.which );
});
</script>
​
</body>
</html>
```
         */
        which: number;

        // MouseEvent, KeyboardEvent, TouchEvent

        altKey: boolean;
        ctrlKey: boolean;
        /**
         * Indicates whether the META key was pressed when the event fired.
         * @see \`{@link https://api.jquery.com/event.metaKey/ }\`
         * @since 1.0.4
         * @example ​ ````Determine whether the META key was pressed when the event fired.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.metaKey demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button value="Test" name="Test" id="checkMetaKey">Click me!</button>
<div id="display"></div>
​
<script>
$( "#checkMetaKey" ).click(function( event ) {
  $( "#display" ).text( event.metaKey );
});
</script>
​
</body>
</html>
```
         */
        metaKey: boolean;
        shiftKey: boolean;

        originalEvent?: _KeyboardEvent;
    }

    interface KeyDownEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends KeyboardEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'keydown';
    }

    interface KeyPressEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends KeyboardEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'keypress';
    }

    interface KeyUpEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends KeyboardEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'keyup';
    }

    // #endregion

    // region TouchEvent
    // #region TouchEvent

    interface TouchEventBase<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends UIEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        /**
         * The other DOM element involved in the event, if any.
         * @see \`{@link https://api.jquery.com/event.relatedTarget/ }\`
         * @since 1.1.4
         * @example ​ ````On mouseout of anchors, alert the element type being entered.
```javascript
$( "a" ).mouseout(function( event ) {
  alert( event.relatedTarget.nodeName ); // "DIV"
});
```
        */
        relatedTarget?: undefined;

        // MouseEvent

        button: undefined;
        buttons: undefined;
        clientX: undefined;
        clientY: undefined;
        offsetX: undefined;
        offsetY: undefined;
        /**
         * The mouse position relative to the left edge of the document.
         * @see \`{@link https://api.jquery.com/event.pageX/ }\`
         * @since 1.0.4
         * @example ​ ````Show the mouse position relative to the left and top edges of the document (within this iframe).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.pageX demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
$( document ).on( "mousemove", function( event ) {
  $( "#log" ).text( "pageX: " + event.pageX + ", pageY: " + event.pageY );
});
</script>
​
</body>
</html>
```
         */
        pageX: undefined;
        /**
         * The mouse position relative to the top edge of the document.
         * @see \`{@link https://api.jquery.com/event.pageY/ }\`
         * @since 1.0.4
         * @example ​ ````Show the mouse position relative to the left and top edges of the document (within this iframe).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.pageY demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
$( document ).on( "mousemove", function( event ) {
  $( "#log" ).text( "pageX: " + event.pageX + ", pageY: " + event.pageY );
});
</script>
​
</body>
</html>
```
         */
        pageY: undefined;
        screenX: undefined;
        screenY: undefined;
        /** @deprecated */
        toElement: undefined;

        // PointerEvent

        pointerId: undefined;
        pointerType: undefined;

        // KeyboardEvent

        /** @deprecated */
        char: undefined;
        /** @deprecated */
        charCode: undefined;
        key: undefined;
        /** @deprecated */
        keyCode: undefined;

        // TouchEvent

        changedTouches: TouchList;
        targetTouches: TouchList;
        touches: TouchList;

        // MouseEvent, KeyboardEvent

        /**
         * For key or mouse events, this property indicates the specific key or button that was pressed.
         * @see \`{@link https://api.jquery.com/event.which/ }\`
         * @since 1.1.3
         * @deprecated ​ Deprecated since 3.3. See \`{@link https://github.com/jquery/api.jquery.com/issues/821 }\`.
         * @example ​ ````Log which key was depressed.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.which demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input id="whichkey" value="type something">
<div id="log"></div>
​
<script>
$( "#whichkey" ).on( "keydown", function( event ) {
  $( "#log" ).html( event.type + ": " +  event.which );
});
</script>
​
</body>
</html>
```
         * @example ​ ````Log which mouse button was depressed.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.which demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input id="whichkey" value="click here">
<div id="log"></div>
​
<script>
$( "#whichkey" ).on( "mousedown", function( event ) {
  $( "#log" ).html( event.type + ": " +  event.which );
});
</script>
​
</body>
</html>
```
         */
        which: undefined;

        // MouseEvent, KeyboardEvent, TouchEvent

        altKey: boolean;
        ctrlKey: boolean;
        /**
         * Indicates whether the META key was pressed when the event fired.
         * @see \`{@link https://api.jquery.com/event.metaKey/ }\`
         * @since 1.0.4
         * @example ​ ````Determine whether the META key was pressed when the event fired.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.metaKey demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button value="Test" name="Test" id="checkMetaKey">Click me!</button>
<div id="display"></div>
​
<script>
$( "#checkMetaKey" ).click(function( event ) {
  $( "#display" ).text( event.metaKey );
});
</script>
​
</body>
</html>
```
         */
        metaKey: boolean;
        shiftKey: boolean;

        originalEvent?: _TouchEvent;
    }

    interface TouchCancelEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends TouchEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'touchcancel';
    }

    interface TouchEndEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends TouchEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'touchend';
    }

    interface TouchMoveEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends TouchEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'touchmove';
    }

    interface TouchStartEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends TouchEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'touchstart';
    }

    // #endregion

    // region FocusEvent
    // #region FocusEvent

    interface FocusEventBase<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends UIEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        /**
         * The other DOM element involved in the event, if any.
         * @see \`{@link https://api.jquery.com/event.relatedTarget/ }\`
         * @since 1.1.4
         * @example ​ ````On mouseout of anchors, alert the element type being entered.
```javascript
$( "a" ).mouseout(function( event ) {
  alert( event.relatedTarget.nodeName ); // "DIV"
});
```
        */
        relatedTarget?: EventTarget | null;

        // MouseEvent

        button: undefined;
        buttons: undefined;
        clientX: undefined;
        clientY: undefined;
        offsetX: undefined;
        offsetY: undefined;
        /**
         * The mouse position relative to the left edge of the document.
         * @see \`{@link https://api.jquery.com/event.pageX/ }\`
         * @since 1.0.4
         * @example ​ ````Show the mouse position relative to the left and top edges of the document (within this iframe).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.pageX demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
$( document ).on( "mousemove", function( event ) {
  $( "#log" ).text( "pageX: " + event.pageX + ", pageY: " + event.pageY );
});
</script>
​
</body>
</html>
```
         */
        pageX: undefined;
        /**
         * The mouse position relative to the top edge of the document.
         * @see \`{@link https://api.jquery.com/event.pageY/ }\`
         * @since 1.0.4
         * @example ​ ````Show the mouse position relative to the left and top edges of the document (within this iframe).
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.pageY demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<div id="log"></div>
​
<script>
$( document ).on( "mousemove", function( event ) {
  $( "#log" ).text( "pageX: " + event.pageX + ", pageY: " + event.pageY );
});
</script>
​
</body>
</html>
```
         */
        pageY: undefined;
        screenX: undefined;
        screenY: undefined;
        /** @deprecated */
        toElement: undefined;

        // PointerEvent

        pointerId: undefined;
        pointerType: undefined;

        // KeyboardEvent

        /** @deprecated */
        char: undefined;
        /** @deprecated */
        charCode: undefined;
        key: undefined;
        /** @deprecated */
        keyCode: undefined;

        // TouchEvent

        changedTouches: undefined;
        targetTouches: undefined;
        touches: undefined;

        // MouseEvent, KeyboardEvent

        /**
         * For key or mouse events, this property indicates the specific key or button that was pressed.
         * @see \`{@link https://api.jquery.com/event.which/ }\`
         * @since 1.1.3
         * @deprecated ​ Deprecated since 3.3. See \`{@link https://github.com/jquery/api.jquery.com/issues/821 }\`.
         * @example ​ ````Log which key was depressed.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.which demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input id="whichkey" value="type something">
<div id="log"></div>
​
<script>
$( "#whichkey" ).on( "keydown", function( event ) {
  $( "#log" ).html( event.type + ": " +  event.which );
});
</script>
​
</body>
</html>
```
         * @example ​ ````Log which mouse button was depressed.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.which demo</title>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<input id="whichkey" value="click here">
<div id="log"></div>
​
<script>
$( "#whichkey" ).on( "mousedown", function( event ) {
  $( "#log" ).html( event.type + ": " +  event.which );
});
</script>
​
</body>
</html>
```
         */
        which: undefined;

        // MouseEvent, KeyboardEvent, TouchEvent

        altKey: undefined;
        ctrlKey: undefined;
        /**
         * Indicates whether the META key was pressed when the event fired.
         * @see \`{@link https://api.jquery.com/event.metaKey/ }\`
         * @since 1.0.4
         * @example ​ ````Determine whether the META key was pressed when the event fired.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>event.metaKey demo</title>
  <style>
  body {
    background-color: #eef;
  }
  div {
    padding: 20px;
  }
  </style>
  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
</head>
<body>
​
<button value="Test" name="Test" id="checkMetaKey">Click me!</button>
<div id="display"></div>
​
<script>
$( "#checkMetaKey" ).click(function( event ) {
  $( "#display" ).text( event.metaKey );
});
</script>
​
</body>
</html>
```
         */
        metaKey: undefined;
        shiftKey: undefined;

        originalEvent?: _FocusEvent;
    }

    interface BlurEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends FocusEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'blur';
    }

    interface FocusEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends FocusEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'focus';
    }

    interface FocusInEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends FocusEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'focusin';
    }

    interface FocusOutEvent<
        TDelegateTarget = any,
        TData = any,
        TCurrentTarget = any,
        TTarget = any
    > extends FocusEventBase<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        type: 'focusout';
    }

    // #endregion

    // #endregion

    interface TypeToTriggeredEventMap<
        TDelegateTarget,
        TData,
        TCurrentTarget,
        TTarget
    > {
        // Event

        change: ChangeEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        resize: ResizeEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        scroll: ScrollEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        select: SelectEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        submit: SubmitEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;

        // UIEvent

        // MouseEvent

        click: ClickEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        contextmenu: ContextMenuEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        dblclick: DoubleClickEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        mousedown: MouseDownEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        mouseenter: MouseEnterEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        mouseleave: MouseLeaveEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        mousemove: MouseMoveEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        mouseout: MouseOutEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        mouseover: MouseOverEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        mouseup: MouseUpEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;

        // DragEvent

        drag: DragEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        dragend: DragEndEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        dragenter: DragEnterEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        dragexit: DragExitEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        dragleave: DragLeaveEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        dragover: DragOverEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        dragstart: DragStartEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        drop: DropEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;

        // KeyboardEvent

        keydown: KeyDownEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        keypress: KeyPressEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        keyup: KeyUpEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;

        // TouchEvent

        touchcancel: TouchCancelEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        touchend: TouchEndEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        touchmove: TouchMoveEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        touchstart: TouchStartEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;

        // FocusEvent

        blur: BlurEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        focus: FocusEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        focusin: FocusInEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
        focusout: FocusOutEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;

        [type: string]: TriggeredEvent<TDelegateTarget, TData, TCurrentTarget, TTarget>;
    }

    // Extra parameters can be passed from trigger()
    type EventHandlerBase<TContext, T> = (this: TContext, t: T, ...args: any[]) => any;

    type EventHandler<
        TCurrentTarget,
        TData = undefined
    > = EventHandlerBase<TCurrentTarget, TriggeredEvent<TCurrentTarget, TData>>;

    type TypeEventHandler<
        TDelegateTarget,
        TData,
        TCurrentTarget,
        TTarget,
        TType extends keyof TypeToTriggeredEventMap<TDelegateTarget, TData, TCurrentTarget, TTarget>
    > = EventHandlerBase<TCurrentTarget, TypeToTriggeredEventMap<TDelegateTarget, TData, TCurrentTarget, TTarget>[TType]>;

    interface TypeEventHandlers<
        TDelegateTarget,
        TData,
        TCurrentTarget,
        TTarget
    > extends _TypeEventHandlers<TDelegateTarget, TData, TCurrentTarget, TTarget> {
        // No idea why it's necessary to include `object` in the union but otherwise TypeScript complains that
        // derived types of Event are not assignable to Event.
        [type: string]: TypeEventHandler<TDelegateTarget, TData, TCurrentTarget, TTarget, string> |
                        false |
                        undefined |
                        object;
    }

    type _TypeEventHandlers<
        TDelegateTarget,
        TData,
        TCurrentTarget,
        TTarget
    > = {
        [TType in keyof TypeToTriggeredEventMap<TDelegateTarget, TData, TCurrentTarget, TTarget>]?:
            TypeEventHandler<TDelegateTarget, TData, TCurrentTarget, TTarget, TType> |
            false |
            object;
    };

    // region Event extensions
    // #region Event extensions

    interface EventExtensions {
        /**
         * The jQuery special event hooks are a set of per-event-name functions and properties that allow code to control the behavior of event processing within jQuery. The mechanism is similar to `fixHooks` in that the special event information is stored in `jQuery.event.special.NAME`, where `NAME` is the name of the special event. Event names are case sensitive.
         *
         * As with `fixHooks`, the special event hooks design assumes it will be very rare that two unrelated pieces of code want to process the same event name. Special event authors who need to modify events with existing hooks will need to take precautions to avoid introducing unwanted side-effects by clobbering those hooks.
         * @see \`{@link https://learn.jquery.com/events/event-extensions/#special-event-hooks }\`
         */
        special: SpecialEventHooks;
    }

    // region Special event hooks
    // #region Special event hooks

    /**
     * The jQuery special event hooks are a set of per-event-name functions and properties that allow code to control the behavior of event processing within jQuery. The mechanism is similar to `fixHooks` in that the special event information is stored in `jQuery.event.special.NAME`, where `NAME` is the name of the special event. Event names are case sensitive.
     *
     * As with `fixHooks`, the special event hooks design assumes it will be very rare that two unrelated pieces of code want to process the same event name. Special event authors who need to modify events with existing hooks will need to take precautions to avoid introducing unwanted side-effects by clobbering those hooks.
     * @see \`{@link https://learn.jquery.com/events/event-extensions/#special-event-hooks }\`
     */
    // Workaround for TypeScript 2.3 which does not have support for weak types handling.
    type SpecialEventHook<TTarget, TData> = {
        /**
         * Indicates whether this event type should be bubbled when the `.trigger()` method is called; by default it is `false`, meaning that a triggered event will bubble to the element's parents up to the document (if attached to a document) and then to the window. Note that defining `noBubble` on an event will effectively prevent that event from being used for delegated events with `.trigger()`.
         * @see \`{@link https://learn.jquery.com/events/event-extensions/#nobubble-boolean }\`
         */
        noBubble: boolean;
    } | {
        /**
         * When defined, these string properties specify that a special event should be handled like another event type until the event is delivered. The `bindType` is used if the event is attached directly, and the `delegateType` is used for delegated events. These types are generally DOM event types, and _should not_ be a special event themselves.
         * @see \`{@link https://learn.jquery.com/events/event-extensions/#bindtype-string-delegatetype-string }\`
         */
        bindType: string;
    } | {
        /**
         * When defined, these string properties specify that a special event should be handled like another event type until the event is delivered. The `bindType` is used if the event is attached directly, and the `delegateType` is used for delegated events. These types are generally DOM event types, and _should not_ be a special event themselves.
         * @see \`{@link https://learn.jquery.com/events/event-extensions/#bindtype-string-delegatetype-string }\`
         */
        delegateType: string;
    } | {
        /**
         * The setup hook is called the first time an event of a particular type is attached to an element; this provides the hook an opportunity to do processing that will apply to all events of this type on this element. The `this` keyword will be a reference to the element where the event is being attached and `eventHandle` is jQuery's event handler function. In most cases the `namespaces` argument should not be used, since it only represents the namespaces of the _first_ event being attached; subsequent events may not have this same namespaces.
         *
         * This hook can perform whatever processing it desires, including attaching its own event handlers to the element or to other elements and recording setup information on the element using the `jQuery.data()` method. If the setup hook wants jQuery to add a browser event (via `addEventListener` or `attachEvent`, depending on browser) it should return `false`. In all other cases, jQuery will not add the browser event, but will continue all its other bookkeeping for the event. This would be appropriate, for example, if the event was never fired by the browser but invoked by `.trigger()`. To attach the jQuery event handler in the setup hook, use the `eventHandle` argument.
         * @see \`{@link https://learn.jquery.com/events/event-extensions/#setup-function-data-object-namespaces-eventhandle-function }\`
         */
        setup(this: TTarget, data: TData, namespaces: string, eventHandle: EventHandler<TTarget, TData>): void | false;
    } | {
        /**
         * The teardown hook is called when the final event of a particular type is removed from an element. The `this` keyword will be a reference to the element where the event is being cleaned up. This hook should return `false` if it wants jQuery to remove the event from the browser's event system (via `removeEventListener` or `detachEvent`). In most cases, the setup and teardown hooks should return the same value.
         *
         * If the setup hook attached event handlers or added data to an element through a mechanism such as `jQuery.data()`, the teardown hook should reverse the process and remove them. jQuery will generally remove the data and events when an element is totally removed from the document, but failing to remove data or events on teardown will cause a memory leak if the element stays in the document.
         * @see \`{@link https://learn.jquery.com/events/event-extensions/#teardown-function }\`
         */
        teardown(this: TTarget): void | false;
    } | {
        /**
         * Each time an event handler is added to an element through an API such as `.on()`, jQuery calls this hook. The `this` keyword will be the element to which the event handler is being added, and the `handleObj` argument is as described in the section above. The return value of this hook is ignored.
         * @see \`{@link https://learn.jquery.com/events/event-extensions/#add-function-handleobj }\`
         */
        add(this: TTarget, handleObj: HandleObject<TTarget, TData>): void;
    } | {
        /**
         * When an event handler is removed from an element using an API such as `.off()`, this hook is called. The `this` keyword will be the element where the handler is being removed, and the `handleObj` argument is as described in the section above. The return value of this hook is ignored.
         * @see \`{@link https://learn.jquery.com/events/event-extensions/#remove-function-handleobj }\`
         */
        remove(this: TTarget, handleObj: HandleObject<TTarget, TData>): void;
    } | {
        /**
         * Called when the `.trigger()` or `.triggerHandler()` methods are used to trigger an event for the special type from code, as opposed to events that originate from within the browser. The `this` keyword will be the element being triggered, and the event argument will be a `jQuery.Event` object constructed from the caller's input. At minimum, the event type, data, namespace, and target properties are set on the event. The data argument represents additional data passed by `.trigger()` if present.
         *
         * The trigger hook is called early in the process of triggering an event, just after the `jQuery.Event` object is constructed and before any handlers have been called. It can process the triggered event in any way, for example by calling `event.stopPropagation()` or `event.preventDefault()` before returning. If the hook returns `false`, jQuery does not perform any further event triggering actions and returns immediately. Otherwise, it performs the normal trigger processing, calling any event handlers for the element and bubbling the event (unless propagation is stopped in advance or `noBubble` was specified for the special event) to call event handlers attached to parent elements.
         * @see \`{@link https://learn.jquery.com/events/event-extensions/#trigger-function-event-jquery-event-data-object }\`
         */
        trigger(this: TTarget, event: Event, data: TData): void | false;
    } | {
        /**
         * When the `.trigger()` method finishes running all the event handlers for an event, it also looks for and runs any method on the target object by the same name unless of the handlers called `event.preventDefault()`. So, `.trigger( "submit" )` will execute the `submit()` method on the element if one exists. When a `_default` hook is specified, the hook is called just prior to checking for and executing the element's default method. If this hook returns the value `false` the element's default method will be called; otherwise it is not.
         * @see \`{@link https://learn.jquery.com/events/event-extensions/#_default-function-event-jquery-event-data-object }\`
         */
        _default(event: TriggeredEvent<TTarget, TData>, data: TData): void | false;
    } | {
        /**
         * jQuery calls a handle hook when the event has occurred and jQuery would normally call the user's event handler specified by `.on()` or another event binding method. If the hook exists, jQuery calls it _instead_ of that event handler, passing it the event and any data passed from `.trigger()` if it was not a native event. The `this` keyword is the DOM element being handled, and `event.handleObj` property has the detailed event information.
         *
         * Based in the information it has, the handle hook should decide whether to call the original handler function which is in `event.handleObj.handler`. It can modify information in the event object before calling the original handler, but _must restore_ that data before returning or subsequent unrelated event handlers may act unpredictably. In most cases, the handle hook should return the result of the original handler, but that is at the discretion of the hook. The handle hook is unique in that it is the only special event function hook that is called under its original special event name when the type is mapped using `bindType` and `delegateType`. For that reason, it is almost always an error to have anything other than a handle hook present if the special event defines a `bindType` and `delegateType`, since those other hooks will never be called.
         * @see \`{@link https://learn.jquery.com/events/event-extensions/#handle-function-event-jquery-event-data-object }\`
         */
        handle(this: TTarget, event: TriggeredEvent<TTarget, TData> & { handleObj: HandleObject<TTarget, TData>; }, ...data: TData[]): void;
    } | {
        preDispatch(this: TTarget, event: Event): false | void;
    } | {
        postDispatch(this: TTarget, event: Event): void;
    } | {
        [key: string]: never;
    };

    interface SpecialEventHooks {
        [event: string]: SpecialEventHook<EventTarget, any>;
    }

    /**
     * Many of the special event hook functions below are passed a `handleObj` object that provides more information about the event, how it was attached, and its current state. This object and its contents should be treated as read-only data, and only the properties below are documented for use by special event handlers.
     * @see \`{@link https://learn.jquery.com/events/event-extensions/#the-handleobj-object }\`
     */
    interface HandleObject<TTarget, TData> {
        /**
         * The type of event, such as `"click"`. When special event mapping is used via `bindType` or `delegateType`, this will be the mapped type.
         */
        readonly type: string;
        /**
         * The original type name regardless of whether it was mapped via `bindType` or `delegateType`. So when a "pushy" event is mapped to "click" its `origType` would be "pushy".
         */
        readonly origType: string;
        /**
         * Namespace(s), if any, provided when the event was attached, such as `"myPlugin"`. When multiple namespaces are given, they are separated by periods and sorted in ascending alphabetical order. If no namespaces are provided, this property is an empty string.
         */
        readonly namespace: string;
        /**
         * For delegated events, this is the selector used to filter descendant elements and determine if the handler should be called. For directly bound events, this property is `null`.
         */
        readonly selector: string | undefined | null;
        /**
         * The data, if any, passed to jQuery during event binding, e.g. `{ myData: 42 }`. If the data argument was omitted or `undefined`, this property is `undefined` as well.
         */
        readonly data: TData;
        /**
         * Event handler function passed to jQuery during event binding. If `false` was passed during event binding, the handler refers to a single shared function that simply returns `false`.
         */
        readonly handler: EventHandler<TTarget, TData>;
    }

    // #endregion

    // #endregion

    // #endregion

    interface NameValuePair {
        name: string;
        value: string;
    }

    // region Coordinates
    // #region Coordinates

    interface Coordinates {
        left: number;
        top: number;
    }

    // Workaround for TypeScript 2.3 which does not have support for weak types handling.
    type CoordinatesPartial =
        Pick<Coordinates, 'left'> |
        Pick<Coordinates, 'top'> |
        { [key: string]: never; };

    // #endregion

    // region Val hooks
    // #region Val hooks

    // Workaround for TypeScript 2.3 which does not have support for weak types handling.
    type ValHook<TElement> = {
        get(elem: TElement): any;
    } | {
        set(elem: TElement, value: any): any;
    } | {
        [key: string]: never;
    };

    interface ValHooks {
        // Set to HTMLElement to minimize breaks but should probably be Element.
        [nodeName: string]: ValHook<HTMLElement>;
    }

    // #endregion

    type _Falsy = false | null | undefined | 0 | '' | typeof document.all;
}

declare const jQuery: JQueryStatic;
declare const $: JQueryStatic;

type _Event = Event;
type _UIEvent = UIEvent;
type _MouseEvent = MouseEvent;
type _DragEvent = DragEvent;
type _KeyboardEvent = KeyboardEvent;
type _TouchEvent = TouchEvent;
type _FocusEvent = FocusEvent;

// region ES5 compatibility
// #region ES5 compatibility

// Forward declaration of `Iterable<T>`.
// tslint:disable-next-line:no-empty-interface
interface Iterable<T> { }

interface SymbolConstructor {
    /**
     * A String value that is used in the creation of the default string description of an object.
     * Called by the built-in method Object.prototype.toString.
     */
    readonly toStringTag: symbol;
}

declare var Symbol: SymbolConstructor;

// #endregion
