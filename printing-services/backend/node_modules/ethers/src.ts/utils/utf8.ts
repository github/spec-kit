/**
 *  Using strings in Ethereum (or any security-basd system) requires
 *  additional care. These utilities attempt to mitigate some of the
 *  safety issues as well as provide the ability to recover and analyse
 *  strings.
 *
 *  @_subsection api/utils:Strings and UTF-8  [about-strings]
 */
import { getBytes } from "./data.js";
import { assertArgument, assertNormalize } from "./errors.js";

import type { BytesLike } from "./index.js";


///////////////////////////////

/**
 *  The stanard normalization forms.
 */
export type UnicodeNormalizationForm = "NFC" | "NFD" | "NFKC" | "NFKD";

/**
 *  When using the UTF-8 error API the following errors can be intercepted
 *  and processed as the %%reason%% passed to the [[Utf8ErrorFunc]].
 *
 *  **``"UNEXPECTED_CONTINUE"``** - a continuation byte was present where there
 *  was nothing to continue.
 *
 *  **``"BAD_PREFIX"``** - an invalid (non-continuation) byte to start a
 *  UTF-8 codepoint was found.
 *
 *  **``"OVERRUN"``** - the string is too short to process the expected
 *  codepoint length.
 *
 *  **``"MISSING_CONTINUE"``** - a missing continuation byte was expected but
 *  not found. The %%offset%% indicates the index the continuation byte
 *  was expected at.
 *
 *  **``"OUT_OF_RANGE"``** - the computed code point is outside the range
 *  for UTF-8. The %%badCodepoint%% indicates the computed codepoint, which was
 *  outside the valid UTF-8 range.
 *
 *  **``"UTF16_SURROGATE"``** - the UTF-8 strings contained a UTF-16 surrogate
 *  pair. The %%badCodepoint%% is the computed codepoint, which was inside the
 *  UTF-16 surrogate range.
 *
 *  **``"OVERLONG"``** - the string is an overlong representation. The
 *  %%badCodepoint%% indicates the computed codepoint, which has already
 *  been bounds checked.
 *
 *
 *  @returns string
 */
export type Utf8ErrorReason = "UNEXPECTED_CONTINUE" | "BAD_PREFIX" | "OVERRUN" |
    "MISSING_CONTINUE" | "OUT_OF_RANGE" | "UTF16_SURROGATE" | "OVERLONG";


/**
 *  A callback that can be used with [[toUtf8String]] to analysis or
 *  recovery from invalid UTF-8 data.
 *
 *  Parsing UTF-8 data is done through a simple Finite-State Machine (FSM)
 *  which calls the ``Utf8ErrorFunc`` if a fault is detected.
 *
 *  The %%reason%% indicates where in the FSM execution the fault
 *  occurred and the %%offset%% indicates where the input failed.
 *
 *  The %%bytes%% represents the raw UTF-8 data that was provided and
 *  %%output%% is the current array of UTF-8 code-points, which may
 *  be updated by the ``Utf8ErrorFunc``.
 *
 *  The value of the %%badCodepoint%% depends on the %%reason%%. See
 *  [[Utf8ErrorReason]] for details.
 *
 *  The function should return the number of bytes that should be skipped
 *  when control resumes to the FSM.
 */
export type Utf8ErrorFunc = (reason: Utf8ErrorReason, offset: number, bytes: Uint8Array, output: Array<number>, badCodepoint?: number) => number;


function errorFunc(reason: Utf8ErrorReason, offset: number, bytes: Uint8Array, output: Array<number>, badCodepoint?: number): number {
    assertArgument(false, `invalid codepoint at offset ${ offset }; ${ reason }`, "bytes", bytes);
}

