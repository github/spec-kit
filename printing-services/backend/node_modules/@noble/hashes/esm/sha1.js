import { SHA2 } from './_sha2.js';
import { wrapConstructor } from './utils.js';
// SHA1 was cryptographically broken.
// It is still widely used in legacy apps. Don't use it for a new protocol.
// RFC 3174
const rotl = (word, shift) => (word << shift) | ((word >>> (32 - shift)) >>> 0);
// Choice: a ? b : c
const Chi = (a, b, c) => (a & b) ^ (~a & c);
// Majority function, true if any two inpust is true
const Maj = (a, b, c) => (a & b) ^ (a & c) ^ (b & c);
// Initial state
const IV = /* @__PURE__ */ new Uint32Array([
    0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476, 0xc3d2e1f0,
]);
// Temporary buffer, not used to store anything between runs
// Named this way because it matches specification.
const SHA1_W = /* @__PURE__ */ new Uint32Array(80);
class SHA1 extends SHA2 {
    constructor() {
        super(64, 20, 8, false);
        this.A = IV[0] | 0;
        this.B = IV[1] | 0;
        this.C = IV[2] | 0;
        this.D = IV[3] | 0;
        this.E = IV[4] | 0;
    }
    get() {
        const { A, B, C, D, E } = this;
        return [A, B, C, D, E];
    }
    set(A, B, C, D, E) {
        this.A = A | 0;
        this.B = B | 0;
        this.C = C | 0;
        this.D = D | 0;
        this.E = E | 0;
    }
    process(view, offset) {
        for (let i = 0; i < 16; i++, offset += 4)
            SHA1_W[i] = view.getUint32(offset, false);
        for (let i = 16; i < 80; i++)
            SHA1_W[i] = rotl(SHA1_W[i - 3] ^ SHA1_W[i - 8] ^ SHA1_W[i - 14] ^ SHA1_W[i - 16], 1);
        // Compression function main loop, 80 rounds
        let { A, B, C, D, E } = this;
        for (let i = 0; i < 80; i++) {
            let F, K;
            if (i < 20) {
                F = Chi(B, C, D);
                K = 0x5a827999;
            }
            else if (i < 40) {
                F = B ^ C ^ D;
                K = 0x6ed9eba1;
            }
            else if (i < 60) {
                F = Maj(B, C, D);
                K = 0x8f1bbcdc;
            }
            else {
                F = B ^ C ^ D;
                K = 0xca62c1d6;
            }
            const T = (rotl(A, 5) + F + E + K + SHA1_W[i]) | 0;
            E = D;
            D = C;
            C = rotl(B, 30);
            B = A;
            A = T;
        }
        // Add the compressed chunk to the current hash value
        A = (A + this.A) | 0;
        B = (B + this.B) | 0;
        C = (C + this.C) | 0;
        D = (D + this.D) | 0;
        E = (E + this.E) | 0;
        this.set(A, B, C, D, E);
    }
    roundClean() {
        SHA1_W.fill(0);
    }
    destroy() {
        this.set(0, 0, 0, 0, 0);
        this.buffer.fill(0);
    }
}
export const sha1 = /* @__PURE__ */ wrapConstructor(() => new SHA1());
//# sourceMappingURL=sha1.js.map