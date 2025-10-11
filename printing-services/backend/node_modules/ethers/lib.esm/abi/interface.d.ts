/**
 *  The Interface class is a low-level class that accepts an
 *  ABI and provides all the necessary functionality to encode
 *  and decode paramaters to and results from methods, events
 *  and errors.
 *
 *  It also provides several convenience methods to automatically
 *  search and find matching transactions and events to parse them.
 *
 *  @_subsection api/abi:Interfaces  [interfaces]
 */
import { AbiCoder } from "./abi-coder.js";
import { checkResultErrors, Result } from "./coders/abstract-coder.js";
import { ConstructorFragment, ErrorFragment, EventFragment, FallbackFragment, Fragment, FunctionFragment, ParamType } from "./fragments.js";
import { Typed } from "./typed.js";
import type { BigNumberish, BytesLike, CallExceptionError, CallExceptionTransaction } from "../utils/index.js";
import type { JsonFragment } from "./fragments.js";
export { checkResultErrors, Result };
/**
 *  When using the [[Interface-parseLog]] to automatically match a Log to its event
 *  for parsing, a **LogDescription** is returned.
 */
export declare class LogDescription {
    /**
     *  The matching fragment for the ``topic0``.
     */
    readonly fragment: EventFragment;
    /**
     *  The name of the Event.
     */
    readonly name: string;
    /**
     *  The full Event signature.
     */
    readonly signature: string;
    /**
     *  The topic hash for the Event.
     */
    readonly topic: string;
    /**
     *  The arguments passed into the Event with ``emit``.
     */
    readonly args: Result;
    /**
     *  @_ignore:
     */
    constructor(fragment: EventFragment, topic: string, args: Result);
}
/**
 *  When using the [[Interface-parseTransaction]] to automatically match
 *  a transaction data to its function for parsing,
 *  a **TransactionDescription** is returned.
 */
export declare class TransactionDescription {
    /**
     *  The matching fragment from the transaction ``data``.
     */
    readonly fragment: FunctionFragment;
    /**
     *  The name of the Function from the transaction ``data``.
     */
    readonly name: string;
    /**
     *  The arguments passed to the Function from the transaction ``data``.
     */
    readonly args: Result;
    /**
     *  The full Function signature from the transaction ``data``.
     */
    readonly signature: string;
    /**
     *  The selector for the Function from the transaction ``data``.
     */
    readonly selector: string;
    /**
     *  The ``value`` (in wei) from the transaction.
     */
    readonly value: bigint;
    /**
     *  @_ignore:
     */
    constructor(fragment: FunctionFragment, selector: string, args: Result, value: bigint);
}
/**
 *  When using the [[Interface-parseError]] to automatically match an
 *  error for a call result for parsing, an **ErrorDescription** is returned.
 */
export declare class ErrorDescription {
    /**
     *  The matching fragment.
     */
    readonly fragment: ErrorFragment;
    /**
     *  The name of the Error.
     */
    readonly name: string;
    /**
     *  The arguments passed to the Error with ``revert``.
     */
    readonly args: Result;
    /**
     *  The full Error signature.
     */
    readonly signature: string;
    /**
     *  The selector for the Error.
     */
    readonly selector: string;
    /**
     *  @_ignore:
     */
    constructor(fragment: ErrorFragment, selector: string, args: Result);
}
/**
 *  An **Indexed** is used as a value when a value that does not
 *  fit within a topic (i.e. not a fixed-length, 32-byte type). It
 *  is the ``keccak256`` of the value, and used for types such as
 *  arrays, tuples, bytes and strings.
 */
export declare class Indexed {
    /**
     *  The ``keccak256`` of the value logged.
     */
    readonly hash: null | string;
    /**
     *  @_ignore:
     */
    readonly _isIndexed: boolean;
    /**
     *  Returns ``true`` if %%value%% is an **Indexed**.
     *
     *  This provides a Type Guard for property access.
     */
    static isIndexed(value: any): value is Indexed;
    /**
     *  @_ignore:
     */
    constructor(hash: null | string);
}
/**
 *  An **InterfaceAbi** may be any supported ABI format.
 *
 *  A string is expected to be a JSON string, which will be parsed
 *  using ``JSON.parse``. This means that the value **must** be a valid
 *  JSON string, with no stray commas, etc.
 *
 *  An array may contain any combination of:
 *  - Human-Readable fragments
 *  - Parsed JSON fragment
 *  - [[Fragment]] instances
 *
 *  A **Human-Readable Fragment** is a string which resembles a Solidity
 *  signature and is introduced in [this blog entry](link-ricmoo-humanreadableabi).
 *  For example, ``function balanceOf(address) view returns (uint)``.
 *
 *  A **Parsed JSON Fragment** is a JavaScript Object desribed in the
 *  [Solidity documentation](link-solc-jsonabi).
 */
