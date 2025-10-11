/**
 *  When sending values to or receiving values from a [[Contract]], the
 *  data is generally encoded using the [ABI standard](link-solc-abi).
 *
 *  The AbiCoder provides a utility to encode values to ABI data and
 *  decode values from ABI data.
 *
 *  Most of the time, developers should favour the [[Contract]] class,
 *  which further abstracts a lot of the finer details of ABI data.
 *
 *  @_section api/abi/abi-coder:ABI Encoding
 */
import { Result } from "./coders/abstract-coder.js";
import { ParamType } from "./fragments.js";
import type { BytesLike, CallExceptionAction, CallExceptionError } from "../utils/index.js";
/**
 *  The **AbiCoder** is a low-level class responsible for encoding JavaScript
 *  values into binary data and decoding binary data into JavaScript values.
 */
export declare class AbiCoder {
    #private;
    /**
     *  Get the default values for the given %%types%%.
     *
     *  For example, a ``uint`` is by default ``0`` and ``bool``
     *  is by default ``false``.
     */
    getDefaultValue(types: ReadonlyArray<string | ParamType>): Result;
    /**
     *  Encode the %%values%% as the %%types%% into ABI data.
     *
     *  @returns DataHexstring
     */
    encode(types: ReadonlyArray<string | ParamType>, values: ReadonlyArray<any>): string;
    /**
     *  Decode the ABI %%data%% as the %%types%% into values.
     *
     *  If %%loose%% decoding is enabled, then strict padding is
     *  not enforced. Some older versions of Solidity incorrectly
     *  padded event data emitted from ``external`` functions.
     */
    decode(types: ReadonlyArray<string | ParamType>, data: BytesLike, loose?: boolean): Result;
    static _setDefaultMaxInflation(value: number): void;
    /**
     *  Returns the shared singleton instance of a default [[AbiCoder]].
     *
     *  On the first call, the instance is created internally.
     */
    static defaultAbiCoder(): AbiCoder;
    /**
     *  Returns an ethers-compatible [[CallExceptionError]] Error for the given
     *  result %%data%% for the [[CallExceptionAction]] %%action%% against
     *  the Transaction %%tx%%.
     */
    static getBuiltinCallException(action: CallExceptionAction, tx: {
        to?: null | string;
        from?: null | string;
        data?: string;
    }, data: null | BytesLike): CallExceptionError;
}
//# sourceMappingURL=abi-coder.d.ts.map