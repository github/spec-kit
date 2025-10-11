"use strict";

const EventImpl = require("./Event-impl").implementation;
const { implementation: DeviceMotionEventAccelerationImpl } =
  require("../deviceorientation/DeviceMotionEventAcceleration-impl");
const { implementation: DeviceMotionEventRotationRateImpl } =
  require("../deviceorientation/DeviceMotionEventRotationRate-impl");

class DeviceMotionEventImpl extends EventImpl {
  constructor(globalObject, args, privateData) {
    super(globalObject, args, privateData);

    const eventInitDict = args[1];

    this.acceleration = null;
    if (eventInitDict?.acceleration) {
      const accelImpl = new DeviceMotionEventAccelerationImpl(globalObject, [], {});
      accelImpl.x = eventInitDict.acceleration.x;
      accelImpl.y = eventInitDict.acceleration.y;
      accelImpl.z = eventInitDict.acceleration.z;
      this.acceleration = accelImpl;
    }

    this.accelerationIncludingGravity = null;
    if (eventInitDict?.accelerationIncludingGravity) {
      const accelGImpl = new DeviceMotionEventAccelerationImpl(globalObject, [], {});
      accelGImpl.x = eventInitDict.accelerationIncludingGravity.x;
      accelGImpl.y = eventInitDict.accelerationIncludingGravity.y;
      accelGImpl.z = eventInitDict.accelerationIncludingGravity.z;
      this.accelerationIncludingGravity = accelGImpl;
    }

    this.rotationRate = null;
    if (eventInitDict?.rotationRate) {
      const rotImpl = new DeviceMotionEventRotationRateImpl(globalObject, [], {});
      rotImpl.alpha = eventInitDict.rotationRate.alpha;
      rotImpl.beta = eventInitDict.rotationRate.beta;
      rotImpl.gamma = eventInitDict.rotationRate.gamma;
      this.rotationRate = rotImpl;
    }

    this.interval = eventInitDict?.interval ?? 0;
  }
}
DeviceMotionEventImpl.defaultInit = Object.create(null);

module.exports = {
  implementation: DeviceMotionEventImpl
};
