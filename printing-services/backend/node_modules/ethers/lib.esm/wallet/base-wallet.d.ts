import { AbstractSigner } from "../providers/index.js";
import type { SigningKey } from "../crypto/index.js";
import type { AuthorizationRequest, TypedDataDomain, TypedDataField } from "../hash/index.js";
import type { Provider, TransactionRequest } from "../providers/index.js";
import type { Authorization } from "../transaction/index.js";
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
export declare class BaseWallet extends AbstractSigner {
    #private;
    /**
     *  The wallet address.
     */
    readonly address: string;
    /**
     *  Creates a new BaseWallet for %%privateKey%%, optionally
     *  connected to %%provider%%.
     *
     *  If %%provider%% is not specified, only offline methods can
     *  be used.
     */
    constructor(privateKey: SigningKey, provider?: null | Provider);
    /**
     *  The [[SigningKey]] used for signing payloads.
     */
    get signingKey(): SigningKey;
    /**
     *  The private key for this wallet.
     */
    get privateKey(): string;
    getAddress(): Promise<string>;
    connect(provider: null | Provider): BaseWallet;
    signTransaction(tx: TransactionRequest): Promise<string>;
    signMessage(message: string | Uint8Array): Promise<string>;
    /**
     *  Returns the signature for %%message%% signed with this wallet.
     */
    signMessageSync(message: string | Uint8Array): string;
    /**
     *  Returns the Authorization for %%auth%%.
     */
    authorizeSync(auth: AuthorizationRequest): Authorization;
    /**
     *  Resolves to the Authorization for %%auth%%.
     */
    authorize(auth: AuthorizationRequest): Promise<Authorization>;
    signTypedData(domain: TypedDataDomain, types: Record<string, Array<TypedDataField>>, value: Record<string, any>): Promise<string>;
}
//# sourceMappingURL=base-wallet.d.ts.map