/**
 * Actions represent the type of change to a location value.
 */
export declare enum Action {
    /**
     * A POP indicates a change to an arbitrary index in the history stack, such
     * as a back or forward navigation. It does not describe the direction of the
     * navigation, only that the current index changed.
     *
     * Note: This is the default action for newly created history objects.
     */
    Pop = "POP",
    /**
     * A PUSH indicates a new entry being added to the history stack, such as when
     * a link is clicked and a new page loads. When this happens, all subsequent
     * entries in the stack are lost.
     */
    Push = "PUSH",
    /**
     * A REPLACE indicates the entry at the current index in the history stack
     * being replaced by a new one.
     */
    Replace = "REPLACE"
}
/**
 * The pathname, search, and hash values of a URL.
 */
export interface Path {
    /**
     * A URL pathname, beginning with a /.
     */
    pathname: string;
    /**
     * A URL search string, beginning with a ?.
     */
    search: string;
    /**
     * A URL fragment identifier, beginning with a #.
     */
    hash: string;
}
/**
 * An entry in a history stack. A location contains information about the
 * URL path, as well as possibly some arbitrary state and a key.
 */
export interface Location<State = any> extends Path {
    /**
     * A value of arbitrary data associated with this location.
     */
    state: State;
    /**
     * A unique string associated with this location. May be used to safely store
     * and retrieve data in some other storage API, like `localStorage`.
     *
     * Note: This value is always "default" on the initial location.
     */
    key: string;
}
/**
 * A change to the current location.
 */
export interface Update {
    /**
     * The action that triggered the change.
     */
    action: Action;
    /**
     * The new location.
     */
    location: Location;
    /**
     * The delta between this location and the former location in the history stack
     */
    delta: number | null;
}
/**
 * A function that receives notifications about location changes.
 */
export interface Listener {
    (update: Update): void;
}
/**
 * Describes a location that is the destination of some navigation, either via
 * `history.push` or `history.replace`. This may be either a URL or the pieces
 * of a URL path.
 */
export type To = string | Partial<Path>;
/**
 * A history is an interface to the navigation stack. The history serves as the
 * source of truth for the current location, as well as provides a set of
 * methods that may be used to change it.
 *
 * It is similar to the DOM's `window.history` object, but with a smaller, more
 * focused API.
 */
export interface History {
    /**
     * The last action that modified the current location. This will always be
     * Action.Pop when a history instance is first created. This value is mutable.
     */
    readonly action: Action;
    /**
     * The current location. This value is mutable.
     */
    readonly location: Location;
    /**
     * Returns a valid href for the given `to` value that may be used as
     * the value of an <a href> attribute.
     *
     * @param to - The destination URL
     */
    createHref(to: To): string;
    /**
     * Returns a URL for the given `to` value
     *
     * @param to - The destination URL
     */
    createURL(to: To): URL;
    /**
     * Encode a location the same way window.history would do (no-op for memory
     * history) so we ensure our PUSH/REPLACE navigations for data routers
     * behave the same as POP
     *
     * @param to Unencoded path
     */
    encodeLocation(to: To): Path;
    /**
     * Pushes a new location onto the history stack, increasing its length by one.
     * If there were any entries in the stack after the current one, they are
     * lost.
     *
     * @param to - The new URL
     * @param state - Data to associate with the new location
     */
    push(to: To, state?: any): void;
    /**
     * Replaces the current location in the history stack with a new one.  The
     * location that was replaced will no longer be available.
     *
     * @param to - The new URL
     * @param state - Data to associate with the new location
     */
    replace(to: To, state?: any): void;
    /**
     * Navigates `n` entries backward/forward in the history stack relative to the
     * current index. For example, a "back" navigation would use go(-1).
     *
     * @param delta - The delta in the stack index
     */
    go(delta: number): void;
    /**
     * Sets up a listener that will be called whenever the current location
     * changes.
     *
     * @param listener - A function that will be called when the location changes
     * @returns unlisten - A function that may be used to stop listening
     */
    listen(listener: Listener): () => void;
}
/**
 * A user-supplied object that describes a location. Used when providing
 * entries to `createMemoryHistory` via its `initialEntries` option.
 */
export type InitialEntry = string | Partial<Location>;
export type MemoryHistoryOptions = {
    initialEntries?: InitialEntry[];
    initialIndex?: number;
    v5Compat?: boolean;
};
/**
 * A memory history stores locations in memory. This is useful in stateful
 * environments where there is no web browser, such as node tests or React
 * Native.
 */
export interface MemoryHistory extends History {
    /**
     * The current index in the history stack.
     */
    readonly index: number;
}
/**
 * Memory history stores the current location in memory. It is designed for use
 * in stateful non-browser environments like tests and React Native.
 */
export declare function createMemoryHistory(options?: MemoryHistoryOptions): MemoryHistory;
/**
 * A browser history stores the current location in regular URLs in a web
 * browser environment. This is the standard for most web apps and provides the
 * cleanest URLs the browser's address bar.
 *
 * @see https://github.com/remix-run/history/tree/main/docs/api-reference.md#browserhistory
 */
export interface BrowserHistory extends UrlHistory {
}
export type BrowserHistoryOptions = UrlHistoryOptions;
/**
 * Browser history stores the location in regular URLs. This is the standard for
 * most web apps, but it requires some configuration on the server to ensure you
 * serve the same app at multiple URLs.
 *
 * @see https://github.com/remix-run/history/tree/main/docs/api-reference.md#createbrowserhistory
 */
export declare function createBrowserHistory(options?: BrowserHistoryOptions): BrowserHistory;
/**
 * A hash history stores the current location in the fragment identifier portion
 * of the URL in a web browser environment.
 *
 * This is ideal for apps that do not control the server for some reason
 * (because the fragment identifier is never sent to the server), including some
 * shared hosting environments that do not provide fine-grained controls over
 * which pages are served at which URLs.
 *
 * @see https://github.com/remix-run/history/tree/main/docs/api-reference.md#hashhistory
 */
export interface HashHistory extends UrlHistory {
}
export type HashHistoryOptions = UrlHistoryOptions;
/**
 * Hash history stores the location in window.location.hash. This makes it ideal
 * for situations where you don't want to send the location to the server for
 * some reason, either because you do cannot configure it or the URL space is
 * reserved for something else.
 *
 * @see https://github.com/remix-run/history/tree/main/docs/api-reference.md#createhashhistory
 */
export declare function createHashHistory(options?: HashHistoryOptions): HashHistory;
/**
 * @private
 */
export declare function invariant(value: boolean, message?: string): asserts value;
export declare function invariant<T>(value: T | null | undefined, message?: string): asserts value is T;
export declare function warning(cond: any, message: string): void;
/**
 * Creates a Location object with a unique key from the given Path
 */
export declare function createLocation(current: string | Location, to: To, state?: any, key?: string): Readonly<Location>;
/**
 * Creates a string URL path from the given pathname, search, and hash components.
 */
export declare function createPath({ pathname, search, hash, }: Partial<Path>): string;
/**
 * Parses a string URL path into its separate pathname, search, and hash components.
 */
export declare function parsePath(path: string): Partial<Path>;
export interface UrlHistory extends History {
}
export type UrlHistoryOptions = {
    window?: Window;
    v5Compat?: boolean;
};
