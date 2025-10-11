"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BLAKE2 = exports.SIGMA = void 0;
const _assert_js_1 = require("./_assert.js");
const utils_js_1 = require("./utils.js");
// Blake is based on ChaCha permutation.
// For BLAKE2b, the two extra permutations for rounds 10 and 11 are SIGMA[10..11] = SIGMA[0..1].
// prettier-ignore
exports.SIGMA = new Uint8Array([
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3,
    11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4,
    7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8,
    9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13,
    2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9,
    12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11,
    13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10,
    6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5,
    10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0,
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3,
]);
class BLAKE2 extends utils_js_1.Hash {
    constructor(blockLen, outputLen, opts = {}, keyLen, saltLen, persLen) {
        super();
        this.blockLen = blockLen;
        this.outputLen = outputLen;
        this.length = 0;
        this.pos = 0;
        this.finished = false;
        this.destroyed = false;
        (0, _assert_js_1.number)(blockLen);
        (0, _assert_js_1.number)(outputLen);
        (0, _assert_js_1.number)(keyLen);
        if (outputLen < 0 || outputLen > keyLen)
            throw new Error('outputLen bigger than keyLen');
        if (opts.key !== undefined && (opts.key.length < 1 || opts.key.length > keyLen))
            throw new Error(`key must be up 1..${keyLen} byte long or undefined`);
        if (opts.salt !== undefined && opts.salt.length !== saltLen)
            throw new Error(`salt must be ${saltLen} byte long or undefined`);
        if (opts.personalization !== undefined && opts.personalization.length !== persLen)
            throw new Error(`personalization must be ${persLen} byte long or undefined`);
        this.buffer32 = (0, utils_js_1.u32)((this.buffer = new Uint8Array(blockLen)));
    }
    update(data) {
        (0, _assert_js_1.exists)(this);
        // Main difference with other hashes: there is flag for last block,
        // so we cannot process current block before we know that there
        // is the next one. This significantly complicates logic and reduces ability
        // to do zero-copy processing
        const { blockLen, buffer, buffer32 } = this;
        data = (0, utils_js_1.toBytes)(data);
        const len = data.length;
        const offset = data.byteOffset;
        const buf = data.buffer;
        for (let pos = 0; pos < len;) {
            // If buffer is full and we still have input (don't process last block, same as blake2s)
            if (this.pos === blockLen) {
                this.compress(buffer32, 0, false);
                this.pos = 0;
            }
            const take = Math.min(blockLen - this.pos, len - pos);
            const dataOffset = offset + pos;
            // full block && aligned to 4 bytes && not last in input
            if (take === blockLen && !(dataOffset % 4) && pos + take < len) {
                const data32 = new Uint32Array(buf, dataOffset, Math.floor((len - pos) / 4));
                for (let pos32 = 0; pos + blockLen < len; pos32 += buffer32.length, pos += blockLen) {
                    this.length += blockLen;
                    this.compress(data32, pos32, false);
                }
                continue;
            }
            buffer.set(data.subarray(pos, pos + take), this.pos);
            this.pos += take;
            this.length += take;
            pos += take;
        }
        return this;
    }
    digestInto(out) {
        (0, _assert_js_1.exists)(this);
        (0, _assert_js_1.output)(out, this);
        const { pos, buffer32 } = this;
        this.finished = true;
        // Padding
        this.buffer.subarray(pos).fill(0);
        this.compress(buffer32, 0, true);
        const out32 = (0, utils_js_1.u32)(out);
        this.get().forEach((v, i) => (out32[i] = v));
    }
    digest() {
        const { buffer, outputLen } = this;
        this.digestInto(buffer);
        const res = buffer.slice(0, outputLen);
        this.destroy();
        return res;
    }
    _cloneInto(to) {
        const { buffer, length, finished, destroyed, outputLen, pos } = this;
        to || (to = new this.constructor({ dkLen: outputLen }));
        to.set(...this.get());
        to.length = length;
        to.finished = finished;
        to.destroyed = destroyed;
        to.outputLen = outputLen;
        to.buffer.set(buffer);
        to.pos = pos;
        return to;
    }
}
exports.BLAKE2 = BLAKE2;
//# sourceMappingURL=_blake2.js.map