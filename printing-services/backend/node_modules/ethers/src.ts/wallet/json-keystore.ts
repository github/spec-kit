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

import { CTR } from "aes-js";

import { getAddress } from "../address/index.js";
import { keccak256, pbkdf2, randomBytes, scrypt, scryptSync } from "../crypto/index.js";
import { computeAddress } from "../transaction/index.js";
import {
    concat, getBytes, hexlify, uuidV4, assert, assertArgument
} from "../utils/index.js";

import { getPassword, spelunk, zpad } from "./utils.js";

import type { ProgressCallback } from "../crypto/index.js";
import type { BytesLike } from "../utils/index.js";

import { version } from "../_version.js";


const defaultPath = "m/44'/60'/0'/0/0";

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
    }
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
   }
}

/**
 *  Returns true if %%json%% is a valid JSON Keystore Wallet.
 */
export function isKeystoreJson(json: string): boolean {
    try {
        const data = JSON.parse(json);
        const version = ((data.version != null) ? parseInt(data.version): 0);
        if (version === 3) { return true; }
    } catch (error) { }
    return false;
}

function decrypt(data: any, key: Uint8Array, ciphertext: Uint8Array): string {
    const cipher = spelunk<string>(data, "crypto.cipher:string");
    if (cipher === "aes-128-ctr") {
        const iv = spelunk<Uint8Array>(data, "crypto.cipherparams.iv:data!")
        const aesCtr = new CTR(key, iv);
        return hexlify(aesCtr.decrypt(ciphertext));
    }

    assert(false, "unsupported cipher", "UNSUPPORTED_OPERATION", {
        operation: "decrypt"
    });
}

function getAccount(data: any, _key: string): KeystoreAccount {
    const key = getBytes(_key);
    const ciphertext = spelunk<Uint8Array>(data, "crypto.ciphertext:data!");

    const computedMAC = hexlify(keccak256(concat([ key.slice(16, 32), ciphertext ]))).substring(2);
    assertArgument(computedMAC === spelunk<string>(data, "crypto.mac:string!").toLowerCase(),
        "incorrect password", "password", "[ REDACTED ]");

    const privateKey = decrypt(data, key.slice(0, 16), ciphertext);

    const address = computeAddress(privateKey);
    if (data.address) {
        let check = data.address.toLowerCase();
        if (!check.startsWith("0x")) { check = "0x" + check; }

        assertArgument(getAddress(check) === address, "keystore address/privateKey mismatch", "address", data.address);
    }

    const account: KeystoreAccount = { address, privateKey };

    // Version 0.1 x-ethers metadata must contain an encrypted mnemonic phrase
    const version = spelunk(data, "x-ethers.version:string");
    if (version === "0.1") {
        const mnemonicKey = key.slice(32, 64);

        const mnemonicCiphertext = spelunk<Uint8Array>(data, "x-ethers.mnemonicCiphertext:data!");
        const mnemonicIv = spelunk<Uint8Array>(data, "x-ethers.mnemonicCounter:data!");

        const mnemonicAesCtr = new CTR(mnemonicKey, mnemonicIv);

        account.mnemonic = {
            path: (spelunk<null | string>(data, "x-ethers.path:string") || defaultPath),
            locale: (spelunk<null | string>(data, "x-ethers.locale:string") || "en"),
            entropy: hexlify(getBytes(mnemonicAesCtr.decrypt(mnemonicCiphertext)))
        };
    }

    return account;
}

type ScryptParams = {
    name: "scrypt";
    salt: Uint8Array;
    N: number;
    r: number;
    p: number;
    dkLen: number;
};

type KdfParams = ScryptParams | {
    name: "pbkdf2";
    salt: Uint8Array;
    count: number;
    dkLen: number;
    algorithm: "sha256" | "sha512";
};

