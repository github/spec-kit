"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.assertFunctionOrSelf = void 0;
/**
 * This function asserts the given value as a function or itself.
 * If the value itself is a function it will evaluate it with the passed in arguments,
 * elsewise it will directly return itself.
 */
function assertFunctionOrSelf(functionOrSelf, ...args) {
    if (typeof functionOrSelf === 'function') {
        return functionOrSelf(...args);
    }
    else {
        return functionOrSelf;
    }
}
exports.assertFunctionOrSelf = assertFunctionOrSelf;
