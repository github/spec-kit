/**
 *  About bytes32 strings...
 *
 *  @_docloc: api/utils:Bytes32 Strings
 */
import { getBytes, toUtf8Bytes, toUtf8String, zeroPadBytes } from "../utils/index.js";
/**
 *  Encodes %%text%% as a Bytes32 string.
 */
export function encodeBytes32String(text) {
    // Get the bytes
    const bytes = toUtf8Bytes(text);
    // Check we have room for null-termination
    if (bytes.length > 31) {
        throw new Error("bytes32 string must be less than 32 bytes");
    }
    // Zero-pad (implicitly null-terminates)
    return zeroPadBytes(bytes, 32);
}
/**
 *  Encodes the Bytes32-encoded %%bytes%% into a string.
 */
export function decodeBytes32String(_bytes) {
    const data = getBytes(_bytes, "bytes");
    // Must be 32 bytes with a null-termination
    if (data.length !== 32) {
        throw new Error("invalid bytes32 - not 32 bytes long");
    }
    if (data[31] !== 0) {
        throw new Error("invalid bytes32 string - no null terminator");
    }
    // Find the null termination
    let length = 31;
    while (data[length - 1] === 0) {
        length--;
    }
    // Determine the string value
    return toUtf8String(data.slice(0, length));
}
//# sourceMappingURL=bytes32.js.map