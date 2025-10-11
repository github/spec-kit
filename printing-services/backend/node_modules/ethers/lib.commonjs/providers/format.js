"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.formatTransactionResponse = exports.formatTransactionReceipt = exports.formatReceiptLog = exports.formatBlock = exports.formatLog = exports.formatUint256 = exports.formatHash = exports.formatData = exports.formatBoolean = exports.object = exports.arrayOf = exports.allowNull = void 0;
/**
 *  @_ignore
 */
const index_js_1 = require("../address/index.js");
const index_js_2 = require("../crypto/index.js");
const index_js_3 = require("../transaction/index.js");
const index_js_4 = require("../utils/index.js");
const BN_0 = BigInt(0);
function allowNull(format, nullValue) {
    return (function (value) {
        if (value == null) {
            return nullValue;
        }
        return format(value);
    });
}
exports.allowNull = allowNull;
function arrayOf(format, allowNull) {
    return ((array) => {
        if (allowNull && array == null) {
            return null;
        }
        if (!Array.isArray(array)) {
            throw new Error("not an array");
        }
        return array.map((i) => format(i));
    });
}
exports.arrayOf = arrayOf;
// Requires an object which matches a fleet of other formatters
// Any FormatFunc may return `undefined` to have the value omitted
// from the result object. Calls preserve `this`.
function object(format, altNames) {
    return ((value) => {
        const result = {};
        for (const key in format) {
            let srcKey = key;
            if (altNames && key in altNames && !(srcKey in value)) {
                for (const altKey of altNames[key]) {
                    if (altKey in value) {
                        srcKey = altKey;
                        break;
                    }
                }
            }
            try {
                const nv = format[key](value[srcKey]);
                if (nv !== undefined) {
                    result[key] = nv;
                }
            }
            catch (error) {
                const message = (error instanceof Error) ? error.message : "not-an-error";
                (0, index_js_4.assert)(false, `invalid value for value.${key} (${message})`, "BAD_DATA", { value });
            }
        }
        return result;
    });
}
exports.object = object;
function formatBoolean(value) {
    switch (value) {
        case true:
        case "true":
            return true;
        case false:
        case "false":
            return false;
    }
    (0, index_js_4.assertArgument)(false, `invalid boolean; ${JSON.stringify(value)}`, "value", value);
}
exports.formatBoolean = formatBoolean;
function formatData(value) {
    (0, index_js_4.assertArgument)((0, index_js_4.isHexString)(value, true), "invalid data", "value", value);
    return value;
}
exports.formatData = formatData;
function formatHash(value) {
    (0, index_js_4.assertArgument)((0, index_js_4.isHexString)(value, 32), "invalid hash", "value", value);
    return value;
}
exports.formatHash = formatHash;
function formatUint256(value) {
    if (!(0, index_js_4.isHexString)(value)) {
        throw new Error("invalid uint256");
    }
    return (0, index_js_4.zeroPadValue)(value, 32);
}
exports.formatUint256 = formatUint256;
const _formatLog = object({
    address: index_js_1.getAddress,
    blockHash: formatHash,
    blockNumber: index_js_4.getNumber,
    data: formatData,
    index: index_js_4.getNumber,
    removed: allowNull(formatBoolean, false),
    topics: arrayOf(formatHash),
    transactionHash: formatHash,
    transactionIndex: index_js_4.getNumber,
}, {
    index: ["logIndex"]
});
function formatLog(value) {
    return _formatLog(value);
}
exports.formatLog = formatLog;
const _formatBlock = object({
    hash: allowNull(formatHash),
    parentHash: formatHash,
    parentBeaconBlockRoot: allowNull(formatHash, null),
    number: index_js_4.getNumber,
    timestamp: index_js_4.getNumber,
    nonce: allowNull(formatData),
    difficulty: index_js_4.getBigInt,
    gasLimit: index_js_4.getBigInt,
    gasUsed: index_js_4.getBigInt,
    stateRoot: allowNull(formatHash, null),
    receiptsRoot: allowNull(formatHash, null),
    blobGasUsed: allowNull(index_js_4.getBigInt, null),
    excessBlobGas: allowNull(index_js_4.getBigInt, null),
    miner: allowNull(index_js_1.getAddress),
    prevRandao: allowNull(formatHash, null),
    extraData: formatData,
    baseFeePerGas: allowNull(index_js_4.getBigInt)
}, {
    prevRandao: ["mixHash"]
});
function formatBlock(value) {
    const result = _formatBlock(value);
    result.transactions = value.transactions.map((tx) => {
        if (typeof (tx) === "string") {
            return tx;
        }
        return formatTransactionResponse(tx);
    });
    return result;
}
exports.formatBlock = formatBlock;
const _formatReceiptLog = object({
    transactionIndex: index_js_4.getNumber,
    blockNumber: index_js_4.getNumber,
    transactionHash: formatHash,
    address: index_js_1.getAddress,
    topics: arrayOf(formatHash),
    data: formatData,
    index: index_js_4.getNumber,
    blockHash: formatHash,
}, {
    index: ["logIndex"]
});
function formatReceiptLog(value) {
    return _formatReceiptLog(value);
}
exports.formatReceiptLog = formatReceiptLog;
const _formatTransactionReceipt = object({
    to: allowNull(index_js_1.getAddress, null),
    from: allowNull(index_js_1.getAddress, null),
    contractAddress: allowNull(index_js_1.getAddress, null),
    // should be allowNull(hash), but broken-EIP-658 support is handled in receipt
    index: index_js_4.getNumber,
    root: allowNull(index_js_4.hexlify),
    gasUsed: index_js_4.getBigInt,
    blobGasUsed: allowNull(index_js_4.getBigInt, null),
    logsBloom: allowNull(formatData),
    blockHash: formatHash,
    hash: formatHash,
    logs: arrayOf(formatReceiptLog),
    blockNumber: index_js_4.getNumber,
    //confirmations: allowNull(getNumber, null),
    cumulativeGasUsed: index_js_4.getBigInt,
    effectiveGasPrice: allowNull(index_js_4.getBigInt),
    blobGasPrice: allowNull(index_js_4.getBigInt, null),
    status: allowNull(index_js_4.getNumber),
    type: allowNull(index_js_4.getNumber, 0)
}, {
    effectiveGasPrice: ["gasPrice"],
    hash: ["transactionHash"],
    index: ["transactionIndex"],
});
function formatTransactionReceipt(value) {
    return _formatTransactionReceipt(value);
}
exports.formatTransactionReceipt = formatTransactionReceipt;
function formatTransactionResponse(value) {
    // Some clients (TestRPC) do strange things like return 0x0 for the
    // 0 address; correct this to be a real address
    if (value.to && (0, index_js_4.getBigInt)(value.to) === BN_0) {
        value.to = "0x0000000000000000000000000000000000000000";
    }
    const result = object({
        hash: formatHash,
        // Some nodes do not return this, usually test nodes (like Ganache)
        index: allowNull(index_js_4.getNumber, undefined),
        type: (value) => {
            if (value === "0x" || value == null) {
                return 0;
            }
            return (0, index_js_4.getNumber)(value);
        },
        accessList: allowNull(index_js_3.accessListify, null),
        blobVersionedHashes: allowNull(arrayOf(formatHash, true), null),
        authorizationList: allowNull(arrayOf((v) => {
            let sig;
            if (v.signature) {
                sig = v.signature;
            }
            else {
                let yParity = v.yParity;
                if (yParity === "0x1b") {
                    yParity = 0;
                }
                else if (yParity === "0x1c") {
                    yParity = 1;
                }
                sig = Object.assign({}, v, { yParity });
            }
            return {
                address: (0, index_js_1.getAddress)(v.address),
                chainId: (0, index_js_4.getBigInt)(v.chainId),
                nonce: (0, index_js_4.getBigInt)(v.nonce),
                signature: index_js_2.Signature.from(sig)
            };
        }, false), null),
        blockHash: allowNull(formatHash, null),
        blockNumber: allowNull(index_js_4.getNumber, null),
        transactionIndex: allowNull(index_js_4.getNumber, null),
        from: index_js_1.getAddress,
        // either (gasPrice) or (maxPriorityFeePerGas + maxFeePerGas) must be set
        gasPrice: allowNull(index_js_4.getBigInt),
        maxPriorityFeePerGas: allowNull(index_js_4.getBigInt),
        maxFeePerGas: allowNull(index_js_4.getBigInt),
        maxFeePerBlobGas: allowNull(index_js_4.getBigInt, null),
        gasLimit: index_js_4.getBigInt,
        to: allowNull(index_js_1.getAddress, null),
        value: index_js_4.getBigInt,
        nonce: index_js_4.getNumber,
        data: formatData,
        creates: allowNull(index_js_1.getAddress, null),
        chainId: allowNull(index_js_4.getBigInt, null)
    }, {
        data: ["input"],
        gasLimit: ["gas"],
        index: ["transactionIndex"]
    })(value);
    // If to and creates are empty, populate the creates from the value
    if (result.to == null && result.creates == null) {
        result.creates = (0, index_js_1.getCreateAddress)(result);
    }
    // @TODO: Check fee data
    // Add an access list to supported transaction types
    if ((value.type === 1 || value.type === 2) && value.accessList == null) {
        result.accessList = [];
    }
    // Compute the signature
    if (value.signature) {
        result.signature = index_js_2.Signature.from(value.signature);
    }
    else {
        result.signature = index_js_2.Signature.from(value);
    }
    // Some backends omit ChainId on legacy transactions, but we can compute it
    if (result.chainId == null) {
        const chainId = result.signature.legacyChainId;
        if (chainId != null) {
            result.chainId = chainId;
        }
    }
    // @TODO: check chainID
    /*
    if (value.chainId != null) {
        let chainId = value.chainId;

        if (isHexString(chainId)) {
            chainId = BigNumber.from(chainId).toNumber();
        }

        result.chainId = chainId;

    } else {
        let chainId = value.networkId;

        // geth-etc returns chainId
        if (chainId == null && result.v == null) {
            chainId = value.chainId;
        }

        if (isHexString(chainId)) {
            chainId = BigNumber.from(chainId).toNumber();
        }

        if (typeof(chainId) !== "number" && result.v != null) {
            chainId = (result.v - 35) / 2;
            if (chainId < 0) { chainId = 0; }
            chainId = parseInt(chainId);
        }

        if (typeof(chainId) !== "number") { chainId = 0; }

        result.chainId = chainId;
    }
    */
    // 0x0000... should actually be null
    if (result.blockHash && (0, index_js_4.getBigInt)(result.blockHash) === BN_0) {
        result.blockHash = null;
    }
    return result;
}
exports.formatTransactionResponse = formatTransactionResponse;
//# sourceMappingURL=format.js.map