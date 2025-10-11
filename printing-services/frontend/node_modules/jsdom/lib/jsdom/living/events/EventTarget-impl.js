"use strict";
const DOMException = require("../generated/DOMException");

const isWindow = require("../helpers/is-window");
const reportException = require("../helpers/runtime-script-errors");
const idlUtils = require("../generated/utils");
const { nodeRoot } = require("../helpers/node");
const {
  isNode, isShadowRoot, isSlotable, getEventTargetParent,
  isShadowInclusiveAncestor, retarget
} = require("../helpers/shadow-dom");

const MouseEvent = require("../generated/MouseEvent");

const EVENT_PHASE = {
  NONE: 0,
  CAPTURING_PHASE: 1,
  AT_TARGET: 2,
  BUBBLING_PHASE: 3
};

class EventTargetImpl {
  constructor(globalObject) {
    this._globalObject = globalObject;
    this._eventListeners = Object.create(null);
  }

  // Default argument is necessary because webidl2js cannot handle `= {}` with unions at the moment.
  addEventListener(type, callback, options = { __proto__: null, capture: false, once: false }) {
    let { capture, once, passive, signal } = flattenMoreEventListenerOptions(options);

    if (signal !== null && signal.aborted) {
      return;
    }

    if (callback === null) {
      return;
    }

    if (passive === null) {
      passive = defaultPassiveValue(type, this);
    }

    if (!this._eventListeners[type]) {
      this._eventListeners[type] = [];
    }

    for (let i = 0; i < this._eventListeners[type].length; ++i) {
      const listener = this._eventListeners[type][i];
      if (
        listener.callback.objectReference === callback.objectReference &&
        listener.capture === capture
      ) {
        return;
      }
    }

    this._eventListeners[type].push({
      callback,
      capture,
      once,
      passive,
      signal
    });

    if (signal !== null) {
      signal._addAlgorithm(() => {
        this.removeEventListener(type, callback, options);
      });
    }
  }

  // Default argument is necessary because webidl2js cannot handle `= {}` with unions at the moment.
  removeEventListener(type, callback, options = { __proto__: null, capture: false }) {
    const capture = flattenEventListenerOptions(options);

    if (callback === null) {
      // Optimization, not in the spec.
      return;
    }

    if (!this._eventListeners[type]) {
      return;
    }

    for (let i = 0; i < this._eventListeners[type].length; ++i) {
      const listener = this._eventListeners[type][i];
      if (
        listener.callback.objectReference === callback.objectReference &&
        listener.capture === capture
      ) {
        this._eventListeners[type].splice(i, 1);
        break;
      }
    }
  }

  dispatchEvent(eventImpl) {
    if (eventImpl._dispatchFlag || !eventImpl._initializedFlag) {
      throw DOMException.create(this._globalObject, [
        "Tried to dispatch an uninitialized event",
        "InvalidStateError"
      ]);
    }
    if (eventImpl.eventPhase !== EVENT_PHASE.NONE) {
      throw DOMException.create(this._globalObject, [
        "Tried to dispatch a dispatching event",
        "InvalidStateError"
      ]);
    }

    eventImpl.isTrusted = false;

    return this._dispatch(eventImpl);
  }

  // https://dom.spec.whatwg.org/#get-the-parent
  _getTheParent() {
    return null;
  }

