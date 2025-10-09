// Project: https://www.cypress.io
// GitHub:  https://github.com/cypress-io/cypress
// Definitions by: Gert Hengeveld <https://github.com/ghengeveld>
//                 Mike Woudenberg <https://github.com/mikewoudenberg>
//                 Robbert van Markus <https://github.com/rvanmarkus>
//                 Nicholas Boll <https://github.com/nicholasboll>
// TypeScript Version: 5.0
// Updated by the Cypress team: https://www.cypress.io/about/

/// <reference path="./cy-blob-util.d.ts" />
/// <reference path="./cy-bluebird.d.ts" />
/// <reference path="./cy-minimatch.d.ts" />
/// <reference path="./cy-chai.d.ts" />
/// <reference path="./lodash/index.d.ts" />
/// <reference path="./sinon/index.d.ts" />
/// <reference path="./sinon-chai/index.d.ts" />
/// <reference path="./mocha/index.d.ts" />
/// <reference path="./jquery/index.d.ts" />
/// <reference path="./chai-jquery/index.d.ts" />

// jQuery includes dependency "sizzle" that provides types
// so we include it too in "node_modules/sizzle".
// This way jQuery can load it using 'reference types="sizzle"' directive

// load ambient declaration for "cypress" NPM module
// hmm, how to load it better?
/// <reference path="./cypress-npm-api.d.ts" />

/// <reference path="./net-stubbing.d.ts" />
/// <reference path="./cypress.d.ts" />
/// <reference path="./cypress-global-vars.d.ts" />
/// <reference path="./cypress-type-helpers.d.ts" />
/// <reference path="./cypress-expect.d.ts" />
