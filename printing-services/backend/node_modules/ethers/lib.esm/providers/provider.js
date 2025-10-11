//import { resolveAddress } from "@ethersproject/address";
import { defineProperties, getBigInt, getNumber, hexlify, isBytesLike, resolveProperties, assert, assertArgument, isError, makeError } from "../utils/index.js";
import { accessListify } from "../transaction/index.js";
const BN_0 = BigInt(0);
// -----------------------
function getValue(value) {
    if (value == null) {
        return null;
    }
    return value;
}
function toJson(value) {
    if (value == null) {
        return null;
    }
    return value.toString();
}
// @TODO? <T extends FeeData = { }> implements Required<T>
/**
 *  A **FeeData** wraps all the fee-related values associated with
 *  the network.
 */
export class FeeData {
    /**
     *  The gas price for legacy networks.
     */
    gasPrice;
    /**
     *  The maximum fee to pay per gas.
     *
     *  The base fee per gas is defined by the network and based on
     *  congestion, increasing the cost during times of heavy load
     *  and lowering when less busy.
     *
     *  The actual fee per gas will be the base fee for the block
     *  and the priority fee, up to the max fee per gas.
     *
     *  This will be ``null`` on legacy networks (i.e. [pre-EIP-1559](link-eip-1559))
     */
    maxFeePerGas;
    /**
     *  The additional amout to pay per gas to encourage a validator
     *  to include the transaction.
     *
     *  The purpose of this is to compensate the validator for the
     *  adjusted risk for including a given transaction.
     *
     *  This will be ``null`` on legacy networks (i.e. [pre-EIP-1559](link-eip-1559))
     */
    maxPriorityFeePerGas;
    /**
     *  Creates a new FeeData for %%gasPrice%%, %%maxFeePerGas%% and
     *  %%maxPriorityFeePerGas%%.
     */
    constructor(gasPrice, maxFeePerGas, maxPriorityFeePerGas) {
        defineProperties(this, {
            gasPrice: getValue(gasPrice),
            maxFeePerGas: getValue(maxFeePerGas),
            maxPriorityFeePerGas: getValue(maxPriorityFeePerGas)
        });
    }
    /**
     *  Returns a JSON-friendly value.
     */
    toJSON() {
        const { gasPrice, maxFeePerGas, maxPriorityFeePerGas } = this;
        return {
            _type: "FeeData",
            gasPrice: toJson(gasPrice),
            maxFeePerGas: toJson(maxFeePerGas),
            maxPriorityFeePerGas: toJson(maxPriorityFeePerGas),
        };
    }
}
;
/**
 *  Returns a copy of %%req%% with all properties coerced to their strict
 *  types.
 */
export function copyRequest(req) {
    const result = {};
    // These could be addresses, ENS names or Addressables
    if (req.to) {
        result.to = req.to;
    }
    if (req.from) {
        result.from = req.from;
    }
    if (req.data) {
        result.data = hexlify(req.data);
    }
    const bigIntKeys = "chainId,gasLimit,gasPrice,maxFeePerBlobGas,maxFeePerGas,maxPriorityFeePerGas,value".split(/,/);
    for (const key of bigIntKeys) {
        if (!(key in req) || req[key] == null) {
            continue;
        }
        result[key] = getBigInt(req[key], `request.${key}`);
    }
    const numberKeys = "type,nonce".split(/,/);
    for (const key of numberKeys) {
        if (!(key in req) || req[key] == null) {
            continue;
        }
        result[key] = getNumber(req[key], `request.${key}`);
    }
    if (req.accessList) {
        result.accessList = accessListify(req.accessList);
    }
    if (req.authorizationList) {
        result.authorizationList = req.authorizationList.slice();
    }
    if ("blockTag" in req) {
        result.blockTag = req.blockTag;
    }
    if ("enableCcipRead" in req) {
        result.enableCcipRead = !!req.enableCcipRead;
    }
    if ("customData" in req) {
        result.customData = req.customData;
    }
    if ("blobVersionedHashes" in req && req.blobVersionedHashes) {
        result.blobVersionedHashes = req.blobVersionedHashes.slice();
    }
    if ("kzg" in req) {
        result.kzg = req.kzg;
    }
    if ("blobs" in req && req.blobs) {
        result.blobs = req.blobs.map((b) => {
            if (isBytesLike(b)) {
                return hexlify(b);
            }
            return Object.assign({}, b);
        });
    }
    return result;
}
/**
 *  A **Block** represents the data associated with a full block on
 *  Ethereum.
 */
