import type { Addressable } from "../address/index.js";
import type { SignatureLike } from "../crypto/index.js";
import type { BigNumberish, Numeric } from "../utils/index.js";
export interface AuthorizationRequest {
    address: string | Addressable;
    nonce?: Numeric;
    chainId?: BigNumberish;
}
/**
 *  Computes the [[link-eip-7702]] authorization digest to sign.
 */
export declare function hashAuthorization(auth: AuthorizationRequest): string;
/**
 *  Return the address of the private key that produced
 *  the signature %%sig%% during signing for %%message%%.
 */
export declare function verifyAuthorization(auth: AuthorizationRequest, sig: SignatureLike): string;
//# sourceMappingURL=authorization.d.ts.map