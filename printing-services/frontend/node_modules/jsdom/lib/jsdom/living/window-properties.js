"use strict";
const idlUtils = require("./generated/utils.js");
const HTMLCollection = require("./generated/HTMLCollection.js");
const { HTML_NS } = require("./helpers/namespaces.js");
const { nodeRoot } = require("./helpers/node.js");
const { treeOrderSorter } = require("../utils.js");

// We count iframe/frame here too even though it's not in the relevant part of the spec because we still need to track
// named iframes/frames, and we'll process the element -> WindowProxy work as special cases.
const nameAttributeElementLocalNames = new Set(["embed", "form", "img", "object", "iframe", "frame"]);

const trackers = new WeakMap(); // WeakMap<WindowProperties, Map<string, Set<Element>>>

function upsert(map, key, value) {
  let set = map.get(key);
  if (!set) {
    set = new Set();
    map.set(key, set);
  }
  set.add(value);
}

function remove(map, key, value) {
  const set = map.get(key);
  if (set) {
    set.delete(value);
    if (set.size === 0) {
      map.delete(key);
    }
  }
}

function getNamedObject(window, name) {
  const tracker = trackers.get(window);
  const set = tracker.get(name);
  if (set === undefined) {
    return undefined;
  }

  const sorted = [...set].sort(treeOrderSorter);
  for (const element of sorted) {
    if (element.localName === "iframe" || element.localName === "frame") {
      const { contentWindow } = element;
      if (contentWindow && element.getAttributeNS(null, "name") === name) {
        return contentWindow;
      }
    }
  }

  if (set.size === 1) {
    return idlUtils.wrapperForImpl(set.values().next().value);
  }

  return HTMLCollection.create(window, [], {
    element: idlUtils.implForWrapper(window._document).documentElement,
    query() {
      // Do *not* reuse `sorted` or `set` from above. We need to re-get and re-iterate the set each time because it
      // might have changed due to elements being attached, removed, or having their names changed!
      const currentSet = tracker.get(name);
      return [...currentSet].sort(treeOrderSorter);
    }
  });
}

exports.elementAttached = element => {
  const window = element._ownerDocument._globalObject;
  if (!window) {
    return;
  }

  if (element.namespaceURI !== HTML_NS) {
    return;
  }
  if (nodeRoot(element) !== element._ownerDocument) {
    return;
  }

  const tracker = trackers.get(window);

  if (nameAttributeElementLocalNames.has(element.localName)) {
    const nameAttr = element.getAttributeNS(null, "name");
    if (nameAttr !== null) {
      upsert(tracker, nameAttr, element);
    }
  }

  const idAttr = element.getAttributeNS(null, "id");
  if (idAttr !== null) {
    upsert(tracker, idAttr, element);
  }
};

exports.elementDetached = element => {
  const window = element._ownerDocument._globalObject;
  if (!window) {
    return;
  }

  if (element.namespaceURI !== HTML_NS) {
    return;
  }

  const tracker = trackers.get(window);

  const idAttr = element.getAttributeNS(null, "id");
  if (idAttr !== null) {
    remove(tracker, idAttr, element);
  }

  const nameAttr = element.getAttributeNS(null, "name");
  if (nameAttr !== null) {
    remove(tracker, nameAttr, element);
  }
};

exports.elementAttributeModified = (element, attributeName, value, oldValue) => {
  const window = element._ownerDocument._globalObject;
  if (!window) {
    return;
  }

  if (element.namespaceURI !== HTML_NS) {
    return;
  }
  if (nodeRoot(element) !== element._ownerDocument) {
    return;
  }

  const tracker = trackers.get(window);

  // TODO what about attribute namespace?

  if (attributeName === "id") {
    if (element.getAttributeNS(null, "name") !== oldValue) {
      remove(tracker, oldValue, element);
    }
    if (value !== null) {
      upsert(tracker, value, element);
    }
  } else if (attributeName === "name") {
    if (nameAttributeElementLocalNames.has(element.localName)) {
      if (element.getAttributeNS(null, "id") !== oldValue) {
        remove(tracker, oldValue, element);
      }
      if (value !== null) {
        upsert(tracker, value, element);
      }
    }
  }
};

exports.create = (eventTargetPrototype, window) => {
  const windowProperties = Object.create(eventTargetPrototype, {
    [Symbol.toStringTag]: {
      value: "WindowProperties",
      configurable: true
    }
  });

  const windowPropertiesProxy = new Proxy(windowProperties, {
    getOwnPropertyDescriptor(target, property) {
      if (typeof property === "symbol") {
        return Reflect.getOwnPropertyDescriptor(target, property);
      }

      // Named property visibility algorithm check, modified as discused in
      // https://github.com/whatwg/webidl/issues/607.
      let targetObj = Object.getPrototypeOf(target);
      while (targetObj !== null) {
        if (Object.hasOwn(targetObj, property)) {
          return Reflect.getOwnPropertyDescriptor(target, property);
        }

        targetObj = Object.getPrototypeOf(targetObj);
      }

      const value = getNamedObject(window, property);
      if (value) {
        return {
          value,
          enumerable: false, // Window is [LegacyUnenumerableNamedProperties]
          writable: true,
          configurable: true
        };
      }

      return Reflect.getOwnPropertyDescriptor(target, property);
    },
    has(target, property) {
      if (typeof property === "symbol") {
        return Reflect.has(target, property);
      }

      const desc = this.getOwnPropertyDescriptor(target, property);
      if (desc !== undefined) {
        return true;
      }

      const parent = Object.getPrototypeOf(target);
      return Reflect.has(parent, property);
    },
    get(target, property, receiver) {
      if (typeof property === "symbol") {
        return Reflect.get(target, property, receiver);
      }

      const desc = this.getOwnPropertyDescriptor(target, property);
      if (desc === undefined) {
        const parent = Object.getPrototypeOf(target);
        return Reflect.get(parent, property, receiver);
      }

      // Named properties object only has data properties.
      return desc.value;
    },
    set(target, property, value, receiver) {
      if (typeof property === "symbol") {
        return Reflect.set(target, property, value, receiver);
      }

      const ownDesc = this.getOwnPropertyDescriptor(target, property);
      return idlUtils.ordinarySetWithOwnDescriptor(target, property, value, receiver, ownDesc);
    },
    defineProperty() {
      return false;
    },
    deleteProperty() {
      return false;
    },
    setPrototypeOf() {
      throw new TypeError("Immutable prototype object WindowProperties cannot have its prototype set.");
    },
    preventExtensions() {
      return false;
    }
  });

  trackers.set(window, new Map());

  return windowPropertiesProxy;
};