export class Block {
    /**
     *  The provider connected to the block used to fetch additional details
     *  if necessary.
     */
    provider;
    /**
     *  The block number, sometimes called the block height. This is a
     *  sequential number that is one higher than the parent block.
     */
    number;
    /**
     *  The block hash.
     *
     *  This hash includes all properties, so can be safely used to identify
     *  an exact set of block properties.
     */
    hash;
    /**
     *  The timestamp for this block, which is the number of seconds since
     *  epoch that this block was included.
     */
    timestamp;
    /**
     *  The block hash of the parent block.
     */
    parentHash;
    /**
     *  The hash tree root of the parent beacon block for the given
     *  execution block. See [[link-eip-4788]].
     */
    parentBeaconBlockRoot;
    /**
     *  The nonce.
     *
     *  On legacy networks, this is the random number inserted which
     *  permitted the difficulty target to be reached.
     */
    nonce;
    /**
     *  The difficulty target.
     *
     *  On legacy networks, this is the proof-of-work target required
     *  for a block to meet the protocol rules to be included.
     *
     *  On modern networks, this is a random number arrived at using
     *  randao.  @TODO: Find links?
     */
    difficulty;
    /**
     *  The total gas limit for this block.
     */
    gasLimit;
    /**
     *  The total gas used in this block.
     */
    gasUsed;
    /**
     *  The root hash for the global state after applying changes
     *  in this block.
     */
    stateRoot;
    /**
     *  The hash of the transaction receipts trie.
     */
    receiptsRoot;
    /**
     *  The total amount of blob gas consumed by the transactions
     *  within the block. See [[link-eip-4844]].
     */
    blobGasUsed;
    /**
     *  The running total of blob gas consumed in excess of the
     *  target, prior to the block. See [[link-eip-4844]].
     */
    excessBlobGas;
    /**
     *  The miner coinbase address, wihch receives any subsidies for
     *  including this block.
     */
    miner;
    /**
     *  The latest RANDAO mix of the post beacon state of
     *  the previous block.
     */
    prevRandao;
    /**
     *  Any extra data the validator wished to include.
     */
    extraData;
    /**
     *  The base fee per gas that all transactions in this block were
     *  charged.
     *
     *  This adjusts after each block, depending on how congested the network
     *  is.
     */
    baseFeePerGas;
    #transactions;
    /**
     *  Create a new **Block** object.
     *
     *  This should generally not be necessary as the unless implementing a
     *  low-level library.
     */
    constructor(block, provider) {
        this.#transactions = block.transactions.map((tx) => {
            if (typeof (tx) !== "string") {
                return new TransactionResponse(tx, provider);
            }
            return tx;
        });
        defineProperties(this, {
            provider,
            hash: getValue(block.hash),
            number: block.number,
            timestamp: block.timestamp,
            parentHash: block.parentHash,
            parentBeaconBlockRoot: block.parentBeaconBlockRoot,
            nonce: block.nonce,
            difficulty: block.difficulty,
            gasLimit: block.gasLimit,
            gasUsed: block.gasUsed,
            blobGasUsed: block.blobGasUsed,
            excessBlobGas: block.excessBlobGas,
            miner: block.miner,
            prevRandao: getValue(block.prevRandao),
            extraData: block.extraData,
            baseFeePerGas: getValue(block.baseFeePerGas),
            stateRoot: block.stateRoot,
            receiptsRoot: block.receiptsRoot,
        });
    }
    /**
     *  Returns the list of transaction hashes, in the order
     *  they were executed within the block.
     */
    get transactions() {
        return this.#transactions.map((tx) => {
            if (typeof (tx) === "string") {
                return tx;
            }
            return tx.hash;
        });
    }
    /**
     *  Returns the complete transactions, in the order they
     *  were executed within the block.
     *
     *  This is only available for blocks which prefetched
     *  transactions, by passing ``true`` to %%prefetchTxs%%
     *  into [[Provider-getBlock]].
     */
    get prefetchedTransactions() {
        const txs = this.#transactions.slice();
        // Doesn't matter...
        if (txs.length === 0) {
            return [];
        }
        // Make sure we prefetched the transactions
        assert(typeof (txs[0]) === "object", "transactions were not prefetched with block request", "UNSUPPORTED_OPERATION", {
            operation: "transactionResponses()"
        });
        return txs;
    }
    /**
     *  Returns a JSON-friendly value.
     */
    toJSON() {
        const { baseFeePerGas, difficulty, extraData, gasLimit, gasUsed, hash, miner, prevRandao, nonce, number, parentHash, parentBeaconBlockRoot, stateRoot, receiptsRoot, timestamp, transactions } = this;
        return {
            _type: "Block",
            baseFeePerGas: toJson(baseFeePerGas),
            difficulty: toJson(difficulty),
            extraData,
            gasLimit: toJson(gasLimit),
            gasUsed: toJson(gasUsed),
            blobGasUsed: toJson(this.blobGasUsed),
            excessBlobGas: toJson(this.excessBlobGas),
            hash, miner, prevRandao, nonce, number, parentHash, timestamp,
            parentBeaconBlockRoot, stateRoot, receiptsRoot,
            transactions,
        };
    }
    [Symbol.iterator]() {
        let index = 0;
        const txs = this.transactions;
        return {
            next: () => {
                if (index < this.length) {
                    return {
                        value: txs[index++], done: false
                    };
                }
                return { value: undefined, done: true };
            }
        };
    }
    /**
     *  The number of transactions in this block.
     */
    get length() { return this.#transactions.length; }
    /**
     *  The [[link-js-date]] this block was included at.
     */
    get date() {
        if (this.timestamp == null) {
            return null;
        }
        return new Date(this.timestamp * 1000);
    }
    /**
     *  Get the transaction at %%indexe%% within this block.
     */
    async getTransaction(indexOrHash) {
        // Find the internal value by its index or hash
        let tx = undefined;
        if (typeof (indexOrHash) === "number") {
            tx = this.#transactions[indexOrHash];
        }
        else {
            const hash = indexOrHash.toLowerCase();
            for (const v of this.#transactions) {
                if (typeof (v) === "string") {
                    if (v !== hash) {
                        continue;
                    }
                    tx = v;
                    break;
                }
                else {
                    if (v.hash !== hash) {
                        continue;
                    }
                    tx = v;
                    break;
                }
            }
        }
        if (tx == null) {
            throw new Error("no such tx");
        }
        if (typeof (tx) === "string") {
            return (await this.provider.getTransaction(tx));
        }
        else {
            return tx;
        }
    }
    /**
     *  If a **Block** was fetched with a request to include the transactions
     *  this will allow synchronous access to those transactions.
     *
     *  If the transactions were not prefetched, this will throw.
     */
    getPrefetchedTransaction(indexOrHash) {
        const txs = this.prefetchedTransactions;
        if (typeof (indexOrHash) === "number") {
            return txs[indexOrHash];
        }
        indexOrHash = indexOrHash.toLowerCase();
        for (const tx of txs) {
            if (tx.hash === indexOrHash) {
                return tx;
            }
        }
        assertArgument(false, "no matching transaction", "indexOrHash", indexOrHash);
    }
    /**
     *  Returns true if this block been mined. This provides a type guard
     *  for all properties on a [[MinedBlock]].
     */
    isMined() { return !!this.hash; }
    /**
     *  Returns true if this block is an [[link-eip-2930]] block.
     */
    isLondon() {
        return !!this.baseFeePerGas;
    }
    /**
     *  @_ignore:
     */
    orphanedEvent() {
        if (!this.isMined()) {
            throw new Error("");
        }
        return createOrphanedBlockFilter(this);
    }
}
//////////////////////
// Log
/**
 *  A **Log** in Ethereum represents an event that has been included in a
 *  transaction using the ``LOG*`` opcodes, which are most commonly used by
 *  Solidity's emit for announcing events.
 */
