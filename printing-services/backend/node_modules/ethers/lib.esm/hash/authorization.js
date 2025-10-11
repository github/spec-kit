import { getAddress } from "../address/index.js";
import { keccak256 } from "../crypto/index.js";
import { recoverAddress } from "../transaction/index.js";
import { assertArgument, concat, encodeRlp, toBeArray } from "../utils/index.js";
/**
 *  Computes the [[link-eip-7702]] authorization digest to sign.
 */
export function hashAuthorization(auth) {
    assertArgument(typeof (auth.address) === "string", "invalid address for hashAuthorization", "auth.address", auth);
    return keccak256(concat([
        "0x05", encodeRlp([
            (auth.chainId != null) ? toBeArray(auth.chainId) : "0x",
            getAddress(auth.address),
            (auth.nonce != null) ? toBeArray(auth.nonce) : "0x",
        ])
    ]));
}
/**
 *  Return the address of the private key that produced
 *  the signature %%sig%% during signing for %%message%%.
 */
export function verifyAuthorization(auth, sig) {
    return recoverAddress(hashAuthorization(auth), sig);
}
//# sourceMappingURL=authorization.js.map