import { number as assertNumber } from './_assert.js';
import { toBytes, wrapConstructorWithOpts, u32 } from './utils.js';
import { Keccak } from './sha3.js';
// cSHAKE && KMAC (NIST SP800-185)
function leftEncode(n) {
    const res = [n & 0xff];
    n >>= 8;
    for (; n > 0; n >>= 8)
        res.unshift(n & 0xff);
    res.unshift(res.length);
    return new Uint8Array(res);
}
function rightEncode(n) {
    const res = [n & 0xff];
    n >>= 8;
    for (; n > 0; n >>= 8)
        res.unshift(n & 0xff);
    res.push(res.length);
    return new Uint8Array(res);
}
function chooseLen(opts, outputLen) {
    return opts.dkLen === undefined ? outputLen : opts.dkLen;
}
const toBytesOptional = (buf) => (buf !== undefined ? toBytes(buf) : new Uint8Array([]));
// NOTE: second modulo is necessary since we don't need to add padding if current element takes whole block
const getPadding = (len, block) => new Uint8Array((block - (len % block)) % block);
// Personalization
function cshakePers(hash, opts = {}) {
    if (!opts || (!opts.personalization && !opts.NISTfn))
        return hash;
    // Encode and pad inplace to avoid unneccesary memory copies/slices (so we don't need to zero them later)
    // bytepad(encode_string(N) || encode_string(S), 168)
    const blockLenBytes = leftEncode(hash.blockLen);
    const fn = toBytesOptional(opts.NISTfn);
    const fnLen = leftEncode(8 * fn.length); // length in bits
    const pers = toBytesOptional(opts.personalization);
    const persLen = leftEncode(8 * pers.length); // length in bits
    if (!fn.length && !pers.length)
        return hash;
    hash.suffix = 0x04;
    hash.update(blockLenBytes).update(fnLen).update(fn).update(persLen).update(pers);
    let totalLen = blockLenBytes.length + fnLen.length + fn.length + persLen.length + pers.length;
    hash.update(getPadding(totalLen, hash.blockLen));
    return hash;
}
const gencShake = (suffix, blockLen, outputLen) => wrapConstructorWithOpts((opts = {}) => cshakePers(new Keccak(blockLen, suffix, chooseLen(opts, outputLen), true), opts));
export const cshake128 = /* @__PURE__ */ (() => gencShake(0x1f, 168, 128 / 8))();
export const cshake256 = /* @__PURE__ */ (() => gencShake(0x1f, 136, 256 / 8))();
class KMAC extends Keccak {
    constructor(blockLen, outputLen, enableXOF, key, opts = {}) {
        super(blockLen, 0x1f, outputLen, enableXOF);
        cshakePers(this, { NISTfn: 'KMAC', personalization: opts.personalization });
        key = toBytes(key);
        // 1. newX = bytepad(encode_string(K), 168) || X || right_encode(L).
        const blockLenBytes = leftEncode(this.blockLen);
        const keyLen = leftEncode(8 * key.length);
        this.update(blockLenBytes).update(keyLen).update(key);
        const totalLen = blockLenBytes.length + keyLen.length + key.length;
        this.update(getPadding(totalLen, this.blockLen));
    }
    finish() {
        if (!this.finished)
            this.update(rightEncode(this.enableXOF ? 0 : this.outputLen * 8)); // outputLen in bits
        super.finish();
    }
    _cloneInto(to) {
        // Create new instance without calling constructor since key already in state and we don't know it.
        // Force "to" to be instance of KMAC instead of Sha3.
        if (!to) {
            to = Object.create(Object.getPrototypeOf(this), {});
            to.state = this.state.slice();
            to.blockLen = this.blockLen;
            to.state32 = u32(to.state);
        }
        return super._cloneInto(to);
    }
    clone() {
        return this._cloneInto();
    }
}
function genKmac(blockLen, outputLen, xof = false) {
    const kmac = (key, message, opts) => kmac.create(key, opts).update(message).digest();
    kmac.create = (key, opts = {}) => new KMAC(blockLen, chooseLen(opts, outputLen), xof, key, opts);
    return kmac;
}
export const kmac128 = /* @__PURE__ */ (() => genKmac(168, 128 / 8))();
export const kmac256 = /* @__PURE__ */ (() => genKmac(136, 256 / 8))();
export const kmac128xof = /* @__PURE__ */ (() => genKmac(168, 128 / 8, true))();
export const kmac256xof = /* @__PURE__ */ (() => genKmac(136, 256 / 8, true))();
// TupleHash
// Usage: tuple(['ab', 'cd']) != tuple(['a', 'bcd'])
class TupleHash extends Keccak {
    constructor(blockLen, outputLen, enableXOF, opts = {}) {
        super(blockLen, 0x1f, outputLen, enableXOF);
        cshakePers(this, { NISTfn: 'TupleHash', personalization: opts.personalization });
        // Change update after cshake processed
        this.update = (data) => {
            data = toBytes(data);
            super.update(leftEncode(data.length * 8));
            super.update(data);
            return this;
        };
    }
    finish() {
        if (!this.finished)
            super.update(rightEncode(this.enableXOF ? 0 : this.outputLen * 8)); // outputLen in bits
        super.finish();
    }
    _cloneInto(to) {
        to || (to = new TupleHash(this.blockLen, this.outputLen, this.enableXOF));
        return super._cloneInto(to);
    }
    clone() {
        return this._cloneInto();
    }
}
function genTuple(blockLen, outputLen, xof = false) {
    const tuple = (messages, opts) => {
        const h = tuple.create(opts);
        for (const msg of messages)
            h.update(msg);
        return h.digest();
    };
    tuple.create = (opts = {}) => new TupleHash(blockLen, chooseLen(opts, outputLen), xof, opts);
    return tuple;
}
export const tuplehash128 = /* @__PURE__ */ (() => genTuple(168, 128 / 8))();
export const tuplehash256 = /* @__PURE__ */ (() => genTuple(136, 256 / 8))();
export const tuplehash128xof = /* @__PURE__ */ (() => genTuple(168, 128 / 8, true))();
export const tuplehash256xof = /* @__PURE__ */ (() => genTuple(136, 256 / 8, true))();
class ParallelHash extends Keccak {
    constructor(blockLen, outputLen, leafCons, enableXOF, opts = {}) {
        super(blockLen, 0x1f, outputLen, enableXOF);
        this.leafCons = leafCons;
        this.chunkPos = 0; // Position of current block in chunk
        this.chunksDone = 0; // How many chunks we already have
        cshakePers(this, { NISTfn: 'ParallelHash', personalization: opts.personalization });
        let { blockLen: B } = opts;
        B || (B = 8);
        assertNumber(B);
        this.chunkLen = B;
        super.update(leftEncode(B));
        // Change update after cshake processed
        this.update = (data) => {
            data = toBytes(data);
            const { chunkLen, leafCons } = this;
            for (let pos = 0, len = data.length; pos < len;) {
                if (this.chunkPos == chunkLen || !this.leafHash) {
                    if (this.leafHash) {
                        super.update(this.leafHash.digest());
                        this.chunksDone++;
                    }
                    this.leafHash = leafCons();
                    this.chunkPos = 0;
                }
                const take = Math.min(chunkLen - this.chunkPos, len - pos);
                this.leafHash.update(data.subarray(pos, pos + take));
                this.chunkPos += take;
                pos += take;
            }
            return this;
        };
    }
    finish() {
        if (this.finished)
            return;
        if (this.leafHash) {
            super.update(this.leafHash.digest());
            this.chunksDone++;
        }
        super.update(rightEncode(this.chunksDone));
        super.update(rightEncode(this.enableXOF ? 0 : this.outputLen * 8)); // outputLen in bits
        super.finish();
    }
    _cloneInto(to) {
        to || (to = new ParallelHash(this.blockLen, this.outputLen, this.leafCons, this.enableXOF));
        if (this.leafHash)
            to.leafHash = this.leafHash._cloneInto(to.leafHash);
        to.chunkPos = this.chunkPos;
        to.chunkLen = this.chunkLen;
        to.chunksDone = this.chunksDone;
        return super._cloneInto(to);
    }
    destroy() {
        super.destroy.call(this);
        if (this.leafHash)
            this.leafHash.destroy();
    }
    clone() {
        return this._cloneInto();
    }
}
function genPrl(blockLen, outputLen, leaf, xof = false) {
    const parallel = (message, opts) => parallel.create(opts).update(message).digest();
    parallel.create = (opts = {}) => new ParallelHash(blockLen, chooseLen(opts, outputLen), () => leaf.create({ dkLen: 2 * outputLen }), xof, opts);
    return parallel;
}
export const parallelhash128 = /* @__PURE__ */ (() => genPrl(168, 128 / 8, cshake128))();
export const parallelhash256 = /* @__PURE__ */ (() => genPrl(136, 256 / 8, cshake256))();
export const parallelhash128xof = /* @__PURE__ */ (() => genPrl(168, 128 / 8, cshake128, true))();
export const parallelhash256xof = /* @__PURE__ */ (() => genPrl(136, 256 / 8, cshake256, true))();
// Kangaroo
// Same as NIST rightEncode, but returns [0] for zero string
function rightEncodeK12(n) {
    const res = [];
    for (; n > 0; n >>= 8)
        res.unshift(n & 0xff);
    res.push(res.length);
    return new Uint8Array(res);
}
const EMPTY = new Uint8Array([]);
class KangarooTwelve extends Keccak {
    constructor(blockLen, leafLen, outputLen, rounds, opts) {
        super(blockLen, 0x07, outputLen, true, rounds);
        this.leafLen = leafLen;
        this.chunkLen = 8192;
        this.chunkPos = 0; // Position of current block in chunk
        this.chunksDone = 0; // How many chunks we already have
        const { personalization } = opts;
        this.personalization = toBytesOptional(personalization);
    }
    update(data) {
        data = toBytes(data);
        const { chunkLen, blockLen, leafLen, rounds } = this;
        for (let pos = 0, len = data.length; pos < len;) {
            if (this.chunkPos == chunkLen) {
                if (this.leafHash)
                    super.update(this.leafHash.digest());
                else {
                    this.suffix = 0x06; // Its safe to change suffix here since its used only in digest()
                    super.update(new Uint8Array([3, 0, 0, 0, 0, 0, 0, 0]));
                }
                this.leafHash = new Keccak(blockLen, 0x0b, leafLen, false, rounds);
                this.chunksDone++;
                this.chunkPos = 0;
            }
            const take = Math.min(chunkLen - this.chunkPos, len - pos);
            const chunk = data.subarray(pos, pos + take);
            if (this.leafHash)
                this.leafHash.update(chunk);
            else
                super.update(chunk);
            this.chunkPos += take;
            pos += take;
        }
        return this;
    }
    finish() {
        if (this.finished)
            return;
        const { personalization } = this;
        this.update(personalization).update(rightEncodeK12(personalization.length));
        // Leaf hash
        if (this.leafHash) {
            super.update(this.leafHash.digest());
            super.update(rightEncodeK12(this.chunksDone));
            super.update(new Uint8Array([0xff, 0xff]));
        }
        super.finish.call(this);
    }
    destroy() {
        super.destroy.call(this);
        if (this.leafHash)
            this.leafHash.destroy();
        // We cannot zero personalization buffer since it is user provided and we don't want to mutate user input
        this.personalization = EMPTY;
    }
    _cloneInto(to) {
        const { blockLen, leafLen, leafHash, outputLen, rounds } = this;
        to || (to = new KangarooTwelve(blockLen, leafLen, outputLen, rounds, {}));
        super._cloneInto(to);
        if (leafHash)
            to.leafHash = leafHash._cloneInto(to.leafHash);
        to.personalization.set(this.personalization);
        to.leafLen = this.leafLen;
        to.chunkPos = this.chunkPos;
        to.chunksDone = this.chunksDone;
        return to;
    }
    clone() {
        return this._cloneInto();
    }
}
// Default to 32 bytes, so it can be used without opts
export const k12 = /* @__PURE__ */ (() => wrapConstructorWithOpts((opts = {}) => new KangarooTwelve(168, 32, chooseLen(opts, 32), 12, opts)))();
// MarsupilamiFourteen
export const m14 = /* @__PURE__ */ (() => wrapConstructorWithOpts((opts = {}) => new KangarooTwelve(136, 64, chooseLen(opts, 64), 14, opts)))();
// https://keccak.team/files/CSF-0.1.pdf
// + https://github.com/XKCP/XKCP/tree/master/lib/high/Keccak/PRG
class KeccakPRG extends Keccak {
    constructor(capacity) {
        assertNumber(capacity);
        // Rho should be full bytes
        if (capacity < 0 || capacity > 1600 - 10 || (1600 - capacity - 2) % 8)
            throw new Error('KeccakPRG: Invalid capacity');
        // blockLen = rho in bytes
        super((1600 - capacity - 2) / 8, 0, 0, true);
        this.rate = 1600 - capacity;
        this.posOut = Math.floor((this.rate + 7) / 8);
    }
    keccak() {
        // Duplex padding
        this.state[this.pos] ^= 0x01;
        this.state[this.blockLen] ^= 0x02; // Rho is full bytes
        super.keccak();
        this.pos = 0;
        this.posOut = 0;
    }
    update(data) {
        super.update(data);
        this.posOut = this.blockLen;
        return this;
    }
    feed(data) {
        return this.update(data);
    }
    finish() { }
    digestInto(_out) {
        throw new Error('KeccakPRG: digest is not allowed, please use .fetch instead.');
    }
    fetch(bytes) {
        return this.xof(bytes);
    }
    // Ensure irreversibility (even if state leaked previous outputs cannot be computed)
    forget() {
        if (this.rate < 1600 / 2 + 1)
            throw new Error('KeccakPRG: rate too low to use forget');
        this.keccak();
        for (let i = 0; i < this.blockLen; i++)
            this.state[i] = 0;
        this.pos = this.blockLen;
        this.keccak();
        this.posOut = this.blockLen;
    }
    _cloneInto(to) {
        const { rate } = this;
        to || (to = new KeccakPRG(1600 - rate));
        super._cloneInto(to);
        to.rate = rate;
        return to;
    }
    clone() {
        return this._cloneInto();
    }
}
export const keccakprg = (capacity = 254) => new KeccakPRG(capacity);
//# sourceMappingURL=sha3-addons.js.map