import { Wordlist } from "./wordlist.js";
/**
 *  The [[link-bip39-ja]] for [mnemonic phrases](link-bip-39).
 *
 *  @_docloc: api/wordlists
 */
export declare class LangJa extends Wordlist {
    /**
     *  Creates a new instance of the Japanese language Wordlist.
     *
     *  This should be unnecessary most of the time as the exported
     *  [[langJa]] should suffice.
     *
     *  @_ignore:
     */
    constructor();
    getWord(index: number): string;
    getWordIndex(word: string): number;
    split(phrase: string): Array<string>;
    join(words: Array<string>): string;
    /**
     *  Returns a singleton instance of a ``LangJa``, creating it
     *  if this is the first time being called.
     */
    static wordlist(): LangJa;
}
//# sourceMappingURL=lang-ja.d.ts.map