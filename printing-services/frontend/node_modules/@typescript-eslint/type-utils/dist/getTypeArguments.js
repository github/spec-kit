"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getTypeArguments = void 0;
/**
 * @deprecated This is in TypeScript as of 3.7.
 */
function getTypeArguments(type, checker) {
    // getTypeArguments was only added in TS3.7
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
    if (checker.getTypeArguments) {
        return checker.getTypeArguments(type);
    }
    return type.typeArguments ?? [];
}
exports.getTypeArguments = getTypeArguments;
//# sourceMappingURL=getTypeArguments.js.map