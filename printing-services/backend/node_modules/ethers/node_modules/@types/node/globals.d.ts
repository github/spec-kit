export {}; // Make this a module

// #region Fetch and friends
// Conditional type aliases, used at the end of this file.
// Will either be empty if lib.dom (or lib.webworker) is included, or the undici version otherwise.
type _Request = typeof globalThis extends { onmessage: any } ? {} : import("undici-types").Request;
type _Response = typeof globalThis extends { onmessage: any } ? {} : import("undici-types").Response;
type _FormData = typeof globalThis extends { onmessage: any } ? {} : import("undici-types").FormData;
type _Headers = typeof globalThis extends { onmessage: any } ? {} : import("undici-types").Headers;
type _MessageEvent = typeof globalThis extends { onmessage: any } ? {} : import("undici-types").MessageEvent;
type _RequestInit = typeof globalThis extends { onmessage: any } ? {}
    : import("undici-types").RequestInit;
type _ResponseInit = typeof globalThis extends { onmessage: any } ? {}
    : import("undici-types").ResponseInit;
type _WebSocket = typeof globalThis extends { onmessage: any } ? {} : import("undici-types").WebSocket;
type _EventSource = typeof globalThis extends { onmessage: any } ? {} : import("undici-types").EventSource;
// #endregion Fetch and friends

// Conditional type definitions for webstorage interface, which conflicts with lib.dom otherwise.
type _Storage = typeof globalThis extends { onabort: any } ? {} : {
    /**
     * Returns the number of key/value pairs.
     *
     * [MDN Reference](https://developer.mozilla.org/docs/Web/API/Storage/length)
     */
    readonly length: number;
    /**
     * Removes all key/value pairs, if there are any.
     *
     * [MDN Reference](https://developer.mozilla.org/docs/Web/API/Storage/clear)
     */
    clear(): void;
    /**
     * Returns the current value associated with the given key, or null if the given key does not exist.
     *
     * [MDN Reference](https://developer.mozilla.org/docs/Web/API/Storage/getItem)
     */
    getItem(key: string): string | null;
    /**
     * Returns the name of the nth key, or null if n is greater than or equal to the number of key/value pairs.
     *
     * [MDN Reference](https://developer.mozilla.org/docs/Web/API/Storage/key)
     */
    key(index: number): string | null;
    /**
     * Removes the key/value pair with the given key, if a key/value pair with the given key exists.
     *
     * [MDN Reference](https://developer.mozilla.org/docs/Web/API/Storage/removeItem)
     */
    removeItem(key: string): void;
    /**
     * Sets the value of the pair identified by key to value, creating a new key/value pair if none existed for key previously.
     *
     * Throws a "QuotaExceededError" DOMException exception if the new value couldn't be set.
     *
     * [MDN Reference](https://developer.mozilla.org/docs/Web/API/Storage/setItem)
     */
    setItem(key: string, value: string): void;
    [key: string]: any;
};

