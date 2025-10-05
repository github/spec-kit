import type { BigNumberish, BytesLike } from "../utils/index.js";
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
/**
 *  A Signature  @TODO
 *
 *
 *  @_docloc: api/crypto:Signing
 */
export declare class Signature {
    #private;
    /**
     *  The ``r`` value for a signature.
     *
     *  This represents the ``x`` coordinate of a "reference" or
     *  challenge point, from which the ``y`` can be computed.
     */
    get r(): string;
    set r(value: BytesLike);
    /**
     *  The ``s`` value for a signature.
     */
    get s(): string;
    set s(_value: BytesLike);
    /**
     *  Return the s value, unchecked for EIP-2 compliance.
     *
     *  This should generally not be used and is for situations where
     *  a non-canonical S value might be relevant, such as Frontier blocks
     *  that were mined prior to EIP-2 or invalid Authorization List
     *  signatures.
     */
    get _s(): string;
    /**
     *  Returns true if the Signature is valid for [[link-eip-2]] signatures.
     */
    isValid(): boolean;
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
    get v(): 27 | 28;
    set v(value: BigNumberish);
    /**
     *  The EIP-155 ``v`` for legacy transactions. For non-legacy
     *  transactions, this value is ``null``.
     */
    get networkV(): null | bigint;
    /**
     *  The chain ID for EIP-155 legacy transactions. For non-legacy
     *  transactions, this value is ``null``.
     */
    get legacyChainId(): null | bigint;
    /**
     *  The ``yParity`` for the signature.
     *
     *  See ``v`` for more details on how this value is used.
     */
    get yParity(): 0 | 1;
    /**
     *  The [[link-eip-2098]] compact representation of the ``yParity``
     *  and ``s`` compacted into a single ``bytes32``.
     */
    get yParityAndS(): string;
    /**
     *  The [[link-eip-2098]] compact representation.
     */
    get compactSerialized(): string;
    /**
     *  The serialized representation.
     */
    get serialized(): string;
    /**
     *  @private
     */
    constructor(guard: any, r: string, s: string, v: 27 | 28);
    /**
     *  Returns a new identical [[Signature]].
     */
    clone(): Signature;
    /**
     *  Returns a representation that is compatible with ``JSON.stringify``.
     */
    toJSON(): any;
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
    static getChainId(v: BigNumberish): bigint;
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
    static getChainIdV(chainId: BigNumberish, v: 27 | 28): bigint;
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
    static getNormalizedV(v: BigNumberish): 27 | 28;
    /**
     *  Creates a new [[Signature]].
     *
     *  If no %%sig%% is provided, a new [[Signature]] is created
     *  with default values.
     *
     *  If %%sig%% is a string, it is parsed.
     */
    static from(sig?: SignatureLike): Signature;
}
//# sourceMappingURL=signature.d.ts.map