"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.encryptKeystoreJson = exports.encryptKeystoreJsonSync = exports.decryptKeystoreJson = exports.decryptKeystoreJsonSync = exports.isKeystoreJson = void 0;
const aes_js_1 = require("aes-js");
const index_js_1 = require("../address/index.js");
const index_js_2 = require("../crypto/index.js");
const index_js_3 = require("../transaction/index.js");
const index_js_4 = require("../utils/index.js");
const utils_js_1 = require("./utils.js");
const _version_js_1 = require("../_version.js");
const defaultPath = "m/44'/60'/0'/0/0";
/**
 *  Returns true if %%json%% is a valid JSON Keystore Wallet.
 */
function isKeystoreJson(json) {
    try {
        const data = JSON.parse(json);
        const version = ((data.version != null) ? parseInt(data.version) : 0);
        if (version === 3) {
            return true;
        }
    }
    catch (error) { }
    return false;
}
exports.isKeystoreJson = isKeystoreJson;
function decrypt(data, key, ciphertext) {
    const cipher = (0, utils_js_1.spelunk)(data, "crypto.cipher:string");
    if (cipher === "aes-128-ctr") {
        const iv = (0, utils_js_1.spelunk)(data, "crypto.cipherparams.iv:data!");
        const aesCtr = new aes_js_1.CTR(key, iv);
        return (0, index_js_4.hexlify)(aesCtr.decrypt(ciphertext));
    }
    (0, index_js_4.assert)(false, "unsupported cipher", "UNSUPPORTED_OPERATION", {
        operation: "decrypt"
    });
}
function getAccount(data, _key) {
    const key = (0, index_js_4.getBytes)(_key);
    const ciphertext = (0, utils_js_1.spelunk)(data, "crypto.ciphertext:data!");
    const computedMAC = (0, index_js_4.hexlify)((0, index_js_2.keccak256)((0, index_js_4.concat)([key.slice(16, 32), ciphertext]))).substring(2);
    (0, index_js_4.assertArgument)(computedMAC === (0, utils_js_1.spelunk)(data, "crypto.mac:string!").toLowerCase(), "incorrect password", "password", "[ REDACTED ]");
    const privateKey = decrypt(data, key.slice(0, 16), ciphertext);
    const address = (0, index_js_3.computeAddress)(privateKey);
    if (data.address) {
        let check = data.address.toLowerCase();
        if (!check.startsWith("0x")) {
            check = "0x" + check;
        }
        (0, index_js_4.assertArgument)((0, index_js_1.getAddress)(check) === address, "keystore address/privateKey mismatch", "address", data.address);
    }
    const account = { address, privateKey };
    // Version 0.1 x-ethers metadata must contain an encrypted mnemonic phrase
    const version = (0, utils_js_1.spelunk)(data, "x-ethers.version:string");
    if (version === "0.1") {
        const mnemonicKey = key.slice(32, 64);
        const mnemonicCiphertext = (0, utils_js_1.spelunk)(data, "x-ethers.mnemonicCiphertext:data!");
        const mnemonicIv = (0, utils_js_1.spelunk)(data, "x-ethers.mnemonicCounter:data!");
        const mnemonicAesCtr = new aes_js_1.CTR(mnemonicKey, mnemonicIv);
        account.mnemonic = {
            path: ((0, utils_js_1.spelunk)(data, "x-ethers.path:string") || defaultPath),
            locale: ((0, utils_js_1.spelunk)(data, "x-ethers.locale:string") || "en"),
            entropy: (0, index_js_4.hexlify)((0, index_js_4.getBytes)(mnemonicAesCtr.decrypt(mnemonicCiphertext)))
        };
    }
    return account;
}
function getDecryptKdfParams(data) {
    const kdf = (0, utils_js_1.spelunk)(data, "crypto.kdf:string");
    if (kdf && typeof (kdf) === "string") {
        if (kdf.toLowerCase() === "scrypt") {
            const salt = (0, utils_js_1.spelunk)(data, "crypto.kdfparams.salt:data!");
            const N = (0, utils_js_1.spelunk)(data, "crypto.kdfparams.n:int!");
            const r = (0, utils_js_1.spelunk)(data, "crypto.kdfparams.r:int!");
            const p = (0, utils_js_1.spelunk)(data, "crypto.kdfparams.p:int!");
            // Make sure N is a power of 2
            (0, index_js_4.assertArgument)(N > 0 && (N & (N - 1)) === 0, "invalid kdf.N", "kdf.N", N);
            (0, index_js_4.assertArgument)(r > 0 && p > 0, "invalid kdf", "kdf", kdf);
            const dkLen = (0, utils_js_1.spelunk)(data, "crypto.kdfparams.dklen:int!");
            (0, index_js_4.assertArgument)(dkLen === 32, "invalid kdf.dklen", "kdf.dflen", dkLen);
            return { name: "scrypt", salt, N, r, p, dkLen: 64 };
        }
        else if (kdf.toLowerCase() === "pbkdf2") {
            const salt = (0, utils_js_1.spelunk)(data, "crypto.kdfparams.salt:data!");
            const prf = (0, utils_js_1.spelunk)(data, "crypto.kdfparams.prf:string!");
            const algorithm = prf.split("-").pop();
            (0, index_js_4.assertArgument)(algorithm === "sha256" || algorithm === "sha512", "invalid kdf.pdf", "kdf.pdf", prf);
            const count = (0, utils_js_1.spelunk)(data, "crypto.kdfparams.c:int!");
            const dkLen = (0, utils_js_1.spelunk)(data, "crypto.kdfparams.dklen:int!");
            (0, index_js_4.assertArgument)(dkLen === 32, "invalid kdf.dklen", "kdf.dklen", dkLen);
            return { name: "pbkdf2", salt, count, dkLen, algorithm };
        }
    }
    (0, index_js_4.assertArgument)(false, "unsupported key-derivation function", "kdf", kdf);
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
function decryptKeystoreJsonSync(json, _password) {
    const data = JSON.parse(json);
    const password = (0, utils_js_1.getPassword)(_password);
    const params = getDecryptKdfParams(data);
    if (params.name === "pbkdf2") {
        const { salt, count, dkLen, algorithm } = params;
        const key = (0, index_js_2.pbkdf2)(password, salt, count, dkLen, algorithm);
        return getAccount(data, key);
    }
    (0, index_js_4.assert)(params.name === "scrypt", "cannot be reached", "UNKNOWN_ERROR", { params });
    const { salt, N, r, p, dkLen } = params;
    const key = (0, index_js_2.scryptSync)(password, salt, N, r, p, dkLen);
    return getAccount(data, key);
}
exports.decryptKeystoreJsonSync = decryptKeystoreJsonSync;
function stall(duration) {
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
async function decryptKeystoreJson(json, _password, progress) {
    const data = JSON.parse(json);
    const password = (0, utils_js_1.getPassword)(_password);
    const params = getDecryptKdfParams(data);
    if (params.name === "pbkdf2") {
        if (progress) {
            progress(0);
            await stall(0);
        }
        const { salt, count, dkLen, algorithm } = params;
        const key = (0, index_js_2.pbkdf2)(password, salt, count, dkLen, algorithm);
        if (progress) {
            progress(1);
            await stall(0);
        }
        return getAccount(data, key);
    }
    (0, index_js_4.assert)(params.name === "scrypt", "cannot be reached", "UNKNOWN_ERROR", { params });
    const { salt, N, r, p, dkLen } = params;
    const key = await (0, index_js_2.scrypt)(password, salt, N, r, p, dkLen, progress);
    return getAccount(data, key);
}
exports.decryptKeystoreJson = decryptKeystoreJson;
function getEncryptKdfParams(options) {
    // Check/generate the salt
    const salt = (options.salt != null) ? (0, index_js_4.getBytes)(options.salt, "options.salt") : (0, index_js_2.randomBytes)(32);
    // Override the scrypt password-based key derivation function parameters
    let N = (1 << 17), r = 8, p = 1;
    if (options.scrypt) {
        if (options.scrypt.N) {
            N = options.scrypt.N;
        }
        if (options.scrypt.r) {
            r = options.scrypt.r;
        }
        if (options.scrypt.p) {
            p = options.scrypt.p;
        }
    }
    (0, index_js_4.assertArgument)(typeof (N) === "number" && N > 0 && Number.isSafeInteger(N) && (BigInt(N) & BigInt(N - 1)) === BigInt(0), "invalid scrypt N parameter", "options.N", N);
    (0, index_js_4.assertArgument)(typeof (r) === "number" && r > 0 && Number.isSafeInteger(r), "invalid scrypt r parameter", "options.r", r);
    (0, index_js_4.assertArgument)(typeof (p) === "number" && p > 0 && Number.isSafeInteger(p), "invalid scrypt p parameter", "options.p", p);
    return { name: "scrypt", dkLen: 32, salt, N, r, p };
}
function _encryptKeystore(key, kdf, account, options) {
    const privateKey = (0, index_js_4.getBytes)(account.privateKey, "privateKey");
    // Override initialization vector
    const iv = (options.iv != null) ? (0, index_js_4.getBytes)(options.iv, "options.iv") : (0, index_js_2.randomBytes)(16);
    (0, index_js_4.assertArgument)(iv.length === 16, "invalid options.iv length", "options.iv", options.iv);
    // Override the uuid
    const uuidRandom = (options.uuid != null) ? (0, index_js_4.getBytes)(options.uuid, "options.uuid") : (0, index_js_2.randomBytes)(16);
    (0, index_js_4.assertArgument)(uuidRandom.length === 16, "invalid options.uuid length", "options.uuid", options.iv);
    // This will be used to encrypt the wallet (as per Web3 secret storage)
    // - 32 bytes   As normal for the Web3 secret storage (derivedKey, macPrefix)
    // - 32 bytes   AES key to encrypt mnemonic with (required here to be Ethers Wallet)
    const derivedKey = key.slice(0, 16);
    const macPrefix = key.slice(16, 32);
    // Encrypt the private key
    const aesCtr = new aes_js_1.CTR(derivedKey, iv);
    const ciphertext = (0, index_js_4.getBytes)(aesCtr.encrypt(privateKey));
    // Compute the message authentication code, used to check the password
    const mac = (0, index_js_2.keccak256)((0, index_js_4.concat)([macPrefix, ciphertext]));
    // See: https://github.com/ethereum/wiki/wiki/Web3-Secret-Storage-Definition
    const data = {
        address: account.address.substring(2).toLowerCase(),
        id: (0, index_js_4.uuidV4)(uuidRandom),
        version: 3,
        Crypto: {
            cipher: "aes-128-ctr",
            cipherparams: {
                iv: (0, index_js_4.hexlify)(iv).substring(2),
            },
            ciphertext: (0, index_js_4.hexlify)(ciphertext).substring(2),
            kdf: "scrypt",
            kdfparams: {
                salt: (0, index_js_4.hexlify)(kdf.salt).substring(2),
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
        const client = (options.client != null) ? options.client : `ethers/${_version_js_1.version}`;
        const path = account.mnemonic.path || defaultPath;
        const locale = account.mnemonic.locale || "en";
        const mnemonicKey = key.slice(32, 64);
        const entropy = (0, index_js_4.getBytes)(account.mnemonic.entropy, "account.mnemonic.entropy");
        const mnemonicIv = (0, index_js_2.randomBytes)(16);
        const mnemonicAesCtr = new aes_js_1.CTR(mnemonicKey, mnemonicIv);
        const mnemonicCiphertext = (0, index_js_4.getBytes)(mnemonicAesCtr.encrypt(entropy));
        const now = new Date();
        const timestamp = (now.getUTCFullYear() + "-" +
            (0, utils_js_1.zpad)(now.getUTCMonth() + 1, 2) + "-" +
            (0, utils_js_1.zpad)(now.getUTCDate(), 2) + "T" +
            (0, utils_js_1.zpad)(now.getUTCHours(), 2) + "-" +
            (0, utils_js_1.zpad)(now.getUTCMinutes(), 2) + "-" +
            (0, utils_js_1.zpad)(now.getUTCSeconds(), 2) + ".0Z");
        const gethFilename = ("UTC--" + timestamp + "--" + data.address);
        data["x-ethers"] = {
            client, gethFilename, path, locale,
            mnemonicCounter: (0, index_js_4.hexlify)(mnemonicIv).substring(2),
            mnemonicCiphertext: (0, index_js_4.hexlify)(mnemonicCiphertext).substring(2),
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
function encryptKeystoreJsonSync(account, password, options) {
    if (options == null) {
        options = {};
    }
    const passwordBytes = (0, utils_js_1.getPassword)(password);
    const kdf = getEncryptKdfParams(options);
    const key = (0, index_js_2.scryptSync)(passwordBytes, kdf.salt, kdf.N, kdf.r, kdf.p, 64);
    return _encryptKeystore((0, index_js_4.getBytes)(key), kdf, account, options);
}
exports.encryptKeystoreJsonSync = encryptKeystoreJsonSync;
/**
 *  Resolved to the JSON Keystore Wallet for %%account%% encrypted
 *  with %%password%%.
 *
 *  The %%options%% can be used to tune the password-based key
 *  derivation function parameters, explicitly set the random values
 *  used and provide a [[ProgressCallback]] to receive periodic updates
 *  on the completion status..
 */
async function encryptKeystoreJson(account, password, options) {
    if (options == null) {
        options = {};
    }
    const passwordBytes = (0, utils_js_1.getPassword)(password);
    const kdf = getEncryptKdfParams(options);
    const key = await (0, index_js_2.scrypt)(passwordBytes, kdf.salt, kdf.N, kdf.r, kdf.p, 64, options.progressCallback);
    return _encryptKeystore((0, index_js_4.getBytes)(key), kdf, account, options);
}
exports.encryptKeystoreJson = encryptKeystoreJson;
//# sourceMappingURL=json-keystore.js.map