// #region DOMException
type _DOMException = typeof globalThis extends { onmessage: any } ? {} : NodeDOMException;
interface NodeDOMException extends Error {
    /**
     * @deprecated
     *
     * [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMException/code)
     */
    readonly code: number;
    /** [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMException/message) */
    readonly message: string;
    /** [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMException/name) */
    readonly name: string;
    readonly INDEX_SIZE_ERR: 1;
    readonly DOMSTRING_SIZE_ERR: 2;
    readonly HIERARCHY_REQUEST_ERR: 3;
    readonly WRONG_DOCUMENT_ERR: 4;
    readonly INVALID_CHARACTER_ERR: 5;
    readonly NO_DATA_ALLOWED_ERR: 6;
    readonly NO_MODIFICATION_ALLOWED_ERR: 7;
    readonly NOT_FOUND_ERR: 8;
    readonly NOT_SUPPORTED_ERR: 9;
    readonly INUSE_ATTRIBUTE_ERR: 10;
    readonly INVALID_STATE_ERR: 11;
    readonly SYNTAX_ERR: 12;
    readonly INVALID_MODIFICATION_ERR: 13;
    readonly NAMESPACE_ERR: 14;
    readonly INVALID_ACCESS_ERR: 15;
    readonly VALIDATION_ERR: 16;
    readonly TYPE_MISMATCH_ERR: 17;
    readonly SECURITY_ERR: 18;
    readonly NETWORK_ERR: 19;
    readonly ABORT_ERR: 20;
    readonly URL_MISMATCH_ERR: 21;
    readonly QUOTA_EXCEEDED_ERR: 22;
    readonly TIMEOUT_ERR: 23;
    readonly INVALID_NODE_TYPE_ERR: 24;
    readonly DATA_CLONE_ERR: 25;
}
interface NodeDOMExceptionConstructor {
    prototype: DOMException;
    new(message?: string, nameOrOptions?: string | { name?: string; cause?: unknown }): DOMException;
    readonly INDEX_SIZE_ERR: 1;
    readonly DOMSTRING_SIZE_ERR: 2;
    readonly HIERARCHY_REQUEST_ERR: 3;
    readonly WRONG_DOCUMENT_ERR: 4;
    readonly INVALID_CHARACTER_ERR: 5;
    readonly NO_DATA_ALLOWED_ERR: 6;
    readonly NO_MODIFICATION_ALLOWED_ERR: 7;
    readonly NOT_FOUND_ERR: 8;
    readonly NOT_SUPPORTED_ERR: 9;
    readonly INUSE_ATTRIBUTE_ERR: 10;
    readonly INVALID_STATE_ERR: 11;
    readonly SYNTAX_ERR: 12;
    readonly INVALID_MODIFICATION_ERR: 13;
    readonly NAMESPACE_ERR: 14;
    readonly INVALID_ACCESS_ERR: 15;
    readonly VALIDATION_ERR: 16;
    readonly TYPE_MISMATCH_ERR: 17;
    readonly SECURITY_ERR: 18;
    readonly NETWORK_ERR: 19;
    readonly ABORT_ERR: 20;
    readonly URL_MISMATCH_ERR: 21;
    readonly QUOTA_EXCEEDED_ERR: 22;
    readonly TIMEOUT_ERR: 23;
    readonly INVALID_NODE_TYPE_ERR: 24;
    readonly DATA_CLONE_ERR: 25;
}
// #endregion DOMException

