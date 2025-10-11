"use strict";
/**
 *  @_subsection: api/wallet:JSON Wallets  [json-wallets]
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.decryptCrowdsaleJson = exports.isCrowdsaleJson = void 0;
const aes_js_1 = require("aes-js");
const index_js_1 = require("../address/index.js");
const index_js_2 = require("../crypto/index.js");
const index_js_3 = require("../hash/index.js");
const index_js_4 = require("../utils/index.js");
const utils_js_1 = require("./utils.js");
/**
 *  Returns true if %%json%% is a valid JSON Crowdsale wallet.
 */
function isCrowdsaleJson(json) {
    try {
        const data = JSON.parse(json);
        if (data.encseed) {
            return true;
        }
    }
    catch (error) { }
    return false;
}
exports.isCrowdsaleJson = isCrowdsaleJson;
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
function decryptCrowdsaleJson(json, _password) {
    const data = JSON.parse(json);
    const password = (0, utils_js_1.getPassword)(_password);
    // Ethereum Address
    const address = (0, index_js_1.getAddress)((0, utils_js_1.spelunk)(data, "ethaddr:string!"));
    // Encrypted Seed
    const encseed = (0, utils_js_1.looseArrayify)((0, utils_js_1.spelunk)(data, "encseed:string!"));
    (0, index_js_4.assertArgument)(encseed && (encseed.length % 16) === 0, "invalid encseed", "json", json);
    const key = (0, index_js_4.getBytes)((0, index_js_2.pbkdf2)(password, password, 2000, 32, "sha256")).slice(0, 16);
    const iv = encseed.slice(0, 16);
    const encryptedSeed = encseed.slice(16);
    // Decrypt the seed
    const aesCbc = new aes_js_1.CBC(key, iv);
    const seed = (0, aes_js_1.pkcs7Strip)((0, index_js_4.getBytes)(aesCbc.decrypt(encryptedSeed)));
    // This wallet format is weird... Convert the binary encoded hex to a string.
    let seedHex = "";
    for (let i = 0; i < seed.length; i++) {
        seedHex += String.fromCharCode(seed[i]);
    }
    return { address, privateKey: (0, index_js_3.id)(seedHex) };
}
exports.decryptCrowdsaleJson = decryptCrowdsaleJson;
//# sourceMappingURL=json-crowdsale.js.map