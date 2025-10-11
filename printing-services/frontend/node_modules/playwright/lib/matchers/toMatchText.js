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
var toMatchText_exports = {};
__export(toMatchText_exports, {
  toMatchText: () => toMatchText
});
module.exports = __toCommonJS(toMatchText_exports);
var import_utils = require("playwright-core/lib/utils");
var import_util = require("../util");
var import_expect = require("./expect");
var import_matcherHint = require("./matcherHint");
var import_expectBundle = require("../common/expectBundle");
async function toMatchText(matcherName, receiver, receiverType, query, expected, options = {}) {
  (0, import_util.expectTypes)(receiver, [receiverType], matcherName);
  const matcherOptions = {
    isNot: this.isNot,
    promise: this.promise
  };
  if (!(typeof expected === "string") && !(expected && typeof expected.test === "function")) {
    throw new Error([
      (0, import_matcherHint.matcherHint)(this, receiverType === "Locator" ? receiver : void 0, matcherName, options.receiverLabel ?? receiver, expected, matcherOptions, void 0, void 0, true),
      `${import_utils.colors.bold("Matcher error")}: ${(0, import_expectBundle.EXPECTED_COLOR)("expected")} value must be a string or regular expression`,
      this.utils.printWithType("Expected", expected, this.utils.printExpected)
    ].join("\n\n"));
  }
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
  const stringSubstring = options.matchSubstring ? "substring" : "string";
  const receivedString = received || "";
  const notFound = received === import_matcherHint.kNoElementsFoundError;
  let printedReceived;
  let printedExpected;
  let printedDiff;
  if (pass) {
    if (typeof expected === "string") {
      if (notFound) {
        printedExpected = `Expected ${stringSubstring}: not ${this.utils.printExpected(expected)}`;
        printedReceived = `Received: ${received}`;
      } else {
        printedExpected = `Expected ${stringSubstring}: not ${this.utils.printExpected(expected)}`;
        const formattedReceived = (0, import_expect.printReceivedStringContainExpectedSubstring)(receivedString, receivedString.indexOf(expected), expected.length);
        printedReceived = `Received string: ${formattedReceived}`;
      }
    } else {
      if (notFound) {
        printedExpected = `Expected pattern: not ${this.utils.printExpected(expected)}`;
        printedReceived = `Received: ${received}`;
      } else {
        printedExpected = `Expected pattern: not ${this.utils.printExpected(expected)}`;
        const formattedReceived = (0, import_expect.printReceivedStringContainExpectedResult)(receivedString, typeof expected.exec === "function" ? expected.exec(receivedString) : null);
        printedReceived = `Received string: ${formattedReceived}`;
      }
    }
  } else {
    const labelExpected = `Expected ${typeof expected === "string" ? stringSubstring : "pattern"}`;
    if (notFound) {
      printedExpected = `${labelExpected}: ${this.utils.printExpected(expected)}`;
      printedReceived = `Received: ${received}`;
    } else {
      printedDiff = this.utils.printDiffOrStringify(expected, receivedString, labelExpected, "Received string", false);
    }
  }
  const message = () => {
    const resultDetails = printedDiff ? printedDiff : printedExpected + "\n" + printedReceived;
    const hints = (0, import_matcherHint.matcherHint)(this, receiverType === "Locator" ? receiver : void 0, matcherName, options.receiverLabel ?? "locator", void 0, matcherOptions, timedOut ? timeout : void 0, resultDetails, true);
    return hints + (0, import_util.callLogText)(log);
  };
  return {
    name: matcherName,
    expected,
    message,
    pass,
    actual: received,
    log,
    timeout: timedOut ? timeout : void 0
  };
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  toMatchText
});
