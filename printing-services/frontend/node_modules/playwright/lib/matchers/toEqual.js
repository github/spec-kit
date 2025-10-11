"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);
var toEqual_exports = {};
__export(toEqual_exports, {
  toEqual: () => toEqual
});
module.exports = __toCommonJS(toEqual_exports);
var import_utils = require("playwright-core/lib/utils");
var import_util = require("../util");
var import_matcherHint = require("./matcherHint");
const EXPECTED_LABEL = "Expected";
const RECEIVED_LABEL = "Received";
async function toEqual(matcherName, receiver, receiverType, query, expected, options = {}, messagePreventExtraStatIndent) {
  (0, import_util.expectTypes)(receiver, [receiverType], matcherName);
  const matcherOptions = {
    comment: options.contains ? "" : "deep equality",
    isNot: this.isNot,
    promise: this.promise
  };
  const timeout = options.timeout ?? this.timeout;
  const { matches: pass, received, log, timedOut } = await query(!!this.isNot, timeout);
  if (pass === !this.isNot) {
    return {
      name: matcherName,
      message: () => "",
      pass,
      expected
    };
  }
  let printedReceived;
  let printedExpected;
  let printedDiff;
  if (pass) {
    printedExpected = `Expected: not ${this.utils.printExpected(expected)}`;
    printedReceived = `Received: ${this.utils.printReceived(received)}`;
  } else if (Array.isArray(expected) && Array.isArray(received)) {
    const normalizedExpected = expected.map((exp, index) => {
      const rec = received[index];
      if ((0, import_utils.isRegExp)(exp))
        return exp.test(rec) ? rec : exp;
      return exp;
    });
    printedDiff = this.utils.printDiffOrStringify(
      normalizedExpected,
      received,
      EXPECTED_LABEL,
      RECEIVED_LABEL,
      false
    );
  } else {
    printedDiff = this.utils.printDiffOrStringify(
      expected,
      received,
      EXPECTED_LABEL,
      RECEIVED_LABEL,
      false
    );
  }
  const message = () => {
    const details = printedDiff || `${printedExpected}
${printedReceived}`;
    const header = (0, import_matcherHint.matcherHint)(this, receiver, matcherName, "locator", void 0, matcherOptions, timedOut ? timeout : void 0, details, messagePreventExtraStatIndent);
    return `${header}${(0, import_util.callLogText)(log)}`;
  };
  return {
    actual: received,
    expected,
    message,
    name: matcherName,
    pass,
    log,
    timeout: timedOut ? timeout : void 0
  };
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  toEqual
});
