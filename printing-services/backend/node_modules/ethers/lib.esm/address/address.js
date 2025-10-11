import { keccak256 } from "../crypto/index.js";
import { getBytes, assertArgument } from "../utils/index.js";
const BN_0 = BigInt(0);
const BN_36 = BigInt(36);
function getChecksumAddress(address) {
    //    if (!isHexString(address, 20)) {
    //        logger.throwArgumentError("invalid address", "address", address);
    //    }
    address = address.toLowerCase();
    const chars = address.substring(2).split("");
    const expanded = new Uint8Array(40);
    for (let i = 0; i < 40; i++) {
        expanded[i] = chars[i].charCodeAt(0);
    }
    const hashed = getBytes(keccak256(expanded));
    for (let i = 0; i < 40; i += 2) {
        if ((hashed[i >> 1] >> 4) >= 8) {
            chars[i] = chars[i].toUpperCase();
        }
        if ((hashed[i >> 1] & 0x0f) >= 8) {
            chars[i + 1] = chars[i + 1].toUpperCase();
        }
    }
    return "0x" + chars.join("");
}
// See: https://en.wikipedia.org/wiki/International_Bank_Account_Number
// Create lookup table
const ibanLookup = {};
for (let i = 0; i < 10; i++) {
    ibanLookup[String(i)] = String(i);
}
for (let i = 0; i < 26; i++) {
    ibanLookup[String.fromCharCode(65 + i)] = String(10 + i);
}
// How many decimal digits can we process? (for 64-bit float, this is 15)
// i.e. Math.floor(Math.log10(Number.MAX_SAFE_INTEGER));
const safeDigits = 15;
function ibanChecksum(address) {
    address = address.toUpperCase();
    address = address.substring(4) + address.substring(0, 2) + "00";
    let expanded = address.split("").map((c) => { return ibanLookup[c]; }).join("");
    // Javascript can handle integers safely up to 15 (decimal) digits
    while (expanded.length >= safeDigits) {
        let block = expanded.substring(0, safeDigits);
        expanded = parseInt(block, 10) % 97 + expanded.substring(block.length);
    }
    let checksum = String(98 - (parseInt(expanded, 10) % 97));
    while (checksum.length < 2) {
        checksum = "0" + checksum;
    }
    return checksum;
}
;
const Base36 = (function () {
    ;
    const result = {};
    for (let i = 0; i < 36; i++) {
        const key = "0123456789abcdefghijklmnopqrstuvwxyz"[i];
        result[key] = BigInt(i);
    }
    return result;
})();
function fromBase36(value) {
    value = value.toLowerCase();
    let result = BN_0;
    for (let i = 0; i < value.length; i++) {
        result = result * BN_36 + Base36[value[i]];
    }
    return result;
}
/**
 *  Returns a normalized and checksumed address for %%address%%.
 *  This accepts non-checksum addresses, checksum addresses and
 *  [[getIcapAddress]] formats.
 *
 *  The checksum in Ethereum uses the capitalization (upper-case
 *  vs lower-case) of the characters within an address to encode
 *  its checksum, which offers, on average, a checksum of 15-bits.
 *
 *  If %%address%% contains both upper-case and lower-case, it is
 *  assumed to already be a checksum address and its checksum is
 *  validated, and if the address fails its expected checksum an
 *  error is thrown.
 *
 *  If you wish the checksum of %%address%% to be ignore, it should
 *  be converted to lower-case (i.e. ``.toLowercase()``) before
 *  being passed in. This should be a very rare situation though,
 *  that you wish to bypass the safegaurds in place to protect
 *  against an address that has been incorrectly copied from another
 *  source.
 *
 *  @example:
 *    // Adds the checksum (via upper-casing specific letters)
 *    getAddress("0x8ba1f109551bd432803012645ac136ddd64dba72")
 *    //_result:
 *
 *    // Converts ICAP address and adds checksum
 *    getAddress("XE65GB6LDNXYOFTX0NSV3FUWKOWIXAMJK36");
 *    //_result:
 *
 *    // Throws an error if an address contains mixed case,
 *    // but the checksum fails
 *    getAddress("0x8Ba1f109551bD432803012645Ac136ddd64DBA72")
 *    //_error:
 */
export function getAddress(address) {
    assertArgument(typeof (address) === "string", "invalid address", "address", address);
    if (address.match(/^(0x)?[0-9a-fA-F]{40}$/)) {
        // Missing the 0x prefix
        if (!address.startsWith("0x")) {
            address = "0x" + address;
        }
        const result = getChecksumAddress(address);
        // It is a checksummed address with a bad checksum
        assertArgument(!address.match(/([A-F].*[a-f])|([a-f].*[A-F])/) || result === address, "bad address checksum", "address", address);
        return result;
    }
    // Maybe ICAP? (we only support direct mode)
    if (address.match(/^XE[0-9]{2}[0-9A-Za-z]{30,31}$/)) {
        // It is an ICAP address with a bad checksum
        assertArgument(address.substring(2, 4) === ibanChecksum(address), "bad icap checksum", "address", address);
        let result = fromBase36(address.substring(4)).toString(16);
        while (result.length < 40) {
            result = "0" + result;
        }
        return getChecksumAddress("0x" + result);
    }
    assertArgument(false, "invalid address", "address", address);
}
/**
 *  The [ICAP Address format](link-icap) format is an early checksum
 *  format which attempts to be compatible with the banking
 *  industry [IBAN format](link-wiki-iban) for bank accounts.
 *
 *  It is no longer common or a recommended format.
 *
 *  @example:
 *    getIcapAddress("0x8ba1f109551bd432803012645ac136ddd64dba72");
 *    //_result:
 *
 *    getIcapAddress("XE65GB6LDNXYOFTX0NSV3FUWKOWIXAMJK36");
 *    //_result:
 *
 *    // Throws an error if the ICAP checksum is wrong
 *    getIcapAddress("XE65GB6LDNXYOFTX0NSV3FUWKOWIXAMJK37");
 *    //_error:
 */
export function getIcapAddress(address) {
    //let base36 = _base16To36(getAddress(address).substring(2)).toUpperCase();
    let base36 = BigInt(getAddress(address)).toString(36).toUpperCase();
    while (base36.length < 30) {
        base36 = "0" + base36;
    }
    return "XE" + ibanChecksum("XE00" + base36) + base36;
}
//# sourceMappingURL=address.js.map