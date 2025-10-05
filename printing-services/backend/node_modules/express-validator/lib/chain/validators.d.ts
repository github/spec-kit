import { CustomValidator, ErrorMessage, FieldMessageFactory } from '../base';
import * as Options from '../options';
export type ExistsOptions = {
    /**
     * Defines which kind of value makes a field _NOT_ exist.
     *
     * - `undefined`: only `undefined` values; equivalent to `value !== undefined`
     * - `null`: only `undefined` and `null` values; equivalent to `value != null`
     * - `falsy`: all falsy values; equivalent to `!!value`
     *
     * @default 'undefined'
     */
    values?: 'undefined' | 'null' | 'falsy';
    /**
     * Whether a field whose value is falsy should be considered non-existent.
     * @default false
     * @deprecated  Use `values` instead
     */
    checkFalsy?: boolean;
    /**
     * Whether a field whose value is `null` or `undefined` should be considered non-existent.
     * @default false
     * @deprecated  Use `values` instead
     */
    checkNull?: boolean;
};
export interface Validators<Return> {
    /**
     * Negates the result of the next validator.
     *
     * @example check('weekday').not().isIn(['sunday', 'saturday'])
     * @returns the current validation chain
     */
    not(): Return;
    /**
     * Sets the error message for the previous validator.
     *
     * @param message the message, which can be any value, or a function for dynamically creating the
     *                error message based on the field value
     * @returns the current validation chain
     */
    withMessage(message: FieldMessageFactory | ErrorMessage): Return;
    /**
     * Adds a custom validator to the validation chain.
     *
     * @param validator the custom validator
     * @returns the current validation chain
     */
    custom(validator: CustomValidator): Return;
    /**
     * Adds a validator to check that the fields exist in the request.
     * By default, this means that the value of the fields may not be `undefined`;
     * all other values are acceptable.
     *
     * @param options
     * @returns the current validation chain
     */
    exists(options?: ExistsOptions): Return;
    /**
     * Adds a validator to check if a value is an array.
     *
     * @param options
     * @returns the current validation chain
     */
    isArray(options?: {
        min?: number;
        max?: number;
    }): Return;
    /**
     * Adds a validator to check if a value is an object.
     *
     * @param options
     * @returns the current validation chain
     */
    isObject(options?: {
        strict?: boolean;
    }): Return;
    /**
     * Adds a validator to check if a value is a string.
     *
     * @returns the current validation chain
     */
    isString(): Return;
    /**
     * Adds a validator to check if a value is a ULID.
     *
     * @returns the current validation chain
     */
    isULID(): Return;
    /**
     * Adds a validator to check if a value is not empty; that is, a string with length of 1 or more.
     *
     * @param options
     * @returns the current validation chain
     */
    notEmpty(options?: Options.IsEmptyOptions): Return;
    contains(elem: any, options?: Options.ContainsOptions): Return;
    equals(comparison: string): Return;
    isAbaRouting(): Return;
    isAfter(dateOrOptions?: string | Options.IsAfterOptions): Return;
    isAlpha(locale?: Options.AlphaLocale, options?: Options.IsAlphaOptions): Return;
    isAlphanumeric(locale?: Options.AlphanumericLocale, options?: Options.IsAlphanumericOptions): Return;
    isAscii(): Return;
    isBase32(options?: Options.IsBase32Options): Return;
    isBase58(): Return;
    isBase64(options?: Options.IsBase64Options): Return;
    isBefore(date?: string): Return;
    isBIC(): Return;
    isBoolean(options?: Options.IsBooleanOptions): Return;
    isBtcAddress(): Return;
    isByteLength(options: Options.MinMaxExtendedOptions): Return;
    isCreditCard(options?: Options.IsCreditCard): Return;
    isCurrency(options?: Options.IsCurrencyOptions): Return;
    isDataURI(): Return;
    isDate(options?: Options.IsDateOptions): Return;
    isDecimal(options?: Options.IsDecimalOptions): Return;
    isDivisibleBy(number: number): Return;
    isEAN(): Return;
    isEmail(options?: Options.IsEmailOptions): Return;
    isEmpty(options?: Options.IsEmptyOptions): Return;
    isEthereumAddress(): Return;
    isFQDN(options?: Options.IsFQDNOptions): Return;
    isFloat(options?: Options.IsFloatOptions): Return;
    isFreightContainerID(): Return;
    isFullWidth(): Return;
    isHalfWidth(): Return;
    isHash(algorithm: Options.HashAlgorithm): Return;
    isHexColor(): Return;
    isHexadecimal(): Return;
    isHSL(): Return;
    isIBAN(options?: Options.IsIBANOptions): Return;
    isIdentityCard(locale?: Options.IdentityCardLocale): Return;
    isIMEI(options?: Options.IsIMEIOptions): Return;
    isIP(version?: Options.IPVersion): Return;
    isIPRange(version?: Options.IPVersion): Return;
    isISBN(versionOrOptions?: number | Options.IsISBNOptions): Return;
    isISSN(options?: Options.IsISSNOptions): Return;
    isISIN(): Return;
    isISO6346(): Return;
    isISO6391(): Return;
    isISO8601(options?: Options.IsISO8601Options): Return;
    isISO31661Alpha2(): Return;
    isISO31661Alpha3(): Return;
    isISO4217(): Return;
    isISRC(): Return;
    isIn(values: readonly any[]): Return;
    isInt(options?: Options.IsIntOptions): Return;
    isJSON(options?: Options.IsJSONOptions): Return;
    isJWT(): Return;
    isLatLong(options?: Options.IsLatLongOptions): Return;
    isLength(options: Options.MinMaxOptions): Return;
    isLicensePlate(locale: Options.IsLicensePlateLocale): Return;
    isLocale(): Return;
    isLowercase(): Return;
    isLuhnNumber(): Return;
    isMagnetURI(): Return;
    isMailtoURI(options?: Options.IsEmailOptions): Return;
    isMACAddress(options?: Options.IsMACAddressOptions): Return;
    isMD5(): Return;
    isMimeType(): Return;
    isMobilePhone(locale: Options.MobilePhoneLocale | readonly Options.MobilePhoneLocale[], options?: Options.IsMobilePhoneOptions): Return;
    isMongoId(): Return;
    isMultibyte(): Return;
    isNumeric(options?: Options.IsNumericOptions): Return;
    isOctal(): Return;
    isPassportNumber(countryCode?: Options.PassportCountryCode): Return;
    isPort(): Return;
    isPostalCode(locale: Options.PostalCodeLocale): Return;
    isRgbColor(includePercentValues?: boolean): Return;
    isRFC3339(): Return;
    isSemVer(): Return;
    isSlug(): Return;
    isStrongPassword(options?: Options.IsStrongPasswordOptions): Return;
    isSurrogatePair(): Return;
    isTaxID(locale: Options.TaxIDLocale): Return;
    isTime(options: Options.IsTimeOptions): Return;
    isURL(options?: Options.IsURLOptions): Return;
    isUUID(version?: Options.UUIDVersion): Return;
    isUppercase(): Return;
    isVariableWidth(): Return;
    isVAT(countryCode: Options.VATCountryCode): Return;
    isWhitelisted(chars: string | readonly string[]): Return;
    matches(pattern: RegExp | string, modifiers?: string): Return;
}