  // https://dom.spec.whatwg.org/#concept-event-dispatch
  // legacyOutputDidListenersThrowFlag optional parameter is not necessary here since it is only used by indexDB.
  _dispatch(eventImpl, legacyTargetOverrideFlag /* , legacyOutputDidListenersThrowFlag */) {
    let targetImpl = this;
    let clearTargets = false;
    let activationTarget = null;

    eventImpl._dispatchFlag = true;

    const targetOverride = legacyTargetOverrideFlag ?
      idlUtils.implForWrapper(targetImpl._globalObject._document) :
      targetImpl;
    let relatedTarget = retarget(eventImpl.relatedTarget, targetImpl);

    if (targetImpl !== relatedTarget || targetImpl === eventImpl.relatedTarget) {
      const touchTargets = [];

      appendToEventPath(eventImpl, targetImpl, targetOverride, relatedTarget, touchTargets, false);

      const isActivationEvent = MouseEvent.isImpl(eventImpl) && eventImpl.type === "click";

      if (isActivationEvent && targetImpl._hasActivationBehavior) {
        activationTarget = targetImpl;
      }

      let slotInClosedTree = false;
      let slotable = isSlotable(targetImpl) && targetImpl._assignedSlot ? targetImpl : null;
      let parent = getEventTargetParent(targetImpl, eventImpl);

      // Populate event path
      // https://dom.spec.whatwg.org/#event-path
      while (parent !== null) {
        if (slotable !== null) {
          if (parent.localName !== "slot") {
            throw new Error(`JSDOM Internal Error: Expected parent to be a Slot`);
          }

          slotable = null;

          const parentRoot = nodeRoot(parent);
          if (isShadowRoot(parentRoot) && parentRoot.mode === "closed") {
            slotInClosedTree = true;
          }
        }

        if (isSlotable(parent) && parent._assignedSlot) {
          slotable = parent;
        }

        relatedTarget = retarget(eventImpl.relatedTarget, parent);

        if (
          (isNode(parent) && isShadowInclusiveAncestor(nodeRoot(targetImpl), parent)) ||
          idlUtils.wrapperForImpl(parent).constructor.name === "Window"
        ) {
          if (isActivationEvent && eventImpl.bubbles && activationTarget === null &&
              parent._hasActivationBehavior) {
            activationTarget = parent;
          }

          appendToEventPath(eventImpl, parent, null, relatedTarget, touchTargets, slotInClosedTree);
        } else if (parent === relatedTarget) {
          parent = null;
        } else {
          targetImpl = parent;

          if (isActivationEvent && activationTarget === null && targetImpl._hasActivationBehavior) {
            activationTarget = targetImpl;
          }

          appendToEventPath(eventImpl, parent, targetImpl, relatedTarget, touchTargets, slotInClosedTree);
        }

        if (parent !== null) {
          parent = getEventTargetParent(parent, eventImpl);
        }

        slotInClosedTree = false;
      }

      let clearTargetsStructIndex = -1;
      for (let i = eventImpl._path.length - 1; i >= 0 && clearTargetsStructIndex === -1; i--) {
        if (eventImpl._path[i].target !== null) {
          clearTargetsStructIndex = i;
        }
      }
      const clearTargetsStruct = eventImpl._path[clearTargetsStructIndex];

      clearTargets =
          (isNode(clearTargetsStruct.target) && isShadowRoot(nodeRoot(clearTargetsStruct.target))) ||
          (isNode(clearTargetsStruct.relatedTarget) && isShadowRoot(nodeRoot(clearTargetsStruct.relatedTarget)));

      if (activationTarget !== null && activationTarget._legacyPreActivationBehavior) {
        activationTarget._legacyPreActivationBehavior();
      }

      for (let i = eventImpl._path.length - 1; i >= 0; --i) {
        const struct = eventImpl._path[i];

        if (struct.target !== null) {
          eventImpl.eventPhase = EVENT_PHASE.AT_TARGET;
        } else {
          eventImpl.eventPhase = EVENT_PHASE.CAPTURING_PHASE;
        }

        invokeEventListeners(struct, eventImpl, "capturing");
      }

      for (let i = 0; i < eventImpl._path.length; i++) {
        const struct = eventImpl._path[i];

        if (struct.target !== null) {
          eventImpl.eventPhase = EVENT_PHASE.AT_TARGET;
        } else {
          if (!eventImpl.bubbles) {
            continue;
          }

          eventImpl.eventPhase = EVENT_PHASE.BUBBLING_PHASE;
        }

        invokeEventListeners(struct, eventImpl, "bubbling");
      }
    }

    eventImpl.eventPhase = EVENT_PHASE.NONE;

    eventImpl.currentTarget = null;
    eventImpl._path = [];
    eventImpl._dispatchFlag = false;
    eventImpl._stopPropagationFlag = false;
    eventImpl._stopImmediatePropagationFlag = false;

    if (clearTargets) {
      eventImpl.target = null;
      eventImpl.relatedTarget = null;
    }

    if (activationTarget !== null) {
      if (!eventImpl._canceledFlag) {
        activationTarget._activationBehavior(eventImpl);
      } else if (activationTarget._legacyCanceledActivationBehavior) {
        activationTarget._legacyCanceledActivationBehavior();
      }
    }

    return !eventImpl._canceledFlag;
  }
}

module.exports = {
  implementation: EventTargetImpl
};

