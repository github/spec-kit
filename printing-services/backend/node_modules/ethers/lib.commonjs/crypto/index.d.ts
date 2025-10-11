/**
 *  A fundamental building block of Ethereum is the underlying
 *  cryptographic primitives.
 *
 *  @_section: api/crypto:Cryptographic Functions   [about-crypto]
 */
import { computeHmac } from "./hmac.js";
import { keccak256 } from "./keccak.js";
import { ripemd160 } from "./ripemd160.js";
import { pbkdf2 } from "./pbkdf2.js";
import { randomBytes } from "./random.js";
import { scrypt, scryptSync } from "./scrypt.js";
import { sha256, sha512 } from "./sha2.js";
export { computeHmac, randomBytes, keccak256, ripemd160, sha256, sha512, pbkdf2, scrypt, scryptSync };
export { SigningKey } from "./signing-key.js";
export { Signature } from "./signature.js";
/**
 *  Once called, prevents any future change to the underlying cryptographic
 *  primitives using the ``.register`` feature for hooks.
 */
declare function lock(): void;
export { lock };
export type { ProgressCallback } from "./scrypt.js";
export type { SignatureLike } from "./signature.js";
//# sourceMappingURL=index.d.ts.map