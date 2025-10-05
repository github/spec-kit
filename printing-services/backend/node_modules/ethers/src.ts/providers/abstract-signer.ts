/**
 *  Generally the [[Wallet]] and [[JsonRpcSigner]] and their sub-classes
 *  are sufficent for most developers, but this is provided to
 *  fascilitate more complex Signers.
 *
 *  @_section: api/providers/abstract-signer: Subclassing Signer [abstract-signer]
 */
import { resolveAddress } from "../address/index.js";
import { Transaction } from "../transaction/index.js";
import {
    defineProperties, getBigInt, resolveProperties,
    assert, assertArgument
} from "../utils/index.js";

import { copyRequest } from "./provider.js";

import type {
    AuthorizationRequest, TypedDataDomain, TypedDataField
} from "../hash/index.js";
import type { Authorization, TransactionLike } from "../transaction/index.js";

import type {
    BlockTag, Provider, TransactionRequest, TransactionResponse
} from "./provider.js";
import type { Signer } from "./signer.js";

function checkProvider(signer: AbstractSigner, operation: string): Provider {
    if (signer.provider) { return signer.provider; }
    assert(false, "missing provider", "UNSUPPORTED_OPERATION", { operation });
}

async function populate(signer: AbstractSigner, tx: TransactionRequest): Promise<TransactionLike<string>> {
    let pop: any = copyRequest(tx);

    if (pop.to != null) { pop.to = resolveAddress(pop.to, signer); }

    if (pop.from != null) {
        const from = pop.from;
        pop.from = Promise.all([
            signer.getAddress(),
            resolveAddress(from, signer)
        ]).then(([ address, from ]) => {
            assertArgument(address.toLowerCase() === from.toLowerCase(),
                "transaction from mismatch", "tx.from", from);
            return address;
        });
    } else {
        pop.from = signer.getAddress();
    }

    return await resolveProperties(pop);
}


/**
 *  An **AbstractSigner** includes most of teh functionality required
 *  to get a [[Signer]] working as expected, but requires a few
 *  Signer-specific methods be overridden.
 *
 */
export abstract class AbstractSigner<P extends null | Provider = null | Provider> implements Signer {
    /**
     *  The provider this signer is connected to.
     */
    readonly provider!: P;

    /**
     *  Creates a new Signer connected to %%provider%%.
     */
    constructor(provider?: P) {
        defineProperties<AbstractSigner>(this, { provider: (provider || null) });
    }

    /**
     *  Resolves to the Signer address.
     */
    abstract getAddress(): Promise<string>;

    /**
     *  Returns the signer connected to %%provider%%.
     *
     *  This may throw, for example, a Signer connected over a Socket or
     *  to a specific instance of a node may not be transferrable.
     */
    abstract connect(provider: null | Provider): Signer;

    async getNonce(blockTag?: BlockTag): Promise<number> {
        return checkProvider(this, "getTransactionCount").getTransactionCount(await this.getAddress(), blockTag);
    }

    async populateCall(tx: TransactionRequest): Promise<TransactionLike<string>> {
        const pop = await populate(this, tx);
        return pop;
    }

    async populateTransaction(tx: TransactionRequest): Promise<TransactionLike<string>> {
        const provider = checkProvider(this, "populateTransaction");

        const pop = await populate(this, tx);

        if (pop.nonce == null) {
            pop.nonce = await this.getNonce("pending");
        }

        if (pop.gasLimit == null) {
            pop.gasLimit = await this.estimateGas(pop);
        }

        // Populate the chain ID
        const network = await (<Provider>(this.provider)).getNetwork();
        if (pop.chainId != null) {
            const chainId = getBigInt(pop.chainId);
            assertArgument(chainId === network.chainId, "transaction chainId mismatch", "tx.chainId", tx.chainId);
        } else {
            pop.chainId = network.chainId;
        }

        // Do not allow mixing pre-eip-1559 and eip-1559 properties
        const hasEip1559 = (pop.maxFeePerGas != null || pop.maxPriorityFeePerGas != null);
        if (pop.gasPrice != null && (pop.type === 2 || hasEip1559)) {
            assertArgument(false, "eip-1559 transaction do not support gasPrice", "tx", tx);
        } else if ((pop.type === 0 || pop.type === 1) && hasEip1559) {
            assertArgument(false, "pre-eip-1559 transaction do not support maxFeePerGas/maxPriorityFeePerGas", "tx", tx);
        }

        if ((pop.type === 2 || pop.type == null) && (pop.maxFeePerGas != null && pop.maxPriorityFeePerGas != null)) {
            // Fully-formed EIP-1559 transaction (skip getFeeData)
            pop.type = 2;

        } else if (pop.type === 0 || pop.type === 1) {
            // Explicit Legacy or EIP-2930 transaction

            // We need to get fee data to determine things
            const feeData = await provider.getFeeData();

            assert(feeData.gasPrice != null, "network does not support gasPrice", "UNSUPPORTED_OPERATION", {
                operation: "getGasPrice" });

            // Populate missing gasPrice
            if (pop.gasPrice == null) { pop.gasPrice = feeData.gasPrice; }

        } else {

            // We need to get fee data to determine things
            const feeData = await provider.getFeeData();

            if (pop.type == null) {
                // We need to auto-detect the intended type of this transaction...

                if (feeData.maxFeePerGas != null && feeData.maxPriorityFeePerGas != null) {
                    // The network supports EIP-1559!

                    // Upgrade transaction from null to eip-1559
                    if (pop.authorizationList && pop.authorizationList.length) {
                        pop.type = 4;
                    } else {
                        pop.type = 2;
                    }

                    if (pop.gasPrice != null) {
                        // Using legacy gasPrice property on an eip-1559 network,
                        // so use gasPrice as both fee properties
                        const gasPrice = pop.gasPrice;
                        delete pop.gasPrice;
                        pop.maxFeePerGas = gasPrice;
                        pop.maxPriorityFeePerGas = gasPrice;

                    } else {
                        // Populate missing fee data

                        if (pop.maxFeePerGas == null) {
                            pop.maxFeePerGas = feeData.maxFeePerGas;
                        }

                        if (pop.maxPriorityFeePerGas == null) {
                            pop.maxPriorityFeePerGas = feeData.maxPriorityFeePerGas;
                        }
                    }

                } else if (feeData.gasPrice != null) {
                    // Network doesn't support EIP-1559...

                    // ...but they are trying to use EIP-1559 properties
                    assert(!hasEip1559, "network does not support EIP-1559", "UNSUPPORTED_OPERATION", {
                            operation: "populateTransaction" });

                    // Populate missing fee data
                    if (pop.gasPrice == null) {
                        pop.gasPrice = feeData.gasPrice;
                    }

                    // Explicitly set untyped transaction to legacy
                    // @TODO: Maybe this shold allow type 1?
                    pop.type = 0;

               } else {
                    // getFeeData has failed us.
                    assert(false, "failed to get consistent fee data", "UNSUPPORTED_OPERATION", {
                        operation: "signer.getFeeData" });
                }

            } else if (pop.type === 2 || pop.type === 3 || pop.type === 4) {
                // Explicitly using EIP-1559 or EIP-4844

                // Populate missing fee data
                if (pop.maxFeePerGas == null) {
                    pop.maxFeePerGas = feeData.maxFeePerGas;
                }

                if (pop.maxPriorityFeePerGas == null) {
                    pop.maxPriorityFeePerGas = feeData.maxPriorityFeePerGas;
                }
            }
        }

//@TOOD: Don't await all over the place; save them up for
// the end for better batching
        return await resolveProperties(pop);
    }