export class Log {
    /**
     *  The provider connected to the log used to fetch additional details
     *  if necessary.
     */
    provider;
    /**
     *  The transaction hash of the transaction this log occurred in. Use the
     *  [[Log-getTransaction]] to get the [[TransactionResponse]].
     */
    transactionHash;
    /**
     *  The block hash of the block this log occurred in. Use the
     *  [[Log-getBlock]] to get the [[Block]].
     */
    blockHash;
    /**
     *  The block number of the block this log occurred in. It is preferred
     *  to use the [[Block-hash]] when fetching the related [[Block]],
     *  since in the case of an orphaned block, the block at that height may
     *  have changed.
     */
    blockNumber;
    /**
     *  If the **Log** represents a block that was removed due to an orphaned
     *  block, this will be true.
     *
     *  This can only happen within an orphan event listener.
     */
    removed;
    /**
     *  The address of the contract that emitted this log.
     */
    address;
    /**
     *  The data included in this log when it was emitted.
     */
    data;
    /**
     *  The indexed topics included in this log when it was emitted.
     *
     *  All topics are included in the bloom filters, so they can be
     *  efficiently filtered using the [[Provider-getLogs]] method.
     */
    topics;
    /**
     *  The index within the block this log occurred at. This is generally
     *  not useful to developers, but can be used with the various roots
     *  to proof inclusion within a block.
     */
    index;
    /**
     *  The index within the transaction of this log.
     */
    transactionIndex;
    /**
     *  @_ignore:
     */
    constructor(log, provider) {
        this.provider = provider;
        const topics = Object.freeze(log.topics.slice());
        defineProperties(this, {
            transactionHash: log.transactionHash,
            blockHash: log.blockHash,
            blockNumber: log.blockNumber,
            removed: log.removed,
            address: log.address,
            data: log.data,
            topics,
            index: log.index,
            transactionIndex: log.transactionIndex,
        });
    }
    /**
     *  Returns a JSON-compatible object.
     */
    toJSON() {
        const { address, blockHash, blockNumber, data, index, removed, topics, transactionHash, transactionIndex } = this;
        return {
            _type: "log",
            address, blockHash, blockNumber, data, index,
            removed, topics, transactionHash, transactionIndex
        };
    }
    /**
     *  Returns the block that this log occurred in.
     */
    async getBlock() {
        const block = await this.provider.getBlock(this.blockHash);
        assert(!!block, "failed to find transaction", "UNKNOWN_ERROR", {});
        return block;
    }
    /**
     *  Returns the transaction that this log occurred in.
     */
    async getTransaction() {
        const tx = await this.provider.getTransaction(this.transactionHash);
        assert(!!tx, "failed to find transaction", "UNKNOWN_ERROR", {});
        return tx;
    }
    /**
     *  Returns the transaction receipt fot the transaction that this
     *  log occurred in.
     */
    async getTransactionReceipt() {
        const receipt = await this.provider.getTransactionReceipt(this.transactionHash);
        assert(!!receipt, "failed to find transaction receipt", "UNKNOWN_ERROR", {});
        return receipt;
    }
    /**
     *  @_ignore:
     */
    removedEvent() {
        return createRemovedLogFilter(this);
    }
}
//////////////////////
// Transaction Receipt
/*
export interface LegacyTransactionReceipt {
    byzantium: false;
    status: null;
    root: string;
}

export interface ByzantiumTransactionReceipt {
    byzantium: true;
    status: number;
    root: null;
}
*/
/**
 *  A **TransactionReceipt** includes additional information about a
 *  transaction that is only available after it has been mined.
 */
