"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.figures = void 0;
const is_unicode_supported_1 = require("./is-unicode-supported");
const FIGURES_MAIN = {
    warning: '⚠',
    cross: '✖',
    arrowDown: '↓',
    tick: '✔',
    arrowRight: '→',
    pointer: '❯',
    checkboxOn: '☒',
    arrowLeft: '←',
    squareSmallFilled: '◼',
    pointerSmall: '›'
};
const FIGURES_FALLBACK = {
    ...FIGURES_MAIN,
    warning: '‼',
    cross: '×',
    tick: '√',
    pointer: '>',
    checkboxOn: '[×]',
    squareSmallFilled: '■'
};
exports.figures = (0, is_unicode_supported_1.isUnicodeSupported)() ? FIGURES_MAIN : FIGURES_FALLBACK;
