/**
 *  @_subsection: api/wallet:JSON Wallets  [json-wallets]
 */

import { CBC, pkcs7Strip } from "aes-js";

import { getAddress } from "../address/index.js";
import { pbkdf2 } from "../crypto/index.js";
import { id } from "../hash/index.js";
import { getBytes, assertArgument } from "../utils/index.js";

import { getPassword, looseArrayify, spelunk } from "./utils.js";


/**
 *  The data stored within a JSON Crowdsale wallet is fairly
 *  minimal.
 */
export type CrowdsaleAccount = {
    privateKey: string;
    address: string;
}

/**
 *  Returns true if %%json%% is a valid JSON Crowdsale wallet.
 */
export function isCrowdsaleJson(json: string): boolean {
    try {
        const data = JSON.parse(json);
        if (data.encseed) { return true; }
    } catch (error) { }
    return false;
}

// See: https://github.com/ethereum/pyethsaletool

/**
 *  Before Ethereum launched, it was necessary to create a wallet
 *  format for backers to use, which would be used to receive ether
 *  as a reward for contributing to the project.
 *
 *  The [[link-crowdsale]] format is now obsolete, but it is still
 *  useful to support and the additional code is fairly trivial as
 *  all the primitives required are used through core portions of
 *  the library.
 */
export function decryptCrowdsaleJson(json: string, _password: string | Uint8Array): CrowdsaleAccount {
    const data = JSON.parse(json);
    const password = getPassword(_password);

    // Ethereum Address
    const address = getAddress(spelunk(data, "ethaddr:string!"));

    // Encrypted Seed
    const encseed = looseArrayify(spelunk(data, "encseed:string!"));
    assertArgument(encseed && (encseed.length % 16) === 0, "invalid encseed", "json", json);

    const key = getBytes(pbkdf2(password, password, 2000, 32, "sha256")).slice(0, 16);

    const iv = encseed.slice(0, 16);
    const encryptedSeed = encseed.slice(16);

    // Decrypt the seed
    const aesCbc = new CBC(key, iv);
    const seed = pkcs7Strip(getBytes(aesCbc.decrypt(encryptedSeed)));

    // This wallet format is weird... Convert the binary encoded hex to a string.
    let seedHex = "";
    for (let i = 0; i < seed.length; i++) {
        seedHex += String.fromCharCode(seed[i]);
    }

    return { address, privateKey: id(seedHex) };
}
