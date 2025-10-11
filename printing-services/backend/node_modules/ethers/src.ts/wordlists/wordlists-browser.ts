
import { LangEn } from "./lang-en.js";

import type { Wordlist } from "./wordlist.js";

export const wordlists: Record<string, Wordlist> = {
  en: LangEn.wordlist(),
};
