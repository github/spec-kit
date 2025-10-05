import type { FormEncType, HTMLFormMethod, RelativeRoutingType } from "@remix-run/router";
export declare const defaultMethod: HTMLFormMethod;
export declare function isHtmlElement(object: any): object is HTMLElement;
export declare function isButtonElement(object: any): object is HTMLButtonElement;
export declare function isFormElement(object: any): object is HTMLFormElement;
export declare function isInputElement(object: any): object is HTMLInputElement;
type LimitedMouseEvent = Pick<MouseEvent, "button" | "metaKey" | "altKey" | "ctrlKey" | "shiftKey">;
export declare function shouldProcessLinkClick(event: LimitedMouseEvent, target?: string): boolean;
export type ParamKeyValuePair = [string, string];
export type URLSearchParamsInit = string | ParamKeyValuePair[] | Record<string, string | string[]> | URLSearchParams;
/**
 * Creates a URLSearchParams object using the given initializer.
 *
 * This is identical to `new URLSearchParams(init)` except it also
 * supports arrays as values in the object form of the initializer
 * instead of just strings. This is convenient when you need multiple
 * values for a given key, but don't want to use an array initializer.
 *
 * For example, instead of:
 *
 *   let searchParams = new URLSearchParams([
 *     ['sort', 'name'],
 *     ['sort', 'price']
 *   ]);
 *
 * you can do:
 *
 *   let searchParams = createSearchParams({
 *     sort: ['name', 'price']
 *   });
 */
export declare function createSearchParams(init?: URLSearchParamsInit): URLSearchParams;
export declare function getSearchParamsForLocation(locationSearch: string, defaultSearchParams: URLSearchParams | null): URLSearchParams;
type JsonObject = {
    [Key in string]: JsonValue;
} & {
    [Key in string]?: JsonValue | undefined;
};
type JsonArray = JsonValue[] | readonly JsonValue[];
type JsonPrimitive = string | number | boolean | null;
type JsonValue = JsonPrimitive | JsonObject | JsonArray;
export type SubmitTarget = HTMLFormElement | HTMLButtonElement | HTMLInputElement | FormData | URLSearchParams | JsonValue | null;
/**
 * Submit options shared by both navigations and fetchers
 */
interface SharedSubmitOptions {
    /**
     * The HTTP method used to submit the form. Overrides `<form method>`.
     * Defaults to "GET".
     */
    method?: HTMLFormMethod;
    /**
     * The action URL path used to submit the form. Overrides `<form action>`.
     * Defaults to the path of the current route.
     */
    action?: string;
    /**
     * The encoding used to submit the form. Overrides `<form encType>`.
     * Defaults to "application/x-www-form-urlencoded".
     */
    encType?: FormEncType;
    /**
     * Determines whether the form action is relative to the route hierarchy or
     * the pathname.  Use this if you want to opt out of navigating the route
     * hierarchy and want to instead route based on /-delimited URL segments
     */
    relative?: RelativeRoutingType;
    /**
     * In browser-based environments, prevent resetting scroll after this
     * navigation when using the <ScrollRestoration> component
     */
    preventScrollReset?: boolean;
    /**
     * Enable flushSync for this submission's state updates
     */
    flushSync?: boolean;
}
/**
 * Submit options available to fetchers
 */
export interface FetcherSubmitOptions extends SharedSubmitOptions {
}
/**
 * Submit options available to navigations
 */
export interface SubmitOptions extends FetcherSubmitOptions {
    /**
     * Set `true` to replace the current entry in the browser's history stack
     * instead of creating a new one (i.e. stay on "the same page"). Defaults
     * to `false`.
     */
    replace?: boolean;
    /**
     * State object to add to the history stack entry for this navigation
     */
    state?: any;
    /**
     * Indicate a specific fetcherKey to use when using navigate=false
     */
    fetcherKey?: string;
    /**
     * navigate=false will use a fetcher instead of a navigation
     */
    navigate?: boolean;
    /**
     * Enable view transitions on this submission navigation
     */
    viewTransition?: boolean;
}
export declare function getFormSubmissionInfo(target: SubmitTarget, basename: string): {
    action: string | null;
    method: string;
    encType: string;
    formData: FormData | undefined;
    body: any;
};
export {};
