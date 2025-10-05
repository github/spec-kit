//import { resolveAddress } from "@ethersproject/address";
import {
    defineProperties, getBigInt, getNumber, hexlify, isBytesLike,
    resolveProperties,
    assert, assertArgument, isError, makeError
} from "../utils/index.js";
import { accessListify } from "../transaction/index.js";

import type { AddressLike, NameResolver } from "../address/index.js";
import type { BigNumberish, EventEmitterable } from "../utils/index.js";
import type { Signature } from "../crypto/index.js";
import type {
    AccessList, AccessListish, Authorization, AuthorizationLike, BlobLike,
    KzgLibraryLike, TransactionLike
} from "../transaction/index.js";

import type { ContractRunner } from "./contracts.js";
import type { Network } from "./network.js";


const BN_0 = BigInt(0);

/**
 *  A **BlockTag** specifies a specific block.
 *
 *  **numeric value** - specifies the block height, where
 *  the genesis block is block 0; many operations accept a negative
 *  value which indicates the block number should be deducted from
 *  the most recent block. A numeric value may be a ``number``, ``bigint``,
 *  or a decimal of hex string.
 *
 *  **blockhash** - specifies a specific block by its blockhash; this allows
 *  potentially orphaned blocks to be specifed, without ambiguity, but many
 *  backends do not support this for some operations.
 */
export type BlockTag = BigNumberish | string;

import {
    BlockParams, LogParams, TransactionReceiptParams,
    TransactionResponseParams
} from "./formatting.js";

// -----------------------

function getValue<T>(value: undefined | null | T): null | T {
    if (value == null) { return null; }
    return value;
}

function toJson(value: null | bigint): null | string {
    if (value == null) { return null; }
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
    readonly gasPrice!: null | bigint;

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
    readonly maxFeePerGas!: null | bigint;

    /**
     *  The additional amout to pay per gas to encourage a validator
     *  to include the transaction.
     *
     *  The purpose of this is to compensate the validator for the
     *  adjusted risk for including a given transaction.
     *
     *  This will be ``null`` on legacy networks (i.e. [pre-EIP-1559](link-eip-1559))
     */
    readonly maxPriorityFeePerGas!: null | bigint;

    /**
     *  Creates a new FeeData for %%gasPrice%%, %%maxFeePerGas%% and
     *  %%maxPriorityFeePerGas%%.
     */
    constructor(gasPrice?: null | bigint, maxFeePerGas?: null | bigint, maxPriorityFeePerGas?: null | bigint) {
        defineProperties<FeeData>(this, {
            gasPrice: getValue(gasPrice),
            maxFeePerGas: getValue(maxFeePerGas),
            maxPriorityFeePerGas: getValue(maxPriorityFeePerGas)
        });
    }

    /**
     *  Returns a JSON-friendly value.
     */
    toJSON(): any {
        const {
            gasPrice, maxFeePerGas, maxPriorityFeePerGas
        } = this;
        return {
            _type: "FeeData",
            gasPrice: toJson(gasPrice),
            maxFeePerGas: toJson(maxFeePerGas),
            maxPriorityFeePerGas: toJson(maxPriorityFeePerGas),
        };
    }
}


/**
 *  A **TransactionRequest** is a transactions with potentially various
 *  properties not defined, or with less strict types for its values.
 *
 *  This is used to pass to various operations, which will internally
 *  coerce any types and populate any necessary values.
 */
export interface TransactionRequest {
    /**
     *  The transaction type.
     */
    type?: null | number;

    /**
     *  The target of the transaction.
     */
    to?: null | AddressLike;

    /**
     *  The sender of the transaction.
     */
    from?: null | AddressLike;

    /**
     *  The nonce of the transaction, used to prevent replay attacks.
     */
    nonce?: null | number;

    /**
     *  The maximum amount of gas to allow this transaction to consume.
     */
    gasLimit?: null | BigNumberish;

    /**
     *  The gas price to use for legacy transactions or transactions on
     *  legacy networks.
     *
     *  Most of the time the ``max*FeePerGas`` is preferred.
     */
    gasPrice?: null | BigNumberish;

    /**
     *  The [[link-eip-1559]] maximum priority fee to pay per gas.
     */
    maxPriorityFeePerGas?: null | BigNumberish;

    /**
     *  The [[link-eip-1559]] maximum total fee to pay per gas. The actual
     *  value used is protocol enforced to be the block's base fee.
     */
    maxFeePerGas?: null | BigNumberish;

    /**
     *  The transaction data.
     */
    data?: null | string;

    /**
     *  The transaction value (in wei).
     */
    value?: null | BigNumberish;

    /**
     *  The chain ID for the network this transaction is valid on.
     */
    chainId?: null | BigNumberish;

    /**
     *  The [[link-eip-2930]] access list. Storage slots included in the access
     *  list are //warmed// by pre-loading them, so their initial cost to
     *  fetch is guaranteed, but then each additional access is cheaper.
     */
    accessList?: null | AccessListish;

    /**
     *  A custom object, which can be passed along for network-specific
     *  values.
     */
    customData?: any;

    // Only meaningful when used for call

    /**
     *  When using ``call`` or ``estimateGas``, this allows a specific
     *  block to be queried. Many backends do not support this and when
     *  unsupported errors are silently squelched and ``"latest"`` is used. 
     */
    blockTag?: BlockTag;

    /**
     *  When using ``call``, this enables CCIP-read, which permits the
     *  provider to be redirected to web-based content during execution,
     *  which is then further validated by the contract.
     *
     *  There are potential security implications allowing CCIP-read, as
     *  it could be used to expose the IP address or user activity during
     *  the fetch to unexpected parties.
     */
    enableCcipRead?: boolean;

    /**
     *  The blob versioned hashes (see [[link-eip-4844]]).
     */
    blobVersionedHashes?: null | Array<string>

    /**
     *  The maximum fee per blob gas (see [[link-eip-4844]]).
     */
    maxFeePerBlobGas?: null | BigNumberish;

    /**
     *  Any blobs to include in the transaction (see [[link-eip-4844]]).
     */
    blobs?: null | Array<BlobLike>;

