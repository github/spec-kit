import { BLAKE2, SIGMA } from './_blake2.js';
import u64 from './_u64.js';
import { toBytes, u32, wrapConstructorWithOpts } from './utils.js';
// Same as SHA-512 but LE
// prettier-ignore
const IV = /* @__PURE__ */ new Uint32Array([
    0xf3bcc908, 0x6a09e667, 0x84caa73b, 0xbb67ae85, 0xfe94f82b, 0x3c6ef372, 0x5f1d36f1, 0xa54ff53a,
    0xade682d1, 0x510e527f, 0x2b3e6c1f, 0x9b05688c, 0xfb41bd6b, 0x1f83d9ab, 0x137e2179, 0x5be0cd19
]);
// Temporary buffer
const BUF = /* @__PURE__ */ new Uint32Array(32);
// Mixing function G splitted in two halfs
function G1(a, b, c, d, msg, x) {
    // NOTE: V is LE here
    const Xl = msg[x], Xh = msg[x + 1]; // prettier-ignore
    let Al = BUF[2 * a], Ah = BUF[2 * a + 1]; // prettier-ignore
    let Bl = BUF[2 * b], Bh = BUF[2 * b + 1]; // prettier-ignore
    let Cl = BUF[2 * c], Ch = BUF[2 * c + 1]; // prettier-ignore
    let Dl = BUF[2 * d], Dh = BUF[2 * d + 1]; // prettier-ignore
    // v[a] = (v[a] + v[b] + x) | 0;
    let ll = u64.add3L(Al, Bl, Xl);
    Ah = u64.add3H(ll, Ah, Bh, Xh);
    Al = ll | 0;
    // v[d] = rotr(v[d] ^ v[a], 32)
    ({ Dh, Dl } = { Dh: Dh ^ Ah, Dl: Dl ^ Al });
    ({ Dh, Dl } = { Dh: u64.rotr32H(Dh, Dl), Dl: u64.rotr32L(Dh, Dl) });
    // v[c] = (v[c] + v[d]) | 0;
    ({ h: Ch, l: Cl } = u64.add(Ch, Cl, Dh, Dl));
    // v[b] = rotr(v[b] ^ v[c], 24)
    ({ Bh, Bl } = { Bh: Bh ^ Ch, Bl: Bl ^ Cl });
    ({ Bh, Bl } = { Bh: u64.rotrSH(Bh, Bl, 24), Bl: u64.rotrSL(Bh, Bl, 24) });
    (BUF[2 * a] = Al), (BUF[2 * a + 1] = Ah);
    (BUF[2 * b] = Bl), (BUF[2 * b + 1] = Bh);
    (BUF[2 * c] = Cl), (BUF[2 * c + 1] = Ch);
    (BUF[2 * d] = Dl), (BUF[2 * d + 1] = Dh);
}
function G2(a, b, c, d, msg, x) {
    // NOTE: V is LE here
    const Xl = msg[x], Xh = msg[x + 1]; // prettier-ignore
    let Al = BUF[2 * a], Ah = BUF[2 * a + 1]; // prettier-ignore
    let Bl = BUF[2 * b], Bh = BUF[2 * b + 1]; // prettier-ignore
    let Cl = BUF[2 * c], Ch = BUF[2 * c + 1]; // prettier-ignore
    let Dl = BUF[2 * d], Dh = BUF[2 * d + 1]; // prettier-ignore
    // v[a] = (v[a] + v[b] + x) | 0;
    let ll = u64.add3L(Al, Bl, Xl);
    Ah = u64.add3H(ll, Ah, Bh, Xh);
    Al = ll | 0;
    // v[d] = rotr(v[d] ^ v[a], 16)
    ({ Dh, Dl } = { Dh: Dh ^ Ah, Dl: Dl ^ Al });
    ({ Dh, Dl } = { Dh: u64.rotrSH(Dh, Dl, 16), Dl: u64.rotrSL(Dh, Dl, 16) });
    // v[c] = (v[c] + v[d]) | 0;
    ({ h: Ch, l: Cl } = u64.add(Ch, Cl, Dh, Dl));
    // v[b] = rotr(v[b] ^ v[c], 63)
    ({ Bh, Bl } = { Bh: Bh ^ Ch, Bl: Bl ^ Cl });
    ({ Bh, Bl } = { Bh: u64.rotrBH(Bh, Bl, 63), Bl: u64.rotrBL(Bh, Bl, 63) });
    (BUF[2 * a] = Al), (BUF[2 * a + 1] = Ah);
    (BUF[2 * b] = Bl), (BUF[2 * b + 1] = Bh);
    (BUF[2 * c] = Cl), (BUF[2 * c + 1] = Ch);
    (BUF[2 * d] = Dl), (BUF[2 * d + 1] = Dh);
}
class BLAKE2b extends BLAKE2 {
    constructor(opts = {}) {
        super(128, opts.dkLen === undefined ? 64 : opts.dkLen, opts, 64, 16, 16);
        // Same as SHA-512, but LE
        this.v0l = IV[0] | 0;
        this.v0h = IV[1] | 0;
        this.v1l = IV[2] | 0;
        this.v1h = IV[3] | 0;
        this.v2l = IV[4] | 0;
        this.v2h = IV[5] | 0;
        this.v3l = IV[6] | 0;
        this.v3h = IV[7] | 0;
        this.v4l = IV[8] | 0;
        this.v4h = IV[9] | 0;
        this.v5l = IV[10] | 0;
        this.v5h = IV[11] | 0;
        this.v6l = IV[12] | 0;
        this.v6h = IV[13] | 0;
        this.v7l = IV[14] | 0;
        this.v7h = IV[15] | 0;
        const keyLength = opts.key ? opts.key.length : 0;
        this.v0l ^= this.outputLen | (keyLength << 8) | (0x01 << 16) | (0x01 << 24);
        if (opts.salt) {
            const salt = u32(toBytes(opts.salt));
            this.v4l ^= salt[0];
            this.v4h ^= salt[1];
            this.v5l ^= salt[2];
            this.v5h ^= salt[3];
        }
        if (opts.personalization) {
            const pers = u32(toBytes(opts.personalization));
            this.v6l ^= pers[0];
            this.v6h ^= pers[1];
            this.v7l ^= pers[2];
            this.v7h ^= pers[3];
        }
        if (opts.key) {
            // Pad to blockLen and update
            const tmp = new Uint8Array(this.blockLen);
            tmp.set(toBytes(opts.key));
            this.update(tmp);
        }
    }
    // prettier-ignore
    get() {
        let { v0l, v0h, v1l, v1h, v2l, v2h, v3l, v3h, v4l, v4h, v5l, v5h, v6l, v6h, v7l, v7h } = this;
        return [v0l, v0h, v1l, v1h, v2l, v2h, v3l, v3h, v4l, v4h, v5l, v5h, v6l, v6h, v7l, v7h];
    }
    // prettier-ignore
    set(v0l, v0h, v1l, v1h, v2l, v2h, v3l, v3h, v4l, v4h, v5l, v5h, v6l, v6h, v7l, v7h) {
        this.v0l = v0l | 0;
        this.v0h = v0h | 0;
        this.v1l = v1l | 0;
        this.v1h = v1h | 0;
        this.v2l = v2l | 0;
        this.v2h = v2h | 0;
        this.v3l = v3l | 0;
        this.v3h = v3h | 0;
        this.v4l = v4l | 0;
        this.v4h = v4h | 0;
        this.v5l = v5l | 0;
        this.v5h = v5h | 0;
        this.v6l = v6l | 0;
        this.v6h = v6h | 0;
        this.v7l = v7l | 0;
        this.v7h = v7h | 0;
    }
    compress(msg, offset, isLast) {
        this.get().forEach((v, i) => (BUF[i] = v)); // First half from state.
        BUF.set(IV, 16); // Second half from IV.
        let { h, l } = u64.fromBig(BigInt(this.length));
        BUF[24] = IV[8] ^ l; // Low word of the offset.
        BUF[25] = IV[9] ^ h; // High word.
        // Invert all bits for last block
        if (isLast) {
            BUF[28] = ~BUF[28];
            BUF[29] = ~BUF[29];
        }
        let j = 0;
        const s = SIGMA;
        for (let i = 0; i < 12; i++) {
            G1(0, 4, 8, 12, msg, offset + 2 * s[j++]);
            G2(0, 4, 8, 12, msg, offset + 2 * s[j++]);
            G1(1, 5, 9, 13, msg, offset + 2 * s[j++]);
            G2(1, 5, 9, 13, msg, offset + 2 * s[j++]);
            G1(2, 6, 10, 14, msg, offset + 2 * s[j++]);
            G2(2, 6, 10, 14, msg, offset + 2 * s[j++]);
            G1(3, 7, 11, 15, msg, offset + 2 * s[j++]);
            G2(3, 7, 11, 15, msg, offset + 2 * s[j++]);
            G1(0, 5, 10, 15, msg, offset + 2 * s[j++]);
            G2(0, 5, 10, 15, msg, offset + 2 * s[j++]);
            G1(1, 6, 11, 12, msg, offset + 2 * s[j++]);
            G2(1, 6, 11, 12, msg, offset + 2 * s[j++]);
            G1(2, 7, 8, 13, msg, offset + 2 * s[j++]);
            G2(2, 7, 8, 13, msg, offset + 2 * s[j++]);
            G1(3, 4, 9, 14, msg, offset + 2 * s[j++]);
            G2(3, 4, 9, 14, msg, offset + 2 * s[j++]);
        }
        this.v0l ^= BUF[0] ^ BUF[16];
        this.v0h ^= BUF[1] ^ BUF[17];
        this.v1l ^= BUF[2] ^ BUF[18];
        this.v1h ^= BUF[3] ^ BUF[19];
        this.v2l ^= BUF[4] ^ BUF[20];
        this.v2h ^= BUF[5] ^ BUF[21];
        this.v3l ^= BUF[6] ^ BUF[22];
        this.v3h ^= BUF[7] ^ BUF[23];
        this.v4l ^= BUF[8] ^ BUF[24];
        this.v4h ^= BUF[9] ^ BUF[25];
        this.v5l ^= BUF[10] ^ BUF[26];
        this.v5h ^= BUF[11] ^ BUF[27];
        this.v6l ^= BUF[12] ^ BUF[28];
        this.v6h ^= BUF[13] ^ BUF[29];
        this.v7l ^= BUF[14] ^ BUF[30];
        this.v7h ^= BUF[15] ^ BUF[31];
        BUF.fill(0);
    }
    destroy() {
        this.destroyed = true;
        this.buffer32.fill(0);
        this.set(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
    }
}
/**
 * BLAKE2b - optimized for 64-bit platforms. JS doesn't have uint64, so it's slower than BLAKE2s.
 * @param msg - message that would be hashed
 * @param opts - dkLen, key, salt, personalization
 */
export const blake2b = /* @__PURE__ */ wrapConstructorWithOpts((opts) => new BLAKE2b(opts));
//# sourceMappingURL=blake2b.js.map