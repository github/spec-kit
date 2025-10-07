"use strict";
const { EventEmitter } = require("events");

module.exports = class VirtualConsole extends EventEmitter {
  constructor() {
    super();

    this.on("error", () => {
      // If "error" event has no listeners,
      // EventEmitter throws an exception
    });
  }

  forwardTo(anyConsole, { jsdomErrors } = {}) {
    for (const method of Object.keys(anyConsole)) {
      if (typeof anyConsole[method] === "function") {
        function onMethodCall(...args) {
          anyConsole[method](...args);
        }
        this.on(method, onMethodCall);
      }
    }

    function forward(e) {
      if (e.type === "unhandled-exception") {
        anyConsole.error(e.cause.stack);
      } else {
        anyConsole.error(e.message);
      }
    }

    if (jsdomErrors === undefined) {
      this.on("jsdomError", forward);
    } else if (Array.isArray(jsdomErrors)) {
      this.on("jsdomError", e => {
        if (jsdomErrors.includes(e.type)) {
          forward(e);
        }
      });
    } else if (jsdomErrors !== "none") {
      throw new TypeError("Invalid jsdomErrors option");
    }

    return this;
  }
};
