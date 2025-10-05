/*! noble-curves - MIT License (c) 2022 Paul Miller (paulmillr.com) */
import { hmac } from '@noble/hashes/hmac';
import { concatBytes, randomBytes } from '@noble/hashes/utils';
import { weierstrass } from './abstract/weierstrass.js';
// connects noble-curves to noble-hashes
export function getHash(hash) {
    return {
        hash,
        hmac: (key, ...msgs) => hmac(hash, key, concatBytes(...msgs)),
        randomBytes,
    };
}
export function createCurve(curveDef, defHash) {
    const create = (hash) => weierstrass({ ...curveDef, ...getHash(hash) });
    return Object.freeze({ ...create(defHash), create });
}
//# sourceMappingURL=_shortw_utils.js.map