import type { Wordlist } from "./wordlist.js";
/**
 *  The available Wordlists by their
 *  [ISO 639-1 Language Code](link-wiki-iso639).
 *
 *  (**i.e.** [cz](LangCz), [en](LangEn), [es](LangEs), [fr](LangFr),
 *  [ja](LangJa), [ko](LangKo), [it](LangIt), [pt](LangPt),
 *  [zh_cn](LangZh), [zh_tw](LangZh))
 *
 *  The dist files (in the ``/dist`` folder) have had all languages
 *  except English stripped out, which reduces the library size by
 *  about 80kb. If required, they are available by importing the
 *  included ``wordlists-extra.min.js`` file.
 */
export declare const wordlists: Record<string, Wordlist>;
//# sourceMappingURL=wordlists.d.ts.map