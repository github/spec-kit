/**
 *   Computes the [[link-solc-packed]] representation of %%values%%
 *   respectively to their %%types%%.
 *
 *   @example:
 *       addr = "0x8ba1f109551bd432803012645ac136ddd64dba72"
 *       solidityPacked([ "address", "uint" ], [ addr, 45 ]);
 *       //_result:
 */
export declare function solidityPacked(types: ReadonlyArray<string>, values: ReadonlyArray<any>): string;
/**
 *   Computes the [[link-solc-packed]] [[keccak256]] hash of %%values%%
 *   respectively to their %%types%%.
 *
 *   @example:
 *       addr = "0x8ba1f109551bd432803012645ac136ddd64dba72"
 *       solidityPackedKeccak256([ "address", "uint" ], [ addr, 45 ]);
 *       //_result:
 */
export declare function solidityPackedKeccak256(types: ReadonlyArray<string>, values: ReadonlyArray<any>): string;
/**
 *   Computes the [[link-solc-packed]] [[sha256]] hash of %%values%%
 *   respectively to their %%types%%.
 *
 *   @example:
 *       addr = "0x8ba1f109551bd432803012645ac136ddd64dba72"
 *       solidityPackedSha256([ "address", "uint" ], [ addr, 45 ]);
 *       //_result:
 */
export declare function solidityPackedSha256(types: ReadonlyArray<string>, values: ReadonlyArray<any>): string;
//# sourceMappingURL=solidity.d.ts.map