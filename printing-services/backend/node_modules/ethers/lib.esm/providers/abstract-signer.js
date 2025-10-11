/**
 *  Generally the [[Wallet]] and [[JsonRpcSigner]] and their sub-classes
 *  are sufficent for most developers, but this is provided to
 *  fascilitate more complex Signers.
 *
 *  @_section: api/providers/abstract-signer: Subclassing Signer [abstract-signer]
 */
import { resolveAddress } from "../address/index.js";
import { Transaction } from "../transaction/index.js";
import { defineProperties, getBigInt, resolveProperties, assert, assertArgument } from "../utils/index.js";
import { copyRequest } from "./provider.js";
function checkProvider(signer, operation) {
    if (signer.provider) {
        return signer.provider;
    }
    assert(false, "missing provider", "UNSUPPORTED_OPERATION", { operation });
}
async function populate(signer, tx) {
    let pop = copyRequest(tx);
    if (pop.to != null) {
        pop.to = resolveAddress(pop.to, signer);
    }
    if (pop.from != null) {
        const from = pop.from;
        pop.from = Promise.all([
            signer.getAddress(),
            resolveAddress(from, signer)
        ]).then(([address, from]) => {
            assertArgument(address.toLowerCase() === from.toLowerCase(), "transaction from mismatch", "tx.from", from);
            return address;
        });
    }
    else {
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
export class AbstractSigner {
    /**
     *  The provider this signer is connected to.
     */
    provider;
    /**
     *  Creates a new Signer connected to %%provider%%.
     */
    constructor(provider) {
        defineProperties(this, { provider: (provider || null) });
    }
    async getNonce(blockTag) {
        return checkProvider(this, "getTransactionCount").getTransactionCount(await this.getAddress(), blockTag);
    }
    async populateCall(tx) {
        const pop = await populate(this, tx);
        return pop;
    }
    async populateTransaction(tx) {
        const provider = checkProvider(this, "populateTransaction");
        const pop = await populate(this, tx);
        if (pop.nonce == null) {
            pop.nonce = await this.getNonce("pending");
        }
        if (pop.gasLimit == null) {
            pop.gasLimit = await this.estimateGas(pop);
        }
        // Populate the chain ID
        const network = await (this.provider).getNetwork();
        if (pop.chainId != null) {
            const chainId = getBigInt(pop.chainId);
            assertArgument(chainId === network.chainId, "transaction chainId mismatch", "tx.chainId", tx.chainId);
        }
        else {
            pop.chainId = network.chainId;
        }
        // Do not allow mixing pre-eip-1559 and eip-1559 properties
        const hasEip1559 = (pop.maxFeePerGas != null || pop.maxPriorityFeePerGas != null);
        if (pop.gasPrice != null && (pop.type === 2 || hasEip1559)) {
            assertArgument(false, "eip-1559 transaction do not support gasPrice", "tx", tx);
        }
        else if ((pop.type === 0 || pop.type === 1) && hasEip1559) {
            assertArgument(false, "pre-eip-1559 transaction do not support maxFeePerGas/maxPriorityFeePerGas", "tx", tx);
        }
        if ((pop.type === 2 || pop.type == null) && (pop.maxFeePerGas != null && pop.maxPriorityFeePerGas != null)) {
            // Fully-formed EIP-1559 transaction (skip getFeeData)
            pop.type = 2;
        }
        else if (pop.type === 0 || pop.type === 1) {
            // Explicit Legacy or EIP-2930 transaction
            // We need to get fee data to determine things
            const feeData = await provider.getFeeData();
            assert(feeData.gasPrice != null, "network does not support gasPrice", "UNSUPPORTED_OPERATION", {
                operation: "getGasPrice"
            });
            // Populate missing gasPrice
            if (pop.gasPrice == null) {
                pop.gasPrice = feeData.gasPrice;
            }
        }
        else {
            // We need to get fee data to determine things
            const feeData = await provider.getFeeData();
            if (pop.type == null) {
                // We need to auto-detect the intended type of this transaction...
                if (feeData.maxFeePerGas != null && feeData.maxPriorityFeePerGas != null) {
                    // The network supports EIP-1559!
                    // Upgrade transaction from null to eip-1559
                    if (pop.authorizationList && pop.authorizationList.length) {
                        pop.type = 4;
                    }
                    else {
                        pop.type = 2;
                    }
                    if (pop.gasPrice != null) {
                        // Using legacy gasPrice property on an eip-1559 network,
                        // so use gasPrice as both fee properties
                        const gasPrice = pop.gasPrice;
                        delete pop.gasPrice;
                        pop.maxFeePerGas = gasPrice;
                        pop.maxPriorityFeePerGas = gasPrice;
                    }
                    else {
                        // Populate missing fee data
                        if (pop.maxFeePerGas == null) {
                            pop.maxFeePerGas = feeData.maxFeePerGas;
                        }
                        if (pop.maxPriorityFeePerGas == null) {
                            pop.maxPriorityFeePerGas = feeData.maxPriorityFeePerGas;
                        }
                    }
                }
                else if (feeData.gasPrice != null) {
                    // Network doesn't support EIP-1559...
                    // ...but they are trying to use EIP-1559 properties
                    assert(!hasEip1559, "network does not support EIP-1559", "UNSUPPORTED_OPERATION", {
                        operation: "populateTransaction"
                    });
                    // Populate missing fee data
                    if (pop.gasPrice == null) {
                        pop.gasPrice = feeData.gasPrice;
                    }
                    // Explicitly set untyped transaction to legacy
                    // @TODO: Maybe this shold allow type 1?
                    pop.type = 0;
                }
                else {
                    // getFeeData has failed us.
                    assert(false, "failed to get consistent fee data", "UNSUPPORTED_OPERATION", {
                        operation: "signer.getFeeData"
                    });
                }
            }
            else if (pop.type === 2 || pop.type === 3 || pop.type === 4) {
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
    async populateAuthorization(_auth) {
        const auth = Object.assign({}, _auth);
        // Add a chain ID if not explicitly set to 0
        if (auth.chainId == null) {
            auth.chainId = (await checkProvider(this, "getNetwork").getNetwork()).chainId;
        }
        // @TODO: Take chain ID into account when populating noce?
        if (auth.nonce == null) {
            auth.nonce = await this.getNonce();
        }
        return auth;
    }
    async estimateGas(tx) {
        return checkProvider(this, "estimateGas").estimateGas(await this.populateCall(tx));
    }
    async call(tx) {
        return checkProvider(this, "call").call(await this.populateCall(tx));
    }
    async resolveName(name) {
        const provider = checkProvider(this, "resolveName");
        return await provider.resolveName(name);
    }
    async sendTransaction(tx) {
        const provider = checkProvider(this, "sendTransaction");
        const pop = await this.populateTransaction(tx);
        delete pop.from;
        const txObj = Transaction.from(pop);
        return await provider.broadcastTransaction(await this.signTransaction(txObj));
    }
    // @TODO: in v7 move this to be abstract
    authorize(authorization) {
        assert(false, "authorization not implemented for this signer", "UNSUPPORTED_OPERATION", { operation: "authorize" });
    }
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
    address;
    /**
     *  Creates a new **VoidSigner** with %%address%% attached to
     *  %%provider%%.
     */
    constructor(address, provider) {
        super(provider);
        defineProperties(this, { address });
    }
    async getAddress() { return this.address; }
    connect(provider) {
        return new VoidSigner(this.address, provider);
    }
    #throwUnsupported(suffix, operation) {
        assert(false, `VoidSigner cannot sign ${suffix}`, "UNSUPPORTED_OPERATION", { operation });
    }
    async signTransaction(tx) {
        this.#throwUnsupported("transactions", "signTransaction");
    }
    async signMessage(message) {
        this.#throwUnsupported("messages", "signMessage");
    }
    async signTypedData(domain, types, value) {
        this.#throwUnsupported("typed-data", "signTypedData");
    }
}
//# sourceMappingURL=abstract-signer.js.map