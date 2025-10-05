
// Use the encode-latin.js script to create the necessary
// data files to be consumed by this class

import { id } from "../hash/index.js";
import { assertArgument } from "../utils/index.js";

import { decodeOwl } from "./decode-owl.js";
import { Wordlist } from "./wordlist.js";

/**
 *  An OWL format Wordlist is an encoding method that exploits
 *  the general locality of alphabetically sorted words to
 *  achieve a simple but effective means of compression.
 *
 *  This class is generally not useful to most developers as
 *  it is used mainly internally to keep Wordlists for languages
 *  based on ASCII-7 small.
 *
 *  If necessary, there are tools within the ``generation/`` folder
 *  to create the necessary data.
 */
export class WordlistOwl extends Wordlist {
    #data: string;
    #checksum: string;

    /**
     *  Creates a new Wordlist for %%locale%% using the OWL %%data%%
     *  and validated against the %%checksum%%.
     */
    constructor(locale: string, data: string, checksum: string) {
        super(locale);
        this.#data = data;
        this.#checksum = checksum;
        this.#words = null;
    }

    /**
     *  The OWL-encoded data.
     */
    get _data(): string { return this.#data; }

    /**
     *  Decode all the words for the wordlist.
     */
    _decodeWords(): Array<string> {
        return decodeOwl(this.#data);
    }

    #words: null | Array<string>;
    #loadWords(): Array<string> {
        if (this.#words == null) {
            const words = this._decodeWords();

            // Verify the computed list matches the official list
            const checksum = id(words.join("\n") + "\n");
            /* c8 ignore start */
            if (checksum !== this.#checksum) {
                throw new Error(`BIP39 Wordlist for ${ this.locale } FAILED`);
            }
            /* c8 ignore stop */

            this.#words = words;
        }
        return this.#words;
    }

    getWord(index: number): string {
        const words = this.#loadWords();
        assertArgument(index >= 0 && index < words.length, `invalid word index: ${ index }`, "index", index);
        return words[index];
    }

    getWordIndex(word: string): number {
        return this.#loadWords().indexOf(word);
    }
}
