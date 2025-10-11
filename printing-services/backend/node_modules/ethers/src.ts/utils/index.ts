/**
 *  There are many simple utilities required to interact with
 *  Ethereum and to simplify the library, without increasing
 *  the library dependencies for simple functions.
 *
 *  @_section api/utils:Utilities  [about-utils]
 */

export { decodeBase58, encodeBase58 } from "./base58.js";

export { decodeBase64, encodeBase64 } from "./base64.js";

export {
    getBytes, getBytesCopy, isHexString, isBytesLike, hexlify, concat, dataLength, dataSlice,
    stripZerosLeft, zeroPadValue, zeroPadBytes
} from "./data.js";

export {
    isCallException, isError,
    assert, assertArgument, assertArgumentCount, assertPrivate, assertNormalize, makeError
} from "./errors.js"

export { EventPayload } from "./events.js";

export {
    FetchRequest, FetchResponse, FetchCancelSignal,
} from "./fetch.js";

export { FixedNumber } from "./fixednumber.js"

export {
    fromTwos, toTwos, mask,
    getBigInt, getNumber, getUint, toBigInt, toNumber, toBeHex, toBeArray, toQuantity
} from "./maths.js";

export { resolveProperties, defineProperties} from "./properties.js";

export { decodeRlp } from "./rlp-decode.js";
export { encodeRlp } from "./rlp-encode.js";

export { formatEther, parseEther, formatUnits, parseUnits } from "./units.js";

export {
    toUtf8Bytes,
    toUtf8CodePoints,
    toUtf8String,

    Utf8ErrorFuncs,
} from "./utf8.js";

export { uuidV4 } from "./uuid.js";

/////////////////////////////
// Types

export type { BytesLike } from "./data.js";

export type {

    //ErrorFetchRequestWithBody, ErrorFetchRequest,
    //ErrorFetchResponseWithBody, ErrorFetchResponse,

    ErrorCode,

    EthersError, UnknownError, NotImplementedError, UnsupportedOperationError, NetworkError,
    ServerError, TimeoutError, BadDataError, CancelledError, BufferOverrunError,
    NumericFaultError, InvalidArgumentError, MissingArgumentError, UnexpectedArgumentError,
    CallExceptionError, InsufficientFundsError, NonceExpiredError, OffchainFaultError,
    ReplacementUnderpricedError, TransactionReplacedError, UnconfiguredNameError,
    ActionRejectedError,

    CallExceptionAction, CallExceptionTransaction,

    CodedEthersError
} from "./errors.js"

export type { EventEmitterable, Listener } from "./events.js";

export type {
    GetUrlResponse,
    FetchPreflightFunc, FetchProcessFunc, FetchRetryFunc,
    FetchGatewayFunc, FetchGetUrlFunc
} from "./fetch.js";

export type { FixedFormat } from "./fixednumber.js"

export type { BigNumberish, Numeric } from "./maths.js";

export type { RlpStructuredData, RlpStructuredDataish } from "./rlp.js";

export type {
    Utf8ErrorFunc,
    UnicodeNormalizationForm,
    Utf8ErrorReason
} from "./utf8.js";
