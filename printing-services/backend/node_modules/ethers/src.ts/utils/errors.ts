/**
 *  All errors in ethers include properties to ensure they are both
 *  human-readable (i.e. ``.message``) and machine-readable (i.e. ``.code``).
 *
 *  The [[isError]] function can be used to check the error ``code`` and
 *  provide a type guard for the properties present on that error interface.
 *
 *  @_section: api/utils/errors:Errors  [about-errors]
 */

import { version } from "../_version.js";

import { defineProperties } from "./properties.js";

import type {
    TransactionRequest, TransactionReceipt, TransactionResponse
} from "../providers/index.js";

import type { FetchRequest, FetchResponse } from "./fetch.js";

/**
 *  An error may contain additional properties, but those must not
 *  conflict with any implicit properties.
 */
export type ErrorInfo<T> = Omit<T, "code" | "name" | "message" | "shortMessage"> & { shortMessage?: string };


function stringify(value: any, seen?: Set<any>): any {
    if (value == null) { return "null"; }

    if (seen == null) { seen = new Set(); }
    if (typeof(value) === "object") {
        if (seen.has(value)) { return "[Circular]"; }
        seen.add(value);
    }

    if (Array.isArray(value)) {
        return "[ " + (value.map((v) => stringify(v, seen))).join(", ") + " ]";
    }

    if (value instanceof Uint8Array) {
        const HEX = "0123456789abcdef";
        let result = "0x";
        for (let i = 0; i < value.length; i++) {
            result += HEX[value[i] >> 4];
            result += HEX[value[i] & 0xf];
        }
        return result;
    }

    if (typeof(value) === "object" && typeof(value.toJSON) === "function") {
        return stringify(value.toJSON(), seen);
    }

    switch (typeof(value)) {
        case "boolean": case "number": case "symbol":
            return value.toString();
        case "bigint":
            return BigInt(value).toString();
        case "string":
            return JSON.stringify(value);
        case "object": {
            const keys = Object.keys(value);
            keys.sort();
            return "{ " + keys.map((k) => `${ stringify(k, seen) }: ${ stringify(value[k], seen) }`).join(", ") + " }";
        }
    }

    return `[ COULD NOT SERIALIZE ]`;
}

/**
 *  All errors emitted by ethers have an **ErrorCode** to help
 *  identify and coalesce errors to simplify programmatic analysis.
 *
 *  Each **ErrorCode** is the %%code%% proerty of a coresponding
 *  [[EthersError]].
 *
 *  **Generic Errors**
 *
 *  **``"UNKNOWN_ERROR"``** - see [[UnknownError]]
 *
 *  **``"NOT_IMPLEMENTED"``** - see [[NotImplementedError]]
 *
 *  **``"UNSUPPORTED_OPERATION"``** - see [[UnsupportedOperationError]]
 *
 *  **``"NETWORK_ERROR"``** - see [[NetworkError]]
 *
 *  **``"SERVER_ERROR"``** - see [[ServerError]]
 *
 *  **``"TIMEOUT"``** - see [[TimeoutError]]
 *
 *  **``"BAD_DATA"``** - see [[BadDataError]]
 *
 *  **``"CANCELLED"``** - see [[CancelledError]]
 *
 *  **Operational Errors**
 *
 *  **``"BUFFER_OVERRUN"``** - see [[BufferOverrunError]]
 *
 *  **``"NUMERIC_FAULT"``** - see [[NumericFaultError]]
 *
 *  **Argument Errors**
 *
 *  **``"INVALID_ARGUMENT"``** - see [[InvalidArgumentError]]
 *
 *  **``"MISSING_ARGUMENT"``** - see [[MissingArgumentError]]
 *
 *  **``"UNEXPECTED_ARGUMENT"``** - see [[UnexpectedArgumentError]]
 *
 *  **``"VALUE_MISMATCH"``** - //unused//
 *
 *  **Blockchain Errors**
 *
 *  **``"CALL_EXCEPTION"``** - see [[CallExceptionError]]
 *
 *  **``"INSUFFICIENT_FUNDS"``** - see [[InsufficientFundsError]]
 *
 *  **``"NONCE_EXPIRED"``** - see [[NonceExpiredError]]
 *
 *  **``"REPLACEMENT_UNDERPRICED"``** - see [[ReplacementUnderpricedError]]
 *
 *  **``"TRANSACTION_REPLACED"``** - see [[TransactionReplacedError]]
 *
 *  **``"UNCONFIGURED_NAME"``** - see [[UnconfiguredNameError]]
 *
 *  **``"OFFCHAIN_FAULT"``** - see [[OffchainFaultError]]
 *
 *  **User Interaction Errors**
 *
 *  **``"ACTION_REJECTED"``** - see [[ActionRejectedError]]
 */
