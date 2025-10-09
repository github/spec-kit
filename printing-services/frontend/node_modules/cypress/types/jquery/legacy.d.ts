// tslint:disable:no-irregular-whitespace

// tslint:disable-next-line:no-empty-interface
interface JQueryCallback extends JQuery.Callbacks { }
interface JQueryDeferred<T> extends JQuery.Deferred<T> { }
// tslint:disable-next-line:no-empty-interface
interface JQueryEventConstructor extends JQuery.EventStatic { }
interface JQueryDeferred<T> extends JQuery.Deferred<T> { }
// tslint:disable-next-line:no-empty-interface
interface JQueryAjaxSettings extends JQuery.AjaxSettings { }
interface JQueryAnimationOptions extends JQuery.EffectsOptions<Element> { }
// tslint:disable-next-line:no-empty-interface
interface JQueryCoordinates extends JQuery.Coordinates { }
interface JQueryGenericPromise<T> extends JQuery.Thenable<T> { }
// tslint:disable-next-line:no-empty-interface
interface JQueryXHR extends JQuery.jqXHR { }
interface JQueryPromise<T> extends JQuery.Promise<T> { }
// tslint:disable-next-line:no-empty-interface
interface JQuerySerializeArrayElement extends JQuery.NameValuePair { }

/**
 * @deprecated ​ Deprecated since 1.9. See \`{@link https://api.jquery.com/jQuery.support/ }\`.
 */
// tslint:disable-next-line:no-empty-interface
interface JQuerySupport extends JQuery.PlainObject { }

// Legacy types that are not represented in the current type definitions are marked deprecated.

/**
 * @deprecated ​ Deprecated. Use \`{@link JQuery.Deferred.Callback }\` or \`{@link JQuery.Deferred.CallbackBase }\`.
 */
interface JQueryPromiseCallback<T> {
    // tslint:disable-next-line:callable-types
    (value?: T, ...args: any[]): void;
}
/**
 * @deprecated ​ Deprecated. Use \`{@link JQueryStatic.param JQueryStatic&#91;'param'&#93;}\`.
 */
interface JQueryParam {
    /**
     * Create a serialized representation of an array or object, suitable for use in a URL query string or Ajax request.
     * @param obj An array or object to serialize.
     * @param traditional A Boolean indicating whether to perform a traditional "shallow" serialization.
     */
    // tslint:disable-next-line:callable-types
    (obj: any, traditional?: boolean): string;
}
/**
 * @deprecated ​ Deprecated. Use \`{@link JQuery.Event }\`.
 */
