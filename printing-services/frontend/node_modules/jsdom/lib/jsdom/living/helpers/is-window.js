"use strict";
const idlUtils = require("../generated/utils");

// Until webidl2js gains support for checking for Window, this would have to do.
module.exports = val => {
  if (typeof val !== "object") {
    return false;
  }
  const wrapper = idlUtils.wrapperForImpl(val);
  if (typeof wrapper === "object") {
    return wrapper === wrapper._globalProxy;
  }

  // `val` may be either impl or wrapper currently, because webidl2js currently unwraps Window objects (and their global
  // proxies) to their underlying EventTargetImpl during conversion, which is not what we want. But at the same time,
  // some internal usage call this constructor with the actual global proxy.
  return module.exports(idlUtils.implForWrapper(val));
};
