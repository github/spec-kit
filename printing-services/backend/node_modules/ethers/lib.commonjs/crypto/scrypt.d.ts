import type { BytesLike } from "../utils/index.js";
/**
 *  A callback during long-running operations to update any
 *  UI or provide programatic access to the progress.
 *
 *  The %%percent%% is a value between ``0`` and ``1``.
 *
 *  @_docloc: api/crypto:Passwords
 */
export type ProgressCallback = (percent: number) => void;
/**
 *  The [[link-wiki-scrypt]] uses a memory and cpu hard method of
 *  derivation to increase the resource cost to brute-force a password
 *  for a given key.
 *
 *  This means this algorithm is intentionally slow, and can be tuned to
 *  become slower. As computation and memory speed improve over time,
 *  increasing the difficulty maintains the cost of an attacker.
 *
 *  For example, if a target time of 5 seconds is used, a legitimate user
 *  which knows their password requires only 5 seconds to unlock their
 *  account. A 6 character password has 68 billion possibilities, which
 *  would require an attacker to invest over 10,000 years of CPU time. This
 *  is of course a crude example (as password generally aren't random),
 *  but demonstrates to value of imposing large costs to decryption.
 *
 *  For this reason, if building a UI which involved decrypting or
 *  encrypting datsa using scrypt, it is recommended to use a
 *  [[ProgressCallback]] (as event short periods can seem lik an eternity
 *  if the UI freezes). Including the phrase //"decrypting"// in the UI
 *  can also help, assuring the user their waiting is for a good reason.
 *
 *  @_docloc: api/crypto:Passwords
 *
 *  @example:
 *    // The password must be converted to bytes, and it is generally
 *    // best practices to ensure the string has been normalized. Many
 *    // formats explicitly indicate the normalization form to use.
 *    password = "hello"
 *    passwordBytes = toUtf8Bytes(password, "NFKC")
 *
 *    salt = id("some-salt")
 *
 *    // Compute the scrypt
 *    scrypt(passwordBytes, salt, 1024, 8, 1, 16)
 *    //_result:
 */
export declare function scrypt(_passwd: BytesLike, _salt: BytesLike, N: number, r: number, p: number, dkLen: number, progress?: ProgressCallback): Promise<string>;
export declare namespace scrypt {
    var _: (passwd: Uint8Array, salt: Uint8Array, N: number, r: number, p: number, dkLen: number, onProgress?: ProgressCallback | undefined) => Promise<Uint8Array>;
    var lock: () => void;
    var register: (func: (passwd: Uint8Array, salt: Uint8Array, N: number, r: number, p: number, dkLen: number, progress?: ProgressCallback | undefined) => Promise<BytesLike>) => void;
}
/**
 *  Provides a synchronous variant of [[scrypt]].
 *
 *  This will completely lock up and freeze the UI in a browser and will
 *  prevent any event loop from progressing. For this reason, it is
 *  preferred to use the [async variant](scrypt).
 *
 *  @_docloc: api/crypto:Passwords
 *
 *  @example:
 *    // The password must be converted to bytes, and it is generally
 *    // best practices to ensure the string has been normalized. Many
 *    // formats explicitly indicate the normalization form to use.
 *    password = "hello"
 *    passwordBytes = toUtf8Bytes(password, "NFKC")
 *
 *    salt = id("some-salt")
 *
 *    // Compute the scrypt
 *    scryptSync(passwordBytes, salt, 1024, 8, 1, 16)
 *    //_result:
 */
export declare function scryptSync(_passwd: BytesLike, _salt: BytesLike, N: number, r: number, p: number, dkLen: number): string;
export declare namespace scryptSync {
    var _: (passwd: Uint8Array, salt: Uint8Array, N: number, r: number, p: number, dkLen: number) => Uint8Array;
    var lock: () => void;
    var register: (func: (passwd: Uint8Array, salt: Uint8Array, N: number, r: number, p: number, dkLen: number) => BytesLike) => void;
}
//# sourceMappingURL=scrypt.d.ts.map