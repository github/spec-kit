/*!
 * CSS color - Resolve, parse, convert CSS color.
 * @license MIT
 * @copyright asamuzaK (Kazz)
 * @see {@link https://github.com/asamuzaK/cssColor/blob/main/LICENSE}
 */
export { convert } from './js/convert.js';
export { resolve } from './js/resolve.js';
export declare const utils: {
    cssCalc: (value: string, opt?: import('./js/typedef.js').Options) => string;
    cssVar: (value: string, opt?: import('./js/typedef.js').Options) => string;
    extractDashedIdent: (value: string) => string[];
    isColor: (value: unknown, opt?: import('./js/typedef.js').Options) => boolean;
    isGradient: (value: string, opt?: import('./js/typedef.js').Options) => boolean;
    resolveGradient: (value: string, opt?: import('./js/typedef.js').Options) => string;
    splitValue: (value: string, opt?: import('./js/typedef.js').Options) => string[];
};
