"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Mnemonic = void 0;
const index_js_1 = require("../crypto/index.js");
const index_js_2 = require("../utils/index.js");
const lang_en_js_1 = require("../wordlists/lang-en.js");
// Returns a byte with the MSB bits set
function getUpperMask(bits) {
    return ((1 << bits) - 1) << (8 - bits) & 0xff;
}
// Returns a byte with the LSB bits set
function getLowerMask(bits) {
    return ((1 << bits) - 1) & 0xff;
}
function mnemonicToEntropy(mnemonic, wordlist) {
    (0, index_js_2.assertNormalize)("NFKD");
    if (wordlist == null) {
        wordlist = lang_en_js_1.LangEn.wordlist();
    }
    const words = wordlist.split(mnemonic);
    (0, index_js_2.assertArgument)((words.length % 3) === 0 && words.length >= 12 && words.length <= 24, "invalid mnemonic length", "mnemonic", "[ REDACTED ]");
    const entropy = new Uint8Array(Math.ceil(11 * words.length / 8));
    let offset = 0;
    for (let i = 0; i < words.length; i++) {
        let index = wordlist.getWordIndex(words[i].normalize("NFKD"));
        (0, index_js_2.assertArgument)(index >= 0, `invalid mnemonic word at index ${i}`, "mnemonic", "[ REDACTED ]");
        for (let bit = 0; bit < 11; bit++) {
            if (index & (1 << (10 - bit))) {
                entropy[offset >> 3] |= (1 << (7 - (offset % 8)));
            }
            offset++;
        }
    }
    const entropyBits = 32 * words.length / 3;
    const checksumBits = words.length / 3;
    const checksumMask = getUpperMask(checksumBits);
    const checksum = (0, index_js_2.getBytes)((0, index_js_1.sha256)(entropy.slice(0, entropyBits / 8)))[0] & checksumMask;
    (0, index_js_2.assertArgument)(checksum === (entropy[entropy.length - 1] & checksumMask), "invalid mnemonic checksum", "mnemonic", "[ REDACTED ]");
    return (0, index_js_2.hexlify)(entropy.slice(0, entropyBits / 8));
}
function entropyToMnemonic(entropy, wordlist) {
    (0, index_js_2.assertArgument)((entropy.length % 4) === 0 && entropy.length >= 16 && entropy.length <= 32, "invalid entropy size", "entropy", "[ REDACTED ]");
    if (wordlist == null) {
        wordlist = lang_en_js_1.LangEn.wordlist();
    }
    const indices = [0];
    let remainingBits = 11;
    for (let i = 0; i < entropy.length; i++) {
        // Consume the whole byte (with still more to go)
        if (remainingBits > 8) {
            indices[indices.length - 1] <<= 8;
            indices[indices.length - 1] |= entropy[i];
            remainingBits -= 8;
            // This byte will complete an 11-bit index
        }
        else {
            indices[indices.length - 1] <<= remainingBits;
            indices[indices.length - 1] |= entropy[i] >> (8 - remainingBits);
            // Start the next word
            indices.push(entropy[i] & getLowerMask(8 - remainingBits));
            remainingBits += 3;
        }
    }
    // Compute the checksum bits
    const checksumBits = entropy.length / 4;
    const checksum = parseInt((0, index_js_1.sha256)(entropy).substring(2, 4), 16) & getUpperMask(checksumBits);
    // Shift the checksum into the word indices
    indices[indices.length - 1] <<= checksumBits;
    indices[indices.length - 1] |= (checksum >> (8 - checksumBits));
    return wordlist.join(indices.map((index) => wordlist.getWord(index)));
}
const _guard = {};
/**
 *  A **Mnemonic** wraps all properties required to compute [[link-bip-39]]
 *  seeds and convert between phrases and entropy.
 */
class Mnemonic {
    /**
     *  The mnemonic phrase of 12, 15, 18, 21 or 24 words.
     *
     *  Use the [[wordlist]] ``split`` method to get the individual words.
     */
    phrase;
    /**
     *  The password used for this mnemonic. If no password is used this
     *  is the empty string (i.e. ``""``) as per the specification.
     */
    password;
    /**
     *  The wordlist for this mnemonic.
     */
    wordlist;
    /**
     *  The underlying entropy which the mnemonic encodes.
     */
    entropy;
    /**
     *  @private
     */
    constructor(guard, entropy, phrase, password, wordlist) {
        if (password == null) {
            password = "";
        }
        if (wordlist == null) {
            wordlist = lang_en_js_1.LangEn.wordlist();
        }
        (0, index_js_2.assertPrivate)(guard, _guard, "Mnemonic");
        (0, index_js_2.defineProperties)(this, { phrase, password, wordlist, entropy });
    }
    /**
     *  Returns the seed for the mnemonic.
     */
    computeSeed() {
        const salt = (0, index_js_2.toUtf8Bytes)("mnemonic" + this.password, "NFKD");
        return (0, index_js_1.pbkdf2)((0, index_js_2.toUtf8Bytes)(this.phrase, "NFKD"), salt, 2048, 64, "sha512");
    }
    /**
     *  Creates a new Mnemonic for the %%phrase%%.
     *
     *  The default %%password%% is the empty string and the default
     *  wordlist is the [English wordlists](LangEn).
     */
    static fromPhrase(phrase, password, wordlist) {
        // Normalize the case and space; throws if invalid
        const entropy = mnemonicToEntropy(phrase, wordlist);
        phrase = entropyToMnemonic((0, index_js_2.getBytes)(entropy), wordlist);
        return new Mnemonic(_guard, entropy, phrase, password, wordlist);
    }
    /**
     *  Create a new **Mnemonic** from the %%entropy%%.
     *
     *  The default %%password%% is the empty string and the default
     *  wordlist is the [English wordlists](LangEn).
     */
    static fromEntropy(_entropy, password, wordlist) {
        const entropy = (0, index_js_2.getBytes)(_entropy, "entropy");
        const phrase = entropyToMnemonic(entropy, wordlist);
        return new Mnemonic(_guard, (0, index_js_2.hexlify)(entropy), phrase, password, wordlist);
    }
    /**
     *  Returns the phrase for %%mnemonic%%.
     */
    static entropyToPhrase(_entropy, wordlist) {
        const entropy = (0, index_js_2.getBytes)(_entropy, "entropy");
        return entropyToMnemonic(entropy, wordlist);
    }
    /**
     *  Returns the entropy for %%phrase%%.
     */
    static phraseToEntropy(phrase, wordlist) {
        return mnemonicToEntropy(phrase, wordlist);
    }
    /**
     *  Returns true if %%phrase%% is a valid [[link-bip-39]] phrase.
     *
     *  This checks all the provided words belong to the %%wordlist%%,
     *  that the length is valid and the checksum is correct.
     */
    static isValidMnemonic(phrase, wordlist) {
        try {
            mnemonicToEntropy(phrase, wordlist);
            return true;
        }
        catch (error) { }
        return false;
    }
}
exports.Mnemonic = Mnemonic;
//# sourceMappingURL=mnemonic.js.map