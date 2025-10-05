import { Options } from './typedef.js';
/**
 * @type ColorStopList - list of color stops
 */
type ColorStopList = [string, string, ...string[]];
/**
 * @typedef ValidateGradientLine - validate gradient line
 * @property line - gradient line
 * @property valid - result
 */
interface ValidateGradientLine {
    line: string;
    valid: boolean;
}
/**
 * @typedef ValidateColorStops - validate color stops
 * @property colorStops - list of color stops
 * @property valid - result
 */
interface ValidateColorStops {
    colorStops: string[];
    valid: boolean;
}
/**
 * @typedef Gradient - parsed CSS gradient
 * @property value - input value
 * @property type - gradient type
 * @property [gradientLine] - gradient line
 * @property colorStopList - list of color stops
 */
interface Gradient {
    value: string;
    type: string;
    gradientLine?: string;
    colorStopList: ColorStopList;
}
/**
 * get gradient type
 * @param value - gradient value
 * @returns gradient type
 */
export declare const getGradientType: (value: string) => string;
/**
 * validate gradient line
 * @param value - gradient line value
 * @param type - gradient type
 * @returns result
 */
export declare const validateGradientLine: (value: string, type: string) => ValidateGradientLine;
/**
 * validate color stop list
 * @param list
 * @param type
 * @param [opt]
 * @returns result
 */
export declare const validateColorStopList: (list: string[], type: string, opt?: Options) => ValidateColorStops;
/**
 * parse CSS gradient
 * @param value - gradient value
 * @param [opt] - options
 * @returns parsed result
 */
export declare const parseGradient: (value: string, opt?: Options) => Gradient | null;
/**
 * resolve CSS gradient
 * @param value - CSS value
 * @param [opt] - options
 * @returns result
 */
export declare const resolveGradient: (value: string, opt?: Options) => string;
/**
 * is CSS gradient
 * @param value - CSS value
 * @param [opt] - options
 * @returns result
 */
export declare const isGradient: (value: string, opt?: Options) => boolean;
export {};