// https://dom.spec.whatwg.org/#concept-event-listener-invoke
function invokeEventListeners(struct, eventImpl, phase) {
  const structIndex = eventImpl._path.indexOf(struct);
  for (let i = structIndex; i >= 0; i--) {
    const t = eventImpl._path[i];
    if (t.target) {
      eventImpl.target = t.target;
      break;
    }
  }

  eventImpl.relatedTarget = idlUtils.wrapperForImpl(struct.relatedTarget);

  if (eventImpl._stopPropagationFlag) {
    return;
  }

  eventImpl.currentTarget = idlUtils.wrapperForImpl(struct.item);

  const listeners = struct.item._eventListeners;
  innerInvokeEventListeners(eventImpl, listeners, phase, struct.itemInShadowTree);
}

// https://dom.spec.whatwg.org/#concept-event-listener-inner-invoke
function innerInvokeEventListeners(eventImpl, listeners, phase, itemInShadowTree) {
  let found = false;

  const { type, target } = eventImpl;
  const wrapper = idlUtils.wrapperForImpl(target);

  if (!listeners || !listeners[type]) {
    return found;
  }

  // Copy event listeners before iterating since the list can be modified during the iteration.
  const handlers = listeners[type].slice();

  for (let i = 0; i < handlers.length; i++) {
    const listener = handlers[i];
    const { callback, capture, once, passive } = listener;

    // Check if the event listener has been removed since the listeners has been cloned.
    if (!listeners[type].includes(listener)) {
      continue;
    }

    found = true;

    if (
      (phase === "capturing" && !capture) ||
      (phase === "bubbling" && capture)
    ) {
      continue;
    }

    if (once) {
      listeners[type].splice(listeners[type].indexOf(listener), 1);
    }

    let window = null;
    if (wrapper && wrapper._document) {
      // Triggered by Window
      window = wrapper;
    } else if (target._ownerDocument) {
      // Triggered by most webidl2js'ed instances
      window = target._ownerDocument._defaultView;
    } else if (wrapper._ownerDocument) {
      // Currently triggered by some non-webidl2js things
      window = wrapper._ownerDocument._defaultView;
    }

    let currentEvent;
    if (window) {
      currentEvent = window._currentEvent;
      if (!itemInShadowTree) {
        window._currentEvent = eventImpl;
      }
    }

    if (passive) {
      eventImpl._inPassiveListenerFlag = true;
    }

    try {
      callback.call(eventImpl.currentTarget, eventImpl);
    } catch (e) {
      if (window) {
        reportException(window, e);
      }
      // Errors in window-less documents just get swallowed... can you think of anything better?
    }

    eventImpl._inPassiveListenerFlag = false;

    if (window) {
      window._currentEvent = currentEvent;
    }

    if (eventImpl._stopImmediatePropagationFlag) {
      return found;
    }
  }

  return found;
}

function flattenMoreEventListenerOptions(options) {
  const dict = {
    capture: flattenEventListenerOptions(options),
    once: false,
    passive: null,
    signal: null
  };

  if (options !== null && typeof options === "object") {
    dict.once = options.once;
    if ("passive" in options) {
      dict.passive = options.passive;
    }
    if ("signal" in options) {
      dict.signal = options.signal;
    }
  }
  return dict;
}

function flattenEventListenerOptions(options) {
  if (typeof options === "boolean") {
    return options;
  }
  return options.capture;
}

function defaultPassiveValue(type, eventTarget) {
  switch (type) {
    case "touchstart":
    case "touchmove":
    case "wheel":
    case "mousewheel":
      return isWindow(eventTarget) ||
        eventTarget._ownerDocument === eventTarget ||
        eventTarget._ownerDocument.documentElement === eventTarget ||
        eventTarget._ownerDocument.body === eventTarget;
    default:
      return false;
  }
}

// https://dom.spec.whatwg.org/#concept-event-path-append
function appendToEventPath(eventImpl, target, targetOverride, relatedTarget, touchTargets, slotInClosedTree) {
  const itemInShadowTree = isNode(target) && isShadowRoot(nodeRoot(target));
  const rootOfClosedTree = isShadowRoot(target) && target.mode === "closed";

  eventImpl._path.push({
    item: target,
    itemInShadowTree,
    target: targetOverride,
    relatedTarget,
    touchTargets,
    rootOfClosedTree,
    slotInClosedTree
  });
}
