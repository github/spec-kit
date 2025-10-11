import { AbstractSigner } from "./abstract-signer.js";
import type { TypedDataDomain, TypedDataField } from "../hash/index.js";
import type { BlockTag, Provider, TransactionRequest, TransactionResponse } from "./provider.js";
import type { Signer } from "./signer.js";
/**
 *  A **NonceManager** wraps another [[Signer]] and automatically manages
 *  the nonce, ensuring serialized and sequential nonces are used during
 *  transaction.
 */
export declare class NonceManager extends AbstractSigner {
    #private;
    /**
     *  The Signer being managed.
     */
    signer: Signer;
    /**
     *  Creates a new **NonceManager** to manage %%signer%%.
     */
    constructor(signer: Signer);
    getAddress(): Promise<string>;
    connect(provider: null | Provider): NonceManager;
    getNonce(blockTag?: BlockTag): Promise<number>;
    /**
     *  Manually increment the nonce. This may be useful when managng
     *  offline transactions.
     */
    increment(): void;
    /**
     *  Resets the nonce, causing the **NonceManager** to reload the current
     *  nonce from the blockchain on the next transaction.
     */
    reset(): void;
    sendTransaction(tx: TransactionRequest): Promise<TransactionResponse>;
    signTransaction(tx: TransactionRequest): Promise<string>;
    signMessage(message: string | Uint8Array): Promise<string>;
    signTypedData(domain: TypedDataDomain, types: Record<string, Array<TypedDataField>>, value: Record<string, any>): Promise<string>;
}
//# sourceMappingURL=signer-noncemanager.d.ts.map