export type ErrorCode =

    // Generic Errors
    "UNKNOWN_ERROR" | "NOT_IMPLEMENTED" | "UNSUPPORTED_OPERATION" |
    "NETWORK_ERROR" | "SERVER_ERROR" | "TIMEOUT" | "BAD_DATA" |
    "CANCELLED" |

    // Operational Errors
    "BUFFER_OVERRUN" |  "NUMERIC_FAULT" |

    // Argument Errors
    "INVALID_ARGUMENT" | "MISSING_ARGUMENT" | "UNEXPECTED_ARGUMENT" |
    "VALUE_MISMATCH" |

    // Blockchain Errors
    "CALL_EXCEPTION" | "INSUFFICIENT_FUNDS" | "NONCE_EXPIRED" |
    "REPLACEMENT_UNDERPRICED" | "TRANSACTION_REPLACED" |
    "UNCONFIGURED_NAME" | "OFFCHAIN_FAULT" |

    // User Interaction
    "ACTION_REJECTED"
;

/**
 *  All errors in Ethers include properties to assist in
 *  machine-readable errors.
 */
export interface EthersError<T extends ErrorCode = ErrorCode> extends Error {
    /**
     *  The string error code.
     */
    code: ErrorCode;

    /**
     *  A short message describing the error, with minimal additional
     *  details.
     */
    shortMessage: string;

    /**
     *  Additional info regarding the error that may be useful.
     *
     *  This is generally helpful mostly for human-based debugging.
     */
    info?: Record<string, any>;

    /**
     *  Any related error.
     */
    error?: Error;
}

// Generic Errors

/**
 *  This Error is a catch-all for when there is no way for Ethers to
 *  know what the underlying problem is.
 */
export interface UnknownError extends EthersError<"UNKNOWN_ERROR"> {
    [ key: string ]: any;
}

/**
 *  This Error is mostly used as a stub for functionality that is
 *  intended for the future, but is currently not implemented.
 */
export interface NotImplementedError extends EthersError<"NOT_IMPLEMENTED"> {
    /**
     *  The attempted operation.
     */
    operation: string;
}

/**
 *  This Error indicates that the attempted operation is not supported.
 *
 *  This could range from a specific JSON-RPC end-point not supporting
 *  a feature to a specific configuration of an object prohibiting the
 *  operation.
 *
 *  For example, a [[Wallet]] with no connected [[Provider]] is unable
 *  to send a transaction.
 */
export interface UnsupportedOperationError extends EthersError<"UNSUPPORTED_OPERATION"> {
    /**
     *  The attempted operation.
     */
    operation: string;
}

/**
 *  This Error indicates a problem connecting to a network.
 */
export interface NetworkError extends EthersError<"NETWORK_ERROR"> {
    /**
     *  The network event.
     */
    event: string;
}

/**
 *  This Error indicates there was a problem fetching a resource from
 *  a server.
 */
export interface ServerError extends EthersError<"SERVER_ERROR"> {
    /**
     *  The requested resource.
     */
    request: FetchRequest | string;

    /**
     *  The response received from the server, if available.
     */
    response?: FetchResponse;
}

/**
 *  This Error indicates that the timeout duration has expired and
 *  that the operation has been implicitly cancelled.
 *
 *  The side-effect of the operation may still occur, as this
 *  generally means a request has been sent and there has simply
 *  been no response to indicate whether it was processed or not.
 */
export interface TimeoutError extends EthersError<"TIMEOUT"> {
    /**
     *  The attempted operation.
     */
    operation: string;

    /**
     *  The reason.
     */
    reason: string;

    /**
     *  The resource request, if available.
     */
    request?: FetchRequest;
}

/**
 *  This Error indicates that a provided set of data cannot
 *  be correctly interpreted.
 */
export interface BadDataError extends EthersError<"BAD_DATA"> {
    /**
     *  The data.
     */
    value: any;
}

/**
 *  This Error indicates that the operation was cancelled by a
 *  programmatic call, for example to ``cancel()``.
 */
export interface CancelledError extends EthersError<"CANCELLED"> {
}


// Operational Errors

/**
 *  This Error indicates an attempt was made to read outside the bounds
 *  of protected data.
 *
 *  Most operations in Ethers are protected by bounds checks, to mitigate
 *  exploits when parsing data.
 */
