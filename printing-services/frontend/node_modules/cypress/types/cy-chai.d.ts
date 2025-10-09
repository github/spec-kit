// Shim definition to export a namespace. Cypress is actually a global module
// so import/export isn't allowed there. We import here and define a global module
/// <reference path="./chai/index.d.ts" />
declare namespace Chai {
  interface Include {
    html(html: string): Assertion
    text(text: string): Assertion
    value(text: string): Assertion
  }
}
