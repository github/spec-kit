
import { keccak256 } from "../crypto/index.js";
import {
    concat, hexlify, assertArgument, toUtf8Bytes
} from "../utils/index.js";


import { ens_normalize } from "@adraffy/ens-normalize";

const Zeros = new Uint8Array(32);
Zeros.fill(0);

function checkComponent(comp: Uint8Array): Uint8Array {
    assertArgument(comp.length !== 0, "invalid ENS name; empty component", "comp", comp)
    return comp;
}

function ensNameSplit(name: string): Array<Uint8Array> {
    const bytes = toUtf8Bytes(ensNormalize(name));
    const comps: Array<Uint8Array> = [ ];

    if (name.length === 0) { return comps; }

    let last = 0;
    for (let i = 0; i < bytes.length; i++) {
        const d = bytes[i];

        // A separator (i.e. "."); copy this component
        if (d === 0x2e) {
            comps.push(checkComponent(bytes.slice(last, i)));
            last = i + 1;
        }
    }

    // There was a stray separator at the end of the name
    assertArgument(last < bytes.length, "invalid ENS name; empty component", "name", name);

    comps.push(checkComponent(bytes.slice(last)));
    return comps;
}

/**
 *  Returns the ENS %%name%% normalized.
 */
export function ensNormalize(name: string): string {
    try {
        if (name.length === 0) { throw new Error("empty label"); }
        return ens_normalize(name);
    } catch (error: any) {
        assertArgument(false, `invalid ENS name (${ error.message })`, "name", name);
    }
}

/**
 *  Returns ``true`` if %%name%% is a valid ENS name.
 */
export function isValidName(name: string): name is string {
    try {
        return (ensNameSplit(name).length !== 0);
    } catch (error) { }
    return false;
}

/**
 *  Returns the [[link-namehash]] for %%name%%.
 */
export function namehash(name: string): string {
    assertArgument(typeof(name) === "string", "invalid ENS name; not a string", "name", name);

    assertArgument(name.length, `invalid ENS name (empty label)`, "name", name);

    let result: string | Uint8Array = Zeros;

    const comps = ensNameSplit(name);
    while (comps.length) {
        result = keccak256(concat([ result, keccak256(<Uint8Array>(comps.pop()))] ));
    }

    return hexlify(result);
}

/**
 *  Returns the DNS encoded %%name%%.
 *
 *  This is used for various parts of ENS name resolution, such
 *  as the wildcard resolution.
 */
export function dnsEncode(name: string, _maxLength?: number): string {
    const length = (_maxLength != null) ? _maxLength: 63;

    assertArgument(length <= 255, "DNS encoded label cannot exceed 255", "length", length);

    return hexlify(concat(ensNameSplit(name).map((comp) => {
        assertArgument(comp.length <= length, `label ${ JSON.stringify(name) } exceeds ${ length } bytes`, "name", name);

        const bytes = new Uint8Array(comp.length + 1);
        bytes.set(comp, 1);
        bytes[0] = bytes.length - 1;
        return bytes;
    }))) + "00";
}