export interface BufferOverrunError extends EthersError<"BUFFER_OVERRUN"> {
    /**
     *  The buffer that was overrun.
     */
    buffer: Uint8Array;

    /**
     *  The length of the buffer.
     */
    length: number;

    /**
     *  The offset that was requested.
     */
    offset: number;
}

/**
 *  This Error indicates an operation which would result in incorrect
 *  arithmetic output has occurred.
 *
 *  For example, trying to divide by zero or using a ``uint8`` to store
 *  a negative value.
 */
export interface NumericFaultError extends EthersError<"NUMERIC_FAULT"> {
    /**
     *  The attempted operation.
     */
    operation: string;

    /**
     *  The fault reported.
     */
    fault: string;

    /**
     *  The value the operation was attempted against.
     */
    value: any;
}


// Argument Errors

/**
 *  This Error indicates an incorrect type or value was passed to
 *  a function or method.
 */
export interface InvalidArgumentError extends EthersError<"INVALID_ARGUMENT"> {
    /**
     *  The name of the argument.
     */
    argument: string;

    /**
     *  The value that was provided.
     */
    value: any;

    info?: Record<string, any>
}

/**
 *  This Error indicates there were too few arguments were provided.
 */
export interface MissingArgumentError extends EthersError<"MISSING_ARGUMENT"> {
    /**
     *  The number of arguments received.
     */
    count: number;

    /**
     *  The number of arguments expected.
     */
    expectedCount: number;
}

/**
 *  This Error indicates too many arguments were provided.
 */
export interface UnexpectedArgumentError extends EthersError<"UNEXPECTED_ARGUMENT"> {
    /**
     *  The number of arguments received.
     */
    count: number;

    /**
     *  The number of arguments expected.
     */
    expectedCount: number;
}


// Blockchain Errors

/**
 *  The action that resulted in the call exception.
 */
export type CallExceptionAction = "call" | "estimateGas" | "getTransactionResult" | "sendTransaction" | "unknown";

/**
 *  The related transaction that caused the error.
 */
export type CallExceptionTransaction = {
    to: null | string;
    from?: string;
    data: string;
};

/**
 *  This **Error** indicates a transaction reverted.
 */
export interface CallExceptionError extends EthersError<"CALL_EXCEPTION"> {

    /**
     *  The action being performed when the revert was encountered.
     */
    action: CallExceptionAction;

    /**
     *  The revert data returned.
     */
    data: null | string;

    /**
     *  A human-readable representation of data, if possible.
     */
    reason: null | string;

    /**
     *  The transaction that triggered the exception.
     */
    transaction: CallExceptionTransaction,

    /**
     *  The contract invocation details, if available.
     */
    invocation: null | {
        method: string;
        signature: string;
        args: Array<any>;
    }

    /**
     *  The built-in or custom revert error, if available
     */
    revert: null | {
        signature: string;
        name: string;
        args: Array<any>;
    }

    /**
     *  If the error occurred in a transaction that was mined
     *  (with a status of ``0``), this is the receipt.
     */
    receipt?: TransactionReceipt;   // @TODO: in v7, make this `null | TransactionReceipt`
}


/**
 *  The sending account has insufficient funds to cover the
 *  entire transaction cost.
 */
export interface InsufficientFundsError extends EthersError<"INSUFFICIENT_FUNDS"> {
    /**
     *  The transaction.
     */
    transaction: TransactionRequest;
}

/**
 *  The sending account has already used this nonce in a
 *  transaction that has been included.
 */
export interface NonceExpiredError extends EthersError<"NONCE_EXPIRED"> {
    /**
     *  The transaction.
     */
    transaction: TransactionRequest;
}

/**
 *  A CCIP-read exception, which cannot be recovered from or
 *  be further processed.
 */
export interface OffchainFaultError extends EthersError<"OFFCHAIN_FAULT"> {
    /**
     *  The transaction.
     */
    transaction?: TransactionRequest;

    /**
     *  The reason the CCIP-read failed.
     */
    reason: string;
}

/**
 *  An attempt was made to replace a transaction, but with an
 *  insufficient additional fee to afford evicting the old
 *  transaction from the memory pool.
 */
export interface ReplacementUnderpricedError extends EthersError<"REPLACEMENT_UNDERPRICED"> {
    /**
     *  The transaction.
     */
    transaction: TransactionRequest;
}

/**
 *  A pending transaction was replaced by another.
 */
export interface TransactionReplacedError extends EthersError<"TRANSACTION_REPLACED"> {
    /**
     *  If the transaction was cancelled, such that the original
     *  effects of the transaction cannot be assured.
     */
    cancelled: boolean;

