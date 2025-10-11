import { WordlistOwl } from "./wordlist-owl.js";
import { decodeOwlA } from "./decode-owla.js";
/**
 *  An OWL-A format Wordlist extends the OWL format to add an
 *  overlay onto an OWL format Wordlist to support diacritic
 *  marks.
 *
 *  This class is generally not useful to most developers as
 *  it is used mainly internally to keep Wordlists for languages
 *  based on latin-1 small.
 *
 *  If necessary, there are tools within the ``generation/`` folder
 *  to create the necessary data.
 */
export class WordlistOwlA extends WordlistOwl {
    #accent;
    /**
     *  Creates a new Wordlist for %%locale%% using the OWLA %%data%%
     *  and %%accent%% data and validated against the %%checksum%%.
     */
    constructor(locale, data, accent, checksum) {
        super(locale, data, checksum);
        this.#accent = accent;
    }
    /**
     *  The OWLA-encoded accent data.
     */
    get _accent() { return this.#accent; }
    /**
     *  Decode all the words for the wordlist.
     */
    _decodeWords() {
        return decodeOwlA(this._data, this._accent);
    }
}
//# sourceMappingURL=wordlist-owla.js.map