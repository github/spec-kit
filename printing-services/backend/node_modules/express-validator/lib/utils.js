"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.bindAll = void 0;
exports.toString = toString;
exports.runAllChains = runAllChains;
const bindAll = (object) => {
    const protoKeys = Object.getOwnPropertyNames(Object.getPrototypeOf(object));
    protoKeys.forEach(key => {
        const maybeFn = object[key];
        if (typeof maybeFn === 'function' && key !== 'constructor') {
            object[key] = maybeFn.bind(object);
        }
    });
    return object;
};
exports.bindAll = bindAll;
function toString(value) {
    if (value instanceof Date) {
        return value.toISOString();
    }
    else if (value && typeof value === 'object' && value.toString) {
        if (typeof value.toString !== 'function') {
            return Object.getPrototypeOf(value).toString.call(value);
        }
        return value.toString();
    }
    else if (value == null || (isNaN(value) && !value.length)) {
        return '';
    }
    return String(value);
}
/**
 * Runs all validation chains, and returns their results.
 *
 * If one of them has a request-level bail set, the previous chains will be awaited on so that
 * results are not skewed, which can be slow.
 * If this same chain also contains errors, no further chains are run.
 */
async function runAllChains(req, chains, runOpts) {
    const promises = [];
    for (const chain of chains) {
        const bails = chain.builder.build().bail;
        if (bails) {
            await Promise.all(promises);
        }
        const resultPromise = chain.run(req, runOpts);
        promises.push(resultPromise);
        if (bails) {
            const result = await resultPromise;
            if (!result.isEmpty()) {
                break;
            }
        }
    }
    return Promise.all(promises);
}
