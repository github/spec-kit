/**
 *  The [Base58 Encoding](link-base58) scheme allows a **numeric** value
 *  to be encoded as a compact string using a radix of 58 using only
 *  alpha-numeric characters. Confusingly similar characters are omitted
 *  (i.e. ``"l0O"``).
 *
 *  Note that Base58 encodes a **numeric** value, not arbitrary bytes,
 *  since any zero-bytes on the left would get removed. To mitigate this
 *  issue most schemes that use Base58 choose specific high-order values
 *  to ensure non-zero prefixes.
 *
 *  @_subsection: api/utils:Base58 Encoding [about-base58]
 */
import type { BytesLike } from "./index.js";
/**
 *  Encode %%value%% as a Base58-encoded string.
 */
export declare function encodeBase58(_value: BytesLike): string;
/**
 *  Decode the Base58-encoded %%value%%.
 */
export declare function decodeBase58(value: string): bigint;
//# sourceMappingURL=base58.d.ts.map