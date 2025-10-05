"use strict";
// Use the encode-latin.js script to create the necessary
// data files to be consumed by this class
Object.defineProperty(exports, "__esModule", { value: true });
exports.WordlistOwl = void 0;
const index_js_1 = require("../hash/index.js");
const index_js_2 = require("../utils/index.js");
const decode_owl_js_1 = require("./decode-owl.js");
const wordlist_js_1 = require("./wordlist.js");
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
class WordlistOwl extends wordlist_js_1.Wordlist {
    #data;
    #checksum;
    /**
     *  Creates a new Wordlist for %%locale%% using the OWL %%data%%
     *  and validated against the %%checksum%%.
     */
    constructor(locale, data, checksum) {
        super(locale);
        this.#data = data;
        this.#checksum = checksum;
        this.#words = null;
    }
    /**
     *  The OWL-encoded data.
     */
    get _data() { return this.#data; }
    /**
     *  Decode all the words for the wordlist.
     */
    _decodeWords() {
        return (0, decode_owl_js_1.decodeOwl)(this.#data);
    }
    #words;
    #loadWords() {
        if (this.#words == null) {
            const words = this._decodeWords();
            // Verify the computed list matches the official list
            const checksum = (0, index_js_1.id)(words.join("\n") + "\n");
            /* c8 ignore start */
            if (checksum !== this.#checksum) {
                throw new Error(`BIP39 Wordlist for ${this.locale} FAILED`);
            }
            /* c8 ignore stop */
            this.#words = words;
        }
        return this.#words;
    }
    getWord(index) {
        const words = this.#loadWords();
        (0, index_js_2.assertArgument)(index >= 0 && index < words.length, `invalid word index: ${index}`, "index", index);
        return words[index];
    }
    getWordIndex(word) {
        return this.#loadWords().indexOf(word);
    }
}
exports.WordlistOwl = WordlistOwl;
//# sourceMappingURL=wordlist-owl.js.map