import type { BytesLike } from "./index.js";
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
export type Utf8ErrorReason = "UNEXPECTED_CONTINUE" | "BAD_PREFIX" | "OVERRUN" | "MISSING_CONTINUE" | "OUT_OF_RANGE" | "UTF16_SURROGATE" | "OVERLONG";
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
export declare const Utf8ErrorFuncs: Readonly<Record<"error" | "ignore" | "replace", Utf8ErrorFunc>>;
/**
 *  Returns the UTF-8 byte representation of %%str%%.
 *
 *  If %%form%% is specified, the string is normalized.
 */
export declare function toUtf8Bytes(str: string, form?: UnicodeNormalizationForm): Uint8Array;
/**
 *  Returns the string represented by the UTF-8 data %%bytes%%.
 *
 *  When %%onError%% function is specified, it is called on UTF-8
 *  errors allowing recovery using the [[Utf8ErrorFunc]] API.
 *  (default: [error](Utf8ErrorFuncs))
 */
export declare function toUtf8String(bytes: BytesLike, onError?: Utf8ErrorFunc): string;
/**
 *  Returns the UTF-8 code-points for %%str%%.
 *
 *  If %%form%% is specified, the string is normalized.
 */
export declare function toUtf8CodePoints(str: string, form?: UnicodeNormalizationForm): Array<number>;
//# sourceMappingURL=utf8.d.ts.map