/**
 *  An **HMAC** enables verification that a given key was used
 *  to authenticate a payload.
 *
 *  See: [[link-wiki-hmac]]
 *
 *  @_subsection: api/crypto:HMAC  [about-hmac]
 */
import { createHmac } from "./crypto.js";
import { getBytes, hexlify } from "../utils/index.js";

import type { BytesLike } from "../utils/index.js";


let locked = false;

const _computeHmac = function(algorithm: "sha256" | "sha512", key: Uint8Array, data: Uint8Array): BytesLike {
    return createHmac(algorithm, key).update(data).digest();
}

let __computeHmac = _computeHmac;

/**
 *  Return the HMAC for %%data%% using the %%key%% key with the underlying
 *  %%algo%% used for compression.
 *
 *  @example:
 *    key = id("some-secret")
 *
 *    // Compute the HMAC
 *    computeHmac("sha256", key, "0x1337")
 *    //_result:
 *
 *    // To compute the HMAC of UTF-8 data, the data must be
 *    // converted to UTF-8 bytes
 *    computeHmac("sha256", key, toUtf8Bytes("Hello World"))
 *    //_result:
 *
 */
export function computeHmac(algorithm: "sha256" | "sha512", _key: BytesLike, _data: BytesLike): string {
    const key = getBytes(_key, "key");
    const data = getBytes(_data, "data");
    return hexlify(__computeHmac(algorithm, key, data));
}
computeHmac._ = _computeHmac;
computeHmac.lock =  function() { locked = true; }
computeHmac.register = function(func: (algorithm: "sha256" | "sha512", key: Uint8Array, data: Uint8Array) => BytesLike) {
    if (locked) { throw new Error("computeHmac is locked"); }
    __computeHmac = func;
}
Object.freeze(computeHmac);
