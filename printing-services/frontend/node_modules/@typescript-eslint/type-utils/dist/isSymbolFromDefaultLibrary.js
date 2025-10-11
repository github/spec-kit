"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.isSymbolFromDefaultLibrary = void 0;
function isSymbolFromDefaultLibrary(program, symbol) {
    if (!symbol) {
        return false;
    }
    const declarations = symbol.getDeclarations() ?? [];
    for (const declaration of declarations) {
        const sourceFile = declaration.getSourceFile();
        if (program.isSourceFileDefaultLibrary(sourceFile)) {
            return true;
        }
    }
    return false;
}
exports.isSymbolFromDefaultLibrary = isSymbolFromDefaultLibrary;
//# sourceMappingURL=isSymbolFromDefaultLibrary.js.map