    /**
     *  The reason the transaction was replaced.
     */
    reason: "repriced" | "cancelled" | "replaced";

    /**
     *  The hash of the replaced transaction.
     */
    hash: string;

    /**
     *  The transaction that replaced the transaction.
     */
    replacement: TransactionResponse;

    /**
     *  The receipt of the transaction that replace the transaction.
     */
    receipt: TransactionReceipt;
}

/**
 *  This Error indicates an ENS name was used, but the name has not
 *  been configured.
 *
 *  This could indicate an ENS name is unowned or that the current
 *  address being pointed to is the [[ZeroAddress]].
 */
export interface UnconfiguredNameError extends EthersError<"UNCONFIGURED_NAME"> {
    /**
     *  The ENS name that was requested
     */
    value: string;
}

/**
 *  This Error indicates a request was rejected by the user.
 *
 *  In most clients (such as MetaMask), when an operation requires user
 *  authorization (such as ``signer.sendTransaction``), the client
 *  presents a dialog box to the user. If the user denies the request
 *  this error is thrown.
 */
export interface ActionRejectedError extends EthersError<"ACTION_REJECTED"> {
    /**
     *  The requested action.
     */
    action: "requestAccess" | "sendTransaction" | "signMessage" | "signTransaction" | "signTypedData" | "unknown",

    /**
     *  The reason the action was rejected.
     *
     *  If there is already a pending request, some clients may indicate
     *  there is already a ``"pending"`` action. This prevents an app
     *  from spamming the user.
     */
    reason: "expired" | "rejected" | "pending"
}

// Coding; converts an ErrorCode its Typed Error

/**
 *  A conditional type that transforms the [[ErrorCode]] T into
 *  its EthersError type.
 *
 *  @flatworm-skip-docs
 */
export type CodedEthersError<T> =
    T extends "UNKNOWN_ERROR" ? UnknownError:
    T extends "NOT_IMPLEMENTED" ? NotImplementedError:
    T extends "UNSUPPORTED_OPERATION" ? UnsupportedOperationError:
    T extends "NETWORK_ERROR" ? NetworkError:
    T extends "SERVER_ERROR" ? ServerError:
    T extends "TIMEOUT" ? TimeoutError:
    T extends "BAD_DATA" ? BadDataError:
    T extends "CANCELLED" ? CancelledError:

    T extends "BUFFER_OVERRUN" ? BufferOverrunError:
    T extends "NUMERIC_FAULT" ? NumericFaultError:

    T extends "INVALID_ARGUMENT" ? InvalidArgumentError:
    T extends "MISSING_ARGUMENT" ? MissingArgumentError:
    T extends "UNEXPECTED_ARGUMENT" ? UnexpectedArgumentError:

    T extends "CALL_EXCEPTION" ? CallExceptionError:
    T extends "INSUFFICIENT_FUNDS" ? InsufficientFundsError:
    T extends "NONCE_EXPIRED" ? NonceExpiredError:
    T extends "OFFCHAIN_FAULT" ? OffchainFaultError:
    T extends "REPLACEMENT_UNDERPRICED" ? ReplacementUnderpricedError:
    T extends "TRANSACTION_REPLACED" ? TransactionReplacedError:
    T extends "UNCONFIGURED_NAME" ? UnconfiguredNameError:

    T extends "ACTION_REJECTED" ? ActionRejectedError:

    never;



/**
 *  Returns true if the %%error%% matches an error thrown by ethers
 *  that matches the error %%code%%.
 *
 *  In TypeScript environments, this can be used to check that %%error%%
 *  matches an EthersError type, which means the expected properties will
 *  be set.
 *
 *  @See [ErrorCodes](api:ErrorCode)
 *  @example
 *    try {
 *      // code....
 *    } catch (e) {
 *      if (isError(e, "CALL_EXCEPTION")) {
 *          // The Type Guard has validated this object
 *          console.log(e.data);
 *      }
 *    }
 */
export function isError<K extends ErrorCode, T extends CodedEthersError<K>>(error: any, code: K): error is T {
    return (error && (<EthersError>error).code === code);
}

/**
 *  Returns true if %%error%% is a [[CallExceptionError].
 */
export function isCallException(error: any): error is CallExceptionError {
    return isError(error, "CALL_EXCEPTION");
}

/**
 *  Returns a new Error configured to the format ethers emits errors, with
 *  the %%message%%, [[api:ErrorCode]] %%code%% and additional properties
 *  for the corresponding EthersError.
 *
 *  Each error in ethers includes the version of ethers, a
 *  machine-readable [[ErrorCode]], and depending on %%code%%, additional
 *  required properties. The error message will also include the %%message%%,
 *  ethers version, %%code%% and all additional properties, serialized.
 */
