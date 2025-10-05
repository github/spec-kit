/*! noble-curves - MIT License (c) 2022 Paul Miller (paulmillr.com) */
import { sha512 } from '@noble/hashes/sha512';
import { concatBytes, randomBytes, utf8ToBytes } from '@noble/hashes/utils';
import { twistedEdwards } from './abstract/edwards.js';
import { blake2s } from '@noble/hashes/blake2s';
import { Field } from './abstract/modular.js';
/**
 * jubjub Twisted Edwards curve.
 * https://neuromancer.sk/std/other/JubJub
 * jubjub does not use EdDSA, so `hash`/sha512 params are passed because interface expects them.
 */
export const jubjub = /* @__PURE__ */ twistedEdwards({
    // Params: a, d
    a: BigInt('0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000000'),
    d: BigInt('0x2a9318e74bfa2b48f5fd9207e6bd7fd4292d7f6d37579d2601065fd6d6343eb1'),
    // Finite field 𝔽p over which we'll do calculations
    // Same value as bls12-381 Fr (not Fp)
    Fp: Field(BigInt('0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001')),
    // Subgroup order: how many points curve has
    n: BigInt('0xe7db4ea6533afa906673b0101343b00a6682093ccc81082d0970e5ed6f72cb7'),
    // Cofactor
    h: BigInt(8),
    // Base point (x, y) aka generator point
    Gx: BigInt('0x11dafe5d23e1218086a365b99fbf3d3be72f6afd7d1f72623e6b071492d1122b'),
    Gy: BigInt('0x1d523cf1ddab1a1793132e78c866c0c33e26ba5cc220fed7cc3f870e59d292aa'),
    hash: sha512,
    randomBytes,
});
const GH_FIRST_BLOCK = utf8ToBytes('096b36a5804bfacef1691e173c366a47ff5ba84a44f26ddd7e8d9f79d5b42df0');
// Returns point at JubJub curve which is prime order and not zero
export function groupHash(tag, personalization) {
    const h = blake2s.create({ personalization, dkLen: 32 });
    h.update(GH_FIRST_BLOCK);
    h.update(tag);
    // NOTE: returns ExtendedPoint, in case it will be multiplied later
    let p = jubjub.ExtendedPoint.fromHex(h.digest());
    // NOTE: cannot replace with isSmallOrder, returns Point*8
    p = p.multiply(jubjub.CURVE.h);
    if (p.equals(jubjub.ExtendedPoint.ZERO))
        throw new Error('Point has small order');
    return p;
}
export function findGroupHash(m, personalization) {
    const tag = concatBytes(m, new Uint8Array([0]));
    for (let i = 0; i < 256; i++) {
        tag[tag.length - 1] = i;
        try {
            return groupHash(tag, personalization);
        }
        catch (e) { }
    }
    throw new Error('findGroupHash tag overflow');
}
//# sourceMappingURL=jubjub.js.map