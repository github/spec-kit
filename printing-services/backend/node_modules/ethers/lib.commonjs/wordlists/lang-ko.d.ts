import { Wordlist } from "./wordlist.js";
/**
 *  The [[link-bip39-ko]] for [mnemonic phrases](link-bip-39).
 *
 *  @_docloc: api/wordlists
 */
export declare class LangKo extends Wordlist {
    /**
     *  Creates a new instance of the Korean language Wordlist.
     *
     *  This should be unnecessary most of the time as the exported
     *  [[langKo]] should suffice.
     *
     *  @_ignore:
     */
    constructor();
    getWord(index: number): string;
    getWordIndex(word: string): number;
    /**
     *  Returns a singleton instance of a ``LangKo``, creating it
     *  if this is the first time being called.
     */
    static wordlist(): LangKo;
}
//# sourceMappingURL=lang-ko.d.ts.map