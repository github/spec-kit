/// <reference types="cypress" />

import * as vue from 'vue';
import { ComponentInternalInstance, FunctionalComponent, ComponentOptions, Component, Directive, Plugin as Plugin$1, AppConfig, VNode, VNodeProps, ComponentPublicInstance, ComputedOptions, MethodOptions, CreateComponentPublicInstance, App, ConcreteComponent, DefineComponent, Prop, EmitsOptions, ComponentOptionsMixin, ExtractPropTypes, ExtractDefaultPropTypes, ComponentOptionsWithoutProps, ComponentOptionsWithArrayProps, ComponentPropsOptions, ComponentOptionsWithObjectProps, AllowedComponentProps, ComponentCustomProps } from 'vue';

interface RefSelector {
    ref: string;
}
interface NameSelector {
    name: string;
    length?: never;
}
type FindAllComponentsSelector = DefinedComponent | FunctionalComponent | ComponentOptions | NameSelector | string;
type FindComponentSelector = RefSelector | FindAllComponentsSelector;
type Slot = VNode | string | {
    render: Function;
} | Function | Component;
type SlotDictionary = {
    [key: string]: Slot;
};
type RawProps = VNodeProps & {
    __v_isVNode?: never;
    [Symbol.iterator]?: never;
} & Record<string, any>;
interface BaseMountingOptions<Props, Data = {}> {
    /**
     * Overrides component's default data. Must be a function.
     * @see https://test-utils.vuejs.org/api/#data
     */
    data?: () => {} extends Data ? any : Data extends object ? Partial<Data> : any;
    /**
     * Sets component props when mounted.
     * @see https://test-utils.vuejs.org/api/#props
     */
    props?: (RawProps & Props) | ({} extends Props ? null : never);
    /**
     * @deprecated use `props` instead.
     */
    propsData?: Props;
    /**
     * Sets component attributes when mounted.
     * @see https://test-utils.vuejs.org/api/#attrs
     */
    attrs?: Record<string, unknown>;
    /**
     * Provide values for slots on a component.
     * @see https://test-utils.vuejs.org/api/#slots
     */
    slots?: SlotDictionary & {
        default?: Slot;
    };
    /**
     * Provides global mounting options to the component.
     */
    global?: GlobalMountOptions$1;
    /**
     * Automatically stub out all the child components.
     * @default false
     * @see https://test-utils.vuejs.org/api/#slots
     */
    shallow?: boolean;
}
/**
 * Mounting options for `mount` and `shallowMount`
 */
interface MountingOptions$1<Props, Data = {}> extends BaseMountingOptions<Props, Data> {
    /**
     * Specify where to mount the component.
     * Can be a valid CSS selector, or an Element connected to the document.
     * @see https://test-utils.vuejs.org/api/#attachto
     */
    attachTo?: Element | string;
}
/**
 * Mounting options for `renderToString`
 */
interface RenderMountingOptions<Props, Data = {}> extends BaseMountingOptions<Props, Data> {
    /**
     * Attach to is not available in SSR mode
     */
    attachTo?: never;
}
type Stub = boolean | Component | Directive;
type Stubs = Record<string, Stub> | Array<string>;
type GlobalMountOptions$1 = {
    /**
     * Installs plugins on the component.
     * @see https://test-utils.vuejs.org/api/#global-plugins
     */
    plugins?: (Plugin$1 | [Plugin$1, ...any[]])[];
    /**
     * Customizes Vue application global configuration
     * @see https://v3.vuejs.org/api/application-config.html#application-config
     */
    config?: Partial<Omit<AppConfig, 'isNativeTag'>>;
    /**
     * Applies a mixin for components under testing.
     * @see https://test-utils.vuejs.org/api/#global-mixins
     */
    mixins?: ComponentOptions[];
    /**
     * Mocks a global instance property.
     * This is designed to mock variables injected by third party plugins, not
     * Vue's native properties such as $root, $children, etc.
     * @see https://test-utils.vuejs.org/api/#global-mocks
     */
    mocks?: Record<string, any>;
    /**
     * Provides data to be received in a setup function via `inject`.
     * @see https://test-utils.vuejs.org/api/#global-provide
     */
    provide?: Record<any, any>;
    /**
     * Registers components globally for components under testing.
     * @see https://test-utils.vuejs.org/api/#global-components
     */
    components?: Record<string, Component | object>;
    /**
     * Registers a directive globally for components under testing
     * @see https://test-utils.vuejs.org/api/#global-directives
     */
    directives?: Record<string, Directive>;
    /**
     * Stubs a component for components under testing.
     * @default "{ transition: true, 'transition-group': true }"
     * @see https://test-utils.vuejs.org/api/#global-stubs
     */
    stubs?: Stubs;
    /**
     * Allows rendering the default slot content, even when using
     * `shallow` or `shallowMount`.
     * @default false
     * @see https://test-utils.vuejs.org/api/#global-renderstubdefaultslot
     */
    renderStubDefaultSlot?: boolean;
};
type VueNode<T extends Node = Node> = T & {
    __vue_app__?: any;
    __vueParentComponent?: ComponentInternalInstance;
};
type DefinedComponent = new (...args: any[]) => any;

