import { SigningKey } from "../crypto/index.js";
import { BaseWallet } from "./base-wallet.js";
import { HDNodeWallet } from "./hdwallet.js";
import type { ProgressCallback } from "../crypto/index.js";
import type { Provider } from "../providers/index.js";
/**
 *  A **Wallet** manages a single private key which is used to sign
 *  transactions, messages and other common payloads.
 *
 *  This class is generally the main entry point for developers
 *  that wish to use a private key directly, as it can create
 *  instances from a large variety of common sources, including
 *  raw private key, [[link-bip-39]] mnemonics and encrypte JSON
 *  wallets.
 */
export declare class Wallet extends BaseWallet {
    #private;
    /**
     *  Create a new wallet for the private %%key%%, optionally connected
     *  to %%provider%%.
     */
    constructor(key: string | SigningKey, provider?: null | Provider);
    connect(provider: null | Provider): Wallet;
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
     *  Creates (asynchronously) a **Wallet** by decrypting the %%json%%
     *  with %%password%%.
     *
     *  If %%progress%% is provided, it is called periodically during
     *  decryption so that any UI can be updated.
     */
    static fromEncryptedJson(json: string, password: Uint8Array | string, progress?: ProgressCallback): Promise<HDNodeWallet | Wallet>;
    /**
     *  Creates a **Wallet** by decrypting the %%json%% with %%password%%.
     *
     *  The [[fromEncryptedJson]] method is preferred, as this method
     *  will lock up and freeze the UI during decryption, which may take
     *  some time.
     */
    static fromEncryptedJsonSync(json: string, password: Uint8Array | string): HDNodeWallet | Wallet;
    /**
     *  Creates a new random [[HDNodeWallet]] using the available
     *  [cryptographic random source](randomBytes).
     *
     *  If there is no crytographic random source, this will throw.
     */
    static createRandom(provider?: null | Provider): HDNodeWallet;
    /**
     *  Creates a [[HDNodeWallet]] for %%phrase%%.
     */
    static fromPhrase(phrase: string, provider?: Provider): HDNodeWallet;
}
//# sourceMappingURL=wallet.d.ts.map