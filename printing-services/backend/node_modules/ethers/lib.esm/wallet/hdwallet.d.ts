/**
 *  Explain HD Wallets..
 *
 *  @_subsection: api/wallet:HD Wallets  [hd-wallets]
 */
import { SigningKey } from "../crypto/index.js";
import { VoidSigner } from "../providers/index.js";
import { BaseWallet } from "./base-wallet.js";
import { Mnemonic } from "./mnemonic.js";
import type { ProgressCallback } from "../crypto/index.js";
import type { Provider } from "../providers/index.js";
import type { BytesLike, Numeric } from "../utils/index.js";
import type { Wordlist } from "../wordlists/index.js";
/**
 *  The default derivation path for Ethereum HD Nodes. (i.e. ``"m/44'/60'/0'/0/0"``)
 */
export declare const defaultPath: string;
/**
 *  An **HDNodeWallet** is a [[Signer]] backed by the private key derived
 *  from an HD Node using the [[link-bip-32]] stantard.
 *
 *  An HD Node forms a hierarchal structure with each HD Node having a
 *  private key and the ability to derive child HD Nodes, defined by
 *  a path indicating the index of each child.
 */
export declare class HDNodeWallet extends BaseWallet {
    #private;
    /**
     *  The compressed public key.
     */
    readonly publicKey: string;
    /**
     *  The fingerprint.
     *
     *  A fingerprint allows quick qay to detect parent and child nodes,
     *  but developers should be prepared to deal with collisions as it
     *  is only 4 bytes.
     */
    readonly fingerprint: string;
    /**
     *  The parent fingerprint.
     */
    readonly parentFingerprint: string;
    /**
     *  The mnemonic used to create this HD Node, if available.
     *
     *  Sources such as extended keys do not encode the mnemonic, in
     *  which case this will be ``null``.
     */
    readonly mnemonic: null | Mnemonic;
    /**
     *  The chaincode, which is effectively a public key used
     *  to derive children.
     */
    readonly chainCode: string;
    /**
     *  The derivation path of this wallet.
     *
     *  Since extended keys do not provide full path details, this
     *  may be ``null``, if instantiated from a source that does not
     *  encode it.
     */
    readonly path: null | string;
    /**
     *  The child index of this wallet. Values over ``2 *\* 31`` indicate
     *  the node is hardened.
     */
    readonly index: number;
    /**
     *  The depth of this wallet, which is the number of components
     *  in its path.
     */
    readonly depth: number;
    /**
     *  @private
     */
    constructor(guard: any, signingKey: SigningKey, parentFingerprint: string, chainCode: string, path: null | string, index: number, depth: number, mnemonic: null | Mnemonic, provider: null | Provider);
    connect(provider: null | Provider): HDNodeWallet;
    /**
     *  Resolves to a [JSON Keystore Wallet](json-wallets) encrypted with
     *  %%password%%.
     *
     *  If %%progressCallback%% is specified, it will receive periodic
     *  updates as the encryption process progreses.
     */
    encrypt(password: Uint8Array | string, progressCallback?: ProgressCallback): Promise<string>;
    /**
     *  Returns a [JSON Keystore Wallet](json-wallets) encryped with
     *  %%password%%.
     *
     *  It is preferred to use the [async version](encrypt) instead,
     *  which allows a [[ProgressCallback]] to keep the user informed.
     *
     *  This method will block the event loop (freezing all UI) until
     *  it is complete, which may be a non-trivial duration.
     */
    encryptSync(password: Uint8Array | string): string;
    /**
     *  The extended key.
     *
     *  This key will begin with the prefix ``xpriv`` and can be used to
     *  reconstruct this HD Node to derive its children.
     */
    get extendedKey(): string;
    /**
     *  Returns true if this wallet has a path, providing a Type Guard
     *  that the path is non-null.
     */
    hasPath(): this is {
        path: string;
    };
    /**
     *  Returns a neutered HD Node, which removes the private details
     *  of an HD Node.
     *
     *  A neutered node has no private key, but can be used to derive
     *  child addresses and other public data about the HD Node.
     */
    neuter(): HDNodeVoidWallet;
    /**
     *  Return the child for %%index%%.
     */
    deriveChild(_index: Numeric): HDNodeWallet;
    /**
     *  Return the HDNode for %%path%% from this node.
     */
    derivePath(path: string): HDNodeWallet;
    /**
     *  Creates a new HD Node from %%extendedKey%%.
     *
     *  If the %%extendedKey%% will either have a prefix or ``xpub`` or
     *  ``xpriv``, returning a neutered HD Node ([[HDNodeVoidWallet]])
     *  or full HD Node ([[HDNodeWallet) respectively.
     */
    static fromExtendedKey(extendedKey: string): HDNodeWallet | HDNodeVoidWallet;
    /**
     *  Creates a new random HDNode.
     */
    static createRandom(password?: string, path?: string, wordlist?: Wordlist): HDNodeWallet;
    /**
     *  Create an HD Node from %%mnemonic%%.
     */
    static fromMnemonic(mnemonic: Mnemonic, path?: string): HDNodeWallet;
    /**
     *  Creates an HD Node from a mnemonic %%phrase%%.
     */
    static fromPhrase(phrase: string, password?: string, path?: string, wordlist?: Wordlist): HDNodeWallet;
    /**
     *  Creates an HD Node from a %%seed%%.
     */
    static fromSeed(seed: BytesLike): HDNodeWallet;
}
/**
 *  A **HDNodeVoidWallet** cannot sign, but provides access to
 *  the children nodes of a [[link-bip-32]] HD wallet addresses.
 *
 *  The can be created by using an extended ``xpub`` key to
 *  [[HDNodeWallet_fromExtendedKey]] or by
 *  [nuetering](HDNodeWallet-neuter) a [[HDNodeWallet]].
 */