declare global {
    // Declare "static" methods in Error
    interface ErrorConstructor {
        /** Create .stack property on a target object */
        captureStackTrace(targetObject: object, constructorOpt?: Function): void;

        /**
         * Optional override for formatting stack traces
         *
         * @see https://v8.dev/docs/stack-trace-api#customizing-stack-traces
         */
        prepareStackTrace?: ((err: Error, stackTraces: NodeJS.CallSite[]) => any) | undefined;

        stackTraceLimit: number;
    }

    /*-----------------------------------------------*
    *                                               *
    *                   GLOBAL                      *
    *                                               *
    ------------------------------------------------*/

    // For backwards compability
    interface NodeRequire extends NodeJS.Require {}
    interface RequireResolve extends NodeJS.RequireResolve {}
    interface NodeModule extends NodeJS.Module {}

    var process: NodeJS.Process;
    var console: Console;

    var __filename: string;
    var __dirname: string;

    var require: NodeRequire;
    var module: NodeModule;

    // Same as module.exports
    var exports: any;

    interface GCFunction {
        (options: {
            execution?: "sync";
            flavor?: "regular" | "last-resort";
            type?: "major-snapshot" | "major" | "minor";
            filename?: string;
        }): void;
        (options: {
            execution: "async";
            flavor?: "regular" | "last-resort";
            type?: "major-snapshot" | "major" | "minor";
            filename?: string;
        }): Promise<void>;
        (options?: boolean): void;
    }

    /**
     * Only available if `--expose-gc` is passed to the process.
     */
    var gc: undefined | GCFunction;

    // #region borrowed
    // from https://github.com/microsoft/TypeScript/blob/38da7c600c83e7b31193a62495239a0fe478cb67/lib/lib.webworker.d.ts#L633 until moved to separate lib
    /** A controller object that allows you to abort one or more DOM requests as and when desired. */
    interface AbortController {
        /**
         * Returns the AbortSignal object associated with this object.
         */

        readonly signal: AbortSignal;
        /**
         * Invoking this method will set this object's AbortSignal's aborted flag and signal to any observers that the associated activity is to be aborted.
         */
        abort(reason?: any): void;
    }

    /** A signal object that allows you to communicate with a DOM request (such as a Fetch) and abort it if required via an AbortController object. */
    interface AbortSignal extends EventTarget {
        /**
         * Returns true if this AbortSignal's AbortController has signaled to abort, and false otherwise.
         */
        readonly aborted: boolean;
        readonly reason: any;
        onabort: null | ((this: AbortSignal, event: Event) => any);
        throwIfAborted(): void;
    }

    var AbortController: typeof globalThis extends { onmessage: any; AbortController: infer T } ? T
        : {
            prototype: AbortController;
            new(): AbortController;
        };

    var AbortSignal: typeof globalThis extends { onmessage: any; AbortSignal: infer T } ? T
        : {
            prototype: AbortSignal;
            new(): AbortSignal;
            abort(reason?: any): AbortSignal;
            timeout(milliseconds: number): AbortSignal;
            any(signals: AbortSignal[]): AbortSignal;
        };
    // #endregion borrowed

    // #region Storage
    /**
     * This Web Storage API interface provides access to a particular domain's session or local storage. It allows, for example, the addition, modification, or deletion of stored data items.
     *
     * [MDN Reference](https://developer.mozilla.org/docs/Web/API/Storage)
     */
    interface Storage extends _Storage {}

    // Conditional on `onabort` rather than `onmessage`, in order to exclude lib.webworker
    var Storage: typeof globalThis extends { onabort: any; Storage: infer T } ? T
        : {
            prototype: Storage;
            new(): Storage;
        };

    /**
     * A browser-compatible implementation of [`localStorage`](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage).
     * Data is stored unencrypted in the file specified by the `--localstorage-file` CLI flag.
     * Any modification of this data outside of the Web Storage API is not supported.
     * Enable this API with the `--experimental-webstorage` CLI flag.
     * @since v22.4.0
     */
    var localStorage: Storage;

    /**
     * A browser-compatible implementation of [`sessionStorage`](https://developer.mozilla.org/en-US/docs/Web/API/Window/sessionStorage).
     * Data is stored in memory, with a storage quota of 10 MB.
     * Any modification of this data outside of the Web Storage API is not supported.
     * Enable this API with the `--experimental-webstorage` CLI flag.
     * @since v22.4.0
     */
    var sessionStorage: Storage;
    // #endregion Storage

    // #region Disposable
    interface SymbolConstructor {
        /**
         * A method that is used to release resources held by an object. Called by the semantics of the `using` statement.
         */
        readonly dispose: unique symbol;

        /**
         * A method that is used to asynchronously release resources held by an object. Called by the semantics of the `await using` statement.
         */
        readonly asyncDispose: unique symbol;
    }

    interface Disposable {
        [Symbol.dispose](): void;
    }

    interface AsyncDisposable {
        [Symbol.asyncDispose](): PromiseLike<void>;
    }
    // #endregion Disposable

    // #region ArrayLike.at()
    interface RelativeIndexable<T> {
        /**
         * Takes an integer value and returns the item at that index,
         * allowing for positive and negative integers.
         * Negative integers count back from the last item in the array.
         */
        at(index: number): T | undefined;
    }
    interface String extends RelativeIndexable<string> {}
    interface Array<T> extends RelativeIndexable<T> {}
    interface ReadonlyArray<T> extends RelativeIndexable<T> {}
    interface Int8Array extends RelativeIndexable<number> {}
    interface Uint8Array extends RelativeIndexable<number> {}
    interface Uint8ClampedArray extends RelativeIndexable<number> {}
    interface Int16Array extends RelativeIndexable<number> {}
    interface Uint16Array extends RelativeIndexable<number> {}
    interface Int32Array extends RelativeIndexable<number> {}
    interface Uint32Array extends RelativeIndexable<number> {}
    interface Float32Array extends RelativeIndexable<number> {}
    interface Float64Array extends RelativeIndexable<number> {}
    interface BigInt64Array extends RelativeIndexable<bigint> {}
    interface BigUint64Array extends RelativeIndexable<bigint> {}
    // #endregion ArrayLike.at() end

    /**
     * @since v17.0.0
     *
     * Creates a deep clone of an object.
     */
    function structuredClone<T>(
        value: T,
        transfer?: { transfer: ReadonlyArray<import("worker_threads").TransferListItem> },
    ): T;

    // #region DOMException
    /**
     * @since v17.0.0
     * An abnormal event (called an exception) which occurs as a result of calling a method or accessing a property of a web API.
     *
     * [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMException)
     */
    interface DOMException extends _DOMException {}

    /**
     * @since v17.0.0
     *
     * The WHATWG `DOMException` class. See [DOMException](https://developer.mozilla.org/docs/Web/API/DOMException) for more details.
     */
    var DOMException: typeof globalThis extends { onmessage: any; DOMException: infer T } ? T
        : NodeDOMExceptionConstructor;
    // #endregion DOMException

    /*----------------------------------------------*
    *                                               *
    *               GLOBAL INTERFACES               *
    *                                               *
    *-----------------------------------------------*/
    namespace NodeJS {
        interface CallSite {
            /**
             * Value of "this"
             */
            getThis(): unknown;

            /**
             * Type of "this" as a string.
             * This is the name of the function stored in the constructor field of
             * "this", if available.  Otherwise the object's [[Class]] internal
             * property.
             */
            getTypeName(): string | null;

            /**
             * Current function
             */
            getFunction(): Function | undefined;

            /**
             * Name of the current function, typically its name property.
             * If a name property is not available an attempt will be made to try
             * to infer a name from the function's context.
             */
            getFunctionName(): string | null;

            /**
             * Name of the property [of "this" or one of its prototypes] that holds
             * the current function
             */
            getMethodName(): string | null;

            /**
             * Name of the script [if this function was defined in a script]
             */
            getFileName(): string | undefined;

            /**
             * Current line number [if this function was defined in a script]
             */
            getLineNumber(): number | null;

            /**
             * Current column number [if this function was defined in a script]
             */
            getColumnNumber(): number | null;

            /**
             * A call site object representing the location where eval was called
             * [if this function was created using a call to eval]
             */
            getEvalOrigin(): string | undefined;

            /**
             * Is this a toplevel invocation, that is, is "this" the global object?
             */
            isToplevel(): boolean;

            /**
             * Does this call take place in code defined by a call to eval?
             */
            isEval(): boolean;

            /**
             * Is this call in native V8 code?
             */
            isNative(): boolean;

            /**
             * Is this a constructor call?
             */
            isConstructor(): boolean;

            /**
             * is this an async call (i.e. await, Promise.all(), or Promise.any())?
             */
            isAsync(): boolean;

            /**
             * is this an async call to Promise.all()?
             */
            isPromiseAll(): boolean;

            /**
             * returns the index of the promise element that was followed in
             * Promise.all() or Promise.any() for async stack traces, or null
             * if the CallSite is not an async
             */
            getPromiseIndex(): number | null;

            getScriptNameOrSourceURL(): string;
            getScriptHash(): string;

            getEnclosingColumnNumber(): number;
            getEnclosingLineNumber(): number;
            getPosition(): number;

            toString(): string;
        }

        interface ErrnoException extends Error {
            errno?: number | undefined;
            code?: string | undefined;
            path?: string | undefined;
            syscall?: string | undefined;
        }

        interface ReadableStream extends EventEmitter {
            readable: boolean;
            read(size?: number): string | Buffer;
            setEncoding(encoding: BufferEncoding): this;
            pause(): this;
            resume(): this;
            isPaused(): boolean;
            pipe<T extends WritableStream>(destination: T, options?: { end?: boolean | undefined }): T;
            unpipe(destination?: WritableStream): this;
            unshift(chunk: string | Uint8Array, encoding?: BufferEncoding): void;
            wrap(oldStream: ReadableStream): this;
            [Symbol.asyncIterator](): AsyncIterableIterator<string | Buffer>;
        }

        interface WritableStream extends EventEmitter {
            writable: boolean;
            write(buffer: Uint8Array | string, cb?: (err?: Error | null) => void): boolean;
            write(str: string, encoding?: BufferEncoding, cb?: (err?: Error | null) => void): boolean;
            end(cb?: () => void): this;
            end(data: string | Uint8Array, cb?: () => void): this;
            end(str: string, encoding?: BufferEncoding, cb?: () => void): this;
        }

        interface ReadWriteStream extends ReadableStream, WritableStream {}

        interface RefCounted {
            ref(): this;
            unref(): this;
        }

        interface Require {
            (id: string): any;
            resolve: RequireResolve;
            cache: Dict<NodeModule>;
            /**
             * @deprecated
             */
            extensions: RequireExtensions;
            main: Module | undefined;
        }

        interface RequireResolve {
            (id: string, options?: { paths?: string[] | undefined }): string;
            paths(request: string): string[] | null;
        }

        interface RequireExtensions extends Dict<(m: Module, filename: string) => any> {
            ".js": (m: Module, filename: string) => any;
            ".json": (m: Module, filename: string) => any;
            ".node": (m: Module, filename: string) => any;
        }
        interface Module {
            /**
             * `true` if the module is running during the Node.js preload
             */
            isPreloading: boolean;
            exports: any;
            require: Require;
            id: string;
            filename: string;
            loaded: boolean;
            /** @deprecated since v14.6.0 Please use `require.main` and `module.children` instead. */
            parent: Module | null | undefined;
            children: Module[];
            /**
             * @since v11.14.0
             *
             * The directory name of the module. This is usually the same as the path.dirname() of the module.id.
             */
            path: string;
            paths: string[];
        }

        interface Dict<T> {
            [key: string]: T | undefined;
        }

        interface ReadOnlyDict<T> {
            readonly [key: string]: T | undefined;
        }
    }

    interface RequestInit extends _RequestInit {}

    function fetch(
        input: string | URL | globalThis.Request,
        init?: RequestInit,
    ): Promise<Response>;

    interface Request extends _Request {}
    var Request: typeof globalThis extends {
        onmessage: any;
        Request: infer T;
    } ? T
        : typeof import("undici-types").Request;

    interface ResponseInit extends _ResponseInit {}

    interface Response extends _Response {}
    var Response: typeof globalThis extends {
        onmessage: any;
        Response: infer T;
    } ? T
        : typeof import("undici-types").Response;

    interface FormData extends _FormData {}
    var FormData: typeof globalThis extends {
        onmessage: any;
        FormData: infer T;
    } ? T
        : typeof import("undici-types").FormData;

    interface Headers extends _Headers {}
    var Headers: typeof globalThis extends {
        onmessage: any;
        Headers: infer T;
    } ? T
        : typeof import("undici-types").Headers;

    interface MessageEvent extends _MessageEvent {}
    /**
     * @since v15.0.0
     */
    var MessageEvent: typeof globalThis extends {
        onmessage: any;
        MessageEvent: infer T;
    } ? T
        : typeof import("undici-types").MessageEvent;

    interface WebSocket extends _WebSocket {}
    var WebSocket: typeof globalThis extends { onmessage: any; WebSocket: infer T } ? T
        : typeof import("undici-types").WebSocket;

    interface EventSource extends _EventSource {}
    /**
     * Only available through the [--experimental-eventsource](https://nodejs.org/api/cli.html#--experimental-eventsource) flag.
     *
     * @since v22.3.0
     */
    var EventSource: typeof globalThis extends { onmessage: any; EventSource: infer T } ? T
        : typeof import("undici-types").EventSource;
}