export type InterfaceAbi = string | ReadonlyArray<Fragment | JsonFragment | string>;
/**
 *  An Interface abstracts many of the low-level details for
 *  encoding and decoding the data on the blockchain.
 *
 *  An ABI provides information on how to encode data to send to
 *  a Contract, how to decode the results and events and how to
 *  interpret revert errors.
 *
 *  The ABI can be specified by [any supported format](InterfaceAbi).
 */
export declare class Interface {
    #private;
    /**
     *  All the Contract ABI members (i.e. methods, events, errors, etc).
     */
    readonly fragments: ReadonlyArray<Fragment>;
    /**
     *  The Contract constructor.
     */
    readonly deploy: ConstructorFragment;
    /**
     *  The Fallback method, if any.
     */
    readonly fallback: null | FallbackFragment;
    /**
     *  If receiving ether is supported.
     */
    readonly receive: boolean;
    /**
     *  Create a new Interface for the %%fragments%%.
     */
    constructor(fragments: InterfaceAbi);
    /**
     *  Returns the entire Human-Readable ABI, as an array of
     *  signatures, optionally as %%minimal%% strings, which
     *  removes parameter names and unneceesary spaces.
     */
    format(minimal?: boolean): Array<string>;
    /**
     *  Return the JSON-encoded ABI. This is the format Solidiy
     *  returns.
     */
    formatJson(): string;
    /**
     *  The ABI coder that will be used to encode and decode binary
     *  data.
     */
    getAbiCoder(): AbiCoder;
    /**
     *  Get the function name for %%key%%, which may be a function selector,
     *  function name or function signature that belongs to the ABI.
     */
    getFunctionName(key: string): string;
    /**
     *  Returns true if %%key%% (a function selector, function name or
     *  function signature) is present in the ABI.
     *
     *  In the case of a function name, the name may be ambiguous, so
     *  accessing the [[FunctionFragment]] may require refinement.
     */
    hasFunction(key: string): boolean;
    /**
     *  Get the [[FunctionFragment]] for %%key%%, which may be a function
     *  selector, function name or function signature that belongs to the ABI.
     *
     *  If %%values%% is provided, it will use the Typed API to handle
     *  ambiguous cases where multiple functions match by name.
     *
     *  If the %%key%% and %%values%% do not refine to a single function in
     *  the ABI, this will throw.
     */
    getFunction(key: string, values?: Array<any | Typed>): null | FunctionFragment;
    /**
     *  Iterate over all functions, calling %%callback%%, sorted by their name.
     */
    forEachFunction(callback: (func: FunctionFragment, index: number) => void): void;
    /**
     *  Get the event name for %%key%%, which may be a topic hash,
     *  event name or event signature that belongs to the ABI.
     */
    getEventName(key: string): string;
    /**
     *  Returns true if %%key%% (an event topic hash, event name or
     *  event signature) is present in the ABI.
     *
     *  In the case of an event name, the name may be ambiguous, so
     *  accessing the [[EventFragment]] may require refinement.
     */
    hasEvent(key: string): boolean;
    /**
     *  Get the [[EventFragment]] for %%key%%, which may be a topic hash,
     *  event name or event signature that belongs to the ABI.
     *
     *  If %%values%% is provided, it will use the Typed API to handle
     *  ambiguous cases where multiple events match by name.
     *
     *  If the %%key%% and %%values%% do not refine to a single event in
     *  the ABI, this will throw.
     */
    getEvent(key: string, values?: Array<any | Typed>): null | EventFragment;
    /**
     *  Iterate over all events, calling %%callback%%, sorted by their name.
     */
    forEachEvent(callback: (func: EventFragment, index: number) => void): void;
    /**
     *  Get the [[ErrorFragment]] for %%key%%, which may be an error
     *  selector, error name or error signature that belongs to the ABI.
     *
     *  If %%values%% is provided, it will use the Typed API to handle
     *  ambiguous cases where multiple errors match by name.
     *
     *  If the %%key%% and %%values%% do not refine to a single error in
     *  the ABI, this will throw.
     */
    getError(key: string, values?: Array<any | Typed>): null | ErrorFragment;
    /**
     *  Iterate over all errors, calling %%callback%%, sorted by their name.
     */
    forEachError(callback: (func: ErrorFragment, index: number) => void): void;
    _decodeParams(params: ReadonlyArray<ParamType>, data: BytesLike): Result;
    _encodeParams(params: ReadonlyArray<ParamType>, values: ReadonlyArray<any>): string;
    /**
     *  Encodes a ``tx.data`` object for deploying the Contract with
     *  the %%values%% as the constructor arguments.
     */
    encodeDeploy(values?: ReadonlyArray<any>): string;
    /**
     *  Decodes the result %%data%% (e.g. from an ``eth_call``) for the
     *  specified error (see [[getError]] for valid values for
     *  %%key%%).
     *
     *  Most developers should prefer the [[parseCallResult]] method instead,
     *  which will automatically detect a ``CALL_EXCEPTION`` and throw the
     *  corresponding error.
     */
    decodeErrorResult(fragment: ErrorFragment | string, data: BytesLike): Result;
    /**
     *  Encodes the transaction revert data for a call result that
     *  reverted from the the Contract with the sepcified %%error%%
     *  (see [[getError]] for valid values for %%fragment%%) with the %%values%%.
     *
     *  This is generally not used by most developers, unless trying to mock
     *  a result from a Contract.
     */
    encodeErrorResult(fragment: ErrorFragment | string, values?: ReadonlyArray<any>): string;
    /**
     *  Decodes the %%data%% from a transaction ``tx.data`` for
     *  the function specified (see [[getFunction]] for valid values
     *  for %%fragment%%).
     *
     *  Most developers should prefer the [[parseTransaction]] method
     *  instead, which will automatically detect the fragment.
     */
    decodeFunctionData(fragment: FunctionFragment | string, data: BytesLike): Result;
    /**
     *  Encodes the ``tx.data`` for a transaction that calls the function
     *  specified (see [[getFunction]] for valid values for %%fragment%%) with
     *  the %%values%%.
     */
    encodeFunctionData(fragment: FunctionFragment | string, values?: ReadonlyArray<any>): string;
    /**
     *  Decodes the result %%data%% (e.g. from an ``eth_call``) for the
     *  specified function (see [[getFunction]] for valid values for
     *  %%key%%).
     *
     *  Most developers should prefer the [[parseCallResult]] method instead,
     *  which will automatically detect a ``CALL_EXCEPTION`` and throw the
     *  corresponding error.
     */
    decodeFunctionResult(fragment: FunctionFragment | string, data: BytesLike): Result;
    makeError(_data: BytesLike, tx: CallExceptionTransaction): CallExceptionError;
    /**
     *  Encodes the result data (e.g. from an ``eth_call``) for the
     *  specified function (see [[getFunction]] for valid values
     *  for %%fragment%%) with %%values%%.
     *
     *  This is generally not used by most developers, unless trying to mock
     *  a result from a Contract.
     */
    encodeFunctionResult(fragment: FunctionFragment | string, values?: ReadonlyArray<any>): string;
    encodeFilterTopics(fragment: EventFragment | string, values: ReadonlyArray<any>): Array<null | string | Array<string>>;
    encodeEventLog(fragment: EventFragment | string, values: ReadonlyArray<any>): {
        data: string;
        topics: Array<string>;
    };
    decodeEventLog(fragment: EventFragment | string, data: BytesLike, topics?: ReadonlyArray<string>): Result;
    /**
     *  Parses a transaction, finding the matching function and extracts
     *  the parameter values along with other useful function details.
     *
     *  If the matching function cannot be found, return null.
     */
    parseTransaction(tx: {
        data: string;
        value?: BigNumberish;
    }): null | TransactionDescription;
    parseCallResult(data: BytesLike): Result;
    /**
     *  Parses a receipt log, finding the matching event and extracts
     *  the parameter values along with other useful event details.
     *
     *  If the matching event cannot be found, returns null.
     */
    parseLog(log: {
        topics: ReadonlyArray<string>;
        data: string;
    }): null | LogDescription;
    /**
     *  Parses a revert data, finding the matching error and extracts
     *  the parameter values along with other useful error details.
     *
     *  If the matching error cannot be found, returns null.
     */
    parseError(data: BytesLike): null | ErrorDescription;
    /**
     *  Creates a new [[Interface]] from the ABI %%value%%.
     *
     *  The %%value%% may be provided as an existing [[Interface]] object,
     *  a JSON-encoded ABI or any Human-Readable ABI format.
     */
    static from(value: InterfaceAbi | Interface): Interface;
}
//# sourceMappingURL=interface.d.ts.map