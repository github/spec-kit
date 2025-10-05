
import { ZeroHash } from "../constants/index.js";
import {
    concat, dataLength, getBigInt, getBytes, getNumber, hexlify,
    toBeArray, isHexString, zeroPadValue,
    assertArgument, assertPrivate
} from "../utils/index.js";

import type {
    BigNumberish, BytesLike, Numeric
} from "../utils/index.js";


// Constants
const BN_0 = BigInt(0);
const BN_1 = BigInt(1);
const BN_2 = BigInt(2);
const BN_27 = BigInt(27);
const BN_28 = BigInt(28);
const BN_35 = BigInt(35);


const _guard = { };

// @TODO: Allow Uint8Array

/**
 *  A SignatureLike
 *
 *  @_docloc: api/crypto:Signing
 */
export type SignatureLike = Signature | string | {
    r: string;
    s: string;
    v: BigNumberish;
    yParity?: 0 | 1;
    yParityAndS?: string;
} | {
    r: string;
    yParityAndS: string;
    yParity?: 0 | 1;
    s?: string;
    v?: number;
} | {
    r: string;
    s: string;
    yParity: 0 | 1;
    v?: BigNumberish;
    yParityAndS?: string;
};

function toUint256(value: BigNumberish): string {
    return zeroPadValue(toBeArray(value), 32);
}

/**
 *  A Signature  @TODO
 *
 *
 *  @_docloc: api/crypto:Signing
 */
export class Signature {
    #r: string;
    #s: string;
    #v: 27 | 28;
    #networkV: null | bigint;

