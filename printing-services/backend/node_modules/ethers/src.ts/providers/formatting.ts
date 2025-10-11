/**
 *  About provider formatting?
 *
 *  @_section: api/providers/formatting:Formatting  [provider-formatting]
 */

import type { Signature } from "../crypto/index.js";
import type { Authorization, AccessList } from "../transaction/index.js";


//////////////////////
// Block

/**
 *  a **BlockParams** encodes the minimal required properties for a
 *  formatted block.
 */
export interface BlockParams {
    /**
     *  The block hash.
     */
    hash?: null | string;

    /**
     *  The block number.
     */
    number: number;

    /**
     *  The timestamp for this block, which is the number of seconds
     *  since epoch that this block was included.
     */
    timestamp: number;

    /**
     *  The hash of the previous block in the blockchain. The genesis block
     *  has the parentHash of the [[ZeroHash]].
     */
    parentHash: string;

    /**
     *  The hash tree root of the parent beacon block for the given
     *  execution block. See [[link-eip-4788]].
     */
    parentBeaconBlockRoot?: null | string;

    /**
     *  A random sequence provided during the mining process for
     *  proof-of-work networks.
     */
    nonce: string;

    /**
     *  For proof-of-work networks, the difficulty target is used to
     *  adjust the difficulty in mining to ensure an expected block rate.
     */
    difficulty: bigint;

    /**
     *  The maximum amount of gas a block can consume.
     */
    gasLimit: bigint;

    /**
     *  The amount of gas a block consumed.
     */
    gasUsed: bigint;

    /**
     *  The total amount of BLOb gas consumed by transactions within
     *  the block. See [[link-eip4844].
     */
    blobGasUsed?: null | bigint;

    /**
     *  The running total of BLOb gas consumed in excess of the target
     *  prior to the block. See [[link-eip-4844]].
     */
    excessBlobGas?: null | bigint;

    /**
     *  The miner (or author) of a block.
     */
    miner: string;

    /**
     *  The latest RANDAO mix of the post beacon state of
     *  the previous block.
     */
    prevRandao?: null | string;

    /**
     *  Additional data the miner choose to include.
     */
    extraData: string;

    /**
     *  The protocol-defined base fee per gas in an [[link-eip-1559]]
     *  block.
     */
    baseFeePerGas: null | bigint;

    /**
     *  The root hash for the global state after applying changes
     *  in this block.
     */
    stateRoot?: null | string;

    /**
     *  The hash of the transaction receipts trie.
     */
    receiptsRoot?: null | string;

    /**
     *  The list of transactions in the block.
     */
    transactions: ReadonlyArray<string | TransactionResponseParams>;
};


//////////////////////
// Log

/**
 *  a **LogParams** encodes the minimal required properties for a
 *  formatted log.
 */
export interface LogParams {
    /**
     *  The transaction hash for the transaxction the log occurred in.
     */
    transactionHash: string;

    /**
     *  The block hash of the block that included the transaction for this
     *  log.
     */
    blockHash: string;

    /**
     *  The block number of the block that included the transaction for this
     *  log.
     */
    blockNumber: number;

    /**
     *  Whether this log was removed due to the transaction it was included
     *  in being removed dur to an orphaned block.
     */
    removed: boolean;

    /**
     *  The address of the contract that emitted this log.
     */
    address: string;

    /**
     *  The data emitted with this log.
     */
    data: string;

    /**
     *  The topics emitted with this log.
     */
    topics: ReadonlyArray<string>;

    /**
     *  The index of this log.
     */
    index: number;

    /**
     *  The transaction index of this log.
     */
    transactionIndex: number;
}


//////////////////////
// Transaction Receipt

/**
 *  a **TransactionReceiptParams** encodes the minimal required properties
 *  for a formatted transaction receipt.
 */
export interface TransactionReceiptParams {
    /**
     *  The target of the transaction. If null, the transaction was trying
     *  to deploy a transaction with the ``data`` as the initi=code.
     */
    to: null | string;

    /**
     *  The sender of the transaction.
     */
    from: string;

    /**
     *  If the transaction was directly deploying a contract, the [[to]]
     *  will be null, the ``data`` will be initcode and if successful, this
     *  will be the address of the contract deployed.
     */
    contractAddress: null | string;

