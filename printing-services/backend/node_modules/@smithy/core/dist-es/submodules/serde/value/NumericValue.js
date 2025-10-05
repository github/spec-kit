export class NumericValue {
    constructor(string, type) {
        this.string = string;
        this.type = type;
        let dot = 0;
        for (let i = 0; i < string.length; ++i) {
            const char = string.charCodeAt(i);
            if (i === 0 && char === 45) {
                continue;
            }
            if (char === 46) {
                if (dot) {
                    throw new Error("@smithy/core/serde - NumericValue must contain at most one decimal point.");
                }
                dot = 1;
                continue;
            }
            if (char < 48 || char > 57) {
                throw new Error(`@smithy/core/serde - NumericValue must only contain [0-9], at most one decimal point ".", and an optional negation prefix "-".`);
            }
        }
    }
    toString() {
        return this.string;
    }
    static [Symbol.hasInstance](object) {
        if (!object || typeof object !== "object") {
            return false;
        }
        const _nv = object;
        const prototypeMatch = NumericValue.prototype.isPrototypeOf(object);
        if (prototypeMatch) {
            return prototypeMatch;
        }
        if (typeof _nv.string === "string" &&
            typeof _nv.type === "string" &&
            _nv.constructor?.name?.endsWith("NumericValue")) {
            return true;
        }
        return prototypeMatch;
    }
}
export function nv(input) {
    return new NumericValue(String(input), "bigDecimal");
}
