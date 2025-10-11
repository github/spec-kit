import type { Addressable, NameResolver } from "../address/index.js";
import type { AuthorizationRequest, TypedDataDomain, TypedDataField } from "../hash/index.js";
import type { Authorization, TransactionLike } from "../transaction/index.js";
import type { ContractRunner } from "./contracts.js";
import type { BlockTag, Provider, TransactionRequest, TransactionResponse } from "./provider.js";
/**
 *  A Signer represents an account on the Ethereum Blockchain, and is most often
 *  backed by a private key represented by a mnemonic or residing on a Hardware Wallet.
 *
 *  The API remains abstract though, so that it can deal with more advanced exotic
 *  Signing entities, such as Smart Contract Wallets or Virtual Wallets (where the
 *  private key may not be known).
 */
export interface Signer extends Addressable, ContractRunner, NameResolver {
    /**
     *  The [[Provider]] attached to this Signer (if any).
     */
    provider: null | Provider;
    /**
     *  Returns a new instance of this Signer connected to //provider// or detached
     *  from any Provider if null.
     */
    connect(provider: null | Provider): Signer;
    /**
     *  Get the address of the Signer.
     */
    getAddress(): Promise<string>;
    /**
     *  Gets the next nonce required for this Signer to send a transaction.
     *
     *  @param blockTag - The blocktag to base the transaction count on, keep in mind
     *         many nodes do not honour this value and silently ignore it [default: ``"latest"``]
     */
    getNonce(blockTag?: BlockTag): Promise<number>;
    /**
     *  Prepares a {@link TransactionRequest} for calling:
     *  - resolves ``to`` and ``from`` addresses
     *  - if ``from`` is specified , check that it matches this Signer
     *
     *  @param tx - The call to prepare
     */
    populateCall(tx: TransactionRequest): Promise<TransactionLike<string>>;
    /**
     *  Prepares a {@link TransactionRequest} for sending to the network by
     *  populating any missing properties:
     *  - resolves ``to`` and ``from`` addresses
     *  - if ``from`` is specified , check that it matches this Signer
     *  - populates ``nonce`` via ``signer.getNonce("pending")``
     *  - populates ``gasLimit`` via ``signer.estimateGas(tx)``
     *  - populates ``chainId`` via ``signer.provider.getNetwork()``
     *  - populates ``type`` and relevant fee data for that type (``gasPrice``
     *    for legacy transactions, ``maxFeePerGas`` for EIP-1559, etc)
     *
     *  @note Some Signer implementations may skip populating properties that
     *        are populated downstream; for example JsonRpcSigner defers to the
     *        node to populate the nonce and fee data.
     *
     *  @param tx - The call to prepare
     */
    populateTransaction(tx: TransactionRequest): Promise<TransactionLike<string>>;
    /**
     *  Estimates the required gas required to execute //tx// on the Blockchain. This
     *  will be the expected amount a transaction will require as its ``gasLimit``
     *  to successfully run all the necessary computations and store the needed state
     *  that the transaction intends.
     *
     *  Keep in mind that this is **best efforts**, since the state of the Blockchain
     *  is in flux, which could affect transaction gas requirements.
     *
     *  @throws UNPREDICTABLE_GAS_LIMIT A transaction that is believed by the node to likely
     *          fail will throw an error during gas estimation. This could indicate that it
     *          will actually fail or that the circumstances are simply too complex for the
     *          node to take into account. In these cases, a manually determined ``gasLimit``
     *          will need to be made.
     */
    estimateGas(tx: TransactionRequest): Promise<bigint>;
    /**
     *  Evaluates the //tx// by running it against the current Blockchain state. This
     *  cannot change state and has no cost in ether, as it is effectively simulating
     *  execution.
     *
     *  This can be used to have the Blockchain perform computations based on its state
     *  (e.g. running a Contract's getters) or to simulate the effect of a transaction
     *  before actually performing an operation.
     */
    call(tx: TransactionRequest): Promise<string>;
    /**
     *  Resolves an ENS Name to an address.
     */
    resolveName(name: string): Promise<null | string>;
    /**
     *  Signs %%tx%%, returning the fully signed transaction. This does not
     *  populate any additional properties within the transaction.
     */
    signTransaction(tx: TransactionRequest): Promise<string>;
    /**
     *  Sends %%tx%% to the Network. The ``signer.populateTransaction(tx)``
     *  is called first to ensure all necessary properties for the
     *  transaction to be valid have been popualted first.
     */
    sendTransaction(tx: TransactionRequest): Promise<TransactionResponse>;
    /**
     *  Signs an [[link-eip-191]] prefixed personal message.
     *
     *  If the %%message%% is a string, it is signed as UTF-8 encoded bytes. It is **not**
     *  interpretted as a [[BytesLike]]; so the string ``"0x1234"`` is signed as six
     *  characters, **not** two bytes.
     *
     *  To sign that example as two bytes, the Uint8Array should be used
     *  (i.e. ``new Uint8Array([ 0x12, 0x34 ])``).
     */
    signMessage(message: string | Uint8Array): Promise<string>;
    /**
     *  Signs the [[link-eip-712]] typed data.
     */
    signTypedData(domain: TypedDataDomain, types: Record<string, Array<TypedDataField>>, value: Record<string, any>): Promise<string>;
    /**
     *  Prepares an [[AuthorizationRequest]] for authorization by
     *  populating any missing properties:
     *  - resolves ``address`` (if an Addressable or ENS name)
     *  - populates ``nonce`` via ``signer.getNonce("pending")``
     *  - populates ``chainId`` via ``signer.provider.getNetwork()``
     */
    populateAuthorization(auth: AuthorizationRequest): Promise<AuthorizationRequest>;
    /**
     *  Signs an %%authorization%% to be used in [[link-eip-7702]]
     *  transactions.
     */
    authorize(authorization: AuthorizationRequest): Promise<Authorization>;
}
//# sourceMappingURL=signer.d.ts.map