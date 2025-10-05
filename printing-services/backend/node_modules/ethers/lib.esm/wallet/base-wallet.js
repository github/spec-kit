import { getAddress, resolveAddress } from "../address/index.js";
import { hashAuthorization, hashMessage, TypedDataEncoder } from "../hash/index.js";
import { AbstractSigner, copyRequest } from "../providers/index.js";
import { computeAddress, Transaction } from "../transaction/index.js";
import { defineProperties, getBigInt, resolveProperties, assert, assertArgument } from "../utils/index.js";
/**
 *  The **BaseWallet** is a stream-lined implementation of a
 *  [[Signer]] that operates with a private key.
 *
 *  It is preferred to use the [[Wallet]] class, as it offers
 *  additional functionality and simplifies loading a variety
 *  of JSON formats, Mnemonic Phrases, etc.
 *
 *  This class may be of use for those attempting to implement
 *  a minimal Signer.
 */
export class BaseWallet extends AbstractSigner {
    /**
     *  The wallet address.
     */
    address;
    #signingKey;
    /**
     *  Creates a new BaseWallet for %%privateKey%%, optionally
     *  connected to %%provider%%.
     *
     *  If %%provider%% is not specified, only offline methods can
     *  be used.
     */
    constructor(privateKey, provider) {
        super(provider);
        assertArgument(privateKey && typeof (privateKey.sign) === "function", "invalid private key", "privateKey", "[ REDACTED ]");
        this.#signingKey = privateKey;
        const address = computeAddress(this.signingKey.publicKey);
        defineProperties(this, { address });
    }
    // Store private values behind getters to reduce visibility
    // in console.log
    /**
     *  The [[SigningKey]] used for signing payloads.
     */
    get signingKey() { return this.#signingKey; }
    /**
     *  The private key for this wallet.
     */
    get privateKey() { return this.signingKey.privateKey; }
    async getAddress() { return this.address; }
    connect(provider) {
        return new BaseWallet(this.#signingKey, provider);
    }
    async signTransaction(tx) {
        tx = copyRequest(tx);
        // Replace any Addressable or ENS name with an address
        const { to, from } = await resolveProperties({
            to: (tx.to ? resolveAddress(tx.to, this) : undefined),
            from: (tx.from ? resolveAddress(tx.from, this) : undefined)
        });
        if (to != null) {
            tx.to = to;
        }
        if (from != null) {
            tx.from = from;
        }
        if (tx.from != null) {
            assertArgument(getAddress((tx.from)) === this.address, "transaction from address mismatch", "tx.from", tx.from);
            delete tx.from;
        }
        // Build the transaction
        const btx = Transaction.from(tx);
        btx.signature = this.signingKey.sign(btx.unsignedHash);
        return btx.serialized;
    }
    async signMessage(message) {
        return this.signMessageSync(message);
    }
    // @TODO: Add a secialized signTx and signTyped sync that enforces
    // all parameters are known?
    /**
     *  Returns the signature for %%message%% signed with this wallet.
     */
    signMessageSync(message) {
        return this.signingKey.sign(hashMessage(message)).serialized;
    }
    /**
     *  Returns the Authorization for %%auth%%.
     */
    authorizeSync(auth) {
        assertArgument(typeof (auth.address) === "string", "invalid address for authorizeSync", "auth.address", auth);
        const signature = this.signingKey.sign(hashAuthorization(auth));
        return Object.assign({}, {
            address: getAddress(auth.address),
            nonce: getBigInt(auth.nonce || 0),
            chainId: getBigInt(auth.chainId || 0),
        }, { signature });
    }
    /**
     *  Resolves to the Authorization for %%auth%%.
     */
    async authorize(auth) {
        auth = Object.assign({}, auth, {
            address: await resolveAddress(auth.address, this)
        });
        return this.authorizeSync(await this.populateAuthorization(auth));
    }
    async signTypedData(domain, types, value) {
        // Populate any ENS names
        const populated = await TypedDataEncoder.resolveNames(domain, types, value, async (name) => {
            // @TODO: this should use resolveName; addresses don't
            //        need a provider
            assert(this.provider != null, "cannot resolve ENS names without a provider", "UNSUPPORTED_OPERATION", {
                operation: "resolveName",
                info: { name }
            });
            const address = await this.provider.resolveName(name);
            assert(address != null, "unconfigured ENS name", "UNCONFIGURED_NAME", {
                value: name
            });
            return address;
        });
        return this.signingKey.sign(TypedDataEncoder.hash(populated.domain, types, populated.value)).serialized;
    }
}
//# sourceMappingURL=base-wallet.js.map