interface BaseJQueryEventObject extends Event {
    /**
     * The current DOM element within the event bubbling phase.
     * @see \`{@link https://api.jquery.com/event.currentTarget/ }\`
     */
    currentTarget: Element;
    /**
     * An optional object of data passed to an event method when the current executing handler is bound.
     * @see \`{@link https://api.jquery.com/event.data/ }\`
     */
    data: any;
    /**
     * The element where the currently-called jQuery event handler was attached.
     * @see \`{@link https://api.jquery.com/event.delegateTarget/ }\`
     */
    delegateTarget: Element;
    /**
     * Returns whether event.preventDefault() was ever called on this event object.
     * @see \`{@link https://api.jquery.com/event.isDefaultPrevented/ }\`
     */
    isDefaultPrevented(): boolean;
    /**
     * Returns whether event.stopImmediatePropagation() was ever called on this event object.
     * @see \`{@link https://api.jquery.com/event.isImmediatePropagationStopped/ }\`
     */
    isImmediatePropagationStopped(): boolean;
    /**
     * Returns whether event.stopPropagation() was ever called on this event object.
     * @see \`{@link https://api.jquery.com/event.isPropagationStopped/ }\`
     */
    isPropagationStopped(): boolean;
    /**
     * The namespace specified when the event was triggered.
     * @see \`{@link https://api.jquery.com/event.namespace/ }\`
     */
    namespace: string;
    /**
     * The browser's original Event object.
     * @see \`{@link https://api.jquery.com/category/events/event-object/ }\`
     */
    originalEvent: Event;
    /**
     * If this method is called, the default action of the event will not be triggered.
     * @see \`{@link https://api.jquery.com/event.preventDefault/ }\`
     */
    preventDefault(): any;
    /**
     * The other DOM element involved in the event, if any.
     * @see \`{@link https://api.jquery.com/event.relatedTarget/ }\`
     */
    relatedTarget: Element;
    /**
     * The last value returned by an event handler that was triggered by this event, unless the value was undefined.
     * @see \`{@link https://api.jquery.com/event.result/ }\`
     */
    result: any;
    /**
     * Keeps the rest of the handlers from being executed and prevents the event from bubbling up the DOM tree.
     * @see \`{@link https://api.jquery.com/event.stopImmediatePropagation/ }\`
     */
    stopImmediatePropagation(): void;
    /**
     * Prevents the event from bubbling up the DOM tree, preventing any parent handlers from being notified of the event.
     * @see \`{@link https://api.jquery.com/event.stopPropagation/ }\`
     */
    stopPropagation(): void;
    /**
     * The DOM element that initiated the event.
     * @see \`{@link https://api.jquery.com/event.target/ }\`
     */
    target: Element;
    /**
     * The mouse position relative to the left edge of the document.
     * @see \`{@link https://api.jquery.com/event.pageX/ }\`
     */
    pageX: number;
    /**
     * The mouse position relative to the top edge of the document.
     * @see \`{@link https://api.jquery.com/event.pageY/ }\`
     */
    pageY: number;
    /**
     * For key or mouse events, this property indicates the specific key or button that was pressed.
     * @see \`{@link https://api.jquery.com/event.which/ }\`
     */
    which: number;
    /**
     * Indicates whether the META key was pressed when the event fired.
     * @see \`{@link https://api.jquery.com/event.metaKey/ }\`
     */
    metaKey: boolean;
}
/**
 * @deprecated ​ Deprecated. Use \`{@link JQuery.Event }\`.
 */
interface JQueryInputEventObject extends BaseJQueryEventObject {
    altKey: boolean;
    ctrlKey: boolean;
    metaKey: boolean;
    shiftKey: boolean;
}
/**
 * @deprecated ​ Deprecated. Use \`{@link JQuery.Event }\`.
 */
interface JQueryMouseEventObject extends JQueryInputEventObject {
    button: number;
    clientX: number;
    clientY: number;
    offsetX: number;
    offsetY: number;
    pageX: number;
    pageY: number;
    screenX: number;
    screenY: number;
}
/**
 * @deprecated ​ Deprecated. Use \`{@link JQuery.Event }\`.
 */
interface JQueryKeyEventObject extends JQueryInputEventObject {
    /** @deprecated */
    char: string;
    /** @deprecated */
    charCode: number;
    key: string;
    /** @deprecated */
    keyCode: number;
}
/**
 * @deprecated ​ Deprecated. Use \`{@link JQuery.Event }\`.
 */
interface JQueryEventObject extends BaseJQueryEventObject, JQueryInputEventObject, JQueryMouseEventObject, JQueryKeyEventObject { }
/**
 * @deprecated ​ Deprecated.
 */
interface JQueryPromiseOperator<T, U> {
    // tslint:disable-next-line:callable-types
    (callback1: JQuery.TypeOrArray<JQueryPromiseCallback<T>>,
     ...callbacksN: Array<JQuery.TypeOrArray<JQueryPromiseCallback<any>>>): JQueryPromise<U>;
}
/**
 * @deprecated ​ Deprecated. Internal. See \`{@link https://github.com/jquery/api.jquery.com/issues/912 }\`.
 */
interface JQueryEasingFunction {
    // tslint:disable-next-line:callable-types
    (percent: number): number;
}
/**
 * @deprecated ​ Deprecated. Internal. See \`{@link https://github.com/jquery/api.jquery.com/issues/912 }\`.
 */
interface JQueryEasingFunctions {
    [name: string]: JQueryEasingFunction;
    linear: JQueryEasingFunction;
    swing: JQueryEasingFunction;
}
