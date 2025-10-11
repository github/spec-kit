/**
 *  @_ignore
 */

import {
    getBytesCopy, assertArgument, toUtf8Bytes
} from "../utils/index.js";

export function looseArrayify(hexString: string): Uint8Array {
    if (typeof(hexString) === "string" && !hexString.startsWith("0x")) {
        hexString = "0x" + hexString;
    }
    return getBytesCopy(hexString);
}

export function zpad(value: String | number, length: number): String {
    value = String(value);
    while (value.length < length) { value = '0' + value; }
    return value;
}

export function getPassword(password: string | Uint8Array): Uint8Array {
    if (typeof(password) === 'string') {
        return toUtf8Bytes(password, "NFKC");
    }
    return getBytesCopy(password);
}

export function spelunk<T>(object: any, _path: string): T {

    const match = _path.match(/^([a-z0-9$_.-]*)(:([a-z]+))?(!)?$/i);
    assertArgument(match != null, "invalid path", "path", _path);

    const path = match[1];
    const type = match[3];
    const reqd = (match[4] === "!");

    let cur = object;
    for (const comp of path.toLowerCase().split('.')) {

        // Search for a child object with a case-insensitive matching key
        if (Array.isArray(cur)) {
            if (!comp.match(/^[0-9]+$/)) { break; }
            cur = cur[parseInt(comp)];

        } else if (typeof(cur) === "object") {
            let found: any = null;
            for (const key in cur) {
                 if (key.toLowerCase() === comp) {
                     found = cur[key];
                     break;
                 }
            }
            cur = found;

        } else {
            cur = null;
        }

        if (cur == null) { break; }
    }

    assertArgument(!reqd || cur != null, "missing required value", "path", path);

    if (type && cur != null) {
        if (type === "int") {
            if (typeof(cur) === "string" && cur.match(/^-?[0-9]+$/)) {
                return <T><unknown>parseInt(cur);
            } else if (Number.isSafeInteger(cur)) {
                return cur;
            }
        }

        if (type === "number") {
            if (typeof(cur) === "string" && cur.match(/^-?[0-9.]*$/)) {
                return <T><unknown>parseFloat(cur);
            }
        }

        if (type === "data") {
            if (typeof(cur) === "string") { return <T><unknown>looseArrayify(cur); }
        }

        if (type === "array" && Array.isArray(cur)) { return <T><unknown>cur; }
        if (type === typeof(cur)) { return cur; }

        assertArgument(false, `wrong type found for ${ type } `, "path", path);
    }

    return cur;
}
/*
export function follow(object: any, path: string): null | string {
    let currentChild = object;

    for (const comp of path.toLowerCase().split('/')) {

        // Search for a child object with a case-insensitive matching key
        let matchingChild = null;
        for (const key in currentChild) {
             if (key.toLowerCase() === comp) {
                 matchingChild = currentChild[key];
                 break;
             }
        }

        if (matchingChild === null) { return null; }

        currentChild = matchingChild;
    }

    return currentChild;
}

// "path/to/something:type!"
export function followRequired(data: any, path: string): string {
    const value = follow(data, path);
    if (value != null) { return value; }
    return logger.throwArgumentError("invalid value", `data:${ path }`,
    JSON.stringify(data));
}
*/
// See: https://www.ietf.org/rfc/rfc4122.txt (Section 4.4)
/*
export function uuidV4(randomBytes: BytesLike): string {
    const bytes = getBytes(randomBytes, "randomBytes");

    // Section: 4.1.3:
    // - time_hi_and_version[12:16] = 0b0100
    bytes[6] = (bytes[6] & 0x0f) | 0x40;

    // Section 4.4
    // - clock_seq_hi_and_reserved[6] = 0b0
    // - clock_seq_hi_and_reserved[7] = 0b1
    bytes[8] = (bytes[8] & 0x3f) | 0x80;

    const value = hexlify(bytes);

    return [
       value.substring(2, 10),
       value.substring(10, 14),
       value.substring(14, 18),
       value.substring(18, 22),
       value.substring(22, 34),
    ].join("-");
}
*/
