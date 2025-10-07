"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getWrappedCode = void 0;
function getWrappedCode(text, nodePrecedence, parentPrecedence) {
    return nodePrecedence > parentPrecedence ? text : `(${text})`;
}
exports.getWrappedCode = getWrappedCode;
//# sourceMappingURL=getWrappedCode.js.map