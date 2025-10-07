/**
 * @fileoverview Main package entrypoint.
 * @author Nicholas C. Zakas
 */

"use strict";

//------------------------------------------------------------------------------
// Public Interface
//------------------------------------------------------------------------------

module.exports = {
    configs: {
        all: require("./configs/eslint-all"),
        recommended: require("./configs/eslint-recommended")
    }
};