function ignoreFunc(reason: Utf8ErrorReason, offset: number, bytes: Uint8Array, output: Array<number>, badCodepoint?: number): number {

    // If there is an invalid prefix (including stray continuation), skip any additional continuation bytes
    if (reason === "BAD_PREFIX" || reason === "UNEXPECTED_CONTINUE") {
        let i = 0;
        for (let o = offset + 1; o < bytes.length; o++) {
            if (bytes[o] >> 6 !== 0x02) { break; }
            i++;
        }
        return i;
    }

    // This byte runs us past the end of the string, so just jump to the end
    // (but the first byte was read already read and therefore skipped)
    if (reason === "OVERRUN") {
        return bytes.length - offset - 1;
    }

    // Nothing to skip
    return 0;
}

function replaceFunc(reason: Utf8ErrorReason, offset: number, bytes: Uint8Array, output: Array<number>, badCodepoint?: number): number {

    // Overlong representations are otherwise "valid" code points; just non-deistingtished
    if (reason === "OVERLONG") {
        assertArgument(typeof(badCodepoint) === "number", "invalid bad code point for replacement", "badCodepoint", badCodepoint);
        output.push(badCodepoint);
        return 0;
    }

    // Put the replacement character into the output
    output.push(0xfffd);

    // Otherwise, process as if ignoring errors
    return ignoreFunc(reason, offset, bytes, output, badCodepoint);
}

/**
 *  A handful of popular, built-in UTF-8 error handling strategies.
 *
 *  **``"error"``** - throws on ANY illegal UTF-8 sequence or
 *  non-canonical (overlong) codepoints (this is the default)
 *
 *  **``"ignore"``** - silently drops any illegal UTF-8 sequence
 *  and accepts non-canonical (overlong) codepoints
 *
 *  **``"replace"``** - replace any illegal UTF-8 sequence with the
 *  UTF-8 replacement character (i.e. ``"\\ufffd"``) and accepts
 *  non-canonical (overlong) codepoints
 *
 *  @returns: Record<"error" | "ignore" | "replace", Utf8ErrorFunc>
 */
export const Utf8ErrorFuncs: Readonly<Record<"error" | "ignore" | "replace", Utf8ErrorFunc>> = Object.freeze({
    error: errorFunc,
    ignore: ignoreFunc,
    replace: replaceFunc
});

// http://stackoverflow.com/questions/13356493/decode-utf-8-with-javascript#13691499
function getUtf8CodePoints(_bytes: BytesLike, onError?: Utf8ErrorFunc): Array<number> {
    if (onError == null) { onError = Utf8ErrorFuncs.error; }

    const bytes = getBytes(_bytes, "bytes");

    const result: Array<number> = [];
    let i = 0;

    // Invalid bytes are ignored
    while(i < bytes.length) {

        const c = bytes[i++];

        // 0xxx xxxx
        if (c >> 7 === 0) {
            result.push(c);
            continue;
        }

        // Multibyte; how many bytes left for this character?
        let extraLength: null | number = null;
        let overlongMask: null | number = null;

        // 110x xxxx 10xx xxxx
        if ((c & 0xe0) === 0xc0) {
            extraLength = 1;
            overlongMask = 0x7f;

        // 1110 xxxx 10xx xxxx 10xx xxxx
        } else if ((c & 0xf0) === 0xe0) {
            extraLength = 2;
            overlongMask = 0x7ff;

        // 1111 0xxx 10xx xxxx 10xx xxxx 10xx xxxx
        } else if ((c & 0xf8) === 0xf0) {
            extraLength = 3;
            overlongMask = 0xffff;

        } else {
            if ((c & 0xc0) === 0x80) {
                i += onError("UNEXPECTED_CONTINUE", i - 1, bytes, result);
            } else {
                i += onError("BAD_PREFIX", i - 1, bytes, result);
            }
            continue;
        }

        // Do we have enough bytes in our data?
        if (i - 1 + extraLength >= bytes.length) {
            i += onError("OVERRUN", i - 1, bytes, result);
            continue;
        }

        // Remove the length prefix from the char
        let res: null | number = c & ((1 << (8 - extraLength - 1)) - 1);

        for (let j = 0; j < extraLength; j++) {
            let nextChar = bytes[i];

            // Invalid continuation byte
            if ((nextChar & 0xc0) != 0x80) {
                i += onError("MISSING_CONTINUE", i, bytes, result);
                res = null;
                break;
            };

            res = (res << 6) | (nextChar & 0x3f);
            i++;
        }

        // See above loop for invalid continuation byte
        if (res === null) { continue; }

        // Maximum code point
        if (res > 0x10ffff) {
            i += onError("OUT_OF_RANGE", i - 1 - extraLength, bytes, result, res);
            continue;
        }

        // Reserved for UTF-16 surrogate halves
        if (res >= 0xd800 && res <= 0xdfff) {
            i += onError("UTF16_SURROGATE", i - 1 - extraLength, bytes, result, res);
            continue;
        }

        // Check for overlong sequences (more bytes than needed)
        if (res <= overlongMask) {
            i += onError("OVERLONG", i - 1 - extraLength, bytes, result, res);
            continue;
        }

        result.push(res);
    }

    return result;
}