export declare class HDNodeVoidWallet extends VoidSigner {
    /**
     *  The compressed public key.
     */
    readonly publicKey: string;
    /**
     *  The fingerprint.
     *
     *  A fingerprint allows quick qay to detect parent and child nodes,
     *  but developers should be prepared to deal with collisions as it
     *  is only 4 bytes.
     */
    readonly fingerprint: string;
    /**
     *  The parent node fingerprint.
     */
    readonly parentFingerprint: string;
    /**
     *  The chaincode, which is effectively a public key used
     *  to derive children.
     */
    readonly chainCode: string;
    /**
     *  The derivation path of this wallet.
     *
     *  Since extended keys do not provider full path details, this
     *  may be ``null``, if instantiated from a source that does not
     *  enocde it.
     */
    readonly path: null | string;
    /**
     *  The child index of this wallet. Values over ``2 *\* 31`` indicate
     *  the node is hardened.
     */
    readonly index: number;
    /**
     *  The depth of this wallet, which is the number of components
     *  in its path.
     */
    readonly depth: number;
    /**
     *  @private
     */
    constructor(guard: any, address: string, publicKey: string, parentFingerprint: string, chainCode: string, path: null | string, index: number, depth: number, provider: null | Provider);
    connect(provider: null | Provider): HDNodeVoidWallet;
    /**
     *  The extended key.
     *
     *  This key will begin with the prefix ``xpub`` and can be used to
     *  reconstruct this neutered key to derive its children addresses.
     */
    get extendedKey(): string;
    /**
     *  Returns true if this wallet has a path, providing a Type Guard
     *  that the path is non-null.
     */
    hasPath(): this is {
        path: string;
    };
    /**
     *  Return the child for %%index%%.
     */
    deriveChild(_index: Numeric): HDNodeVoidWallet;
    /**
     *  Return the signer for %%path%% from this node.
     */
    derivePath(path: string): HDNodeVoidWallet;
}
/**
 *  Returns the [[link-bip-32]] path for the account at %%index%%.
 *
 *  This is the pattern used by wallets like Ledger.
 *
 *  There is also an [alternate pattern](getIndexedAccountPath) used by
 *  some software.
 */
export declare function getAccountPath(_index: Numeric): string;
/**
 *  Returns the path using an alternative pattern for deriving accounts,
 *  at %%index%%.
 *
 *  This derivation path uses the //index// component rather than the
 *  //account// component to derive sequential accounts.
 *
 *  This is the pattern used by wallets like MetaMask.
 */
export declare function getIndexedAccountPath(_index: Numeric): string;
//# sourceMappingURL=hdwallet.d.ts.map