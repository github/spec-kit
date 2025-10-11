
import { LangCz } from "./lang-cz.js";
import { LangEn } from "./lang-en.js";
import { LangEs } from "./lang-es.js";
import { LangFr } from "./lang-fr.js";
import { LangJa } from "./lang-ja.js";
import { LangKo } from "./lang-ko.js";
import { LangIt } from "./lang-it.js";
import { LangPt } from "./lang-pt.js";
import { LangZh } from "./lang-zh.js";

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
export const wordlists: Record<string, Wordlist> = {
  cz: LangCz.wordlist(),
  en: LangEn.wordlist(),
  es: LangEs.wordlist(),
  fr: LangFr.wordlist(),
  it: LangIt.wordlist(),
  pt: LangPt.wordlist(),
  ja: LangJa.wordlist(),
  ko: LangKo.wordlist(),
  zh_cn: LangZh.wordlist("cn"),
  zh_tw: LangZh.wordlist("tw"),
};
