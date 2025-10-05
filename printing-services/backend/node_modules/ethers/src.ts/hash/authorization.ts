import { getAddress } from "../address/index.js";
import { keccak256 } from "../crypto/index.js";
import { recoverAddress } from "../transaction/index.js";
import {
    assertArgument, concat, encodeRlp, toBeArray
} from "../utils/index.js";

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
export function hashAuthorization(auth: AuthorizationRequest): string {
    assertArgument(typeof(auth.address) === "string", "invalid address for hashAuthorization", "auth.address", auth);
    return keccak256(concat([
        "0x05", encodeRlp([
            (auth.chainId != null) ? toBeArray(auth.chainId): "0x",
            getAddress(auth.address),
            (auth.nonce != null) ? toBeArray(auth.nonce): "0x",
        ])
    ]));
}

/**
 *  Return the address of the private key that produced
 *  the signature %%sig%% during signing for %%message%%.
 */
export function verifyAuthorization(auth: AuthorizationRequest, sig: SignatureLike): string {
    return recoverAddress(hashAuthorization(auth), sig);
}
