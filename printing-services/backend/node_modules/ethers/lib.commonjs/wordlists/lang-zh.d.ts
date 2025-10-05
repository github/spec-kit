import { Wordlist } from "./wordlist.js";
/**
 *  The [[link-bip39-zh_cn]] and [[link-bip39-zh_tw]] for
 *  [mnemonic phrases](link-bip-39).
 *
 *  @_docloc: api/wordlists
 */
export declare class LangZh extends Wordlist {
    /**
     *  Creates a new instance of the Chinese language Wordlist for
     *  the %%dialect%%, either ``"cn"`` or ``"tw"`` for simplified
     *  or traditional, respectively.
     *
     *  This should be unnecessary most of the time as the exported
     *  [[langZhCn]] and [[langZhTw]] should suffice.
     *
     *  @_ignore:
     */
    constructor(dialect: string);
    getWord(index: number): string;
    getWordIndex(word: string): number;
    split(phrase: string): Array<string>;
    /**
     *  Returns a singleton instance of a ``LangZh`` for %%dialect%%,
     *  creating it if this is the first time being called.
     *
     *  Use the %%dialect%% ``"cn"`` or ``"tw"`` for simplified or
     *  traditional, respectively.
     */
    static wordlist(dialect: string): LangZh;
}
//# sourceMappingURL=lang-zh.d.ts.map