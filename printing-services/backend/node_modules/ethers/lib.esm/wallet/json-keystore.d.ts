/**
 *  The JSON Wallet formats allow a simple way to store the private
 *  keys needed in Ethereum along with related information and allows
 *  for extensible forms of encryption.
 *
 *  These utilities facilitate decrypting and encrypting the most common
 *  JSON Wallet formats.
 *
 *  @_subsection: api/wallet:JSON Wallets  [json-wallets]
 */
import type { ProgressCallback } from "../crypto/index.js";
import type { BytesLike } from "../utils/index.js";
/**
 *  The contents of a JSON Keystore Wallet.
 */
export type KeystoreAccount = {
    address: string;
    privateKey: string;
    mnemonic?: {
        path?: string;
        locale?: string;
        entropy: string;
    };
};
/**
 *  The parameters to use when encrypting a JSON Keystore Wallet.
 */
export type EncryptOptions = {
    progressCallback?: ProgressCallback;
    iv?: BytesLike;
    entropy?: BytesLike;
    client?: string;
    salt?: BytesLike;
    uuid?: string;
    scrypt?: {
        N?: number;
        r?: number;
        p?: number;
    };
};
/**
 *  Returns true if %%json%% is a valid JSON Keystore Wallet.
 */
export declare function isKeystoreJson(json: string): boolean;
/**
 *  Returns the account details for the JSON Keystore Wallet %%json%%
 *  using %%password%%.
 *
 *  It is preferred to use the [async version](decryptKeystoreJson)
 *  instead, which allows a [[ProgressCallback]] to keep the user informed
 *  as to the decryption status.
 *
 *  This method will block the event loop (freezing all UI) until decryption
 *  is complete, which can take quite some time, depending on the wallet
 *  paramters and platform.
 */
export declare function decryptKeystoreJsonSync(json: string, _password: string | Uint8Array): KeystoreAccount;
/**
 *  Resolves to the decrypted JSON Keystore Wallet %%json%% using the
 *  %%password%%.
 *
 *  If provided, %%progress%% will be called periodically during the
 *  decrpytion to provide feedback, and if the function returns
 *  ``false`` will halt decryption.
 *
 *  The %%progressCallback%% will **always** receive ``0`` before
 *  decryption begins and ``1`` when complete.
 */
export declare function decryptKeystoreJson(json: string, _password: string | Uint8Array, progress?: ProgressCallback): Promise<KeystoreAccount>;
/**
 *  Return the JSON Keystore Wallet for %%account%% encrypted with
 *  %%password%%.
 *
 *  The %%options%% can be used to tune the password-based key
 *  derivation function parameters, explicitly set the random values
 *  used. Any provided [[ProgressCallback]] is ignord.
 */
export declare function encryptKeystoreJsonSync(account: KeystoreAccount, password: string | Uint8Array, options?: EncryptOptions): string;
/**
 *  Resolved to the JSON Keystore Wallet for %%account%% encrypted
 *  with %%password%%.
 *
 *  The %%options%% can be used to tune the password-based key
 *  derivation function parameters, explicitly set the random values
 *  used and provide a [[ProgressCallback]] to receive periodic updates
 *  on the completion status..
 */
export declare function encryptKeystoreJson(account: KeystoreAccount, password: string | Uint8Array, options?: EncryptOptions): Promise<string>;
//# sourceMappingURL=json-keystore.d.ts.map