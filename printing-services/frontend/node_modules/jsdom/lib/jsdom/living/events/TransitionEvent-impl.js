"use strict";
const EventImpl = require("./Event-impl").implementation;
const TransitionEventInit = require("../generated/TransitionEventInit");

class TransitionEventImpl extends EventImpl {}
TransitionEventImpl.defaultInit = TransitionEventInit.convert(undefined, undefined);

module.exports = {
  implementation: TransitionEventImpl
};