type DomEventName = keyof typeof domEvents;
declare const systemKeyModifiers: readonly ["ctrl", "shift", "alt", "meta"];
declare const mouseKeyModifiers: readonly ["left", "middle", "right"];
declare const keyCodesByKeyName: {
    readonly backspace: 8;
    readonly tab: 9;
    readonly enter: 13;
    readonly esc: 27;
    readonly space: 32;
    readonly pageup: 33;
    readonly pagedown: 34;
    readonly end: 35;
    readonly home: 36;
    readonly left: 37;
    readonly up: 38;
    readonly right: 39;
    readonly down: 40;
    readonly insert: 45;
    readonly delete: 46;
};
type DomEventNameWithModifier = DomEventName | `${DomEventName}.${(typeof systemKeyModifiers)[number]}` | `click.${(typeof mouseKeyModifiers)[number]}` | `click.${(typeof systemKeyModifiers)[number]}.${(typeof mouseKeyModifiers)[number]}` | `${'keydown' | 'keyup'}.${keyof typeof keyCodesByKeyName}` | `${'keydown' | 'keyup'}.${(typeof systemKeyModifiers)[number]}.${keyof typeof keyCodesByKeyName}`;
declare const domEvents: {
    readonly abort: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly afterprint: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly animationend: {
        readonly eventInterface: "AnimationEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly animationiteration: {
        readonly eventInterface: "AnimationEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly animationstart: {
        readonly eventInterface: "AnimationEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly appinstalled: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    /**
     * @deprecated
     */
    readonly audioprocess: {
        readonly eventInterface: "AudioProcessingEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly audioend: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly audiostart: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly beforeprint: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly beforeunload: {
        readonly eventInterface: "BeforeUnloadEvent";
        readonly bubbles: false;
        readonly cancelable: true;
    };
    readonly beginEvent: {
        readonly eventInterface: "TimeEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly blur: {
        readonly eventInterface: "FocusEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly boundary: {
        readonly eventInterface: "SpeechSynthesisEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly cached: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly canplay: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly canplaythrough: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly change: {
        readonly eventInterface: "Event";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly chargingchange: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly chargingtimechange: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly checking: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly click: {
        readonly eventInterface: "MouseEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly close: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly complete: {
        readonly eventInterface: "OfflineAudioCompletionEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly compositionend: {
        readonly eventInterface: "CompositionEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly compositionstart: {
        readonly eventInterface: "CompositionEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly compositionupdate: {
        readonly eventInterface: "CompositionEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly contextmenu: {
        readonly eventInterface: "MouseEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly copy: {
        readonly eventInterface: "ClipboardEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly cut: {
        readonly eventInterface: "ClipboardEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly dblclick: {
        readonly eventInterface: "MouseEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly devicechange: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly devicelight: {
        readonly eventInterface: "DeviceLightEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly devicemotion: {
        readonly eventInterface: "DeviceMotionEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly deviceorientation: {
        readonly eventInterface: "DeviceOrientationEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly deviceproximity: {
        readonly eventInterface: "DeviceProximityEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly dischargingtimechange: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly DOMActivate: {
        readonly eventInterface: "UIEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly DOMAttributeNameChanged: {
        readonly eventInterface: "MutationNameEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly DOMAttrModified: {
        readonly eventInterface: "MutationEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly DOMCharacterDataModified: {
        readonly eventInterface: "MutationEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly DOMContentLoaded: {
        readonly eventInterface: "Event";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly DOMElementNameChanged: {
        readonly eventInterface: "MutationNameEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly DOMFocusIn: {
        readonly eventInterface: "FocusEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly DOMFocusOut: {
        readonly eventInterface: "FocusEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly DOMNodeInserted: {
        readonly eventInterface: "MutationEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly DOMNodeInsertedIntoDocument: {
        readonly eventInterface: "MutationEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly DOMNodeRemoved: {
        readonly eventInterface: "MutationEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly DOMNodeRemovedFromDocument: {
        readonly eventInterface: "MutationEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    /**
     * @deprecated
     */
    readonly DOMSubtreeModified: {
        readonly eventInterface: "MutationEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly downloading: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly drag: {
        readonly eventInterface: "DragEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly dragend: {
        readonly eventInterface: "DragEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly dragenter: {
        readonly eventInterface: "DragEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly dragleave: {
        readonly eventInterface: "DragEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly dragover: {
        readonly eventInterface: "DragEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly dragstart: {
        readonly eventInterface: "DragEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly drop: {
        readonly eventInterface: "DragEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly durationchange: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly emptied: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly end: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly ended: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly endEvent: {
        readonly eventInterface: "TimeEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly error: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly focus: {
        readonly eventInterface: "FocusEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly focusin: {
        readonly eventInterface: "FocusEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly focusout: {
        readonly eventInterface: "FocusEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly fullscreenchange: {
        readonly eventInterface: "Event";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly fullscreenerror: {
        readonly eventInterface: "Event";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly gamepadconnected: {
        readonly eventInterface: "GamepadEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly gamepaddisconnected: {
        readonly eventInterface: "GamepadEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly gotpointercapture: {
        readonly eventInterface: "PointerEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly hashchange: {
        readonly eventInterface: "HashChangeEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly lostpointercapture: {
        readonly eventInterface: "PointerEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly input: {
        readonly eventInterface: "Event";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly invalid: {
        readonly eventInterface: "Event";
        readonly cancelable: true;
        readonly bubbles: false;
    };
    readonly keydown: {
        readonly eventInterface: "KeyboardEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly keypress: {
        readonly eventInterface: "KeyboardEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly keyup: {
        readonly eventInterface: "KeyboardEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly languagechange: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly levelchange: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly load: {
        readonly eventInterface: "UIEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly loadeddata: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly loadedmetadata: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly loadend: {
        readonly eventInterface: "ProgressEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly loadstart: {
        readonly eventInterface: "ProgressEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly mark: {
        readonly eventInterface: "SpeechSynthesisEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly message: {
        readonly eventInterface: "MessageEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly messageerror: {
        readonly eventInterface: "MessageEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly mousedown: {
        readonly eventInterface: "MouseEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly mouseenter: {
        readonly eventInterface: "MouseEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly mouseleave: {
        readonly eventInterface: "MouseEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly mousemove: {
        readonly eventInterface: "MouseEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly mouseout: {
        readonly eventInterface: "MouseEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly mouseover: {
        readonly eventInterface: "MouseEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly mouseup: {
        readonly eventInterface: "MouseEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly nomatch: {
        readonly eventInterface: "SpeechRecognitionEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly notificationclick: {
        readonly eventInterface: "NotificationEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly noupdate: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly obsolete: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly offline: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly online: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly open: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly orientationchange: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly pagehide: {
        readonly eventInterface: "PageTransitionEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly pageshow: {
        readonly eventInterface: "PageTransitionEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly paste: {
        readonly eventInterface: "ClipboardEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly pause: {
        readonly eventInterface: "SpeechSynthesisEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly pointercancel: {
        readonly eventInterface: "PointerEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly pointerdown: {
        readonly eventInterface: "PointerEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly pointerenter: {
        readonly eventInterface: "PointerEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly pointerleave: {
        readonly eventInterface: "PointerEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly pointerlockchange: {
        readonly eventInterface: "Event";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly pointerlockerror: {
        readonly eventInterface: "Event";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly pointermove: {
        readonly eventInterface: "PointerEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly pointerout: {
        readonly eventInterface: "PointerEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly pointerover: {
        readonly eventInterface: "PointerEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly pointerup: {
        readonly eventInterface: "PointerEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly play: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly playing: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly popstate: {
        readonly eventInterface: "PopStateEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly progress: {
        readonly eventInterface: "ProgressEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly push: {
        readonly eventInterface: "PushEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly pushsubscriptionchange: {
        readonly eventInterface: "PushEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly ratechange: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly readystatechange: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly repeatEvent: {
        readonly eventInterface: "TimeEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly reset: {
        readonly eventInterface: "Event";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly resize: {
        readonly eventInterface: "UIEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly resourcetimingbufferfull: {
        readonly eventInterface: "Performance";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly result: {
        readonly eventInterface: "SpeechRecognitionEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly resume: {
        readonly eventInterface: "SpeechSynthesisEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly scroll: {
        readonly eventInterface: "UIEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly seeked: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly seeking: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly select: {
        readonly eventInterface: "UIEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly selectstart: {
        readonly eventInterface: "Event";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly selectionchange: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly show: {
        readonly eventInterface: "MouseEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly slotchange: {
        readonly eventInterface: "Event";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly soundend: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly soundstart: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly speechend: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly speechstart: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly stalled: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly start: {
        readonly eventInterface: "SpeechSynthesisEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly storage: {
        readonly eventInterface: "StorageEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly submit: {
        readonly eventInterface: "Event";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly success: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly suspend: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly SVGAbort: {
        readonly eventInterface: "SVGEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly SVGError: {
        readonly eventInterface: "SVGEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly SVGLoad: {
        readonly eventInterface: "SVGEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly SVGResize: {
        readonly eventInterface: "SVGEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly SVGScroll: {
        readonly eventInterface: "SVGEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly SVGUnload: {
        readonly eventInterface: "SVGEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly SVGZoom: {
        readonly eventInterface: "SVGZoomEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly timeout: {
        readonly eventInterface: "ProgressEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly timeupdate: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly touchcancel: {
        readonly eventInterface: "TouchEvent";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly touchend: {
        readonly eventInterface: "TouchEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly touchmove: {
        readonly eventInterface: "TouchEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly touchstart: {
        readonly eventInterface: "TouchEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly transitionend: {
        readonly eventInterface: "TransitionEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
    readonly unload: {
        readonly eventInterface: "UIEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly updateready: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly userproximity: {
        readonly eventInterface: "UserProximityEvent";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly voiceschanged: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly visibilitychange: {
        readonly eventInterface: "Event";
        readonly bubbles: true;
        readonly cancelable: false;
    };
    readonly volumechange: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly waiting: {
        readonly eventInterface: "Event";
        readonly bubbles: false;
        readonly cancelable: false;
    };
    readonly wheel: {
        readonly eventInterface: "WheelEvent";
        readonly bubbles: true;
        readonly cancelable: true;
    };
};

interface TriggerOptions {
    code?: String;
    key?: String;
    keyCode?: Number;
    [custom: string]: any;
}

declare class DOMWrapper<NodeType extends Node> extends BaseWrapper<NodeType> {
    constructor(element: NodeType | null | undefined);
    getRootNodes(): VueNode<NodeType>[];
    getCurrentComponent(): vue.ComponentInternalInstance | undefined;
    find<K extends keyof HTMLElementTagNameMap>(selector: K): DOMWrapper<HTMLElementTagNameMap[K]>;
    find<K extends keyof SVGElementTagNameMap>(selector: K): DOMWrapper<SVGElementTagNameMap[K]>;
    find<T extends Element = Element>(selector: string): DOMWrapper<T>;
    find<T extends Node = Node>(selector: string | RefSelector): DOMWrapper<T>;
    findAll<K extends keyof HTMLElementTagNameMap>(selector: K): DOMWrapper<HTMLElementTagNameMap[K]>[];
    findAll<K extends keyof SVGElementTagNameMap>(selector: K): DOMWrapper<SVGElementTagNameMap[K]>[];
    findAll<T extends Element>(selector: string): DOMWrapper<T>[];
    findAllComponents(selector: any): any;
    private setChecked;
    setValue(value?: any): Promise<void>;
    private setSelected;
}

interface WrapperLike {
    readonly element: Node;
    find<K extends keyof HTMLElementTagNameMap>(selector: K): DOMWrapper<HTMLElementTagNameMap[K]>;
    find<K extends keyof SVGElementTagNameMap>(selector: K): DOMWrapper<SVGElementTagNameMap[K]>;
    find<T extends Element = Element>(selector: string): DOMWrapper<T>;
    find<T extends Node = Node>(selector: string | RefSelector): DOMWrapper<T>;
    findAll<K extends keyof HTMLElementTagNameMap>(selector: K): DOMWrapper<HTMLElementTagNameMap[K]>[];
    findAll<K extends keyof SVGElementTagNameMap>(selector: K): DOMWrapper<SVGElementTagNameMap[K]>[];
    findAll<T extends Element>(selector: string): DOMWrapper<T>[];
    findAll(selector: string): DOMWrapper<Element>[];
    findComponent<T extends never>(selector: string): WrapperLike;
    findComponent<T extends DefinedComponent>(selector: T | Exclude<FindComponentSelector, FunctionalComponent>): VueWrapper<InstanceType<T>>;
    findComponent<T extends FunctionalComponent>(selector: T | string): DOMWrapper<Element>;
    findComponent<T extends never>(selector: NameSelector | RefSelector): VueWrapper;
    findComponent<T extends ComponentPublicInstance>(selector: T | FindComponentSelector): VueWrapper<T>;
    findComponent(selector: FindComponentSelector): WrapperLike;
    findAllComponents<T extends never>(selector: string): WrapperLike[];
    findAllComponents<T extends DefinedComponent>(selector: T | Exclude<FindAllComponentsSelector, FunctionalComponent>): VueWrapper<InstanceType<T>>[];
    findAllComponents<T extends FunctionalComponent>(selector: string): DOMWrapper<Element>[];
    findAllComponents<T extends FunctionalComponent>(selector: T): DOMWrapper<Node>[];
    findAllComponents<T extends never>(selector: NameSelector): VueWrapper[];
    findAllComponents<T extends ComponentPublicInstance>(selector: T | FindAllComponentsSelector): VueWrapper<T>[];
    findAllComponents(selector: FindAllComponentsSelector): WrapperLike[];
    get<K extends keyof HTMLElementTagNameMap>(selector: K): Omit<DOMWrapper<HTMLElementTagNameMap[K]>, 'exists'>;
    get<K extends keyof SVGElementTagNameMap>(selector: K): Omit<DOMWrapper<SVGElementTagNameMap[K]>, 'exists'>;
    get<T extends Element = Element>(selector: string): Omit<DOMWrapper<T>, 'exists'>;
    get<T extends Node = Node>(selector: string | RefSelector): Omit<DOMWrapper<T>, 'exists'>;
    getComponent<T extends never>(selector: string): Omit<WrapperLike, 'exists'>;
    getComponent<T extends DefinedComponent>(selector: T | Exclude<FindComponentSelector, FunctionalComponent>): Omit<VueWrapper<InstanceType<T>>, 'exists'>;
    getComponent<T extends FunctionalComponent>(selector: T | string): Omit<DOMWrapper<Element>, 'exists'>;
    getComponent<T extends ComponentPublicInstance>(selector: T | FindComponentSelector): Omit<VueWrapper<T>, 'exists'>;
    getComponent<T extends never>(selector: FindComponentSelector): Omit<WrapperLike, 'exists'>;
    html(): string;
    classes(): string[];
    classes(className: string): boolean;
    classes(className?: string): string[] | boolean;
    attributes(): {
        [key: string]: string;
    };
    attributes(key: string): string | undefined;
    attributes(key?: string): {
        [key: string]: string;
    } | string | undefined;
    text(): string;
    exists(): boolean;
    setValue(value: any): Promise<void>;
    isVisible(): boolean;
    trigger(eventString: DomEventNameWithModifier, options?: TriggerOptions): Promise<void>;
    trigger(eventString: string, options?: TriggerOptions): Promise<void>;
}

declare abstract class BaseWrapper<ElementType extends Node> implements WrapperLike {
    protected readonly wrapperElement: VueNode<ElementType>;
    protected abstract getRootNodes(): VueNode[];
    get element(): VueNode<ElementType>;
    protected constructor(element: ElementType);
    protected findAllDOMElements(selector: string): Element[];
    find<K extends keyof HTMLElementTagNameMap>(selector: K): DOMWrapper<HTMLElementTagNameMap[K]>;
    find<K extends keyof SVGElementTagNameMap>(selector: K): DOMWrapper<SVGElementTagNameMap[K]>;
    find<T extends Element = Element>(selector: string): DOMWrapper<T>;
    find<T extends Node = Node>(selector: string | RefSelector): DOMWrapper<T>;
    abstract findAll<K extends keyof HTMLElementTagNameMap>(selector: K): DOMWrapper<HTMLElementTagNameMap[K]>[];
    abstract findAll<K extends keyof SVGElementTagNameMap>(selector: K): DOMWrapper<SVGElementTagNameMap[K]>[];
    abstract findAll<T extends Element>(selector: string): DOMWrapper<T>[];
    abstract findAll(selector: string): DOMWrapper<Element>[];
    findComponent<T extends never>(selector: string): WrapperLike;
    findComponent<Props, RawBindings = any, D = any, C extends ComputedOptions = ComputedOptions, M extends MethodOptions = MethodOptions>(selector: ComponentOptions<Props, RawBindings, D, C, M>): VueWrapper<CreateComponentPublicInstance<Props, RawBindings, D, C, M>>;
    findComponent<T extends ComponentOptions>(selector: string): VueWrapper<T extends ComponentOptions<infer Props, infer RawBindings, infer D, infer C, infer M> ? CreateComponentPublicInstance<Props, RawBindings, D, C, M> : VueWrapper<CreateComponentPublicInstance>>;
    findComponent<T extends DefinedComponent>(selector: T | Exclude<FindComponentSelector, FunctionalComponent>): VueWrapper<InstanceType<T>>;
    findComponent<T extends FunctionalComponent>(selector: T): DOMWrapper<Node>;
    findComponent<T extends FunctionalComponent>(selector: string): DOMWrapper<Element>;
    findComponent<T extends never>(selector: NameSelector | RefSelector): VueWrapper;
    findComponent<T extends ComponentPublicInstance>(selector: T | FindComponentSelector): VueWrapper<T>;
    findComponent<T extends never>(selector: FindComponentSelector): WrapperLike;
    findAllComponents<T extends never>(selector: string): WrapperLike[];
    findAllComponents<T extends DefinedComponent>(selector: T | Exclude<FindAllComponentsSelector, FunctionalComponent>): VueWrapper<InstanceType<T>>[];
    findAllComponents<T extends FunctionalComponent>(selector: T): DOMWrapper<Node>[];
    findAllComponents<T extends FunctionalComponent>(selector: string): DOMWrapper<Element>[];
    findAllComponents<T extends never>(selector: NameSelector): VueWrapper[];
    findAllComponents<T extends ComponentPublicInstance>(selector: T | FindAllComponentsSelector): VueWrapper<T>[];
    findAllComponents<T extends never>(selector: FindAllComponentsSelector): WrapperLike[];
    abstract setValue(value?: any): Promise<void>;
    html(options?: {
        raw?: boolean;
    }): string;
    classes(): string[];
    classes(className: string): boolean;
    attributes(): {
        [key: string]: string;
    };
    attributes(key: string): string | undefined;
    text(): string;
    exists(): boolean;
    get<K extends keyof HTMLElementTagNameMap>(selector: K): Omit<DOMWrapper<HTMLElementTagNameMap[K]>, 'exists'>;
    get<K extends keyof SVGElementTagNameMap>(selector: K): Omit<DOMWrapper<SVGElementTagNameMap[K]>, 'exists'>;
    get<T extends Element = Element>(selector: string): Omit<DOMWrapper<T>, 'exists'>;
    get<T extends Node = Node>(selector: string | RefSelector): Omit<DOMWrapper<T>, 'exists'>;
    getComponent<T extends never>(selector: string): Omit<WrapperLike, 'exists'>;
    getComponent<T extends DefinedComponent>(selector: T | Exclude<FindComponentSelector, FunctionalComponent>): Omit<VueWrapper<InstanceType<T>>, 'exists'>;
    getComponent<T extends FunctionalComponent>(selector: T | string): Omit<DOMWrapper<Element>, 'exists'>;
    getComponent<T extends never>(selector: NameSelector | RefSelector): Omit<VueWrapper, 'exists'>;
    getComponent<T extends ComponentPublicInstance>(selector: T | FindComponentSelector): Omit<VueWrapper<T>, 'exists'>;
    getComponent<T extends never>(selector: FindComponentSelector): Omit<WrapperLike, 'exists'>;
    protected isDisabled: () => boolean;
    isVisible(): boolean;
    protected abstract getCurrentComponent(): ComponentInternalInstance | void;
    trigger(eventString: DomEventNameWithModifier, options?: TriggerOptions): Promise<void>;
    trigger(eventString: string, options?: TriggerOptions): Promise<void>;
}

declare class VueWrapper<VM = unknown, T extends ComponentPublicInstance = VM & ComponentPublicInstance> extends BaseWrapper<Node> {
    private readonly componentVM;
    private readonly rootVM;
    private readonly __app;
    private readonly __setProps;
    private cleanUpCallbacks;
    constructor(app: App | null, vm: T, setProps?: (props: Record<string, unknown>) => void);
    private get hasMultipleRoots();
    protected getRootNodes(): VueNode[];
    private get parentElement();
    getCurrentComponent(): vue.ComponentInternalInstance;
    exists(): boolean;
    findAll<K extends keyof HTMLElementTagNameMap>(selector: K): DOMWrapper<HTMLElementTagNameMap[K]>[];
    findAll<K extends keyof SVGElementTagNameMap>(selector: K): DOMWrapper<SVGElementTagNameMap[K]>[];
    findAll<T extends Element>(selector: string): DOMWrapper<T>[];
    private attachNativeEventListener;
    get element(): T['$el'];
    get vm(): T;
    props(): T['$props'];
    props<Selector extends keyof T['$props']>(selector: Selector): T['$props'][Selector];
    emitted<T = unknown>(): Record<string, T[]>;
    emitted<T = unknown[]>(eventName: string): undefined | T[];
    isVisible(): boolean;
    setData(data: Record<string, unknown>): Promise<void>;
    setProps(props: Partial<T['$props']>): Promise<void>;
    setValue(value: unknown, prop?: string): Promise<void>;
    unmount(): void;
}

type CustomCreateStub = (params: {
    name: string;
    component: ConcreteComponent;
    registerStub: (config: {
        source: Component;
        stub: Component;
    }) => void;
}) => ConcreteComponent;

interface GlobalConfigOptions {
    global: Required<Omit<GlobalMountOptions$1, 'stubs'>> & {
        stubs: Record<string, Stub>;
    };
    plugins: {
        VueWrapper: Pluggable<VueWrapper>;
        DOMWrapper: Pluggable<DOMWrapper<Node>>;
        createStubs?: CustomCreateStub;
    };
    /**
     * @deprecated use global.
     */
    renderStubDefaultSlot?: boolean;
}
interface Plugin<Instance, O> {
    handler(instance: Instance): Record<string, any>;
    handler(instance: Instance, options: O): Record<string, any>;
    options: O;
}
declare class Pluggable<Instance = DOMWrapper<Node>> {
    installedPlugins: Plugin<Instance, any>[];
    install<O>(handler: (instance: Instance) => Record<string, any>): void;
    install<O>(handler: (instance: Instance, options: O) => Record<string, any>, options: O): void;
    extend(instance: Instance): void;
    /** For testing */
    reset(): void;
}

type ComponentProps<T> = T extends new (...args: any) => {
    $props: infer P;
} ? NonNullable<P> : T extends (props: infer P, ...args: any) => any ? P : {};
type ComponentSlots<T> = T extends new (...args: any) => {
    $slots: infer S;
} ? NonNullable<S> : T extends (props: any, ctx: {
    slots: infer S;
    attrs: any;
    emit: any;
}, ...args: any) => any ? NonNullable<S> : {};

type ShimSlotReturnType<T> = T extends (...args: infer P) => any ? (...args: P) => any : never;
type WithArray<T> = T | T[];
type ComponentData<T> = T extends {
    data?(...args: any): infer D;
} ? D : {};
type ComponentMountingOptions$1<T, P extends ComponentProps<T> = ComponentProps<T>> = Omit<MountingOptions$1<P, ComponentData<T>>, 'slots'> & {
    slots?: {
        [K in keyof ComponentSlots<T>]: WithArray<ShimSlotReturnType<ComponentSlots<T>[K]> | string | VNode | (new () => any) | {
            template: string;
        }>;
    };
} & Record<string, unknown>;

declare function renderToString<T, C = T extends ((...args: any) => any) | (new (...args: any) => any) ? T : T extends {
    props?: infer Props;
} ? DefineComponent<Props extends Readonly<(infer PropNames)[]> | (infer PropNames)[] ? {
    [key in PropNames extends string ? PropNames : string]?: any;
} : Props> : DefineComponent>(originalComponent: T, options?: ComponentMountingOptions$1<C> & Pick<RenderMountingOptions<any>, 'attachTo'>): Promise<string>;

declare function createWrapperError<T extends object>(wrapperType: 'DOMWrapper' | 'VueWrapper'): T;

declare function flushPromises(): Promise<unknown>;

declare function disableAutoUnmount(): void;
declare function enableAutoUnmount(hook: (callback: () => void) => void): void;

declare const VueTestUtils: {
    renderToString: typeof renderToString;
    enableAutoUnmount: typeof enableAutoUnmount;
    disableAutoUnmount: typeof disableAutoUnmount;
    RouterLinkStub: any;
    VueWrapper: typeof VueWrapper;
    DOMWrapper: typeof DOMWrapper;
    BaseWrapper: typeof BaseWrapper;
    config: GlobalConfigOptions;
    flushPromises: typeof flushPromises;
    createWrapperError: typeof createWrapperError;
};

type GlobalMountOptions = Required<MountingOptions$1<any>>['global'];
declare global {
    namespace Cypress {
        interface Cypress {
            vueWrapper: VueWrapper<ComponentPublicInstance>;
            vue: ComponentPublicInstance;
        }
    }
}
type MountingOptions<Props, Data = {}> = Omit<MountingOptions$1<Props, Data>, 'attachTo'> & {
    log?: boolean;
    /**
     * @deprecated use vue-test-utils `global` instead
     */
    extensions?: GlobalMountOptions & {
        use?: GlobalMountOptions['plugins'];
        mixin?: GlobalMountOptions['mixins'];
    };
};
type CyMountOptions<Props, Data = {}> = MountingOptions<Props, Data>;
/**
 * The types for mount have been copied directly from the VTU mount
 * https://github.com/vuejs/vue-test-utils-next/blob/master/src/mount.ts.
 *
 * There isn't a good way to make them generic enough that we can extend them.
 *
 * In addition, we modify the types slightly.
 *
 * `MountOptions` are modifying, including some Cypress specific options like `styles`.
 * The return type is different. Instead of VueWrapper, it's Cypress.Chainable<VueWrapper<...>>.
 */
type PublicProps = VNodeProps & AllowedComponentProps & ComponentCustomProps;
type ComponentMountingOptions<T> = T extends DefineComponent<infer PropsOrPropOptions, any, infer D, any, any> ? MountingOptions<Partial<ExtractDefaultPropTypes<PropsOrPropOptions>> & Omit<Readonly<ExtractPropTypes<PropsOrPropOptions>> & PublicProps, keyof ExtractDefaultPropTypes<PropsOrPropOptions>>, D> & Record<string, any> : MountingOptions<any>;
declare function mount<V extends {}>(originalComponent: {
    new (...args: any[]): V;
    __vccOpts: any;
}, options?: MountingOptions<any> & Record<string, any>): Cypress.Chainable<{
    wrapper: VueWrapper<ComponentPublicInstance<V>>;
    component: VueWrapper<ComponentPublicInstance<V>>['vm'];
}>;
declare function mount<V extends {}, P>(originalComponent: {
    new (...args: any[]): V;
    __vccOpts: any;
    defaultProps?: Record<string, Prop<any>> | string[];
}, options?: MountingOptions<P & PublicProps> & Record<string, any>): Cypress.Chainable<{
    wrapper: VueWrapper<ComponentPublicInstance<V>>;
    component: VueWrapper<ComponentPublicInstance<V>>['vm'];
}>;
declare function mount<V extends {}>(originalComponent: {
    new (...args: any[]): V;
    registerHooks(keys: string[]): void;
}, options?: MountingOptions<any> & Record<string, any>): Cypress.Chainable<{
    wrapper: VueWrapper<ComponentPublicInstance<V>>;
    component: VueWrapper<ComponentPublicInstance<V>>['vm'];
}>;
declare function mount<V extends {}, P>(originalComponent: {
    new (...args: any[]): V;
    props(Props: P): any;
    registerHooks(keys: string[]): void;
}, options?: MountingOptions<P & PublicProps> & Record<string, any>): Cypress.Chainable<{
    wrapper: VueWrapper<ComponentPublicInstance<V>>;
    component: VueWrapper<ComponentPublicInstance<V>>['vm'];
}>;
declare function mount<Props extends {}, E extends EmitsOptions = {}>(originalComponent: FunctionalComponent<Props, E>, options?: MountingOptions<Props & PublicProps> & Record<string, any>): Cypress.Chainable<{
    wrapper: VueWrapper<ComponentPublicInstance<Props>>;
    component: VueWrapper<ComponentPublicInstance<Props>>['vm'];
}>;
declare function mount<PropsOrPropOptions = {}, RawBindings = {}, D = {}, C extends ComputedOptions = ComputedOptions, M extends MethodOptions = MethodOptions, Mixin extends ComponentOptionsMixin = ComponentOptionsMixin, Extends extends ComponentOptionsMixin = ComponentOptionsMixin, E extends EmitsOptions = Record<string, any>, EE extends string = string, PP = PublicProps, Props = Readonly<ExtractPropTypes<PropsOrPropOptions>>, Defaults extends {} = ExtractDefaultPropTypes<PropsOrPropOptions>>(component: DefineComponent<PropsOrPropOptions, RawBindings, D, C, M, Mixin, Extends, E, EE, PP, Props, Defaults>, options?: MountingOptions<Partial<Defaults> & Omit<Props & PublicProps, keyof Defaults>, D> & Record<string, any>): Cypress.Chainable<{
    wrapper: VueWrapper<InstanceType<DefineComponent<PropsOrPropOptions, RawBindings, D, C, M, Mixin, Extends, EmitsOptions, EE, PP, Props, Defaults>>>;
    component: VueWrapper<InstanceType<DefineComponent<PropsOrPropOptions, RawBindings, D, C, M, Mixin, Extends, EmitsOptions, EE, PP, Props, Defaults>>>['vm'];
}>;
declare function mount<T extends DefineComponent<any, any, any, any, any>>(component: T, options?: ComponentMountingOptions<T>): Cypress.Chainable<{
    wrapper: VueWrapper<InstanceType<T>>;
    component: VueWrapper<InstanceType<T>>['vm'];
}>;
declare function mount<Props = {}, RawBindings = {}, D extends {} = {}, C extends ComputedOptions = {}, M extends Record<string, Function> = {}, E extends EmitsOptions = Record<string, any>, Mixin extends ComponentOptionsMixin = ComponentOptionsMixin, Extends extends ComponentOptionsMixin = ComponentOptionsMixin, EE extends string = string>(componentOptions: ComponentOptionsWithoutProps<Props, RawBindings, D, C, M, E, Mixin, Extends, EE>, options?: MountingOptions<Props & PublicProps, D>): Cypress.Chainable<{
    wrapper: VueWrapper<ComponentPublicInstance<Props, RawBindings, D, C, M, E, VNodeProps & Props>> & Record<string, any>;
    component: VueWrapper<ComponentPublicInstance<Props, RawBindings, D, C, M, E, VNodeProps & Props>> & Record<string, any>['vm'];
}>;
declare function mount<PropNames extends string, RawBindings, D extends {}, C extends ComputedOptions = {}, M extends Record<string, Function> = {}, E extends EmitsOptions = Record<string, any>, Mixin extends ComponentOptionsMixin = ComponentOptionsMixin, Extends extends ComponentOptionsMixin = ComponentOptionsMixin, EE extends string = string, Props extends Readonly<{
    [key in PropNames]?: any;
}> = Readonly<{
    [key in PropNames]?: any;
}>>(componentOptions: ComponentOptionsWithArrayProps<PropNames, RawBindings, D, C, M, E, Mixin, Extends, EE, Props>, options?: MountingOptions<Props & PublicProps, D>): Cypress.Chainable<{
    wrapper: VueWrapper<ComponentPublicInstance<Props, RawBindings, D, C, M, E>>;
    component: VueWrapper<ComponentPublicInstance<Props, RawBindings, D, C, M, E>>['vm'];
}>;
declare function mount<PropsOptions extends Readonly<ComponentPropsOptions>, RawBindings, D extends {}, C extends ComputedOptions = {}, M extends Record<string, Function> = {}, E extends EmitsOptions = Record<string, any>, Mixin extends ComponentOptionsMixin = ComponentOptionsMixin, Extends extends ComponentOptionsMixin = ComponentOptionsMixin, EE extends string = string>(componentOptions: ComponentOptionsWithObjectProps<PropsOptions, RawBindings, D, C, M, E, Mixin, Extends, EE>, options?: MountingOptions<ExtractPropTypes<PropsOptions> & PublicProps, D>): Cypress.Chainable<{
    wrapper: VueWrapper<ComponentPublicInstance<ExtractPropTypes<PropsOptions>, RawBindings, D, C, M, E, VNodeProps & ExtractPropTypes<PropsOptions>>>;
    component: VueWrapper<ComponentPublicInstance<ExtractPropTypes<PropsOptions>, RawBindings, D, C, M, E, VNodeProps & ExtractPropTypes<PropsOptions>>>['vm'];
}>;

export { CyMountOptions, VueTestUtils, mount };
