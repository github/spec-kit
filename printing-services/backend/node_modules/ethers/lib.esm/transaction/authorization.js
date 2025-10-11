import { getAddress } from "../address/index.js";
import { Signature } from "../crypto/index.js";
import { getBigInt } from "../utils/index.js";
export function authorizationify(auth) {
    return {
        address: getAddress(auth.address),
        nonce: getBigInt((auth.nonce != null) ? auth.nonce : 0),
        chainId: getBigInt((auth.chainId != null) ? auth.chainId : 0),
        signature: Signature.from(auth.signature)
    };
}
//# sourceMappingURL=authorization.js.map