    /**
     *  The ``r`` value for a signature.
     *
     *  This represents the ``x`` coordinate of a "reference" or
     *  challenge point, from which the ``y`` can be computed.
     */
    get r(): string { return this.#r; }
    set r(value: BytesLike) {
        assertArgument(dataLength(value) === 32, "invalid r", "value", value);
        this.#r = hexlify(value);
    }

    /**
     *  The ``s`` value for a signature.
     */
    get s(): string {
        assertArgument(parseInt(this.#s.substring(0, 3)) < 8, "non-canonical s; use ._s", "s", this.#s);
        return this.#s;
    }
    set s(_value: BytesLike) {
        assertArgument(dataLength(_value) === 32, "invalid s", "value", _value);
        this.#s = hexlify(_value);
    }

    /**
     *  Return the s value, unchecked for EIP-2 compliance.
     *
     *  This should generally not be used and is for situations where
     *  a non-canonical S value might be relevant, such as Frontier blocks
     *  that were mined prior to EIP-2 or invalid Authorization List
     *  signatures.
     */
    get _s(): string { return this.#s; }

    /**
     *  Returns true if the Signature is valid for [[link-eip-2]] signatures.
     */
    isValid(): boolean {
        return (parseInt(this.#s.substring(0, 3)) < 8);
    }

    /**
     *  The ``v`` value for a signature.
     *
     *  Since a given ``x`` value for ``r`` has two possible values for
     *  its correspondin ``y``, the ``v`` indicates which of the two ``y``
     *  values to use.
     *
     *  It is normalized to the values ``27`` or ``28`` for legacy
     *  purposes.
     */
    get v(): 27 | 28 { return this.#v; }
    set v(value: BigNumberish) {
        const v = getNumber(value, "value");
        assertArgument(v === 27 || v === 28, "invalid v", "v", value);
        this.#v = v;
    }

    /**
     *  The EIP-155 ``v`` for legacy transactions. For non-legacy
     *  transactions, this value is ``null``.
     */
    get networkV(): null | bigint { return this.#networkV; }

    /**
     *  The chain ID for EIP-155 legacy transactions. For non-legacy
     *  transactions, this value is ``null``.
     */
    get legacyChainId(): null | bigint {
        const v = this.networkV;
        if (v == null) { return null; }
        return Signature.getChainId(v);
    }

    /**
     *  The ``yParity`` for the signature.
     *
     *  See ``v`` for more details on how this value is used.
     */
    get yParity(): 0 | 1 {
        return (this.v === 27) ? 0: 1;
    }

    /**
     *  The [[link-eip-2098]] compact representation of the ``yParity``
     *  and ``s`` compacted into a single ``bytes32``.
     */
    get yParityAndS(): string {
        // The EIP-2098 compact representation
        const yParityAndS = getBytes(this.s);
        if (this.yParity) { yParityAndS[0] |= 0x80; }
        return hexlify(yParityAndS);
    }

    /**
     *  The [[link-eip-2098]] compact representation.
     */
    get compactSerialized(): string {
        return concat([ this.r, this.yParityAndS ]);
    }

    /**
     *  The serialized representation.
     */
    get serialized(): string {
        return concat([ this.r, this.s, (this.yParity ? "0x1c": "0x1b") ]);
    }

    /**
     *  @private
     */
    constructor(guard: any, r: string, s: string, v: 27 | 28) {
        assertPrivate(guard, _guard, "Signature");
        this.#r = r;
        this.#s = s;
        this.#v = v;
        this.#networkV = null;
    }

    [Symbol.for('nodejs.util.inspect.custom')](): string {
        return `Signature { r: "${ this.r }", s: "${ this._s }"${ this.isValid() ? "": ', valid: "false"'}, yParity: ${ this.yParity }, networkV: ${ this.networkV } }`;
    }

    /**
     *  Returns a new identical [[Signature]].
     */
    clone(): Signature {
        const clone = new Signature(_guard, this.r, this._s, this.v);
        if (this.networkV) { clone.#networkV = this.networkV; }
        return clone;
    }

    /**
     *  Returns a representation that is compatible with ``JSON.stringify``.
     */
    toJSON(): any {
        const networkV = this.networkV;
        return {
            _type: "signature",
            networkV: ((networkV != null) ? networkV.toString(): null),
            r: this.r, s: this._s, v: this.v,
        };
    }

    /**
     *  Compute the chain ID from the ``v`` in a legacy EIP-155 transactions.
     *
     *  @example:
     *    Signature.getChainId(45)
     *    //_result:
     *
     *    Signature.getChainId(46)
     *    //_result:
     */
    static getChainId(v: BigNumberish): bigint {
        const bv = getBigInt(v, "v");

        // The v is not an EIP-155 v, so it is the unspecified chain ID
        if ((bv == BN_27) || (bv == BN_28)) { return BN_0; }

        // Bad value for an EIP-155 v
        assertArgument(bv >= BN_35, "invalid EIP-155 v", "v", v);

        return (bv - BN_35) / BN_2;
    }

    /**
     *  Compute the ``v`` for a chain ID for a legacy EIP-155 transactions.
     *
     *  Legacy transactions which use [[link-eip-155]] hijack the ``v``
     *  property to include the chain ID.
     *
     *  @example:
     *    Signature.getChainIdV(5, 27)
     *    //_result:
     *
     *    Signature.getChainIdV(5, 28)
     *    //_result:
     *
     */
    static getChainIdV(chainId: BigNumberish, v: 27 | 28): bigint {
        return (getBigInt(chainId) * BN_2) + BigInt(35 + v - 27);
    }

    /**
     *  Compute the normalized legacy transaction ``v`` from a ``yParirty``,
     *  a legacy transaction ``v`` or a legacy [[link-eip-155]] transaction.
     *
     *  @example:
     *    // The values 0 and 1 imply v is actually yParity
     *    Signature.getNormalizedV(0)
     *    //_result:
     *
     *    // Legacy non-EIP-1559 transaction (i.e. 27 or 28)
     *    Signature.getNormalizedV(27)
     *    //_result:
     *
     *    // Legacy EIP-155 transaction (i.e. >= 35)
     *    Signature.getNormalizedV(46)
     *    //_result:
     *
     *    // Invalid values throw
     *    Signature.getNormalizedV(5)
     *    //_error:
     */
    static getNormalizedV(v: BigNumberish): 27 | 28 {
        const bv = getBigInt(v);

        if (bv === BN_0 || bv === BN_27) { return 27; }
        if (bv === BN_1 || bv === BN_28) { return 28; }

        assertArgument(bv >= BN_35, "invalid v", "v", v);

        // Otherwise, EIP-155 v means odd is 27 and even is 28
        return (bv & BN_1) ? 27: 28;
    }

    /**
     *  Creates a new [[Signature]].
     *
     *  If no %%sig%% is provided, a new [[Signature]] is created
     *  with default values.
     *
     *  If %%sig%% is a string, it is parsed.
     */
    static from(sig?: SignatureLike): Signature {
        function assertError(check: unknown, message: string): asserts check {
            assertArgument(check, message, "signature", sig);
        };

        if (sig == null) {
            return new Signature(_guard, ZeroHash, ZeroHash, 27);
        }

        if (typeof(sig) === "string") {
            const bytes = getBytes(sig, "signature");
            if (bytes.length === 64) {
                const r = hexlify(bytes.slice(0, 32));
                const s = bytes.slice(32, 64);
                const v = (s[0] & 0x80) ? 28: 27;
                s[0] &= 0x7f;
                return new Signature(_guard, r, hexlify(s), v);
            }

            if (bytes.length === 65) {
                const r = hexlify(bytes.slice(0, 32));
                const s = hexlify(bytes.slice(32, 64));
                const v = Signature.getNormalizedV(bytes[64]);
                return new Signature(_guard, r, s, v);
            }

            assertError(false, "invalid raw signature length");
        }

        if (sig instanceof Signature) { return sig.clone(); }

        // Get r
        const _r = sig.r;
        assertError(_r != null, "missing r");
        const r = toUint256(_r);

        // Get s; by any means necessary (we check consistency below)
        const s = (function(s?: string, yParityAndS?: string) {
            if (s != null) { return toUint256(s); }

            if (yParityAndS != null) {
                assertError(isHexString(yParityAndS, 32), "invalid yParityAndS");
                const bytes = getBytes(yParityAndS);
                bytes[0] &= 0x7f;
                return hexlify(bytes);
            }

            assertError(false, "missing s");
        })(sig.s, sig.yParityAndS);

        // Get v; by any means necessary (we check consistency below)
        const { networkV, v } = (function(_v?: BigNumberish, yParityAndS?: string, yParity?: Numeric): { networkV?: bigint, v: 27 | 28 } {
            if (_v != null) {
                const v = getBigInt(_v);
                return {
                    networkV: ((v >= BN_35) ? v: undefined),
                    v: Signature.getNormalizedV(v)
                };
            }

            if (yParityAndS != null) {
                assertError(isHexString(yParityAndS, 32), "invalid yParityAndS");
                return { v: ((getBytes(yParityAndS)[0] & 0x80) ? 28: 27) };
            }

            if (yParity != null) {
                switch (getNumber(yParity, "sig.yParity")) {
                    case 0: return { v: 27 };
                    case 1: return { v: 28 };
                }
                assertError(false, "invalid yParity");
            }

            assertError(false, "missing v");
        })(sig.v, sig.yParityAndS, sig.yParity);

        const result = new Signature(_guard, r, s, v);
        if (networkV) { result.#networkV =  networkV; }

        // If multiple of v, yParity, yParityAndS we given, check they match
        assertError(sig.yParity == null || getNumber(sig.yParity, "sig.yParity") === result.yParity, "yParity mismatch");
        assertError(sig.yParityAndS == null || sig.yParityAndS === result.yParityAndS, "yParityAndS mismatch");

        return result;
    }
}
