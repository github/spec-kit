import type { BytesLike } from "../utils/index.js";
import type { Wordlist } from "../wordlists/index.js";
/**
 *  A **Mnemonic** wraps all properties required to compute [[link-bip-39]]
 *  seeds and convert between phrases and entropy.
 */
export declare class Mnemonic {
    /**
     *  The mnemonic phrase of 12, 15, 18, 21 or 24 words.
     *
     *  Use the [[wordlist]] ``split`` method to get the individual words.
     */
    readonly phrase: string;
    /**
     *  The password used for this mnemonic. If no password is used this
     *  is the empty string (i.e. ``""``) as per the specification.
     */
    readonly password: string;
    /**
     *  The wordlist for this mnemonic.
     */
    readonly wordlist: Wordlist;
    /**
     *  The underlying entropy which the mnemonic encodes.
     */
    readonly entropy: string;
    /**
     *  @private
     */
    constructor(guard: any, entropy: string, phrase: string, password?: null | string, wordlist?: null | Wordlist);
    /**
     *  Returns the seed for the mnemonic.
     */
    computeSeed(): string;
    /**
     *  Creates a new Mnemonic for the %%phrase%%.
     *
     *  The default %%password%% is the empty string and the default
     *  wordlist is the [English wordlists](LangEn).
     */
    static fromPhrase(phrase: string, password?: null | string, wordlist?: null | Wordlist): Mnemonic;
    /**
     *  Create a new **Mnemonic** from the %%entropy%%.
     *
     *  The default %%password%% is the empty string and the default
     *  wordlist is the [English wordlists](LangEn).
     */
    static fromEntropy(_entropy: BytesLike, password?: null | string, wordlist?: null | Wordlist): Mnemonic;
    /**
     *  Returns the phrase for %%mnemonic%%.
     */
    static entropyToPhrase(_entropy: BytesLike, wordlist?: null | Wordlist): string;
    /**
     *  Returns the entropy for %%phrase%%.
     */
    static phraseToEntropy(phrase: string, wordlist?: null | Wordlist): string;
    /**
     *  Returns true if %%phrase%% is a valid [[link-bip-39]] phrase.
     *
     *  This checks all the provided words belong to the %%wordlist%%,
     *  that the length is valid and the checksum is correct.
     */
    static isValidMnemonic(phrase: string, wordlist?: null | Wordlist): boolean;
}
//# sourceMappingURL=mnemonic.d.ts.map