function getDecryptKdfParams<T>(data: any): KdfParams {
    const kdf = spelunk(data, "crypto.kdf:string");
    if (kdf && typeof(kdf) === "string") {
        if (kdf.toLowerCase() === "scrypt") {
            const salt = spelunk<Uint8Array>(data, "crypto.kdfparams.salt:data!");
            const N = spelunk<number>(data, "crypto.kdfparams.n:int!");
            const r = spelunk<number>(data, "crypto.kdfparams.r:int!");
            const p = spelunk<number>(data, "crypto.kdfparams.p:int!");

            // Make sure N is a power of 2
            assertArgument(N > 0 && (N & (N - 1)) === 0, "invalid kdf.N", "kdf.N", N);
            assertArgument(r > 0 && p > 0, "invalid kdf", "kdf", kdf);

            const dkLen = spelunk<number>(data, "crypto.kdfparams.dklen:int!");
            assertArgument(dkLen === 32, "invalid kdf.dklen", "kdf.dflen", dkLen);

            return { name: "scrypt", salt, N, r, p, dkLen: 64 };

        } else if (kdf.toLowerCase() === "pbkdf2") {

            const salt = spelunk<Uint8Array>(data, "crypto.kdfparams.salt:data!");

            const prf = spelunk<string>(data, "crypto.kdfparams.prf:string!");
            const algorithm = prf.split("-").pop();
            assertArgument(algorithm === "sha256" || algorithm === "sha512", "invalid kdf.pdf", "kdf.pdf", prf);

            const count = spelunk<number>(data, "crypto.kdfparams.c:int!");

            const dkLen = spelunk<number>(data, "crypto.kdfparams.dklen:int!");
            assertArgument(dkLen === 32, "invalid kdf.dklen", "kdf.dklen", dkLen);

            return { name: "pbkdf2", salt, count, dkLen, algorithm };
        }
    }

    assertArgument(false, "unsupported key-derivation function", "kdf", kdf);
}


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
export function decryptKeystoreJsonSync(json: string, _password: string | Uint8Array): KeystoreAccount {
    const data = JSON.parse(json);

    const password = getPassword(_password);

    const params = getDecryptKdfParams(data);
    if (params.name === "pbkdf2") {
        const { salt, count, dkLen, algorithm } = params;
        const key = pbkdf2(password, salt, count, dkLen, algorithm);
        return getAccount(data, key);
    }

    assert(params.name === "scrypt", "cannot be reached", "UNKNOWN_ERROR", { params })

    const { salt, N, r, p, dkLen } = params;
    const key = scryptSync(password, salt, N, r, p, dkLen);
    return getAccount(data, key);
}

function stall(duration: number): Promise<void> {
    return new Promise((resolve) => { setTimeout(() => { resolve(); }, duration); });
}

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
export async function decryptKeystoreJson(json: string, _password: string | Uint8Array, progress?: ProgressCallback): Promise<KeystoreAccount> {
    const data = JSON.parse(json);

    const password = getPassword(_password);

    const params = getDecryptKdfParams(data);
    if (params.name === "pbkdf2") {
        if (progress) {
            progress(0);
            await stall(0);
        }
        const { salt, count, dkLen, algorithm } = params;
        const key = pbkdf2(password, salt, count, dkLen, algorithm);
        if (progress) {
            progress(1);
            await stall(0);
        }
        return getAccount(data, key);
    }

    assert(params.name === "scrypt", "cannot be reached", "UNKNOWN_ERROR", { params })

    const { salt, N, r, p, dkLen } = params;
    const key = await scrypt(password, salt, N, r, p, dkLen, progress);
    return getAccount(data, key);
}

function getEncryptKdfParams(options: EncryptOptions): ScryptParams {
    // Check/generate the salt
    const salt = (options.salt != null) ? getBytes(options.salt, "options.salt"): randomBytes(32);

    // Override the scrypt password-based key derivation function parameters
    let N = (1 << 17), r = 8, p = 1;
    if (options.scrypt) {
        if (options.scrypt.N) { N = options.scrypt.N; }
        if (options.scrypt.r) { r = options.scrypt.r; }
        if (options.scrypt.p) { p = options.scrypt.p; }
    }
    assertArgument(typeof(N) === "number" && N > 0 && Number.isSafeInteger(N) && (BigInt(N) & BigInt(N - 1)) === BigInt(0), "invalid scrypt N parameter", "options.N", N);
    assertArgument(typeof(r) === "number" && r > 0 && Number.isSafeInteger(r), "invalid scrypt r parameter", "options.r", r);
    assertArgument(typeof(p) === "number" && p > 0 && Number.isSafeInteger(p), "invalid scrypt p parameter", "options.p", p);

    return { name: "scrypt", dkLen: 32, salt, N, r, p };
}

