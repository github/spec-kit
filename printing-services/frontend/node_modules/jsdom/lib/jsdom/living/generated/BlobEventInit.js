"use strict";

const conversions = require("webidl-conversions");
const utils = require("./utils.js");

const Blob = require("./Blob.js");
const EventInit = require("./EventInit.js");

exports._convertInherit = (globalObject, obj, ret, { context = "The provided value" } = {}) => {
  EventInit._convertInherit(globalObject, obj, ret, { context });

  {
    const key = "data";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      value = Blob.convert(globalObject, value, { context: context + " has member 'data' that" });

      ret[key] = value;
    } else {
      throw new globalObject.TypeError("data is required in 'BlobEventInit'");
    }
  }

  {
    const key = "timecode";
    let value = obj === undefined || obj === null ? undefined : obj[key];
    if (value !== undefined) {
      value = conversions["double"](value, { context: context + " has member 'timecode' that", globals: globalObject });

      ret[key] = value;
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
