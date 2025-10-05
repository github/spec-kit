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
import { getBytes } from "./data.js";
import { assertArgument } from "./errors.js";
import { toBigInt } from "./maths.js";
const Alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
let Lookup = null;
function getAlpha(letter) {
    if (Lookup == null) {
        Lookup = {};
        for (let i = 0; i < Alphabet.length; i++) {
            Lookup[Alphabet[i]] = BigInt(i);
        }
    }
    const result = Lookup[letter];
    assertArgument(result != null, `invalid base58 value`, "letter", letter);
    return result;
}
const BN_0 = BigInt(0);
const BN_58 = BigInt(58);
/**
 *  Encode %%value%% as a Base58-encoded string.
 */
export function encodeBase58(_value) {
    const bytes = getBytes(_value);
    let value = toBigInt(bytes);
    let result = "";
    while (value) {
        result = Alphabet[Number(value % BN_58)] + result;
        value /= BN_58;
    }
    // Account for leading padding zeros
    for (let i = 0; i < bytes.length; i++) {
        if (bytes[i]) {
            break;
        }
        result = Alphabet[0] + result;
    }
    return result;
}
/**
 *  Decode the Base58-encoded %%value%%.
 */
export function decodeBase58(value) {
    let result = BN_0;
    for (let i = 0; i < value.length; i++) {
        result *= BN_58;
        result += getAlpha(value[i]);
    }
    return result;
}
//# sourceMappingURL=base58.js.map