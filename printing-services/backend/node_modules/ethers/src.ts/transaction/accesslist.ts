import { getAddress } from "../address/index.js";
import { assertArgument, isHexString } from "../utils/index.js";

import type { AccessList, AccessListish } from "./index.js";


function accessSetify(addr: string, storageKeys: Array<string>): { address: string,storageKeys: Array<string> } {
    return {
        address: getAddress(addr),
        storageKeys: storageKeys.map((storageKey, index) => {
            assertArgument(isHexString(storageKey, 32), "invalid slot", `storageKeys[${ index }]`, storageKey);
            return storageKey.toLowerCase();
        })
    };
}

/**
 *  Returns a [[AccessList]] from any ethers-supported access-list structure.
 */
export function accessListify(value: AccessListish): AccessList {
    if (Array.isArray(value)) {
        return (<Array<[ string, Array<string>] | { address: string, storageKeys: Array<string>}>>value).map((set, index) => {
            if (Array.isArray(set)) {
                assertArgument(set.length === 2, "invalid slot set", `value[${ index }]`, set);
                return accessSetify(set[0], set[1])
            }
            assertArgument(set != null && typeof(set) === "object", "invalid address-slot set", "value", value);
            return accessSetify(set.address, set.storageKeys);
        });
    }

    assertArgument(value != null && typeof(value) === "object", "invalid access list", "value", value);

    const result: Array<{ address: string, storageKeys: Array<string> }> = Object.keys(value).map((addr) => {
        const storageKeys: Record<string, true> = value[addr].reduce((accum, storageKey) => {
            accum[storageKey] = true;
            return accum;
        }, <Record<string, true>>{ });
        return accessSetify(addr, Object.keys(storageKeys).sort())
    });
    result.sort((a, b) => (a.address.localeCompare(b.address)));
    return result;
}
