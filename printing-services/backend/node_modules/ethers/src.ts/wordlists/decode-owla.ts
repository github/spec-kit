import { assertArgument } from "../utils/index.js";

import { decodeBits } from "./bit-reader.js";
import { decodeOwl } from "./decode-owl.js";

/**
 *  @_ignore
 */
export function decodeOwlA(data: string, accents: string): Array<string> {
    let words = decodeOwl(data).join(",");

    // Inject the accents
    accents.split(/,/g).forEach((accent) => {

        const match = accent.match(/^([a-z]*)([0-9]+)([0-9])(.*)$/);
        assertArgument(match !== null, "internal error parsing accents", "accents", accents);

        let posOffset = 0;
        const positions = decodeBits(parseInt(match[3]), match[4]);
        const charCode = parseInt(match[2]);
        const regex = new RegExp(`([${ match[1] }])`, "g");
        words = words.replace(regex, (all, letter) => {
            const rem = --positions[posOffset];
            if (rem === 0) {
                letter = String.fromCharCode(letter.charCodeAt(0), charCode);
                posOffset++;
            }
            return letter;
        });
    });

    return words.split(",");
}
