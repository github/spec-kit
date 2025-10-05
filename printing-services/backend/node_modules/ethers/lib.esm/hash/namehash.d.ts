/**
 *  Returns the ENS %%name%% normalized.
 */
export declare function ensNormalize(name: string): string;
/**
 *  Returns ``true`` if %%name%% is a valid ENS name.
 */
export declare function isValidName(name: string): name is string;
/**
 *  Returns the [[link-namehash]] for %%name%%.
 */
export declare function namehash(name: string): string;
/**
 *  Returns the DNS encoded %%name%%.
 *
 *  This is used for various parts of ENS name resolution, such
 *  as the wildcard resolution.
 */
export declare function dnsEncode(name: string, _maxLength?: number): string;
//# sourceMappingURL=namehash.d.ts.map