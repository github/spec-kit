"use strict";
const EventImpl = require("./Event-impl").implementation;

class PromiseRejectionEventImpl extends EventImpl {}

// Cannot use the usual pattern because `promise` is required.
PromiseRejectionEventImpl.defaultInit = {
  __proto__: null,
  reason: undefined
};

module.exports = {
  implementation: PromiseRejectionEventImpl
};
