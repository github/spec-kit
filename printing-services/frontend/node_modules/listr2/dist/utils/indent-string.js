"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.indentString = void 0;
function indentString(string, count) {
    return string.replace(/^(?!\s*$)/gm, ' '.repeat(count));
}
exports.indentString = indentString;
