"use strict";

const EventImpl = require("./Event-impl").implementation;

const EventInit = require("../generated/EventInit");

class BeforeUnloadEventImpl extends EventImpl {}
BeforeUnloadEventImpl.defaultInit = EventInit.convert(undefined, undefined);

module.exports = {
  implementation: BeforeUnloadEventImpl
};