    /**
     *  An external library for computing the KZG commitments and
     *  proofs necessary for EIP-4844 transactions (see [[link-eip-4844]]).
     *
     *  This is generally ``null``, unless you are creating BLOb
     *  transactions.
     */
    kzg?: null | KzgLibraryLike;

    /**
     *  The [[link-eip-7702]] authorizations (if any).
     */
    authorizationList?: null | Array<AuthorizationLike>;

    // Todo?
    //gasMultiplier?: number;
};

/**
 *  A **PreparedTransactionRequest** is identical to a [[TransactionRequest]]
 *  except all the property types are strictly enforced.
 */
export interface PreparedTransactionRequest {
    /**
     *  The transaction type.
     */
    type?: number;


    /**
     *  The target of the transaction.
     */
    to?: AddressLike;

    /**
     *  The sender of the transaction.
     */
    from?: AddressLike;

    /**
     *  The nonce of the transaction, used to prevent replay attacks.
     */

    nonce?: number;

    /**
     *  The maximum amount of gas to allow this transaction to consume.
     */
    gasLimit?: bigint;

    /**
     *  The gas price to use for legacy transactions or transactions on
     *  legacy networks.
     *
     *  Most of the time the ``max*FeePerGas`` is preferred.
     */
    gasPrice?: bigint;

    /**
     *  The [[link-eip-1559]] maximum priority fee to pay per gas.
     */
    maxPriorityFeePerGas?: bigint;

    /**
     *  The [[link-eip-1559]] maximum total fee to pay per gas. The actual
     *  value used is protocol enforced to be the block's base fee.
     */
    maxFeePerGas?: bigint;

    /**
     *  The transaction data.
     */
    data?: string;


    /**
     *  The transaction value (in wei).
     */
    value?: bigint;

    /**
     *  The chain ID for the network this transaction is valid on.
     */
    chainId?: bigint;

    /**
     *  The [[link-eip-2930]] access list. Storage slots included in the access
     *  list are //warmed// by pre-loading them, so their initial cost to
     *  fetch is guaranteed, but then each additional access is cheaper.
     */
    accessList?: AccessList;

    /**
     *  The [[link-eip-7702]] authorizations (if any).
     */
    authorizationList?: Array<Authorization>;

    /**
     *  A custom object, which can be passed along for network-specific
     *  values.
     */
    customData?: any;



    /**
     *  When using ``call`` or ``estimateGas``, this allows a specific
     *  block to be queried. Many backends do not support this and when
     *  unsupported errors are silently squelched and ``"latest"`` is used. 
     */
    blockTag?: BlockTag;

    /**
     *  When using ``call``, this enables CCIP-read, which permits the
     *  provider to be redirected to web-based content during execution,
     *  which is then further validated by the contract.
     *
     *  There are potential security implications allowing CCIP-read, as
     *  it could be used to expose the IP address or user activity during
     *  the fetch to unexpected parties.
     */
    enableCcipRead?: boolean;
}

/**
 *  Returns a copy of %%req%% with all properties coerced to their strict
 *  types.
 */
export function copyRequest(req: TransactionRequest): PreparedTransactionRequest {
    const result: any = { };

    // These could be addresses, ENS names or Addressables
    if (req.to) { result.to = req.to; }
    if (req.from) { result.from = req.from; }

    if (req.data) { result.data = hexlify(req.data); }

    const bigIntKeys = "chainId,gasLimit,gasPrice,maxFeePerBlobGas,maxFeePerGas,maxPriorityFeePerGas,value".split(/,/);
    for (const key of bigIntKeys) {
        if (!(key in req) || (<any>req)[key] == null) { continue; }
        result[key] = getBigInt((<any>req)[key], `request.${ key }`);
    }

    const numberKeys = "type,nonce".split(/,/);
    for (const key of numberKeys) {
        if (!(key in req) || (<any>req)[key] == null) { continue; }
        result[key] = getNumber((<any>req)[key], `request.${ key }`);
    }

    if (req.accessList) {
        result.accessList = accessListify(req.accessList);
    }

    if (req.authorizationList) {
        result.authorizationList = req.authorizationList.slice();
    }

    if ("blockTag" in req) { result.blockTag = req.blockTag; }

    if ("enableCcipRead" in req) {
        result.enableCcipRead = !!req.enableCcipRead
    }

    if ("customData" in req) {
        result.customData = req.customData;
    }

    if ("blobVersionedHashes" in req && req.blobVersionedHashes) {
        result.blobVersionedHashes = req.blobVersionedHashes.slice();
    }

    if ("kzg" in req) { result.kzg = req.kzg; }

    if ("blobs" in req && req.blobs) {
        result.blobs = req.blobs.map((b) => {
            if (isBytesLike(b)) { return hexlify(b); }
            return Object.assign({ }, b);
        });
    }

    return result;
}

//////////////////////
// Block

/**
 *  An Interface to indicate a [[Block]] has been included in the
 *  blockchain. This asserts a Type Guard that necessary properties
 *  are non-null.
 *
 *  Before a block is included, it is a //pending// block.
 */
export interface MinedBlock extends Block {
    /**
     *  The block number also known as the block height.
     */
    readonly number: number;

    /**
     *  The block hash.
     */
    readonly hash: string;

    /**
     *  The block timestamp, in seconds from epoch.
     */
    readonly timestamp: number;

    /**
     *  The block date, created from the [[timestamp]].
     */
    readonly date: Date;

    /**
     *  The miner of the block, also known as the ``author`` or
     *  block ``producer``.
     */
    readonly miner: string;
}

/**
 *  A **Block** represents the data associated with a full block on
 *  Ethereum.
 */
export class Block implements BlockParams, Iterable<string> {

    /**
     *  The provider connected to the block used to fetch additional details
     *  if necessary.
     */
    readonly provider!: Provider;

    /**
     *  The block number, sometimes called the block height. This is a
     *  sequential number that is one higher than the parent block.
     */
    readonly number!: number;

    /**
     *  The block hash.
     *
     *  This hash includes all properties, so can be safely used to identify
     *  an exact set of block properties.
     */
    readonly hash!: null | string;

    /**
     *  The timestamp for this block, which is the number of seconds since
     *  epoch that this block was included.
     */
    readonly timestamp!: number;

    /**
     *  The block hash of the parent block.
     */
    readonly parentHash!: string;

