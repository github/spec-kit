import { CustomSanitizer } from '../base';
import * as Options from '../options';
export interface Sanitizers<Return> {
    /**
     * Adds a custom sanitizer to the validation chain.
     *
     * @param sanitizer the custom sanitizer
     * @returns the current validation chain
     */
    customSanitizer(sanitizer: CustomSanitizer): Return;
    /**
     * Replaces the value of the field if it's one of `''`, `null`, `undefined` or `NaN`.
     *
     * @param default_value the value to replace with
     * @returns the current validation chain
     */
    default(default_value: any): Return;
    /**
     * Replaces a field's value with another value.
     *
     * @param values_to_replace one or more values that should be replaced
     * @param new_value the value to replace with
     * @returns the current validation chain
     */
    replace(values_to_replace: any, new_value: any): Return;
    blacklist(chars: string): Return;
    escape(): Return;
    unescape(): Return;
    ltrim(chars?: string): Return;
    normalizeEmail(options?: Options.NormalizeEmailOptions): Return;
    rtrim(chars?: string): Return;
    stripLow(keep_new_lines?: boolean): Return;
    toArray(): Return;
    toBoolean(strict?: boolean): Return;
    toDate(): Return;
    toFloat(): Return;
    toInt(radix?: number): Return;
    toLowerCase(): Return;
    toUpperCase(): Return;
    trim(chars?: string): Return;
    whitelist(chars: string): Return;
}
