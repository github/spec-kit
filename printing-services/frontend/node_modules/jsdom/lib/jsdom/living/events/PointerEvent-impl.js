"use strict";
const MouseEventImpl = require("./MouseEvent-impl").implementation;
const PointerEventInit = require("../generated/PointerEventInit");

class PointerEventImpl extends MouseEventImpl {
  getCoalescedEvents() {
    // The EventImpl constructor initializes this.coalescedEvents from the init dictionary.
    // Return a new array each time (webidl2js doesn't handle this for us.)
    return [...this.coalescedEvents];
  }

  getPredictedEvents() {
    // As above.
    return [...this.predictedEvents];
  }
}
PointerEventImpl.defaultInit = PointerEventInit.convert(undefined, undefined);

module.exports = {
  implementation: PointerEventImpl
};
