import type { AuthorizationRequest, TypedDataDomain, TypedDataField } from "../hash/index.js";
import type { Authorization, TransactionLike } from "../transaction/index.js";
import type { BlockTag, Provider, TransactionRequest, TransactionResponse } from "./provider.js";
import type { Signer } from "./signer.js";
/**
 *  An **AbstractSigner** includes most of teh functionality required
 *  to get a [[Signer]] working as expected, but requires a few
 *  Signer-specific methods be overridden.
 *
 */
export declare abstract class AbstractSigner<P extends null | Provider = null | Provider> implements Signer {
    /**
     *  The provider this signer is connected to.
     */
    readonly provider: P;
    /**
     *  Creates a new Signer connected to %%provider%%.
     */
    constructor(provider?: P);
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
    getNonce(blockTag?: BlockTag): Promise<number>;
    populateCall(tx: TransactionRequest): Promise<TransactionLike<string>>;
    populateTransaction(tx: TransactionRequest): Promise<TransactionLike<string>>;
    populateAuthorization(_auth: AuthorizationRequest): Promise<AuthorizationRequest>;
    estimateGas(tx: TransactionRequest): Promise<bigint>;
    call(tx: TransactionRequest): Promise<string>;
    resolveName(name: string): Promise<null | string>;
    sendTransaction(tx: TransactionRequest): Promise<TransactionResponse>;
    authorize(authorization: AuthorizationRequest): Promise<Authorization>;
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
export declare class VoidSigner extends AbstractSigner {
    #private;
    /**
     *  The signer address.
     */
    readonly address: string;
    /**
     *  Creates a new **VoidSigner** with %%address%% attached to
     *  %%provider%%.
     */
    constructor(address: string, provider?: null | Provider);
    getAddress(): Promise<string>;
    connect(provider: null | Provider): VoidSigner;
    signTransaction(tx: TransactionRequest): Promise<string>;
    signMessage(message: string | Uint8Array): Promise<string>;
    signTypedData(domain: TypedDataDomain, types: Record<string, Array<TypedDataField>>, value: Record<string, any>): Promise<string>;
}
//# sourceMappingURL=abstract-signer.d.ts.map