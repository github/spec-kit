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
var toHaveURL_exports = {};
__export(toHaveURL_exports, {
  toHaveURLWithPredicate: () => toHaveURLWithPredicate
});
module.exports = __toCommonJS(toHaveURL_exports);
var import_utils = require("playwright-core/lib/utils");
var import_utils2 = require("playwright-core/lib/utils");
var import_expect = require("./expect");
var import_matcherHint = require("./matcherHint");
var import_expectBundle = require("../common/expectBundle");
async function toHaveURLWithPredicate(page, expected, options) {
  const matcherName = "toHaveURL";
  const expression = "page";
  const matcherOptions = {
    isNot: this.isNot,
    promise: this.promise
  };
  if (typeof expected !== "function") {
    throw new Error(
      [
        // Always display `expected` in expectation place
        (0, import_matcherHint.matcherHint)(this, void 0, matcherName, expression, void 0, matcherOptions, void 0, void 0, true),
        `${import_utils2.colors.bold("Matcher error")}: ${(0, import_expectBundle.EXPECTED_COLOR)("expected")} value must be a string, regular expression, or predicate`,
        this.utils.printWithType("Expected", expected, this.utils.printExpected)
      ].join("\n\n")
    );
  }
  const timeout = options?.timeout ?? this.timeout;
  const baseURL = page.context()._options.baseURL;
  let conditionSucceeded = false;
  let lastCheckedURLString = void 0;
  try {
    await page.mainFrame().waitForURL(
      (url) => {
        lastCheckedURLString = url.toString();
        if (options?.ignoreCase) {
          return !this.isNot === (0, import_utils.urlMatches)(
            baseURL?.toLocaleLowerCase(),
            lastCheckedURLString.toLocaleLowerCase(),
            expected
          );
        }
        return !this.isNot === (0, import_utils.urlMatches)(baseURL, lastCheckedURLString, expected);
      },
      { timeout }
    );
    conditionSucceeded = true;
  } catch (e) {
    conditionSucceeded = false;
  }
  if (conditionSucceeded)
    return { name: matcherName, pass: !this.isNot, message: () => "" };
  return {
    name: matcherName,
    pass: this.isNot,
    message: () => toHaveURLMessage(
      this,
      matcherName,
      expression,
      expected,
      lastCheckedURLString,
      this.isNot,
      true,
      timeout
    ),
    actual: lastCheckedURLString,
    timeout
  };
}
function toHaveURLMessage(state, matcherName, expression, expected, received, pass, didTimeout, timeout) {
  const matcherOptions = {
    isNot: state.isNot,
    promise: state.promise
  };
  const receivedString = received || "";
  const messagePrefix = (0, import_matcherHint.matcherHint)(state, void 0, matcherName, expression, void 0, matcherOptions, didTimeout ? timeout : void 0, void 0, true);
  let printedReceived;
  let printedExpected;
  let printedDiff;
  if (typeof expected === "function") {
    printedExpected = `Expected predicate to ${!state.isNot ? "succeed" : "fail"}`;
    printedReceived = `Received string: ${(0, import_expectBundle.printReceived)(receivedString)}`;
  } else {
    if (pass) {
      printedExpected = `Expected pattern: not ${state.utils.printExpected(expected)}`;
      const formattedReceived = (0, import_expect.printReceivedStringContainExpectedResult)(receivedString, null);
      printedReceived = `Received string: ${formattedReceived}`;
    } else {
      const labelExpected = `Expected ${typeof expected === "string" ? "string" : "pattern"}`;
      printedDiff = state.utils.printDiffOrStringify(expected, receivedString, labelExpected, "Received string", false);
    }
  }
  const resultDetails = printedDiff ? printedDiff : printedExpected + "\n" + printedReceived;
  return messagePrefix + resultDetails;
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  toHaveURLWithPredicate
});
