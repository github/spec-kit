import type { BytesLike } from "../utils/index.js";
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
export declare function computeHmac(algorithm: "sha256" | "sha512", _key: BytesLike, _data: BytesLike): string;
export declare namespace computeHmac {
    var _: (algorithm: "sha256" | "sha512", key: Uint8Array, data: Uint8Array) => BytesLike;
    var lock: () => void;
    var register: (func: (algorithm: "sha256" | "sha512", key: Uint8Array, data: Uint8Array) => BytesLike) => void;
}
//# sourceMappingURL=hmac.d.ts.map