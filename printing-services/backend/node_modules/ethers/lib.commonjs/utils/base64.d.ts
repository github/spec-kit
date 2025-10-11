import type { BytesLike } from "./data.js";
/**
 *  Decodes the base-64 encoded %%value%%.
 *
 *  @example:
 *    // The decoded value is always binary data...
 *    result = decodeBase64("SGVsbG8gV29ybGQhIQ==")
 *    //_result:
 *
 *    // ...use toUtf8String to convert it to a string.
 *    toUtf8String(result)
 *    //_result:
 *
 *    // Decoding binary data
 *    decodeBase64("EjQ=")
 *    //_result:
 */
export declare function decodeBase64(value: string): Uint8Array;
/**
 *  Encodes %%data%% as a base-64 encoded string.
 *
 *  @example:
 *    // Encoding binary data as a hexstring
 *    encodeBase64("0x1234")
 *    //_result:
 *
 *    // Encoding binary data as a Uint8Array
 *    encodeBase64(new Uint8Array([ 0x12, 0x34 ]))
 *    //_result:
 *
 *    // The input MUST be data...
 *    encodeBase64("Hello World!!")
 *    //_error:
 *
 *    // ...use toUtf8Bytes for this.
 *    encodeBase64(toUtf8Bytes("Hello World!!"))
 *    //_result:
 */
export declare function encodeBase64(data: BytesLike): string;
//# sourceMappingURL=base64.d.ts.map