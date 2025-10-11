"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Wordlist = void 0;
const index_js_1 = require("../utils/index.js");
/**
 *  A Wordlist represents a collection of language-specific
 *  words used to encode and devoce [[link-bip-39]] encoded data
 *  by mapping words to 11-bit values and vice versa.
 */
class Wordlist {
    locale;
    /**
     *  Creates a new Wordlist instance.
     *
     *  Sub-classes MUST call this if they provide their own constructor,
     *  passing in the locale string of the language.
     *
     *  Generally there is no need to create instances of a Wordlist,
     *  since each language-specific Wordlist creates an instance and
     *  there is no state kept internally, so they are safe to share.
     */
    constructor(locale) {
        (0, index_js_1.defineProperties)(this, { locale });
    }
    /**
     *  Sub-classes may override this to provide a language-specific
     *  method for spliting %%phrase%% into individual words.
     *
     *  By default, %%phrase%% is split using any sequences of
     *  white-space as defined by regular expressions (i.e. ``/\s+/``).
     */
    split(phrase) {
        return phrase.toLowerCase().split(/\s+/g);
    }
    /**
     *  Sub-classes may override this to provider a language-specific
     *  method for joining %%words%% into a phrase.
     *
     *  By default, %%words%% are joined by a single space.
     */
    join(words) {
        return words.join(" ");
    }
}
exports.Wordlist = Wordlist;
//# sourceMappingURL=wordlist.js.map