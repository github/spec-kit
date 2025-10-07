"use strict";
const EventImpl = require("./Event-impl").implementation;
const DeviceOrientationEventInit = require("../generated/DeviceOrientationEventInit");

class DeviceOrientationEventImpl extends EventImpl {}
DeviceOrientationEventImpl.defaultInit = DeviceOrientationEventInit.convert(undefined, undefined);

module.exports = {
  implementation: DeviceOrientationEventImpl
};
