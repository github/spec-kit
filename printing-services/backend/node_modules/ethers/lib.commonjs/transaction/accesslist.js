"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.accessListify = void 0;
const index_js_1 = require("../address/index.js");
const index_js_2 = require("../utils/index.js");
function accessSetify(addr, storageKeys) {
    return {
        address: (0, index_js_1.getAddress)(addr),
        storageKeys: storageKeys.map((storageKey, index) => {
            (0, index_js_2.assertArgument)((0, index_js_2.isHexString)(storageKey, 32), "invalid slot", `storageKeys[${index}]`, storageKey);
            return storageKey.toLowerCase();
        })
    };
}
/**
 *  Returns a [[AccessList]] from any ethers-supported access-list structure.
 */
function accessListify(value) {
    if (Array.isArray(value)) {
        return value.map((set, index) => {
            if (Array.isArray(set)) {
                (0, index_js_2.assertArgument)(set.length === 2, "invalid slot set", `value[${index}]`, set);
                return accessSetify(set[0], set[1]);
            }
            (0, index_js_2.assertArgument)(set != null && typeof (set) === "object", "invalid address-slot set", "value", value);
            return accessSetify(set.address, set.storageKeys);
        });
    }
    (0, index_js_2.assertArgument)(value != null && typeof (value) === "object", "invalid access list", "value", value);
    const result = Object.keys(value).map((addr) => {
        const storageKeys = value[addr].reduce((accum, storageKey) => {
            accum[storageKey] = true;
            return accum;
        }, {});
        return accessSetify(addr, Object.keys(storageKeys).sort());
    });
    result.sort((a, b) => (a.address.localeCompare(b.address)));
    return result;
}
exports.accessListify = accessListify;
//# sourceMappingURL=accesslist.js.map