export function makeError<K extends ErrorCode, T extends CodedEthersError<K>>(message: string, code: K, info?: ErrorInfo<T>): T {
    let shortMessage = message;

    {
        const details: Array<string> = [];
        if (info) {
            if ("message" in info || "code" in info || "name" in info) {
                throw new Error(`value will overwrite populated values: ${ stringify(info) }`);
            }
            for (const key in info) {
                if (key === "shortMessage") { continue; }
                const value = <any>(info[<keyof ErrorInfo<T>>key]);
//                try {
                    details.push(key + "=" + stringify(value));
//                } catch (error: any) {
//                console.log("MMM", error.message);
//                    details.push(key + "=[could not serialize object]");
//                }
            }
        }
        details.push(`code=${ code }`);
        details.push(`version=${ version }`);

        if (details.length) {
            message += " (" + details.join(", ") + ")";
        }
    }

    let error;
    switch (code) {
        case "INVALID_ARGUMENT":
            error = new TypeError(message);
            break;
        case "NUMERIC_FAULT":
        case "BUFFER_OVERRUN":
            error = new RangeError(message);
            break;
        default:
            error = new Error(message);
    }

    defineProperties<EthersError>(<EthersError>error, { code });

    if (info) { Object.assign(error, info); }

    if ((<any>error).shortMessage == null) {
        defineProperties<EthersError>(<EthersError>error, { shortMessage });
    }

    return <T>error;
}

/**
 *  Throws an EthersError with %%message%%, %%code%% and additional error
 *  %%info%% when %%check%% is falsish..
 *
 *  @see [[api:makeError]]
 */
export function assert<K extends ErrorCode, T extends CodedEthersError<K>>(check: unknown, message: string, code: K, info?: ErrorInfo<T>): asserts check {
    if (!check) { throw makeError(message, code, info); }
}


/**
 *  A simple helper to simply ensuring provided arguments match expected
 *  constraints, throwing if not.
 *
 *  In TypeScript environments, the %%check%% has been asserted true, so
 *  any further code does not need additional compile-time checks.
 */
export function assertArgument(check: unknown, message: string, name: string, value: unknown): asserts check {
    assert(check, message, "INVALID_ARGUMENT", { argument: name, value: value });
}

export function assertArgumentCount(count: number, expectedCount: number, message?: string): void {
    if (message == null) { message = ""; }
    if (message) { message = ": " + message; }

    assert(count >= expectedCount, "missing argument" + message, "MISSING_ARGUMENT", {
        count: count,
        expectedCount: expectedCount
    });

    assert(count <= expectedCount, "too many arguments" + message, "UNEXPECTED_ARGUMENT", {
        count: count,
        expectedCount: expectedCount
    });
}

const _normalizeForms = ["NFD", "NFC", "NFKD", "NFKC"].reduce((accum, form) => {
    try {
        // General test for normalize
        /* c8 ignore start */
        if ("test".normalize(form) !== "test") { throw new Error("bad"); };
        /* c8 ignore stop */

        if (form === "NFD") {
            const check = String.fromCharCode(0xe9).normalize("NFD");
            const expected = String.fromCharCode(0x65, 0x0301)
            /* c8 ignore start */
            if (check !== expected) { throw new Error("broken") }
            /* c8 ignore stop */
        }

        accum.push(form);
    } catch(error) { }

    return accum;
}, <Array<string>>[]);

/**
 *  Throws if the normalization %%form%% is not supported.
 */
export function assertNormalize(form: string): void {
    assert(_normalizeForms.indexOf(form) >= 0, "platform missing String.prototype.normalize", "UNSUPPORTED_OPERATION", {
        operation: "String.prototype.normalize", info: { form }
    });
}

/**
 *  Many classes use file-scoped values to guard the constructor,
 *  making it effectively private. This facilitates that pattern
 *  by ensuring the %%givenGaurd%% matches the file-scoped %%guard%%,
 *  throwing if not, indicating the %%className%% if provided.
 */
export function assertPrivate(givenGuard: any, guard: any, className?: string): void {
    if (className == null) { className = ""; }
    if (givenGuard !== guard) {
        let method = className, operation = "new";
        if (className) {
            method += ".";
            operation += " " + className;
        }
        assert(false, `private constructor; use ${ method }from* methods`, "UNSUPPORTED_OPERATION", {
            operation
        });
    }
}
