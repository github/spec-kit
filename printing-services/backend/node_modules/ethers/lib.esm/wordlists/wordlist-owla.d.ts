import { WordlistOwl } from "./wordlist-owl.js";
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
export declare class WordlistOwlA extends WordlistOwl {
    #private;
    /**
     *  Creates a new Wordlist for %%locale%% using the OWLA %%data%%
     *  and %%accent%% data and validated against the %%checksum%%.
     */
    constructor(locale: string, data: string, accent: string, checksum: string);
    /**
     *  The OWLA-encoded accent data.
     */
    get _accent(): string;
    /**
     *  Decode all the words for the wordlist.
     */
    _decodeWords(): Array<string>;
}
//# sourceMappingURL=wordlist-owla.d.ts.map