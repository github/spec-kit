/**
 *  A [[HexString]] whose length is even, which ensures it is a valid
 *  representation of binary data.
 */
export type DataHexString = string;
/**
 *  A string which is prefixed with ``0x`` and followed by any number
 *  of case-agnostic hexadecimal characters.
 *
 *  It must match the regular expression ``/0x[0-9A-Fa-f]*\/``.
 */
export type HexString = string;
/**
 *  An object that can be used to represent binary data.
 */
export type BytesLike = DataHexString | Uint8Array;
/**
 *  Get a typed Uint8Array for %%value%%. If already a Uint8Array
 *  the original %%value%% is returned; if a copy is required use
 *  [[getBytesCopy]].
 *
 *  @see: getBytesCopy
 */
export declare function getBytes(value: BytesLike, name?: string): Uint8Array;
/**
 *  Get a typed Uint8Array for %%value%%, creating a copy if necessary
 *  to prevent any modifications of the returned value from being
 *  reflected elsewhere.
 *
 *  @see: getBytes
 */
export declare function getBytesCopy(value: BytesLike, name?: string): Uint8Array;
/**
 *  Returns true if %%value%% is a valid [[HexString]].
 *
 *  If %%length%% is ``true`` or a //number//, it also checks that
 *  %%value%% is a valid [[DataHexString]] of %%length%% (if a //number//)
 *  bytes of data (e.g. ``0x1234`` is 2 bytes).
 */
export declare function isHexString(value: any, length?: number | boolean): value is `0x${string}`;
/**
 *  Returns true if %%value%% is a valid representation of arbitrary
 *  data (i.e. a valid [[DataHexString]] or a Uint8Array).
 */
export declare function isBytesLike(value: any): value is BytesLike;
/**
 *  Returns a [[DataHexString]] representation of %%data%%.
 */
export declare function hexlify(data: BytesLike): string;
/**
 *  Returns a [[DataHexString]] by concatenating all values
 *  within %%data%%.
 */
export declare function concat(datas: ReadonlyArray<BytesLike>): string;
/**
 *  Returns the length of %%data%%, in bytes.
 */
export declare function dataLength(data: BytesLike): number;
/**
 *  Returns a [[DataHexString]] by slicing %%data%% from the %%start%%
 *  offset to the %%end%% offset.
 *
 *  By default %%start%% is 0 and %%end%% is the length of %%data%%.
 */
export declare function dataSlice(data: BytesLike, start?: number, end?: number): string;
/**
 *  Return the [[DataHexString]] result by stripping all **leading**
 ** zero bytes from %%data%%.
 */
export declare function stripZerosLeft(data: BytesLike): string;
/**
 *  Return the [[DataHexString]] of %%data%% padded on the **left**
 *  to %%length%% bytes.
 *
 *  If %%data%% already exceeds %%length%%, a [[BufferOverrunError]] is
 *  thrown.
 *
 *  This pads data the same as **values** are in Solidity
 *  (e.g. ``uint128``).
 */
export declare function zeroPadValue(data: BytesLike, length: number): string;
/**
 *  Return the [[DataHexString]] of %%data%% padded on the **right**
 *  to %%length%% bytes.
 *
 *  If %%data%% already exceeds %%length%%, a [[BufferOverrunError]] is
 *  thrown.
 *
 *  This pads data the same as **bytes** are in Solidity
 *  (e.g. ``bytes16``).
 */
export declare function zeroPadBytes(data: BytesLike, length: number): string;
//# sourceMappingURL=data.d.ts.map