"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.cloneObject = void 0;
const rfdc = require("rfdc");
const clone = rfdc({ circles: true });
/**
 * Deep clones a object in the most easiest manner.
 */
function cloneObject(obj) {
    return clone(obj);
}
exports.cloneObject = cloneObject;
