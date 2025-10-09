"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.isUnicodeSupported = void 0;
function isUnicodeSupported() {
    if (process.platform !== 'win32') {
        return true;
    }
    /* istanbul ignore next */
    return (Boolean(process.env.CI) || Boolean(process.env.WT_SESSION) || process.env.TERM_PROGRAM === 'vscode' || process.env.TERM === 'xterm-256color' || process.env.TERM === 'alacritty');
}
exports.isUnicodeSupported = isUnicodeSupported;
