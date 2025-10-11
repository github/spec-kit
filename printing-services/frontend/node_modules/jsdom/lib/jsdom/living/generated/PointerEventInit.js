"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const PointerEvent = require("./PointerEvent.js");
const MouseEventInit = require("./MouseEventInit.js");

exports._convertInherit = (globalObject, obj, ret, { context = "The provided value" } = {}) => {
  MouseEventInit._convertInherit(globalObject, obj, ret, { context });

  {
    const key = "altitudeAngle";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      value = conversions["double"](value, {
        context: context + " has member 'altitudeAngle' that",
        globals: globalObject
      });

      ret[key] = value;
    }
  }

  {
    const key = "azimuthAngle";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      value = conversions["double"](value, {
        context: context + " has member 'azimuthAngle' that",
        globals: globalObject
      });

      ret[key] = value;
    }
  }

  {
    const key = "coalescedEvents";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      if (!utils.isObject(value)) {
        throw new globalObject.TypeError(
          context + " has member 'coalescedEvents' that" + " is not an iterable object."
        );
      } else {
        const V = [];
        const tmp = value;
        for (let nextItem of tmp) {
          nextItem = PointerEvent.convert(globalObject, nextItem, {
            context: context + " has member 'coalescedEvents' that" + "'s element"
          });

          V.push(nextItem);
        }
        value = V;
      }

      ret[key] = value;
    } else {
      ret[key] = [];
    }
  }

  {
    const key = "height";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      value = conversions["double"](value, { context: context + " has member 'height' that", globals: globalObject });

      ret[key] = value;
    } else {
      ret[key] = 1;
    }
  }

  {
    const key = "isPrimary";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      value = conversions["boolean"](value, {
        context: context + " has member 'isPrimary' that",
        globals: globalObject
      });

      ret[key] = value;
    } else {
      ret[key] = false;
    }
  }

  {
    const key = "persistentDeviceId";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      value = conversions["long"](value, {
        context: context + " has member 'persistentDeviceId' that",
        globals: globalObject
      });

      ret[key] = value;
    } else {
      ret[key] = 0;
    }
  }

  {
    const key = "pointerId";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      value = conversions["long"](value, { context: context + " has member 'pointerId' that", globals: globalObject });

      ret[key] = value;
    } else {
      ret[key] = 0;
    }
  }

  {
    const key = "pointerType";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      value = conversions["DOMString"](value, {
        context: context + " has member 'pointerType' that",
        globals: globalObject
      });

      ret[key] = value;
    } else {
      ret[key] = "";
    }
  }

  {
    const key = "predictedEvents";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      if (!utils.isObject(value)) {
        throw new globalObject.TypeError(
          context + " has member 'predictedEvents' that" + " is not an iterable object."
        );
      } else {
        const V = [];
        const tmp = value;
        for (let nextItem of tmp) {
          nextItem = PointerEvent.convert(globalObject, nextItem, {
            context: context + " has member 'predictedEvents' that" + "'s element"
          });

          V.push(nextItem);
        }
        value = V;
      }

      ret[key] = value;
    } else {
      ret[key] = [];
    }
  }

  {
    const key = "pressure";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      value = conversions["float"](value, { context: context + " has member 'pressure' that", globals: globalObject });

      ret[key] = value;
    } else {
      ret[key] = 0;
    }
  }

  {
    const key = "tangentialPressure";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      value = conversions["float"](value, {
        context: context + " has member 'tangentialPressure' that",
        globals: globalObject
      });

      ret[key] = value;
    } else {
      ret[key] = 0;
    }
  }

  {
    const key = "tiltX";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      value = conversions["long"](value, { context: context + " has member 'tiltX' that", globals: globalObject });

      ret[key] = value;
    }
  }

  {
    const key = "tiltY";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      value = conversions["long"](value, { context: context + " has member 'tiltY' that", globals: globalObject });

      ret[key] = value;
    }
  }

  {
    const key = "twist";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      value = conversions["long"](value, { context: context + " has member 'twist' that", globals: globalObject });

      ret[key] = value;
    } else {
      ret[key] = 0;
    }
  }

  {
    const key = "width";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      value = conversions["double"](value, { context: context + " has member 'width' that", globals: globalObject });

      ret[key] = value;
    } else {
      ret[key] = 1;
    }
  }
};

exports.convert = (globalObject, obj, { context = "The provided value" } = {}) => {
  if (obj !== undefined && typeof obj !== "object" && typeof obj !== "function") {
    throw new globalObject.TypeError(`${context} is not an object.`);
  }

  const ret = Object.create(null);
  exports._convertInherit(globalObject, obj, ret, { context });
  return ret;
};