    /**
     *  The hash tree root of the parent beacon block for the given
     *  execution block. See [[link-eip-4788]].
     */
    parentBeaconBlockRoot!: null | string;

    /**
     *  The nonce.
     *
     *  On legacy networks, this is the random number inserted which
     *  permitted the difficulty target to be reached.
     */
    readonly nonce!: string;

    /**
     *  The difficulty target.
     *
     *  On legacy networks, this is the proof-of-work target required
     *  for a block to meet the protocol rules to be included.
     *
     *  On modern networks, this is a random number arrived at using
     *  randao.  @TODO: Find links?
     */
    readonly difficulty!: bigint;


    /**
     *  The total gas limit for this block.
     */
    readonly gasLimit!: bigint;

    /**
     *  The total gas used in this block.
     */
    readonly gasUsed!: bigint;


    /**
     *  The root hash for the global state after applying changes
     *  in this block.
     */
    readonly stateRoot!: null | string;

    /**
     *  The hash of the transaction receipts trie.
     */
    readonly receiptsRoot!: null | string;

    /**
     *  The total amount of blob gas consumed by the transactions
     *  within the block. See [[link-eip-4844]].
     */
    readonly blobGasUsed!: null | bigint;

    /**
     *  The running total of blob gas consumed in excess of the
     *  target, prior to the block. See [[link-eip-4844]].
     */
    readonly excessBlobGas!: null | bigint;

    /**
     *  The miner coinbase address, wihch receives any subsidies for
     *  including this block.
     */
    readonly miner!: string;

    /**
     *  The latest RANDAO mix of the post beacon state of
     *  the previous block.
     */
    readonly prevRandao!: null | string;

    /**
     *  Any extra data the validator wished to include.
     */
    readonly extraData!: string;

    /**
     *  The base fee per gas that all transactions in this block were
     *  charged.
     *
     *  This adjusts after each block, depending on how congested the network
     *  is.
     */
    readonly baseFeePerGas!: null | bigint;

    readonly #transactions: Array<string | TransactionResponse>;