function _encryptKeystore(key: Uint8Array, kdf: ScryptParams, account: KeystoreAccount, options: EncryptOptions): any {

    const privateKey = getBytes(account.privateKey, "privateKey");

    // Override initialization vector
    const iv = (options.iv != null) ? getBytes(options.iv, "options.iv"): randomBytes(16);
    assertArgument(iv.length === 16, "invalid options.iv length", "options.iv", options.iv);

    // Override the uuid
    const uuidRandom = (options.uuid != null) ? getBytes(options.uuid, "options.uuid"): randomBytes(16);
    assertArgument(uuidRandom.length === 16, "invalid options.uuid length", "options.uuid", options.iv);

    // This will be used to encrypt the wallet (as per Web3 secret storage)
    // - 32 bytes   As normal for the Web3 secret storage (derivedKey, macPrefix)
    // - 32 bytes   AES key to encrypt mnemonic with (required here to be Ethers Wallet)
    const derivedKey = key.slice(0, 16);
    const macPrefix = key.slice(16, 32);

    // Encrypt the private key
    const aesCtr = new CTR(derivedKey, iv);
    const ciphertext = getBytes(aesCtr.encrypt(privateKey));

    // Compute the message authentication code, used to check the password
    const mac = keccak256(concat([ macPrefix, ciphertext ]))

    // See: https://github.com/ethereum/wiki/wiki/Web3-Secret-Storage-Definition
    const data: { [key: string]: any } = {
        address: account.address.substring(2).toLowerCase(),
        id: uuidV4(uuidRandom),
        version: 3,
        Crypto: {
            cipher: "aes-128-ctr",
            cipherparams: {
                iv: hexlify(iv).substring(2),
            },
            ciphertext: hexlify(ciphertext).substring(2),
            kdf: "scrypt",
            kdfparams: {
                salt: hexlify(kdf.salt).substring(2),
                n: kdf.N,
                dklen: 32,
                p: kdf.p,
                r: kdf.r
            },
            mac: mac.substring(2)
        }
    };

    // If we have a mnemonic, encrypt it into the JSON wallet
    if (account.mnemonic) {
        const client = (options.client != null) ? options.client: `ethers/${ version }`;

        const path = account.mnemonic.path || defaultPath;
        const locale = account.mnemonic.locale || "en";

        const mnemonicKey = key.slice(32, 64);

        const entropy = getBytes(account.mnemonic.entropy, "account.mnemonic.entropy");
        const mnemonicIv = randomBytes(16);
        const mnemonicAesCtr = new CTR(mnemonicKey, mnemonicIv);
        const mnemonicCiphertext = getBytes(mnemonicAesCtr.encrypt(entropy));

        const now = new Date();
        const timestamp = (now.getUTCFullYear() + "-" +
                           zpad(now.getUTCMonth() + 1, 2) + "-" +
                           zpad(now.getUTCDate(), 2) + "T" +
                           zpad(now.getUTCHours(), 2) + "-" +
                           zpad(now.getUTCMinutes(), 2) + "-" +
                           zpad(now.getUTCSeconds(), 2) + ".0Z");
        const gethFilename = ("UTC--" + timestamp + "--" + data.address);

        data["x-ethers"] = {
            client, gethFilename, path, locale,
            mnemonicCounter: hexlify(mnemonicIv).substring(2),
            mnemonicCiphertext: hexlify(mnemonicCiphertext).substring(2),
            version: "0.1"
        };
    }

    return JSON.stringify(data);
}

/**
 *  Return the JSON Keystore Wallet for %%account%% encrypted with
 *  %%password%%.
 *
 *  The %%options%% can be used to tune the password-based key
 *  derivation function parameters, explicitly set the random values
 *  used. Any provided [[ProgressCallback]] is ignord.
 */
export function encryptKeystoreJsonSync(account: KeystoreAccount, password: string | Uint8Array, options?: EncryptOptions): string {
    if (options == null) { options = { }; }

    const passwordBytes = getPassword(password);
    const kdf = getEncryptKdfParams(options);
    const key = scryptSync(passwordBytes, kdf.salt, kdf.N, kdf.r, kdf.p, 64);
    return _encryptKeystore(getBytes(key), kdf, account, options);
}

/**
 *  Resolved to the JSON Keystore Wallet for %%account%% encrypted
 *  with %%password%%.
 *
 *  The %%options%% can be used to tune the password-based key
 *  derivation function parameters, explicitly set the random values
 *  used and provide a [[ProgressCallback]] to receive periodic updates
 *  on the completion status..
 */
export async function encryptKeystoreJson(account: KeystoreAccount, password: string | Uint8Array, options?: EncryptOptions): Promise<string> {
    if (options == null) { options = { }; }

    const passwordBytes = getPassword(password);
    const kdf = getEncryptKdfParams(options);
    const key = await scrypt(passwordBytes, kdf.salt, kdf.N, kdf.r, kdf.p, 64, options.progressCallback);
    return _encryptKeystore(getBytes(key), kdf, account, options);
}

