import { getAddress } from "../address/index.js";
import {
    keccak256 as _keccak256, sha256 as _sha256
} from "../crypto/index.js";
import {
    concat, dataLength, getBytes, hexlify, toBeArray, toTwos, toUtf8Bytes, zeroPadBytes, zeroPadValue,
    assertArgument
} from "../utils/index.js";


const regexBytes = new RegExp("^bytes([0-9]+)$");
const regexNumber = new RegExp("^(u?int)([0-9]*)$");
const regexArray = new RegExp("^(.*)\\[([0-9]*)\\]$");


function _pack(type: string, value: any, isArray?: boolean): Uint8Array {
    switch(type) {
        case "address":
            if (isArray) { return getBytes(zeroPadValue(value, 32)); }
            return getBytes(getAddress(value));
        case "string":
            return toUtf8Bytes(value);
        case "bytes":
            return getBytes(value);
        case "bool":
            value = (!!value ? "0x01": "0x00");
            if (isArray) { return getBytes(zeroPadValue(value, 32)); }
            return getBytes(value);
    }

    let match =  type.match(regexNumber);
    if (match) {
        let signed = (match[1] === "int");
        let size = parseInt(match[2] || "256")

        assertArgument((!match[2] || match[2] === String(size)) && (size % 8 === 0) && size !== 0 && size <= 256, "invalid number type", "type", type);

        if (isArray) { size = 256; }

        if (signed) { value = toTwos(value, size); }

        return getBytes(zeroPadValue(toBeArray(value), size / 8));
    }

    match = type.match(regexBytes);
    if (match) {
        const size = parseInt(match[1]);

        assertArgument(String(size) === match[1] && size !== 0 && size <= 32, "invalid bytes type", "type", type);
        assertArgument(dataLength(value) === size, `invalid value for ${ type }`, "value", value);

        if (isArray) { return getBytes(zeroPadBytes(value, 32)); }
        return value;
    }

    match = type.match(regexArray);
    if (match && Array.isArray(value)) {
        const baseType = match[1];
        const count = parseInt(match[2] || String(value.length));
        assertArgument(count === value.length, `invalid array length for ${ type }`, "value", value);

        const result: Array<Uint8Array> = [];
        value.forEach(function(value) {
            result.push(_pack(baseType, value, true));
        });
        return getBytes(concat(result));
    }

    assertArgument(false, "invalid type", "type", type)
}

// @TODO: Array Enum

/**
 *   Computes the [[link-solc-packed]] representation of %%values%%
 *   respectively to their %%types%%.
 *
 *   @example:
 *       addr = "0x8ba1f109551bd432803012645ac136ddd64dba72"
 *       solidityPacked([ "address", "uint" ], [ addr, 45 ]);
 *       //_result:
 */
export function solidityPacked(types: ReadonlyArray<string>, values: ReadonlyArray<any>): string {
    assertArgument(types.length === values.length, "wrong number of values; expected ${ types.length }", "values", values);

    const tight: Array<Uint8Array> = [];
    types.forEach(function(type, index) {
        tight.push(_pack(type, values[index]));
    });
    return hexlify(concat(tight));
}

/**
 *   Computes the [[link-solc-packed]] [[keccak256]] hash of %%values%%
 *   respectively to their %%types%%.
 *
 *   @example:
 *       addr = "0x8ba1f109551bd432803012645ac136ddd64dba72"
 *       solidityPackedKeccak256([ "address", "uint" ], [ addr, 45 ]);
 *       //_result:
 */
export function solidityPackedKeccak256(types: ReadonlyArray<string>, values: ReadonlyArray<any>): string {
    return _keccak256(solidityPacked(types, values));
}

/**
 *   Computes the [[link-solc-packed]] [[sha256]] hash of %%values%%
 *   respectively to their %%types%%.
 *
 *   @example:
 *       addr = "0x8ba1f109551bd432803012645ac136ddd64dba72"
 *       solidityPackedSha256([ "address", "uint" ], [ addr, 45 ]);
 *       //_result:
 */
export function solidityPackedSha256(types: ReadonlyArray<string>, values: ReadonlyArray<any>): string {
    return _sha256(solidityPacked(types, values));
}