export class TransactionReceipt {
    /**
     *  The provider connected to the log used to fetch additional details
     *  if necessary.
     */
    provider;
    /**
     *  The address the transaction was sent to.
     */
    to;
    /**
     *  The sender of the transaction.
     */
    from;
    /**
     *  The address of the contract if the transaction was directly
     *  responsible for deploying one.
     *
     *  This is non-null **only** if the ``to`` is empty and the ``data``
     *  was successfully executed as initcode.
     */
    contractAddress;
    /**
     *  The transaction hash.
     */
    hash;
    /**
     *  The index of this transaction within the block transactions.
     */
    index;
    /**
     *  The block hash of the [[Block]] this transaction was included in.
     */
    blockHash;
    /**
     *  The block number of the [[Block]] this transaction was included in.
     */
    blockNumber;
    /**
     *  The bloom filter bytes that represent all logs that occurred within
     *  this transaction. This is generally not useful for most developers,
     *  but can be used to validate the included logs.
     */
    logsBloom;
    /**
     *  The actual amount of gas used by this transaction.
     *
     *  When creating a transaction, the amount of gas that will be used can
     *  only be approximated, but the sender must pay the gas fee for the
     *  entire gas limit. After the transaction, the difference is refunded.
     */
    gasUsed;
    /**
     *  The gas used for BLObs. See [[link-eip-4844]].
     */
    blobGasUsed;
    /**
     *  The amount of gas used by all transactions within the block for this
     *  and all transactions with a lower ``index``.
     *
     *  This is generally not useful for developers but can be used to
     *  validate certain aspects of execution.
     */
    cumulativeGasUsed;
    /**
     *  The actual gas price used during execution.
     *
     *  Due to the complexity of [[link-eip-1559]] this value can only
     *  be caluclated after the transaction has been mined, snce the base
     *  fee is protocol-enforced.
     */
    gasPrice;
    /**
     *  The price paid per BLOB in gas. See [[link-eip-4844]].
     */
    blobGasPrice;
    /**
     *  The [[link-eip-2718]] transaction type.
     */
    type;
    //readonly byzantium!: boolean;
    /**
     *  The status of this transaction, indicating success (i.e. ``1``) or
     *  a revert (i.e. ``0``).
     *
     *  This is available in post-byzantium blocks, but some backends may
     *  backfill this value.
     */
    status;
    /**
     *  The root hash of this transaction.
     *
     *  This is no present and was only included in pre-byzantium blocks, but
     *  could be used to validate certain parts of the receipt.
     */
    root;
    #logs;
    /**
     *  @_ignore:
     */
    constructor(tx, provider) {
        this.#logs = Object.freeze(tx.logs.map((log) => {
            return new Log(log, provider);
        }));
        let gasPrice = BN_0;
        if (tx.effectiveGasPrice != null) {
            gasPrice = tx.effectiveGasPrice;
        }
        else if (tx.gasPrice != null) {
            gasPrice = tx.gasPrice;
        }
        defineProperties(this, {
            provider,
            to: tx.to,
            from: tx.from,
            contractAddress: tx.contractAddress,
            hash: tx.hash,
            index: tx.index,
            blockHash: tx.blockHash,
            blockNumber: tx.blockNumber,
            logsBloom: tx.logsBloom,
            gasUsed: tx.gasUsed,
            cumulativeGasUsed: tx.cumulativeGasUsed,
            blobGasUsed: tx.blobGasUsed,
            gasPrice,
            blobGasPrice: tx.blobGasPrice,
            type: tx.type,
            //byzantium: tx.byzantium,
            status: tx.status,
            root: tx.root
        });
    }
    /**
     *  The logs for this transaction.
     */
    get logs() { return this.#logs; }
    /**
     *  Returns a JSON-compatible representation.
     */
    toJSON() {
        const { to, from, contractAddress, hash, index, blockHash, blockNumber, logsBloom, logs, //byzantium, 
        status, root } = this;
        return {
            _type: "TransactionReceipt",
            blockHash, blockNumber,
            //byzantium, 
            contractAddress,
            cumulativeGasUsed: toJson(this.cumulativeGasUsed),
            from,
            gasPrice: toJson(this.gasPrice),
            blobGasUsed: toJson(this.blobGasUsed),
            blobGasPrice: toJson(this.blobGasPrice),
            gasUsed: toJson(this.gasUsed),
            hash, index, logs, logsBloom, root, status, to
        };
    }
    /**
     *  @_ignore:
     */
    get length() { return this.logs.length; }
    [Symbol.iterator]() {
        let index = 0;
        return {
            next: () => {
                if (index < this.length) {
                    return { value: this.logs[index++], done: false };
                }
                return { value: undefined, done: true };
            }
        };
    }
    /**
     *  The total fee for this transaction, in wei.
     */
    get fee() {
        return this.gasUsed * this.gasPrice;
    }
    /**
     *  Resolves to the block this transaction occurred in.
     */
    async getBlock() {
        const block = await this.provider.getBlock(this.blockHash);
        if (block == null) {
            throw new Error("TODO");
        }
        return block;
    }
    /**
     *  Resolves to the transaction this transaction occurred in.
     */
    async getTransaction() {
        const tx = await this.provider.getTransaction(this.hash);
        if (tx == null) {
            throw new Error("TODO");
        }
        return tx;
    }
    /**
     *  Resolves to the return value of the execution of this transaction.
     *
     *  Support for this feature is limited, as it requires an archive node
     *  with the ``debug_`` or ``trace_`` API enabled.
     */
    async getResult() {
        return (await this.provider.getTransactionResult(this.hash));
    }
    /**
     *  Resolves to the number of confirmations this transaction has.
     */
    async confirmations() {
        return (await this.provider.getBlockNumber()) - this.blockNumber + 1;
    }
    /**
     *  @_ignore:
     */
    removedEvent() {
        return createRemovedTransactionFilter(this);
    }
    /**
     *  @_ignore:
     */
    reorderedEvent(other) {
        assert(!other || other.isMined(), "unmined 'other' transction cannot be orphaned", "UNSUPPORTED_OPERATION", { operation: "reorderedEvent(other)" });
        return createReorderedTransactionFilter(this, other);
    }
}
/**
 *  A **TransactionResponse** includes all properties about a transaction
 *  that was sent to the network, which may or may not be included in a
 *  block.
 *
 *  The [[TransactionResponse-isMined]] can be used to check if the
 *  transaction has been mined as well as type guard that the otherwise
 *  possibly ``null`` properties are defined.
 */
