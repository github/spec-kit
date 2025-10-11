"use strict";
// OWL Data Format
//
// The Official WordList data format exported by this encoder
// encodes sorted latin-1 words (letters only) based on the
// fact that sorted words have prefixes with substantial
// overlap.
//
// For example, the words:
//   [ Another, Apple, Apricot, Bread ]
// could be folded once with a single special character, such
// as ":" to yield:
//   [ nother, pple, pricot, :, read ].
// The First letter has been removed, but can be inferred by
// starting at A and incrementing to the next letter when ":"
// is encountered.
//
// The fold operation can be repeated for large sets as even within
// each folded set, there is substatial overlap in prefix. With the
// second special symbol ";", we get:
//   [ ; x 13, other, :, ple, ricot, :, ; x 18, ead ]
// which can be further compressed by using numbers instead of the
// special character:
//   [ 13, other, :, ple, ricot, :, 18, ead ]
// and to keep all values within a single byte, we only allow a
// maximum value of 10 (using 0 through 9 to represent 1 through 10),
// we get:
//   [ 9, 2, other, :, ple, ricot, :, 9, 7, ead ]
// and we use camel-case to imply the bounrary, giving the final string:
//   "92Other:PleRicot:97Ead"
//
// Once the entire latin-1 set has been collapsed, we use the remaining
// printable characters (except " and \, which require 2 bytes to represent
// in string) to substiture for the most common 2-letter pairs of letters
// in the string.
//
// OWLA Accent Format
//
// OWLA first removes all accents, and encodes that data using the OWL
// data format and encodes the accents as a base-64 series of 6-bit
// packed bits representing the distance from one followed letter to the
// next.
//
// For example, the acute accent in a given language may follow either
// a or e, in which case the follow-set is "ae". Each letter in the entire
// set is indexed, so the set of words with the accents:
//   "thisA/ppleDoe/sNotMa/tterToMe/"
//   "   1^   2^ 3^     4^  5^   6^ " <-- follow-set members, ALL a's and e's
// which gives the positions:
//   [ 0, 2, 3, 4, 6 ]
// which then reduce to the distances
//   [ 0, 2, 1, 1, 2 ]
// each of which fit into a 2-bit value, so this can be encoded as the
// base-64 encoded string:
//   00 10 01 01 10  =  001001 1010xx
//
// The base-64 set used has all number replaced with their
// shifted-counterparts to prevent comflicting with the numbers used in
// the fold operation to indicate the number of ";".
Object.defineProperty(exports, "__esModule", { value: true });
exports.encodeOwl = exports.extractAccents = exports.BitWriter = void 0;
const tslib_1 = require("tslib");
const fs_1 = tslib_1.__importDefault(require("fs"));
const id_js_1 = require("../../hash/id.js");
const decode_owl_js_1 = require("../decode-owl.js");
const decode_owla_js_1 = require("../decode-owla.js");
const subsChrs = " !#$%&'()*+,-./<=>?@[]^_`{|}~";
const Word = /^[a-z'`]*$/i;
function fold(words, sep) {
    const output = [];
    let initial = 97;
    for (const word of words) {
        if (word.match(Word)) {
            while (initial < word.charCodeAt(0)) {
                initial++;
                output.push(sep);
            }
            output.push(word.substring(1));
        }
        else {
            initial = 97;
            output.push(word);
        }
    }
    return output;
}
function camelcase(words) {
    return words.map((word) => {
        if (word.match(Word)) {
            return word[0].toUpperCase() + word.substring(1);
        }
        else {
            return word;
        }
    }).join("");
}
//let cc = 0, ce = 0;
/*
function getChar(c: string): string {
    //if (c === "e") { ce++; }
    if (c >= 'a' && c <= 'z') { return c; }
    if (c.charCodeAt(1)) {
        throw new Error(`bad char: "${ c }"`);
    }
    //cc++;
    return "";
    if (c.charCodeAt(0) === 768) { return "`"; }
    if (c.charCodeAt(0) === 769) { return "'"; }
    if (c.charCodeAt(0) === 771) { return "~"; }
    throw new Error(`Unsupported character: ${ c } (${ c.charCodeAt(0) }, ${ c.charCodeAt(1) })`);
}
function mangle(text: string): { word: string, special: string } {
    const result: Array<string> = [ ];
    for (let i = 0; i < text.length; i++) {
        const c = getChar(text[i]);
        result.push(c);
    }

    const word = result.join("");
    if (word[1] >= 'a' && word[1] <= 'z') { return { word, special: " " }; }
    return { word: word[0] + word.substring(2), special: word[1] };
}
*/
/*
  Store: [ accent ][ targets ][ rle data; base64-tail  ]
           `         ae         3, 100 = (63, 37), 15
           ~         n          63, 64 = (63, 1), 27
*/
const Base64 = ")!@#$%^&*(ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_";
class BitWriter {
    width;
    #data;
    #bitLength;
    constructor(width) {
        this.width = width;
        this.#data = [];
        this.#bitLength = 0;
    }
    write(value) {
        const maxValue = ((1 << this.width) - 1);
        while (value > maxValue) {
            this.#data.push(0);
            this.#bitLength += this.width;
            value -= maxValue;
        }
        this.#data.push(value);
        this.#bitLength += this.width;
    }
    get length() {
        return 1 + Math.trunc((this.#bitLength + 5) / 6);
    }
    get data() {
        let result = String(this.width);
        let bits = 0;
        let accum = 0;
        const data = this.#data.slice();
        let bitMod = this.#bitLength % 6;
        while (bitMod !== 0 && bitMod < 6) {
            data.push(0);
            bitMod += this.width;
        }
        for (const value of data) {
            accum <<= this.width;
            accum |= value;
            bits += this.width;
            if (bits < 6) {
                continue;
            }
            result += Base64[accum >> (bits - 6)];
            bits -= 6;
            accum &= ((1 << bits) - 1);
        }
        if (result.length !== this.length) {
            throw new Error(`Hmm: ${this.length} ${result.length} ${result}`);
        }
        return result;
    }
}
exports.BitWriter = BitWriter;
;
function sorted(text) {
    const letters = text.split("");
    letters.sort();
    return letters.join("");
}
//    if (c.charCodeAt(0) === 768) { return "`"; }
//    if (c.charCodeAt(0) === 769) { return "'"; }
//    if (c.charCodeAt(0) === 771) { return "~"; }
function extractAccents(words) {
    // Build a list that maps accents to the letters it can follow
    const followsMap = new Map();
    for (const word of words) {
        for (let i = 0; i < word.length; i++) {
            const c = word[i];
            if (c >= 'a' && c <= 'z') {
                continue;
            }
            // Make sure this positions and codepoint make sense
            if (c.charCodeAt(1)) {
                throw new Error(`unsupported codepoint: "${c}"`);
            }
            if (i === 0) {
                throw new Error(`unmatched accent: ${c}`);
            }
            const ac = c.charCodeAt(0), lastLetter = word[i - 1];
            ;
            const follows = (followsMap.get(ac) || "");
            if (follows.indexOf(lastLetter) === -1) {
                followsMap.set(ac, sorted(follows + lastLetter));
            }
        }
    }
    // Build the positions of each follow-set for those accents
    const positionsMap = new Map();
    for (const [accent, follows] of followsMap) {
        let count = 0;
        for (const word of words) {
            for (let i = 0; i < word.length; i++) {
                const c = word[i], ac = c.charCodeAt(0);
                if (follows.indexOf(c) >= 0) {
                    count++;
                }
                if (ac === accent) {
                    const pos = positionsMap.get(ac) || [];
                    pos.push(count);
                    positionsMap.set(ac, pos);
                }
            }
        }
    }
    const accents = [];
    for (const [accent, follows] of followsMap) {
        let last = -1;
        const positions = (positionsMap.get(accent) || []).map((value, index) => {
            const delta = value - last;
            last = value;
            if (index === 0) {
                return value;
            }
            return delta;
        });
        // Find the best encoding of the position data
        let positionData = "";
        for (let i = 2; i < 7; i++) {
            const bitWriter = new BitWriter(i);
            for (const p of positions) {
                bitWriter.write(p);
            }
            if (positionData === "" || bitWriter.length < positionData.length) {
                positionData = bitWriter.data;
            }
        }
        const positionsLength = positions.length;
        const positionDataLength = positionData.length;
        accents.push({ accent, follows, positions, positionsLength, positionData, positionDataLength });
    }
    words = words.map((word) => {
        let result = "";
        for (let i = 0; i < word.length; i++) {
            const c = word[i];
            if (c >= 'a' && c <= 'z') {
                result += c;
            }
        }
        return result;
    });
    return { accents, words };
}
exports.extractAccents = extractAccents;
// Encode Official WordList
function encodeOwl(words) {
    // Fold the sorted words by indicating delta for the first 2 letters
    let data = camelcase(fold(fold(words, ":"), ";"));
    // Replace semicolons with counts (e.g. ";;;" with "3")
    data = data.replace(/(;+)/g, (all, semis) => {
        let result = "";
        while (semis.length) {
            let count = semis.length;
            if (count > 10) {
                count = 10;
            }
            result += String(count - 1);
            semis = semis.substring(count);
        }
        return result;
    });
    // Finds the best option for a shortcut replacement using the
    // unused ascii7 characters
    function findBest() {
        const tally = {};
        const l = 2;
        for (let i = l; i < data.length; i++) {
            const key = data.substring(i - l, i);
            tally[key] = (tally[key] || 0) + 1;
        }
        const sorted = Object.keys(tally).map((text) => {
            return { text, count: tally[text], save: (tally[text] * (text.length - 1)) };
        });
        sorted.sort((a, b) => (b.save - a.save));
        return sorted[0].text;
    }
    // Make substitutions
    let subs = "";
    for (let i = 0; i < subsChrs.length; i++) {
        const n = subsChrs[i], o = findBest();
        subs += o;
        data = data.split(o).join(n);
    }
    return { data, subs };
}
exports.encodeOwl = encodeOwl;
// Returns either:
//  - OWL data for accent-free latin-1: { data, accentds: "" }
//  - OWLA data for accented latin-1: { data, accents }
function encodeWords(_words) {
    const { accents, words } = extractAccents(_words);
    const { data, subs } = encodeOwl(words);
    const accentData = accents.map(({ accent, follows, positionData }) => {
        return `${follows}${accent}${positionData}`;
    }).join(",");
    return {
        data: `0${subs}${data}`,
        accents: accentData
    };
}
// CLI
const content = fs_1.default.readFileSync(process.argv[2]).toString();
const words = content.split("\n").filter(Boolean);
const { data, accents } = encodeWords(words);
if (accents) {
    const rec = (0, decode_owla_js_1.decodeOwlA)(data, accents);
    console.log("DATA:     ", JSON.stringify(data));
    console.log("ACCENTS:  ", JSON.stringify(accents));
    console.log("LENGTH:   ", data.length);
    console.log("CHECKSUM: ", (0, id_js_1.id)(content));
    console.log("RATIO:    ", Math.trunc(100 * data.length / content.length) + "%");
    if (rec.join("\n") !== words.join("\n")) {
        throw new Error("no match!");
    }
}
else {
    const rec = (0, decode_owl_js_1.decodeOwl)(data);
    console.log("DATA:     ", JSON.stringify(data));
    console.log("LENGTH:   ", data.length);
    console.log("CHECKSUM: ", (0, id_js_1.id)(content));
    console.log("RATIO:    ", Math.trunc(100 * data.length / content.length) + "%");
    if (rec.join("\n") !== words.join("\n")) {
        throw new Error("no match!");
    }
}
//# sourceMappingURL=encode-latin.js.map