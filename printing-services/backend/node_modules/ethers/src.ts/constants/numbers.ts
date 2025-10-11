
/**
 *  A constant for the order N for the secp256k1 curve.
 *
 *  (**i.e.** ``0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141n``)
 */
export const N: bigint = BigInt("0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141");

/**
 *  A constant for the number of wei in a single ether.
 *
 *  (**i.e.** ``1000000000000000000n``)
 */
export const WeiPerEther: bigint = BigInt("1000000000000000000");

/**
 *  A constant for the maximum value for a ``uint256``.
 *
 *  (**i.e.** ``0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffn``)
 */
export const MaxUint256: bigint = BigInt("0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff");

/**
 *  A constant for the minimum value for an ``int256``.
 *
 *  (**i.e.** ``-8000000000000000000000000000000000000000000000000000000000000000n``)
 */
export const MinInt256: bigint = BigInt("0x8000000000000000000000000000000000000000000000000000000000000000") * BigInt(-1);

/**
 *  A constant for the maximum value for an ``int256``.
 *
 *  (**i.e.** ``0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffn``)
 */
export const MaxInt256: bigint = BigInt("0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff");
