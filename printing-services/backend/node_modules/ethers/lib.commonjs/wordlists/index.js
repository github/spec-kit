"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.wordlists = exports.WordlistOwlA = exports.WordlistOwl = exports.LangEn = exports.Wordlist = void 0;
/**
 *  A Wordlist is a set of 2048 words used to encode private keys
 *  (or other binary data) that is easier for humans to write down,
 *  transcribe and dictate.
 *
 *  The [[link-bip-39]] standard includes several checksum bits,
 *  depending on the size of the mnemonic phrase.
 *
 *  A mnemonic phrase may be 12, 15, 18, 21 or 24 words long. For
 *  most purposes 12 word mnemonics should be used, as including
 *  additional words increases the difficulty and potential for
 *  mistakes and does not offer any effective improvement on security.
 *
 *  There are a variety of [[link-bip39-wordlists]] for different
 *  languages, but for maximal compatibility, the
 *  [English Wordlist](LangEn) is recommended.
 *
 *  @_section: api/wordlists:Wordlists [about-wordlists]
 */
var wordlist_js_1 = require("./wordlist.js");
Object.defineProperty(exports, "Wordlist", { enumerable: true, get: function () { return wordlist_js_1.Wordlist; } });
var lang_en_js_1 = require("./lang-en.js");
Object.defineProperty(exports, "LangEn", { enumerable: true, get: function () { return lang_en_js_1.LangEn; } });
var wordlist_owl_js_1 = require("./wordlist-owl.js");
Object.defineProperty(exports, "WordlistOwl", { enumerable: true, get: function () { return wordlist_owl_js_1.WordlistOwl; } });
var wordlist_owla_js_1 = require("./wordlist-owla.js");
Object.defineProperty(exports, "WordlistOwlA", { enumerable: true, get: function () { return wordlist_owla_js_1.WordlistOwlA; } });
var wordlists_js_1 = require("./wordlists.js");
Object.defineProperty(exports, "wordlists", { enumerable: true, get: function () { return wordlists_js_1.wordlists; } });
//# sourceMappingURL=index.js.map