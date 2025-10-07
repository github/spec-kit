"use strict";

exports.notImplementedMethod = (window, className, methodName, specialCircumstances) => {
  exports.notImplemented(
    window,
    `${className}'s ${methodName}() method${specialCircumstances ? `: ${specialCircumstances}` : ""}`
  );
};

exports.notImplemented = (window, message) => {
  if (!window) {
    // Do nothing for window-less documents.
    return;
  }

  const error = new Error(`Not implemented: ${message}`);
  error.type = "not-implemented";

  window._virtualConsole.emit("jsdomError", error);
};