    async populateAuthorization(_auth: AuthorizationRequest): Promise<AuthorizationRequest> {
        const auth = Object.assign({ }, _auth);

        // Add a chain ID if not explicitly set to 0
        if (auth.chainId == null) {
            auth.chainId = (await checkProvider(this, "getNetwork").getNetwork()).chainId;
        }

        // @TODO: Take chain ID into account when populating noce?

        if (auth.nonce == null) { auth.nonce = await this.getNonce(); }

        return auth;
    }

    async estimateGas(tx: TransactionRequest): Promise<bigint> {
        return checkProvider(this, "estimateGas").estimateGas(await this.populateCall(tx));
    }

    async call(tx: TransactionRequest): Promise<string> {
        return checkProvider(this, "call").call(await this.populateCall(tx));
    }

    async resolveName(name: string): Promise<null | string> {
        const provider = checkProvider(this, "resolveName");
        return await provider.resolveName(name);
    }

    async sendTransaction(tx: TransactionRequest): Promise<TransactionResponse> {
        const provider = checkProvider(this, "sendTransaction");

        const pop = await this.populateTransaction(tx);
        delete pop.from;
        const txObj = Transaction.from(pop);
        return await provider.broadcastTransaction(await this.signTransaction(txObj));
    }

    // @TODO: in v7 move this to be abstract
    authorize(authorization: AuthorizationRequest): Promise<Authorization> {
        assert(false, "authorization not implemented for this signer",
          "UNSUPPORTED_OPERATION", { operation: "authorize" });
    }

    abstract signTransaction(tx: TransactionRequest): Promise<string>;
    abstract signMessage(message: string | Uint8Array): Promise<string>;
    abstract signTypedData(domain: TypedDataDomain, types: Record<string, Array<TypedDataField>>, value: Record<string, any>): Promise<string>;
}

/**
 *  A **VoidSigner** is a class deisgned to allow an address to be used
 *  in any API which accepts a Signer, but for which there are no
 *  credentials available to perform any actual signing.
 *
 *  This for example allow impersonating an account for the purpose of
 *  static calls or estimating gas, but does not allow sending transactions.
 */
export class VoidSigner extends AbstractSigner {
    /**
     *  The signer address.
     */
    readonly address!: string;

    /**
     *  Creates a new **VoidSigner** with %%address%% attached to
     *  %%provider%%.
     */
    constructor(address: string, provider?: null | Provider) {
        super(provider);
        defineProperties<VoidSigner>(this, { address });
    }

    async getAddress(): Promise<string> { return this.address; }

    connect(provider: null | Provider): VoidSigner {
        return new VoidSigner(this.address, provider);
    }

    #throwUnsupported(suffix: string, operation: string): never {
        assert(false, `VoidSigner cannot sign ${ suffix }`, "UNSUPPORTED_OPERATION", { operation });
    }

    async signTransaction(tx: TransactionRequest): Promise<string> {
        this.#throwUnsupported("transactions", "signTransaction");
    }

    async signMessage(message: string | Uint8Array): Promise<string> {
        this.#throwUnsupported("messages", "signMessage");
    }

    async signTypedData(domain: TypedDataDomain, types: Record<string, Array<TypedDataField>>, value: Record<string, any>): Promise<string> {
        this.#throwUnsupported("typed-data", "signTypedData");
    }
}