// http://stackoverflow.com/questions/18729405/how-to-convert-utf8-string-to-byte-array

/**
 *  Returns the UTF-8 byte representation of %%str%%.
 *
 *  If %%form%% is specified, the string is normalized.
 */
export function toUtf8Bytes(str: string, form?: UnicodeNormalizationForm): Uint8Array {
    assertArgument(typeof(str) === "string", "invalid string value", "str", str);

    if (form != null) {
        assertNormalize(form);
        str = str.normalize(form);
    }

    let result: Array<number> = [];
    for (let i = 0; i < str.length; i++) {
        const c = str.charCodeAt(i);

        if (c < 0x80) {
            result.push(c);

        } else if (c < 0x800) {
            result.push((c >> 6) | 0xc0);
            result.push((c & 0x3f) | 0x80);

        } else if ((c & 0xfc00) == 0xd800) {
            i++;
            const c2 = str.charCodeAt(i);

            assertArgument(i < str.length && ((c2 & 0xfc00) === 0xdc00),
                "invalid surrogate pair", "str", str);

            // Surrogate Pair
            const pair = 0x10000 + ((c & 0x03ff) << 10) + (c2 & 0x03ff);
            result.push((pair >> 18) | 0xf0);
            result.push(((pair >> 12) & 0x3f) | 0x80);
            result.push(((pair >> 6) & 0x3f) | 0x80);
            result.push((pair & 0x3f) | 0x80);

        } else {
            result.push((c >> 12) | 0xe0);
            result.push(((c >> 6) & 0x3f) | 0x80);
            result.push((c & 0x3f) | 0x80);
        }
    }

    return new Uint8Array(result);
};

//export 
function _toUtf8String(codePoints: Array<number>): string {
    return codePoints.map((codePoint) => {
        if (codePoint <= 0xffff) {
            return String.fromCharCode(codePoint);
        }
        codePoint -= 0x10000;
        return String.fromCharCode(
            (((codePoint >> 10) & 0x3ff) + 0xd800),
            ((codePoint & 0x3ff) + 0xdc00)
        );
    }).join("");
}

/**
 *  Returns the string represented by the UTF-8 data %%bytes%%.
 *
 *  When %%onError%% function is specified, it is called on UTF-8
 *  errors allowing recovery using the [[Utf8ErrorFunc]] API.
 *  (default: [error](Utf8ErrorFuncs))
 */
export function toUtf8String(bytes: BytesLike, onError?: Utf8ErrorFunc): string {
    return _toUtf8String(getUtf8CodePoints(bytes, onError));
}

/**
 *  Returns the UTF-8 code-points for %%str%%.
 *
 *  If %%form%% is specified, the string is normalized.
 */
export function toUtf8CodePoints(str: string, form?: UnicodeNormalizationForm): Array<number> {
    return getUtf8CodePoints(toUtf8Bytes(str, form));
}