    /**
     *  Create a new **Block** object.
     *
     *  This should generally not be necessary as the unless implementing a
     *  low-level library.
     */
    constructor(block: BlockParams, provider: Provider) {

        this.#transactions = block.transactions.map((tx) => {
            if (typeof(tx) !== "string") {
                return new TransactionResponse(tx, provider);
            }
            return tx;
        });

        defineProperties<Block>(this, {
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
    get transactions(): ReadonlyArray<string> {
        return this.#transactions.map((tx) => {
            if (typeof(tx) === "string") { return tx; }
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
    get prefetchedTransactions(): Array<TransactionResponse> {
        const txs = this.#transactions.slice();

        // Doesn't matter...
        if (txs.length === 0) { return [ ]; }

        // Make sure we prefetched the transactions
        assert(typeof(txs[0]) === "object", "transactions were not prefetched with block request", "UNSUPPORTED_OPERATION", {
            operation: "transactionResponses()"
        });

        return <Array<TransactionResponse>>txs;
    }

    /**
     *  Returns a JSON-friendly value.
     */
    toJSON(): any {
        const {
            baseFeePerGas, difficulty, extraData, gasLimit, gasUsed, hash,
            miner, prevRandao, nonce, number, parentHash, parentBeaconBlockRoot,
            stateRoot, receiptsRoot, timestamp, transactions
        } = this;

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

    [Symbol.iterator](): Iterator<string> {
        let index = 0;
        const txs = this.transactions;
        return {
            next: () => {
                if (index < this.length) {
                    return {
                        value: txs[index++], done: false
                    }
                }
                return { value: undefined, done: true };
            }
        };
    }

    /**
     *  The number of transactions in this block.
     */
    get length(): number { return this.#transactions.length; }

    /**
     *  The [[link-js-date]] this block was included at.
     */
    get date(): null | Date {
        if (this.timestamp == null) { return null; }
        return new Date(this.timestamp * 1000);
    }

    /**
     *  Get the transaction at %%indexe%% within this block.
     */
    async getTransaction(indexOrHash: number | string): Promise<TransactionResponse> {
        // Find the internal value by its index or hash
        let tx: string | TransactionResponse | undefined = undefined;
        if (typeof(indexOrHash) === "number") {
            tx = this.#transactions[indexOrHash];

        } else {
            const hash = indexOrHash.toLowerCase();
            for (const v of this.#transactions) {
                if (typeof(v) === "string") {
                    if (v !== hash) { continue; }
                    tx = v;
                    break;
                } else {
                    if (v.hash !== hash) { continue; }
                    tx = v;
                    break;
                }
            }
        }
        if (tx == null) { throw new Error("no such tx"); }

        if (typeof(tx) === "string") {
            return <TransactionResponse>(await this.provider.getTransaction(tx));
        } else {
            return tx;
        }
    }

    /**
     *  If a **Block** was fetched with a request to include the transactions
     *  this will allow synchronous access to those transactions.
     *
     *  If the transactions were not prefetched, this will throw.
     */
    getPrefetchedTransaction(indexOrHash: number | string): TransactionResponse {
        const txs = this.prefetchedTransactions;
        if (typeof(indexOrHash) === "number") {
            return txs[indexOrHash];
        }

        indexOrHash = indexOrHash.toLowerCase();
        for (const tx of txs) {
            if (tx.hash === indexOrHash) { return tx; }
        }

        assertArgument(false, "no matching transaction", "indexOrHash", indexOrHash);
    }

    /**
     *  Returns true if this block been mined. This provides a type guard
     *  for all properties on a [[MinedBlock]].
     */
    isMined(): this is MinedBlock { return !!this.hash; }

    /**
     *  Returns true if this block is an [[link-eip-2930]] block.
     */
    isLondon(): this is (Block & { baseFeePerGas: bigint }) {
        return !!this.baseFeePerGas;
    }

    /**
     *  @_ignore:
     */
    orphanedEvent(): OrphanFilter {
        if (!this.isMined()) { throw new Error(""); }
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
export class Log implements LogParams {

    /**
     *  The provider connected to the log used to fetch additional details
     *  if necessary.
     */
    readonly provider: Provider;

    /**
     *  The transaction hash of the transaction this log occurred in. Use the
     *  [[Log-getTransaction]] to get the [[TransactionResponse]].
     */
    readonly transactionHash!: string;

    /**
     *  The block hash of the block this log occurred in. Use the
     *  [[Log-getBlock]] to get the [[Block]].
     */
    readonly blockHash!: string;

    /**
     *  The block number of the block this log occurred in. It is preferred
     *  to use the [[Block-hash]] when fetching the related [[Block]],
     *  since in the case of an orphaned block, the block at that height may
     *  have changed.
     */
    readonly blockNumber!: number;

    /**
     *  If the **Log** represents a block that was removed due to an orphaned
     *  block, this will be true.
     *
     *  This can only happen within an orphan event listener.
     */
    readonly removed!: boolean;

    /**
     *  The address of the contract that emitted this log.
     */
    readonly address!: string;

    /**
     *  The data included in this log when it was emitted.
     */
    readonly data!: string;

    /**
     *  The indexed topics included in this log when it was emitted.
     *
     *  All topics are included in the bloom filters, so they can be
     *  efficiently filtered using the [[Provider-getLogs]] method.
     */
    readonly topics!: ReadonlyArray<string>;

    /**
     *  The index within the block this log occurred at. This is generally
     *  not useful to developers, but can be used with the various roots
     *  to proof inclusion within a block.
     */
    readonly index!: number;

    /**
     *  The index within the transaction of this log.
     */
    readonly transactionIndex!: number;

    /**
     *  @_ignore:
     */
    constructor(log: LogParams, provider: Provider) {
        this.provider = provider;

        const topics = Object.freeze(log.topics.slice());
        defineProperties<Log>(this, {
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
    toJSON(): any {
        const {
            address, blockHash, blockNumber, data, index,
            removed, topics, transactionHash, transactionIndex
        } = this;

        return {
            _type: "log",
            address, blockHash, blockNumber, data, index,
            removed, topics, transactionHash, transactionIndex
        };
    }

    /**
     *  Returns the block that this log occurred in.
     */
    async getBlock(): Promise<Block> {
        const block = await this.provider.getBlock(this.blockHash);
        assert(!!block, "failed to find transaction", "UNKNOWN_ERROR", { });
        return block;
    }

    /**
     *  Returns the transaction that this log occurred in.
     */
    async getTransaction(): Promise<TransactionResponse> {
        const tx = await this.provider.getTransaction(this.transactionHash);
        assert(!!tx, "failed to find transaction", "UNKNOWN_ERROR", { });
        return tx;
    }

    /**
     *  Returns the transaction receipt fot the transaction that this
     *  log occurred in.
     */
    async getTransactionReceipt(): Promise<TransactionReceipt> {
        const receipt = await this.provider.getTransactionReceipt(this.transactionHash);
        assert(!!receipt, "failed to find transaction receipt", "UNKNOWN_ERROR", { });
        return receipt;
    }

    /**
     *  @_ignore:
     */
    removedEvent(): OrphanFilter {
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
export class TransactionReceipt implements TransactionReceiptParams, Iterable<Log> {
    /**
     *  The provider connected to the log used to fetch additional details
     *  if necessary.
     */
    readonly provider!: Provider;

    /**
     *  The address the transaction was sent to.
     */
    readonly to!: null | string;

    /**
     *  The sender of the transaction.
     */
    readonly from!: string;

    /**
     *  The address of the contract if the transaction was directly
     *  responsible for deploying one.
     *
     *  This is non-null **only** if the ``to`` is empty and the ``data``
     *  was successfully executed as initcode.
     */
    readonly contractAddress!: null | string;

    /**
     *  The transaction hash.
     */
    readonly hash!: string;

    /**
     *  The index of this transaction within the block transactions.
     */
    readonly index!: number;

    /**
     *  The block hash of the [[Block]] this transaction was included in.
     */
    readonly blockHash!: string;

    /**
     *  The block number of the [[Block]] this transaction was included in.
     */
    readonly blockNumber!: number;

    /**
     *  The bloom filter bytes that represent all logs that occurred within
     *  this transaction. This is generally not useful for most developers,
     *  but can be used to validate the included logs.
     */
    readonly logsBloom!: string;

    /**
     *  The actual amount of gas used by this transaction.
     *
     *  When creating a transaction, the amount of gas that will be used can
     *  only be approximated, but the sender must pay the gas fee for the
     *  entire gas limit. After the transaction, the difference is refunded.
     */
    readonly gasUsed!: bigint;

    /**
     *  The gas used for BLObs. See [[link-eip-4844]].
     */
    readonly blobGasUsed!: null | bigint;

    /**
     *  The amount of gas used by all transactions within the block for this
     *  and all transactions with a lower ``index``.
     *
     *  This is generally not useful for developers but can be used to
     *  validate certain aspects of execution.
     */
    readonly cumulativeGasUsed!: bigint;

    /**
     *  The actual gas price used during execution.
     *
     *  Due to the complexity of [[link-eip-1559]] this value can only
     *  be caluclated after the transaction has been mined, snce the base
     *  fee is protocol-enforced.
     */
    readonly gasPrice!: bigint;

    /**
     *  The price paid per BLOB in gas. See [[link-eip-4844]].
     */
    readonly blobGasPrice!: null | bigint;

    /**
     *  The [[link-eip-2718]] transaction type.
     */
    readonly type!: number;
    //readonly byzantium!: boolean;

    /**
     *  The status of this transaction, indicating success (i.e. ``1``) or
     *  a revert (i.e. ``0``).
     *
     *  This is available in post-byzantium blocks, but some backends may
     *  backfill this value.
     */
    readonly status!: null | number;

    /**
     *  The root hash of this transaction.
     *
     *  This is no present and was only included in pre-byzantium blocks, but
     *  could be used to validate certain parts of the receipt.
     */
    readonly root!: null | string;

    readonly #logs: ReadonlyArray<Log>;

    /**
     *  @_ignore:
     */
    constructor(tx: TransactionReceiptParams, provider: Provider) {
        this.#logs = Object.freeze(tx.logs.map((log) => {
            return new Log(log, provider);
        }));

        let gasPrice = BN_0;
        if (tx.effectiveGasPrice != null) {
            gasPrice = tx.effectiveGasPrice;
        } else if (tx.gasPrice != null) {
            gasPrice = tx.gasPrice;
        }

        defineProperties<TransactionReceipt>(this, {
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
    get logs(): ReadonlyArray<Log> { return this.#logs; }

    /**
     *  Returns a JSON-compatible representation.
     */
    toJSON(): any {
        const {
            to, from, contractAddress, hash, index,
            blockHash, blockNumber, logsBloom,
            logs, //byzantium, 
            status, root
        } = this;

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
    get length(): number { return this.logs.length; }

    [Symbol.iterator](): Iterator<Log> {
        let index = 0;
        return {
            next: () => {
                if (index < this.length) {
                    return { value: this.logs[index++], done: false }
                }
                return { value: undefined, done: true };
            }
        };
    }

    /**
     *  The total fee for this transaction, in wei.
     */
    get fee(): bigint {
        return this.gasUsed * this.gasPrice;
    }

    /**
     *  Resolves to the block this transaction occurred in.
     */
    async getBlock(): Promise<Block> {
        const block = await this.provider.getBlock(this.blockHash);
        if (block == null) { throw new Error("TODO"); }
        return block;
    }

    /**
     *  Resolves to the transaction this transaction occurred in.
     */
    async getTransaction(): Promise<TransactionResponse> {
        const tx = await this.provider.getTransaction(this.hash);
        if (tx == null) { throw new Error("TODO"); }
        return tx;
    }

    /**
     *  Resolves to the return value of the execution of this transaction.
     *
     *  Support for this feature is limited, as it requires an archive node
     *  with the ``debug_`` or ``trace_`` API enabled.
     */
    async getResult(): Promise<string> {
        return <string>(await this.provider.getTransactionResult(this.hash));
    }

    /**
     *  Resolves to the number of confirmations this transaction has.
     */
    async confirmations(): Promise<number> {
        return (await this.provider.getBlockNumber()) - this.blockNumber + 1;
    }

    /**
     *  @_ignore:
     */
    removedEvent(): OrphanFilter {
        return createRemovedTransactionFilter(this);
    }

    /**
     *  @_ignore:
     */
    reorderedEvent(other?: TransactionResponse): OrphanFilter {
        assert(!other || other.isMined(), "unmined 'other' transction cannot be orphaned",
            "UNSUPPORTED_OPERATION", { operation: "reorderedEvent(other)" });
        return createReorderedTransactionFilter(this, other);
    }
}


//////////////////////
// Transaction Response

/**
 *  A **MinedTransactionResponse** is an interface representing a
 *  transaction which has been mined and allows for a type guard for its
 *  property values being defined.
 */
export interface MinedTransactionResponse extends TransactionResponse {
    /**
     *  The block number this transaction occurred in.
     */
    blockNumber: number;

    /**
     *  The block hash this transaction occurred in.
     */
    blockHash: string;

    /**
     *  The date this transaction occurred on.
     */
    date: Date;
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
export class TransactionResponse implements TransactionLike<string>, TransactionResponseParams {
    /**
     *  The provider this is connected to, which will influence how its
     *  methods will resolve its async inspection methods.
     */
    readonly provider: Provider;

    /**
     *  The block number of the block that this transaction was included in.
     *
     *  This is ``null`` for pending transactions.
     */
    readonly blockNumber: null | number;

    /**
     *  The blockHash of the block that this transaction was included in.
     *
     *  This is ``null`` for pending transactions.
     */
    readonly blockHash: null | string;

    /**
     *  The index within the block that this transaction resides at.
     */
    readonly index!: number;

    /**
     *  The transaction hash.
     */
    readonly hash!: string;

    /**
     *  The [[link-eip-2718]] transaction envelope type. This is
     *  ``0`` for legacy transactions types.
     */
    readonly type!: number;

    /**
     *  The receiver of this transaction.
     *
     *  If ``null``, then the transaction is an initcode transaction.
     *  This means the result of executing the [[data]] will be deployed
     *  as a new contract on chain (assuming it does not revert) and the
     *  address may be computed using [[getCreateAddress]].
     */
    readonly to!: null | string;

    /**
     *  The sender of this transaction. It is implicitly computed
     *  from the transaction pre-image hash (as the digest) and the
     *  [[signature]] using ecrecover.
     */
    readonly from!: string;

    /**
     *  The nonce, which is used to prevent replay attacks and offer
     *  a method to ensure transactions from a given sender are explicitly
     *  ordered.
     *
     *  When sending a transaction, this must be equal to the number of
     *  transactions ever sent by [[from]].
     */
    readonly nonce!: number;

    /**
     *  The maximum units of gas this transaction can consume. If execution
     *  exceeds this, the entries transaction is reverted and the sender
     *  is charged for the full amount, despite not state changes being made.
     */
    readonly gasLimit!: bigint;

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
    readonly gasPrice!: bigint;

    /**
     *  The maximum priority fee (per unit of gas) to allow a
     *  validator to charge the sender. This is inclusive of the
     *  [[maxFeeFeePerGas]].
     */
    readonly maxPriorityFeePerGas!: null | bigint;

    /**
     *  The maximum fee (per unit of gas) to allow this transaction
     *  to charge the sender.
     */
    readonly maxFeePerGas!: null | bigint;

    /**
     *  The [[link-eip-4844]] max fee per BLOb gas.
     */
    readonly maxFeePerBlobGas!: null | bigint;

    /**
     *  The data.
     */
    readonly data!: string;

    /**
     *  The value, in wei. Use [[formatEther]] to format this value
     *  as ether.
     */
    readonly value!: bigint;

    /**
     *  The chain ID.
     */
    readonly chainId!: bigint;

    /**
     *  The signature.
     */
    readonly signature!: Signature;

    /**
     *  The [[link-eip-2930]] access list for transaction types that
     *  support it, otherwise ``null``.
     */
    readonly accessList!: null | AccessList;

    /**
     *  The [[link-eip-4844]] BLOb versioned hashes.
     */
    readonly blobVersionedHashes!: null | Array<string>;

    /**
     *  The [[link-eip-7702]] authorizations (if any).
     */
    readonly authorizationList!: null | Array<Authorization>;

    #startBlock: number;

    /**
     *  @_ignore:
     */
    constructor(tx: TransactionResponseParams, provider: Provider) {
        this.provider = provider;

        this.blockNumber = (tx.blockNumber != null) ? tx.blockNumber: null;
        this.blockHash = (tx.blockHash != null) ? tx.blockHash: null;

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
        this.maxPriorityFeePerGas = (tx.maxPriorityFeePerGas != null) ? tx.maxPriorityFeePerGas: null;
        this.maxFeePerGas = (tx.maxFeePerGas != null) ? tx.maxFeePerGas: null;
        this.maxFeePerBlobGas = (tx.maxFeePerBlobGas != null) ? tx.maxFeePerBlobGas: null;

        this.chainId = tx.chainId;
        this.signature = tx.signature;

        this.accessList = (tx.accessList != null) ? tx.accessList: null;
        this.blobVersionedHashes = (tx.blobVersionedHashes != null) ? tx.blobVersionedHashes: null;

        this.authorizationList = (tx.authorizationList != null) ? tx.authorizationList: null;

        this.#startBlock = -1;
    }

    /**
     *  Returns a JSON-compatible representation of this transaction.
     */
    toJSON(): any {
        const {
            blockNumber, blockHash, index, hash, type, to, from, nonce,
            data, signature, accessList, blobVersionedHashes
        } = this;

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
    async getBlock(): Promise<null | Block> {
        let blockNumber = this.blockNumber;
        if (blockNumber == null) {
            const tx = await this.getTransaction();
            if (tx) { blockNumber = tx.blockNumber; }
        }
        if (blockNumber == null) { return null; }
        const block = this.provider.getBlock(blockNumber);
        if (block == null) { throw new Error("TODO"); }
        return block;
    }

    /**
     *  Resolves to this transaction being re-requested from the
     *  provider. This can be used if you have an unmined transaction
     *  and wish to get an up-to-date populated instance.
     */
    async getTransaction(): Promise<null | TransactionResponse> {
        return this.provider.getTransaction(this.hash);
    }

    /**
     *  Resolve to the number of confirmations this transaction has.
     */
    async confirmations(): Promise<number> {
        if (this.blockNumber == null) {
            const { tx, blockNumber } = await resolveProperties({
                tx: this.getTransaction(),
                blockNumber: this.provider.getBlockNumber()
            });

            // Not mined yet...
            if (tx == null || tx.blockNumber == null) { return 0; }

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
    async wait(_confirms?: number, _timeout?: number): Promise<null | TransactionReceipt> {
        const confirms = (_confirms == null) ? 1: _confirms;
        const timeout = (_timeout == null) ? 0: _timeout;

        let startBlock = this.#startBlock
        let nextScan = -1;
        let stopScanning = (startBlock === -1) ? true: false;
        const checkReplacement = async () => {
            // Get the current transaction count for this sender
            if (stopScanning) { return null; }
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
            if (stopScanning) { return null; }
            const mined = await this.getTransaction();
            if (mined && mined.blockNumber != null) { return; }

            // We were replaced; start scanning for that transaction

            // Starting to scan; look back a few extra blocks for safety
            if (nextScan === -1) {
                nextScan = startBlock - 3;
                if (nextScan < this.#startBlock) { nextScan = this.#startBlock; }
            }

            while (nextScan <= blockNumber) {
                // Get the next block to scan
                if (stopScanning) { return null; }
                const block = await this.provider.getBlock(nextScan, true);

                // This should not happen; but we'll try again shortly
                if (block == null) { return; }

                // We were mined; no replacement
                for (const hash of block) {
                    if (hash === this.hash) { return; }
                }

                // Search for the transaction that replaced us
                for (let i = 0; i < block.length; i++) {
                    const tx: TransactionResponse = await block.getTransaction(i);

                    if (tx.from === this.from && tx.nonce === this.nonce) {
                        // Get the receipt
                        if (stopScanning) { return null; }
                        const receipt = await this.provider.getTransactionReceipt(tx.hash);

                        // This should not happen; but we'll try again shortly
                        if (receipt == null) { return; }

                        // We will retry this on the next block (this case could be optimized)
                        if ((blockNumber - receipt.blockNumber + 1) < confirms) { return; }

                        // The reason we were replaced
                        let reason: "replaced" | "repriced" | "cancelled" = "replaced";
                        if (tx.data === this.data && tx.to === this.to && tx.value === this.value) {
                            reason = "repriced";
                        } else  if (tx.data === "0x" && tx.from === tx.to && tx.value === BN_0) {
                            reason = "cancelled"
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

        const checkReceipt = (receipt: null | TransactionReceipt) => {
            if (receipt == null || receipt.status !== 0) { return receipt; }
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

        if (confirms === 0) { return checkReceipt(receipt); }

        if (receipt) {
            if (confirms === 1 || (await receipt.confirmations()) >= confirms) {
                return checkReceipt(receipt);
            }

        } else {
            // Check for a replacement; throws if a replacement was found
            await checkReplacement();

            // Allow null only when the confirms is 0
            if (confirms === 0) { return null; }
        }

        const waiter = new Promise((resolve, reject) => {
            // List of things to cancel when we have a result (one way or the other)
            const cancellers: Array<() => void> = [ ];
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

            const txListener = async (receipt: TransactionReceipt) => {
                // Done; return it!
                if ((await receipt.confirmations()) >= confirms) {
                    cancel();
                    try {
                        resolve(checkReceipt(receipt));
                    } catch (error) { reject(error); }
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

                    } catch (error) {
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

        return await <Promise<TransactionReceipt>>waiter;
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
    isMined(): this is MinedTransactionResponse {
        return (this.blockHash != null);
    }

    /**
     *  Returns true if the transaction is a legacy (i.e. ``type == 0``)
     *  transaction.
     *
     *  This provides a Type Guard that this transaction will have
     *  the ``null``-ness for hardfork-specific properties set correctly.
     */
    isLegacy(): this is (TransactionResponse & { accessList: null, maxFeePerGas: null, maxPriorityFeePerGas: null }) {
        return (this.type === 0)
    }

    /**
     *  Returns true if the transaction is a Berlin (i.e. ``type == 1``)
     *  transaction. See [[link-eip-2070]].
     *
     *  This provides a Type Guard that this transaction will have
     *  the ``null``-ness for hardfork-specific properties set correctly.
     */
    isBerlin(): this is (TransactionResponse & { accessList: AccessList, maxFeePerGas: null, maxPriorityFeePerGas: null }) {
        return (this.type === 1);
    }

    /**
     *  Returns true if the transaction is a London (i.e. ``type == 2``)
     *  transaction. See [[link-eip-1559]].
     *
     *  This provides a Type Guard that this transaction will have
     *  the ``null``-ness for hardfork-specific properties set correctly.
     */
    isLondon(): this is (TransactionResponse & { accessList: AccessList, maxFeePerGas: bigint, maxPriorityFeePerGas: bigint }){
        return (this.type === 2);
    }

    /**
     *  Returns true if hte transaction is a Cancun (i.e. ``type == 3``)
     *  transaction. See [[link-eip-4844]].
     */
    isCancun(): this is (TransactionResponse & { accessList: AccessList, maxFeePerGas: bigint, maxPriorityFeePerGas: bigint, maxFeePerBlobGas: bigint, blobVersionedHashes: Array<string> }){
        return (this.type === 3);
    }

    /**
     *  Returns a filter which can be used to listen for orphan events
     *  that evict this transaction.
     */
    removedEvent(): OrphanFilter {
        assert(this.isMined(), "unmined transaction canot be orphaned",
            "UNSUPPORTED_OPERATION", { operation: "removeEvent()" });
        return createRemovedTransactionFilter(this);
    }

    /**
     *  Returns a filter which can be used to listen for orphan events
     *  that re-order this event against %%other%%.
     */
    reorderedEvent(other?: TransactionResponse): OrphanFilter {
        assert(this.isMined(), "unmined transaction canot be orphaned",
            "UNSUPPORTED_OPERATION", { operation: "removeEvent()" });

        assert(!other || other.isMined(), "unmined 'other' transaction canot be orphaned",
            "UNSUPPORTED_OPERATION", { operation: "removeEvent()" });

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
    replaceableTransaction(startBlock: number): TransactionResponse {
        assertArgument(Number.isInteger(startBlock) && startBlock >= 0, "invalid startBlock", "startBlock", startBlock);
        const tx = new TransactionResponse(this, this.provider);
        tx.#startBlock = startBlock;
        return tx;
    }
}


//////////////////////
// OrphanFilter

/**
 *  An Orphan Filter allows detecting when an orphan block has
 *  resulted in dropping a block or transaction or has resulted
 *  in transactions changing order.
 *
 *  Not currently fully supported.
 */
export type OrphanFilter = {
    orphan: "drop-block",
    hash: string,
    number: number
} | {
    orphan: "drop-transaction",
    tx: { hash: string, blockHash: string, blockNumber: number },
    other?: { hash: string, blockHash: string, blockNumber: number }
} | {
    orphan: "reorder-transaction",
    tx: { hash: string, blockHash: string, blockNumber: number },
    other?: { hash: string, blockHash: string, blockNumber: number }
} | {
    orphan: "drop-log",
    log: {
        transactionHash: string,
        blockHash: string,
        blockNumber: number,
        address: string,
        data: string,
        topics: ReadonlyArray<string>,
        index: number
    }
};

function createOrphanedBlockFilter(block: { hash: string, number: number }): OrphanFilter {
    return { orphan: "drop-block", hash: block.hash, number: block.number };
}

function createReorderedTransactionFilter(tx: { hash: string, blockHash: string, blockNumber: number }, other?: { hash: string, blockHash: string, blockNumber: number }): OrphanFilter {
    return { orphan: "reorder-transaction", tx, other };
}

function createRemovedTransactionFilter(tx: { hash: string, blockHash: string, blockNumber: number }): OrphanFilter {
    return { orphan: "drop-transaction", tx };
}

function createRemovedLogFilter(log: { blockHash: string, transactionHash: string, blockNumber: number, address: string, data: string, topics: ReadonlyArray<string>, index: number }): OrphanFilter {
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

//////////////////////
// EventFilter

/**
 *  A **TopicFilter** provides a struture to define bloom-filter
 *  queries.
 *
 *  Each field that is ``null`` matches **any** value, a field that is
 *  a ``string`` must match exactly that value and ``array`` is
 *  effectively an ``OR``-ed set, where any one of those values must
 *  match.
 */
export type TopicFilter = Array<null | string | Array<string>>;

// @TODO:
//export type DeferableTopicFilter = Array<null | string | Promise<string> | Array<string | Promise<string>>>;

/**
 *  An **EventFilter** allows efficiently filtering logs (also known as
 *  events) using bloom filters included within blocks.
 */
export interface EventFilter {
    address?: AddressLike | Array<AddressLike>;
    topics?: TopicFilter;
}

/**
 *  A **Filter** allows searching a specific range of blocks for mathcing
 *  logs.
 */
export interface Filter extends EventFilter {

    /**
     *  The start block for the filter (inclusive).
     */
    fromBlock?: BlockTag;

    /**
     *  The end block for the filter (inclusive).
     */
    toBlock?: BlockTag;
}

/**
 *  A **FilterByBlockHash** allows searching a specific block for mathcing
 *  logs.
 */
export interface FilterByBlockHash extends EventFilter {
    /**
     *  The blockhash of the specific block for the filter.
     */
    blockHash?: string;
}


//////////////////////
// ProviderEvent

/**
 *  A **ProviderEvent** provides the types of events that can be subscribed
 *  to on a [[Provider]].
 *
 *  Each provider may include additional possible events it supports, but
 *  the most commonly supported are:
 *
 *  **``"block"``** - calls the listener with the current block number on each
 *  new block.
 *
 *  **``"error"``** - calls the listener on each async error that occurs during
 *  the event loop, with the error.
 *
 *  **``"debug"``** - calls the listener on debug events, which can be used to
 *  troubleshoot network errors, provider problems, etc.
 *
 *  **``transaction hash``** - calls the listener on each block after the
 *  transaction has been mined; generally ``.once`` is more appropriate for
 *  this event.
 *
 *  **``Array``** - calls the listener on each log that matches the filter.
 *
 *  [[EventFilter]] - calls the listener with each matching log
 */
export type ProviderEvent = string | Array<string | Array<string>> | EventFilter | OrphanFilter;


//////////////////////
// Provider

/**
 *  A **Provider** is the primary method to interact with the read-only
 *  content on Ethereum.
 *
 *  It allows access to details about accounts, blocks and transactions
 *  and the ability to query event logs and simulate contract execution.
 *
 *  Account data includes the [balance](getBalance),
 *  [transaction count](getTransactionCount), [code](getCode) and
 *  [state trie storage](getStorage).
 *
 *  Simulating execution can be used to [call](call),
 *  [estimate gas](estimateGas) and
 *  [get transaction results](getTransactionResult).
 *
 *  The [[broadcastTransaction]] is the only method which allows updating
 *  the blockchain, but it is usually accessed by a [[Signer]], since a
 *  private key must be used to sign the transaction before it can be
 *  broadcast.
 */
export interface Provider extends ContractRunner, EventEmitterable<ProviderEvent>, NameResolver {

    /**
     *  The provider iteself.
     *
     *  This is part of the necessary API for executing a contract, as
     *  it provides a common property on any [[ContractRunner]] that
     *  can be used to access the read-only portion of the runner.
     */
    provider: this;

    /**
     *  Shutdown any resources this provider is using. No additional
     *  calls should be made to this provider after calling this.
     */
    destroy(): void;

    ////////////////////
    // State

    /**
     *  Get the current block number.
     */
    getBlockNumber(): Promise<number>;

    /**
     *  Get the connected [[Network]].
     */
    getNetwork(): Promise<Network>;

    /**
     *  Get the best guess at the recommended [[FeeData]].
     */
    getFeeData(): Promise<FeeData>;


    ////////////////////
    // Account

    /**
     *  Get the account balance (in wei) of %%address%%. If %%blockTag%%
     *  is specified and the node supports archive access for that
     *  %%blockTag%%, the balance is as of that [[BlockTag]].
     *
     *  @note On nodes without archive access enabled, the %%blockTag%% may be
     *        **silently ignored** by the node, which may cause issues if relied on.
     */
    getBalance(address: AddressLike, blockTag?: BlockTag): Promise<bigint>;

    /**
     *  Get the number of transactions ever sent for %%address%%, which
     *  is used as the ``nonce`` when sending a transaction. If
     *  %%blockTag%% is specified and the node supports archive access
     *  for that %%blockTag%%, the transaction count is as of that
     *  [[BlockTag]].
     *
     *  @note On nodes without archive access enabled, the %%blockTag%% may be
     *        **silently ignored** by the node, which may cause issues if relied on.
     */
    getTransactionCount(address: AddressLike, blockTag?: BlockTag): Promise<number>;

    /**
     *  Get the bytecode for %%address%%.
     *
     *  @note On nodes without archive access enabled, the %%blockTag%% may be
     *        **silently ignored** by the node, which may cause issues if relied on.
     */
    getCode(address: AddressLike, blockTag?: BlockTag): Promise<string>

    /**
     *  Get the storage slot value for %%address%% at slot %%position%%.
     *
     *  @note On nodes without archive access enabled, the %%blockTag%% may be
     *        **silently ignored** by the node, which may cause issues if relied on.
     */
    getStorage(address: AddressLike, position: BigNumberish, blockTag?: BlockTag): Promise<string>


    ////////////////////
    // Execution

    /**
     *  Estimates the amount of gas required to execute %%tx%%.
     */
    estimateGas(tx: TransactionRequest): Promise<bigint>;

    /**
     *  Simulate the execution of %%tx%%. If the call reverts, it will
     *  throw a [[CallExceptionError]] which includes the revert data.
     */
    call(tx: TransactionRequest): Promise<string>

    /**
     *  Broadcasts the %%signedTx%% to the network, adding it to the
     *  memory pool of any node for which the transaction meets the
     *  rebroadcast requirements.
     */
    broadcastTransaction(signedTx: string): Promise<TransactionResponse>;


    ////////////////////
    // Queries

    /**
     *  Resolves to the block for %%blockHashOrBlockTag%%.
     *
     *  If %%prefetchTxs%%, and the backend supports including transactions
     *  with block requests, all transactions will be included and the
     *  [[Block]] object will not need to make remote calls for getting
     *  transactions.
     */
    getBlock(blockHashOrBlockTag: BlockTag | string, prefetchTxs?: boolean): Promise<null | Block>;

    /**
     *  Resolves to the transaction for %%hash%%.
     *
     *  If the transaction is unknown or on pruning nodes which
     *  discard old transactions this resolves to ``null``.
     */
    getTransaction(hash: string): Promise<null | TransactionResponse>;

    /**
     *  Resolves to the transaction receipt for %%hash%%, if mined.
     *
     *  If the transaction has not been mined, is unknown or on
     *  pruning nodes which discard old transactions this resolves to
     *  ``null``.
     */
    getTransactionReceipt(hash: string): Promise<null | TransactionReceipt>;

    /**
     *  Resolves to the result returned by the executions of %%hash%%.
     *
     *  This is only supported on nodes with archive access and with
     *  the necessary debug APIs enabled.
     */
    getTransactionResult(hash: string): Promise<null | string>;


    ////////////////////
    // Bloom-filter Queries

    /**
     *  Resolves to the list of Logs that match %%filter%%
     */
    getLogs(filter: Filter | FilterByBlockHash): Promise<Array<Log>>;


    ////////////////////
    // ENS

    /**
     *  Resolves to the address configured for the %%ensName%% or
     *  ``null`` if unconfigured.
     */
    resolveName(ensName: string): Promise<null | string>;

    /**
     *  Resolves to the ENS name associated for the %%address%% or
     *  ``null`` if the //primary name// is not configured.
     *
     *  Users must perform additional steps to configure a //primary name//,
     *  which is not currently common.
     */
    lookupAddress(address: string): Promise<null | string>;

    /**
     *  Waits until the transaction %%hash%% is mined and has %%confirms%%
     *  confirmations.
     */
    waitForTransaction(hash: string, confirms?: number, timeout?: number): Promise<null | TransactionReceipt>;

    /**
     *  Resolves to the block at %%blockTag%% once it has been mined.
     *
     *  This can be useful for waiting some number of blocks by using
     *  the ``currentBlockNumber + N``.
     */
    waitForBlock(blockTag?: BlockTag): Promise<Block>;
}