    /**
     *  The transaction hash.
     */
    hash: string;

    /**
     *  The transaction index.
     */
    index: number;

    /**
     *  The block hash of the block that included this transaction.
     */
    blockHash: string;

    /**
     *  The block number of the block that included this transaction.
     */
    blockNumber: number;

    /**
     *  The bloom filter for the logs emitted during execution of this
     *  transaction.
     */
    logsBloom: string;

    /**
     *  The logs emitted during the execution of this transaction.
     */
    logs: ReadonlyArray<LogParams>;

    /**
     *  The amount of gas consumed executing this transaciton.
     */
    gasUsed: bigint;

    /**
     *  The amount of BLOb gas used. See [[link-eip-4844]].
     */
    blobGasUsed?: null | bigint;

    /**
     *  The total amount of gas consumed during the entire block up to
     *  and including this transaction.
     */
    cumulativeGasUsed: bigint;

    /**
     *  The actual gas price per gas charged for this transaction.
     */
    gasPrice?: null | bigint;

    /**
     *  The actual BLOb gas price that was charged. See [[link-eip-4844]].
     */
    blobGasPrice?: null | bigint;

    /**
     *  The actual gas price per gas charged for this transaction.
     */
    effectiveGasPrice?: null | bigint;

    /**
     *  The [[link-eip-2718]] envelope type.
     */
    type: number;
    //byzantium: boolean;

    /**
     *  The status of the transaction execution. If ``1`` then the
     *  the transaction returned success, if ``0`` then the transaction
     *  was reverted. For pre-byzantium blocks, this is usually null, but
     *  some nodes may have backfilled this data.
     */
    status: null | number;

    /**
     *  The root of this transaction in a pre-bazatium block. In
     *  post-byzantium blocks this is null.
     */
    root: null | string;

}

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



//////////////////////
// Transaction Response

/**
 *  a **TransactionResponseParams** encodes the minimal required properties
 *  for a formatted transaction response.
 */
export interface TransactionResponseParams {
    /**
     *  The block number of the block that included this transaction.
     */
    blockNumber: null | number;

    /**
     *  The block hash of the block that included this transaction.
     */
    blockHash: null | string;

    /**
     *  The transaction hash.
     */
    hash: string;

    /**
     *  The transaction index.
     */
    index: number;

    /**
     *  The [[link-eip-2718]] transaction type.
     */
    type: number;

    /**
     *  The target of the transaction. If ``null``, the ``data`` is initcode
     *  and this transaction is a deployment transaction.
     */
    to: null | string;

    /**
     *  The sender of the transaction.
     */
    from: string;

    /**
     *  The nonce of the transaction, used for replay protection.
     */
    nonce: number;

    /**
     *  The maximum amount of gas this transaction is authorized to consume.
     */
    gasLimit: bigint;

    /**
     *  For legacy transactions, this is the gas price per gas to pay.
     */
    gasPrice: bigint;

    /**
     *  For [[link-eip-1559]] transactions, this is the maximum priority
     *  fee to allow a producer to claim.
     */
    maxPriorityFeePerGas: null | bigint;

    /**
     *  For [[link-eip-1559]] transactions, this is the maximum fee that
     *  will be paid.
     */
    maxFeePerGas: null | bigint;

    /**
     *  For [[link-eip-4844]] transactions, this is the maximum fee that
     *  will be paid per BLOb.
     */
    maxFeePerBlobGas?: null | bigint;

    /**
     *  The transaction data.
     */
    data: string;

    /**
     *  The transaction value (in wei).
     */
    value: bigint;

    /**
     *  The chain ID this transaction is valid on.
     */
    chainId: bigint;

    /**
     *  The signature of the transaction.
     */
    signature: Signature;

    /**
     *  The transaction access list.
     */
    accessList: null | AccessList;

    /**
     *  The [[link-eip-4844]] BLOb versioned hashes.
     */
    blobVersionedHashes?: null | Array<string>;  // @TODO: drop the "?"? (v7)

    /**
     *  The [[link-eip-7702]] authorizations (if any).
     */
    authorizationList: null | Array<Authorization>;
};


