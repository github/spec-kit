"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.NonceManager = void 0;
const index_js_1 = require("../utils/index.js");
const abstract_signer_js_1 = require("./abstract-signer.js");
/**
 *  A **NonceManager** wraps another [[Signer]] and automatically manages
 *  the nonce, ensuring serialized and sequential nonces are used during
 *  transaction.
 */
class NonceManager extends abstract_signer_js_1.AbstractSigner {
    /**
     *  The Signer being managed.
     */
    signer;
    #noncePromise;
    #delta;
    /**
     *  Creates a new **NonceManager** to manage %%signer%%.
     */
    constructor(signer) {
        super(signer.provider);
        (0, index_js_1.defineProperties)(this, { signer });
        this.#noncePromise = null;
        this.#delta = 0;
    }
    async getAddress() {
        return this.signer.getAddress();
    }
    connect(provider) {
        return new NonceManager(this.signer.connect(provider));
    }
    async getNonce(blockTag) {
        if (blockTag === "pending") {
            if (this.#noncePromise == null) {
                this.#noncePromise = super.getNonce("pending");
            }
            const delta = this.#delta;
            return (await this.#noncePromise) + delta;
        }
        return super.getNonce(blockTag);
    }
    /**
     *  Manually increment the nonce. This may be useful when managng
     *  offline transactions.
     */
    increment() {
        this.#delta++;
    }
    /**
     *  Resets the nonce, causing the **NonceManager** to reload the current
     *  nonce from the blockchain on the next transaction.
     */
    reset() {
        this.#delta = 0;
        this.#noncePromise = null;
    }
    async sendTransaction(tx) {
        const noncePromise = this.getNonce("pending");
        this.increment();
        tx = await this.signer.populateTransaction(tx);
        tx.nonce = await noncePromise;
        // @TODO: Maybe handle interesting/recoverable errors?
        // Like don't increment if the tx was certainly not sent
        return await this.signer.sendTransaction(tx);
    }
    signTransaction(tx) {
        return this.signer.signTransaction(tx);
    }
    signMessage(message) {
        return this.signer.signMessage(message);
    }
    signTypedData(domain, types, value) {
        return this.signer.signTypedData(domain, types, value);
    }
}
exports.NonceManager = NonceManager;
//# sourceMappingURL=signer-noncemanager.js.map