export class TransactionResponse {
    /**
     *  The provider this is connected to, which will influence how its
     *  methods will resolve its async inspection methods.
     */
    provider;
    /**
     *  The block number of the block that this transaction was included in.
     *
     *  This is ``null`` for pending transactions.
     */
    blockNumber;
    /**
     *  The blockHash of the block that this transaction was included in.
     *
     *  This is ``null`` for pending transactions.
     */
    blockHash;
    /**
     *  The index within the block that this transaction resides at.
     */
    index;
    /**
     *  The transaction hash.
     */
    hash;
    /**
     *  The [[link-eip-2718]] transaction envelope type. This is
     *  ``0`` for legacy transactions types.
     */
    type;
    /**
     *  The receiver of this transaction.
     *
     *  If ``null``, then the transaction is an initcode transaction.
     *  This means the result of executing the [[data]] will be deployed
     *  as a new contract on chain (assuming it does not revert) and the
     *  address may be computed using [[getCreateAddress]].
     */
    to;
    /**
     *  The sender of this transaction. It is implicitly computed
     *  from the transaction pre-image hash (as the digest) and the
     *  [[signature]] using ecrecover.
     */
    from;
    /**
     *  The nonce, which is used to prevent replay attacks and offer
     *  a method to ensure transactions from a given sender are explicitly
     *  ordered.
     *
     *  When sending a transaction, this must be equal to the number of
     *  transactions ever sent by [[from]].
     */
    nonce;
    /**
     *  The maximum units of gas this transaction can consume. If execution
     *  exceeds this, the entries transaction is reverted and the sender
     *  is charged for the full amount, despite not state changes being made.
     */
    gasLimit;
    /**
     *  The gas price can have various values, depending on the network.
     *
     *  In modern networks, for transactions that are included this is
     *  the //effective gas price// (the fee per gas that was actually
     *  charged), while for transactions that have not been included yet
     *  is the [[maxFeePerGas]].
     *
     *  For legacy transactions, or transactions on legacy networks, this
     *  is the fee that will be charged per unit of gas the transaction
     *  consumes.
     */
    gasPrice;
    /**
     *  The maximum priority fee (per unit of gas) to allow a
     *  validator to charge the sender. This is inclusive of the
     *  [[maxFeeFeePerGas]].
     */
    maxPriorityFeePerGas;
    /**
     *  The maximum fee (per unit of gas) to allow this transaction
     *  to charge the sender.
     */
    maxFeePerGas;
    /**
     *  The [[link-eip-4844]] max fee per BLOb gas.
     */
    maxFeePerBlobGas;
    /**
     *  The data.
     */
    data;
    /**
     *  The value, in wei. Use [[formatEther]] to format this value
     *  as ether.
     */
    value;
    /**
     *  The chain ID.
     */
    chainId;
    /**
     *  The signature.
     */
    signature;
    /**
     *  The [[link-eip-2930]] access list for transaction types that
     *  support it, otherwise ``null``.
     */
    accessList;
    /**
     *  The [[link-eip-4844]] BLOb versioned hashes.
     */
    blobVersionedHashes;
    /**
     *  The [[link-eip-7702]] authorizations (if any).
     */
    authorizationList;
    #startBlock;
    /**
     *  @_ignore:
     */
    constructor(tx, provider) {
        this.provider = provider;
        this.blockNumber = (tx.blockNumber != null) ? tx.blockNumber : null;
        this.blockHash = (tx.blockHash != null) ? tx.blockHash : null;
        this.hash = tx.hash;
        this.index = tx.index;
        this.type = tx.type;
        this.from = tx.from;
        this.to = tx.to || null;
        this.gasLimit = tx.gasLimit;
        this.nonce = tx.nonce;
        this.data = tx.data;
        this.value = tx.value;
        this.gasPrice = tx.gasPrice;
        this.maxPriorityFeePerGas = (tx.maxPriorityFeePerGas != null) ? tx.maxPriorityFeePerGas : null;
        this.maxFeePerGas = (tx.maxFeePerGas != null) ? tx.maxFeePerGas : null;
        this.maxFeePerBlobGas = (tx.maxFeePerBlobGas != null) ? tx.maxFeePerBlobGas : null;
        this.chainId = tx.chainId;
        this.signature = tx.signature;
        this.accessList = (tx.accessList != null) ? tx.accessList : null;
        this.blobVersionedHashes = (tx.blobVersionedHashes != null) ? tx.blobVersionedHashes : null;
        this.authorizationList = (tx.authorizationList != null) ? tx.authorizationList : null;
        this.#startBlock = -1;
    }
    /**
     *  Returns a JSON-compatible representation of this transaction.
     */
    toJSON() {
        const { blockNumber, blockHash, index, hash, type, to, from, nonce, data, signature, accessList, blobVersionedHashes } = this;
        return {
            _type: "TransactionResponse",
            accessList, blockNumber, blockHash,
            blobVersionedHashes,
            chainId: toJson(this.chainId),
            data, from,
            gasLimit: toJson(this.gasLimit),
            gasPrice: toJson(this.gasPrice),
            hash,
            maxFeePerGas: toJson(this.maxFeePerGas),
            maxPriorityFeePerGas: toJson(this.maxPriorityFeePerGas),
            maxFeePerBlobGas: toJson(this.maxFeePerBlobGas),
            nonce, signature, to, index, type,
            value: toJson(this.value),
        };
    }
    /**
     *  Resolves to the Block that this transaction was included in.
     *
     *  This will return null if the transaction has not been included yet.
     */
    async getBlock() {
        let blockNumber = this.blockNumber;
        if (blockNumber == null) {
            const tx = await this.getTransaction();
            if (tx) {
                blockNumber = tx.blockNumber;
            }
        }
        if (blockNumber == null) {
            return null;
        }
        const block = this.provider.getBlock(blockNumber);
        if (block == null) {
            throw new Error("TODO");
        }
        return block;
    }
    /**
     *  Resolves to this transaction being re-requested from the
     *  provider. This can be used if you have an unmined transaction
     *  and wish to get an up-to-date populated instance.
     */
    async getTransaction() {
        return this.provider.getTransaction(this.hash);
    }
    /**
     *  Resolve to the number of confirmations this transaction has.
     */
    async confirmations() {
        if (this.blockNumber == null) {
            const { tx, blockNumber } = await resolveProperties({
                tx: this.getTransaction(),
                blockNumber: this.provider.getBlockNumber()
            });
            // Not mined yet...
            if (tx == null || tx.blockNumber == null) {
                return 0;
            }
            return blockNumber - tx.blockNumber + 1;
        }
        const blockNumber = await this.provider.getBlockNumber();
        return blockNumber - this.blockNumber + 1;
    }
    /**
     *  Resolves once this transaction has been mined and has
     *  %%confirms%% blocks including it (default: ``1``) with an
     *  optional %%timeout%%.
     *
     *  This can resolve to ``null`` only if %%confirms%% is ``0``
     *  and the transaction has not been mined, otherwise this will
     *  wait until enough confirmations have completed.
     */
    async wait(_confirms, _timeout) {
        const confirms = (_confirms == null) ? 1 : _confirms;
        const timeout = (_timeout == null) ? 0 : _timeout;
        let startBlock = this.#startBlock;
        let nextScan = -1;
        let stopScanning = (startBlock === -1) ? true : false;
        const checkReplacement = async () => {
            // Get the current transaction count for this sender
            if (stopScanning) {
                return null;
            }
            const { blockNumber, nonce } = await resolveProperties({
                blockNumber: this.provider.getBlockNumber(),
                nonce: this.provider.getTransactionCount(this.from)
            });
            // No transaction or our nonce has not been mined yet; but we
            // can start scanning later when we do start
            if (nonce < this.nonce) {
                startBlock = blockNumber;
                return;
            }
            // We were mined; no replacement
            if (stopScanning) {
                return null;
            }
            const mined = await this.getTransaction();
            if (mined && mined.blockNumber != null) {
                return;
            }
            // We were replaced; start scanning for that transaction
            // Starting to scan; look back a few extra blocks for safety
            if (nextScan === -1) {
                nextScan = startBlock - 3;
                if (nextScan < this.#startBlock) {
                    nextScan = this.#startBlock;
                }
            }
            while (nextScan <= blockNumber) {
                // Get the next block to scan
                if (stopScanning) {
                    return null;
                }
                const block = await this.provider.getBlock(nextScan, true);
                // This should not happen; but we'll try again shortly
                if (block == null) {
                    return;
                }
                // We were mined; no replacement
                for (const hash of block) {
                    if (hash === this.hash) {
                        return;
                    }
                }
                // Search for the transaction that replaced us
                for (let i = 0; i < block.length; i++) {
                    const tx = await block.getTransaction(i);
                    if (tx.from === this.from && tx.nonce === this.nonce) {
                        // Get the receipt
                        if (stopScanning) {
                            return null;
                        }
                        const receipt = await this.provider.getTransactionReceipt(tx.hash);
                        // This should not happen; but we'll try again shortly
                        if (receipt == null) {
                            return;
                        }
                        // We will retry this on the next block (this case could be optimized)
                        if ((blockNumber - receipt.blockNumber + 1) < confirms) {
                            return;
                        }
                        // The reason we were replaced
                        let reason = "replaced";
                        if (tx.data === this.data && tx.to === this.to && tx.value === this.value) {
                            reason = "repriced";
                        }
                        else if (tx.data === "0x" && tx.from === tx.to && tx.value === BN_0) {
                            reason = "cancelled";
                        }
                        assert(false, "transaction was replaced", "TRANSACTION_REPLACED", {
                            cancelled: (reason === "replaced" || reason === "cancelled"),
                            reason,
                            replacement: tx.replaceableTransaction(startBlock),
                            hash: tx.hash,
                            receipt
                        });
                    }
                }
                nextScan++;
            }
            return;
        };
        const checkReceipt = (receipt) => {
            if (receipt == null || receipt.status !== 0) {
                return receipt;
            }
            assert(false, "transaction execution reverted", "CALL_EXCEPTION", {
                action: "sendTransaction",
                data: null, reason: null, invocation: null, revert: null,
                transaction: {
                    to: receipt.to,
                    from: receipt.from,
                    data: "" // @TODO: in v7, split out sendTransaction properties
                }, receipt
            });
        };
        const receipt = await this.provider.getTransactionReceipt(this.hash);
        if (confirms === 0) {
            return checkReceipt(receipt);
        }
        if (receipt) {
            if (confirms === 1 || (await receipt.confirmations()) >= confirms) {
                return checkReceipt(receipt);
            }
        }
        else {
            // Check for a replacement; throws if a replacement was found
            await checkReplacement();
            // Allow null only when the confirms is 0
            if (confirms === 0) {
                return null;
            }
        }
        const waiter = new Promise((resolve, reject) => {
            // List of things to cancel when we have a result (one way or the other)
            const cancellers = [];
            const cancel = () => { cancellers.forEach((c) => c()); };
            // On cancel, stop scanning for replacements
            cancellers.push(() => { stopScanning = true; });
            // Set up any timeout requested
            if (timeout > 0) {
                const timer = setTimeout(() => {
                    cancel();
                    reject(makeError("wait for transaction timeout", "TIMEOUT"));
                }, timeout);
                cancellers.push(() => { clearTimeout(timer); });
            }
            const txListener = async (receipt) => {
                // Done; return it!
                if ((await receipt.confirmations()) >= confirms) {
                    cancel();
                    try {
                        resolve(checkReceipt(receipt));
                    }
                    catch (error) {
                        reject(error);
                    }
                }
            };
            cancellers.push(() => { this.provider.off(this.hash, txListener); });
            this.provider.on(this.hash, txListener);
            // We support replacement detection; start checking
            if (startBlock >= 0) {
                const replaceListener = async () => {
                    try {
                        // Check for a replacement; this throws only if one is found
                        await checkReplacement();
                    }
                    catch (error) {
                        // We were replaced (with enough confirms); re-throw the error
                        if (isError(error, "TRANSACTION_REPLACED")) {
                            cancel();
                            reject(error);
                            return;
                        }
                    }
                    // Rescheudle a check on the next block
                    if (!stopScanning) {
                        this.provider.once("block", replaceListener);
                    }
                };
                cancellers.push(() => { this.provider.off("block", replaceListener); });
                this.provider.once("block", replaceListener);
            }
        });
        return await waiter;
    }
    /**
     *  Returns ``true`` if this transaction has been included.
     *
     *  This is effective only as of the time the TransactionResponse
     *  was instantiated. To get up-to-date information, use
     *  [[getTransaction]].
     *
     *  This provides a Type Guard that this transaction will have
     *  non-null property values for properties that are null for
     *  unmined transactions.
     */
    isMined() {
        return (this.blockHash != null);
    }
    /**
     *  Returns true if the transaction is a legacy (i.e. ``type == 0``)
     *  transaction.
     *
     *  This provides a Type Guard that this transaction will have
     *  the ``null``-ness for hardfork-specific properties set correctly.
     */
    isLegacy() {
        return (this.type === 0);
    }
    /**
     *  Returns true if the transaction is a Berlin (i.e. ``type == 1``)
     *  transaction. See [[link-eip-2070]].
     *
     *  This provides a Type Guard that this transaction will have
     *  the ``null``-ness for hardfork-specific properties set correctly.
     */
    isBerlin() {
        return (this.type === 1);
    }
    /**
     *  Returns true if the transaction is a London (i.e. ``type == 2``)
     *  transaction. See [[link-eip-1559]].
     *
     *  This provides a Type Guard that this transaction will have
     *  the ``null``-ness for hardfork-specific properties set correctly.
     */
    isLondon() {
        return (this.type === 2);
    }
    /**
     *  Returns true if hte transaction is a Cancun (i.e. ``type == 3``)
     *  transaction. See [[link-eip-4844]].
     */
    isCancun() {
        return (this.type === 3);
    }
    /**
     *  Returns a filter which can be used to listen for orphan events
     *  that evict this transaction.
     */
    removedEvent() {
        assert(this.isMined(), "unmined transaction canot be orphaned", "UNSUPPORTED_OPERATION", { operation: "removeEvent()" });
        return createRemovedTransactionFilter(this);
    }
    /**
     *  Returns a filter which can be used to listen for orphan events
     *  that re-order this event against %%other%%.
     */
    reorderedEvent(other) {
        assert(this.isMined(), "unmined transaction canot be orphaned", "UNSUPPORTED_OPERATION", { operation: "removeEvent()" });
        assert(!other || other.isMined(), "unmined 'other' transaction canot be orphaned", "UNSUPPORTED_OPERATION", { operation: "removeEvent()" });
        return createReorderedTransactionFilter(this, other);
    }
    /**
     *  Returns a new TransactionResponse instance which has the ability to
     *  detect (and throw an error) if the transaction is replaced, which
     *  will begin scanning at %%startBlock%%.
     *
     *  This should generally not be used by developers and is intended
     *  primarily for internal use. Setting an incorrect %%startBlock%% can
     *  have devastating performance consequences if used incorrectly.
     */
    replaceableTransaction(startBlock) {
        assertArgument(Number.isInteger(startBlock) && startBlock >= 0, "invalid startBlock", "startBlock", startBlock);
        const tx = new TransactionResponse(this, this.provider);
        tx.#startBlock = startBlock;
        return tx;
    }
}
function createOrphanedBlockFilter(block) {
    return { orphan: "drop-block", hash: block.hash, number: block.number };
}
function createReorderedTransactionFilter(tx, other) {
    return { orphan: "reorder-transaction", tx, other };
}
function createRemovedTransactionFilter(tx) {
    return { orphan: "drop-transaction", tx };
}
function createRemovedLogFilter(log) {
    return { orphan: "drop-log", log: {
            transactionHash: log.transactionHash,
            blockHash: log.blockHash,
            blockNumber: log.blockNumber,
            address: log.address,
            data: log.data,
            topics: Object.freeze(log.topics.slice()),
            index: log.index
        } };
}
//# sourceMappingURL=provider.js.map