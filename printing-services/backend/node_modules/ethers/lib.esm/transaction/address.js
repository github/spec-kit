import { getAddress } from "../address/index.js";
import { keccak256, SigningKey } from "../crypto/index.js";
/**
 *  Returns the address for the %%key%%.
 *
 *  The key may be any standard form of public key or a private key.
 */
export function computeAddress(key) {
    let pubkey;
    if (typeof (key) === "string") {
        pubkey = SigningKey.computePublicKey(key, false);
    }
    else {
        pubkey = key.publicKey;
    }
    return getAddress(keccak256("0x" + pubkey.substring(4)).substring(26));
}
/**
 *  Returns the recovered address for the private key that was
 *  used to sign %%digest%% that resulted in %%signature%%.
 */
export function recoverAddress(digest, signature) {
    return computeAddress(SigningKey.recoverPublicKey(digest, signature));
}
//# sourceMappingURL=address.js.map