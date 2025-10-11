import type { SignatureLike } from "../crypto/index.js";
/**
 *  Computes the [[link-eip-191]] personal-sign message digest to sign.
 *
 *  This prefixes the message with [[MessagePrefix]] and the decimal length
 *  of %%message%% and computes the [[keccak256]] digest.
 *
 *  If %%message%% is a string, it is converted to its UTF-8 bytes
 *  first. To compute the digest of a [[DataHexString]], it must be converted
 *  to [bytes](getBytes).
 *
 *  @example:
 *    hashMessage("Hello World")
 *    //_result:
 *
 *    // Hashes the SIX (6) string characters, i.e.
 *    // [ "0", "x", "4", "2", "4", "3" ]
 *    hashMessage("0x4243")
 *    //_result:
 *
 *    // Hashes the TWO (2) bytes [ 0x42, 0x43 ]...
 *    hashMessage(getBytes("0x4243"))
 *    //_result:
 *
 *    // ...which is equal to using data
 *    hashMessage(new Uint8Array([ 0x42, 0x43 ]))
 *    //_result:
 *
 */
export declare function hashMessage(message: Uint8Array | string): string;
/**
 *  Return the address of the private key that produced
 *  the signature %%sig%% during signing for %%message%%.
 */
export declare function verifyMessage(message: Uint8Array | string, sig: SignatureLike): string;
//# sourceMappingURL=message.d.ts.map