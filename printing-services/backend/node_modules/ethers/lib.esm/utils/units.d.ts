import type { BigNumberish, Numeric } from "../utils/index.js";
/**
 *  Converts %%value%% into a //decimal string//, assuming %%unit%% decimal
 *  places. The %%unit%% may be the number of decimal places or the name of
 *  a unit (e.g. ``"gwei"`` for 9 decimal places).
 *
 */
export declare function formatUnits(value: BigNumberish, unit?: string | Numeric): string;
/**
 *  Converts the //decimal string// %%value%% to a BigInt, assuming
 *  %%unit%% decimal places. The %%unit%% may the number of decimal places
 *  or the name of a unit (e.g. ``"gwei"`` for 9 decimal places).
 */
export declare function parseUnits(value: string, unit?: string | Numeric): bigint;
/**
 *  Converts %%value%% into a //decimal string// using 18 decimal places.
 */
export declare function formatEther(wei: BigNumberish): string;
/**
 *  Converts the //decimal string// %%ether%% to a BigInt, using 18
 *  decimal places.
 */
export declare function parseEther(ether: string): bigint;
//# sourceMappingURL=units.d.ts.map