"use strict";

const isWindow = require("../helpers/is-window");
const UIEventInit = require("../generated/UIEventInit");
const EventImpl = require("./Event-impl").implementation;

class UIEventImpl extends EventImpl {
  constructor(globalObject, args, privateData) {
    const eventInitDict = args[1];

    // undefined check included so that we can omit the property in internal usage.
    if (eventInitDict && eventInitDict.view !== null && eventInitDict.view !== undefined) {
      if (!isWindow(eventInitDict.view)) {
        throw new TypeError(`Failed to construct '${new.target.name.replace(/Impl$/, "")}': member view is not of ` +
                            "type Window.");
      }
    }

    super(globalObject, args, privateData);
  }

  initUIEvent(type, bubbles, cancelable, view, detail) {
    if (view !== null) {
      if (!isWindow(view)) {
        throw new TypeError(`Failed to execute 'initUIEvent' on '${this.constructor.name.replace(/Impl$/, "")}': ` +
                            "parameter 4 is not of type 'Window'.");
      }
    }

    if (this._dispatchFlag) {
      return;
    }

    this.initEvent(type, bubbles, cancelable);
    this.view = view;
    this.detail = detail;
  }
}
UIEventImpl.defaultInit = UIEventInit.convert(undefined, undefined);

module.exports = {
  implementation: UIEventImpl
};
