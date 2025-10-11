import { number as assertNumber } from './_assert.js';
import { Input, toBytes, wrapConstructorWithOpts, u32, Hash, HashXOF } from './utils.js';
import { Keccak, ShakeOpts } from './sha3.js';
// cSHAKE && KMAC (NIST SP800-185)
function leftEncode(n: number): Uint8Array {
  const res = [n & 0xff];
  n >>= 8;
  for (; n > 0; n >>= 8) res.unshift(n & 0xff);
  res.unshift(res.length);
  return new Uint8Array(res);
}

function rightEncode(n: number): Uint8Array {
  const res = [n & 0xff];
  n >>= 8;
  for (; n > 0; n >>= 8) res.unshift(n & 0xff);
  res.push(res.length);
  return new Uint8Array(res);
}

function chooseLen(opts: ShakeOpts, outputLen: number): number {
  return opts.dkLen === undefined ? outputLen : opts.dkLen;
}

const toBytesOptional = (buf?: Input) => (buf !== undefined ? toBytes(buf) : new Uint8Array([]));
// NOTE: second modulo is necessary since we don't need to add padding if current element takes whole block
const getPadding = (len: number, block: number) => new Uint8Array((block - (len % block)) % block);
export type cShakeOpts = ShakeOpts & { personalization?: Input; NISTfn?: Input };

// Personalization
function cshakePers(hash: Keccak, opts: cShakeOpts = {}): Keccak {
  if (!opts || (!opts.personalization && !opts.NISTfn)) return hash;
  // Encode and pad inplace to avoid unneccesary memory copies/slices (so we don't need to zero them later)
  // bytepad(encode_string(N) || encode_string(S), 168)
  const blockLenBytes = leftEncode(hash.blockLen);
  const fn = toBytesOptional(opts.NISTfn);
  const fnLen = leftEncode(8 * fn.length); // length in bits
  const pers = toBytesOptional(opts.personalization);
  const persLen = leftEncode(8 * pers.length); // length in bits
  if (!fn.length && !pers.length) return hash;
  hash.suffix = 0x04;
  hash.update(blockLenBytes).update(fnLen).update(fn).update(persLen).update(pers);
  let totalLen = blockLenBytes.length + fnLen.length + fn.length + persLen.length + pers.length;
  hash.update(getPadding(totalLen, hash.blockLen));
  return hash;
}

const gencShake = (suffix: number, blockLen: number, outputLen: number) =>
  wrapConstructorWithOpts<Keccak, cShakeOpts>((opts: cShakeOpts = {}) =>
    cshakePers(new Keccak(blockLen, suffix, chooseLen(opts, outputLen), true), opts)
  );

export const cshake128 = /* @__PURE__ */ (() => gencShake(0x1f, 168, 128 / 8))();
export const cshake256 = /* @__PURE__ */ (() => gencShake(0x1f, 136, 256 / 8))();

class KMAC extends Keccak implements HashXOF<KMAC> {
  constructor(
    blockLen: number,
    outputLen: number,
    enableXOF: boolean,
    key: Input,
    opts: cShakeOpts = {}
  ) {
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
  protected finish() {
    if (!this.finished) this.update(rightEncode(this.enableXOF ? 0 : this.outputLen * 8)); // outputLen in bits
    super.finish();
  }
  _cloneInto(to?: KMAC): KMAC {
    // Create new instance without calling constructor since key already in state and we don't know it.
    // Force "to" to be instance of KMAC instead of Sha3.
    if (!to) {
      to = Object.create(Object.getPrototypeOf(this), {}) as KMAC;
      to.state = this.state.slice();
      to.blockLen = this.blockLen;
      to.state32 = u32(to.state);
    }
    return super._cloneInto(to) as KMAC;
  }
  clone(): KMAC {
    return this._cloneInto();
  }
}

function genKmac(blockLen: number, outputLen: number, xof = false) {
  const kmac = (key: Input, message: Input, opts?: cShakeOpts): Uint8Array =>
    kmac.create(key, opts).update(message).digest();
  kmac.create = (key: Input, opts: cShakeOpts = {}) =>
    new KMAC(blockLen, chooseLen(opts, outputLen), xof, key, opts);
  return kmac;
}

export const kmac128 = /* @__PURE__ */ (() => genKmac(168, 128 / 8))();
export const kmac256 = /* @__PURE__ */ (() => genKmac(136, 256 / 8))();
export const kmac128xof = /* @__PURE__ */ (() => genKmac(168, 128 / 8, true))();
export const kmac256xof = /* @__PURE__ */ (() => genKmac(136, 256 / 8, true))();

// TupleHash
// Usage: tuple(['ab', 'cd']) != tuple(['a', 'bcd'])
class TupleHash extends Keccak implements HashXOF<TupleHash> {
  constructor(blockLen: number, outputLen: number, enableXOF: boolean, opts: cShakeOpts = {}) {
    super(blockLen, 0x1f, outputLen, enableXOF);
    cshakePers(this, { NISTfn: 'TupleHash', personalization: opts.personalization });
    // Change update after cshake processed
    this.update = (data: Input) => {
      data = toBytes(data);
      super.update(leftEncode(data.length * 8));
      super.update(data);
      return this;
    };
  }
  protected finish() {
    if (!this.finished) super.update(rightEncode(this.enableXOF ? 0 : this.outputLen * 8)); // outputLen in bits
    super.finish();
  }
  _cloneInto(to?: TupleHash): TupleHash {
    to ||= new TupleHash(this.blockLen, this.outputLen, this.enableXOF);
    return super._cloneInto(to) as TupleHash;
  }
  clone(): TupleHash {
    return this._cloneInto();
  }
}

function genTuple(blockLen: number, outputLen: number, xof = false) {
  const tuple = (messages: Input[], opts?: cShakeOpts): Uint8Array => {
    const h = tuple.create(opts);
    for (const msg of messages) h.update(msg);
    return h.digest();
  };
  tuple.create = (opts: cShakeOpts = {}) =>
    new TupleHash(blockLen, chooseLen(opts, outputLen), xof, opts);
  return tuple;
}

export const tuplehash128 = /* @__PURE__ */ (() => genTuple(168, 128 / 8))();
export const tuplehash256 = /* @__PURE__ */ (() => genTuple(136, 256 / 8))();
export const tuplehash128xof = /* @__PURE__ */ (() => genTuple(168, 128 / 8, true))();
export const tuplehash256xof = /* @__PURE__ */ (() => genTuple(136, 256 / 8, true))();

// ParallelHash (same as K12/M14, but without speedup for inputs less 8kb, reduced number of rounds and more simple)
type ParallelOpts = cShakeOpts & { blockLen?: number };

class ParallelHash extends Keccak implements HashXOF<ParallelHash> {
  private leafHash?: Hash<Keccak>;
  private chunkPos = 0; // Position of current block in chunk
  private chunksDone = 0; // How many chunks we already have
  private chunkLen: number;
  constructor(
    blockLen: number,
    outputLen: number,
    protected leafCons: () => Hash<Keccak>,
    enableXOF: boolean,
    opts: ParallelOpts = {}
  ) {
    super(blockLen, 0x1f, outputLen, enableXOF);
    cshakePers(this, { NISTfn: 'ParallelHash', personalization: opts.personalization });
    let { blockLen: B } = opts;
    B ||= 8;
    assertNumber(B);
    this.chunkLen = B;
    super.update(leftEncode(B));
    // Change update after cshake processed
    this.update = (data: Input) => {
      data = toBytes(data);
      const { chunkLen, leafCons } = this;
      for (let pos = 0, len = data.length; pos < len; ) {
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
  protected finish() {
    if (this.finished) return;
    if (this.leafHash) {
      super.update(this.leafHash.digest());
      this.chunksDone++;
    }
    super.update(rightEncode(this.chunksDone));
    super.update(rightEncode(this.enableXOF ? 0 : this.outputLen * 8)); // outputLen in bits
    super.finish();
  }
  _cloneInto(to?: ParallelHash): ParallelHash {
    to ||= new ParallelHash(this.blockLen, this.outputLen, this.leafCons, this.enableXOF);
    if (this.leafHash) to.leafHash = this.leafHash._cloneInto(to.leafHash as Keccak);
    to.chunkPos = this.chunkPos;
    to.chunkLen = this.chunkLen;
    to.chunksDone = this.chunksDone;
    return super._cloneInto(to) as ParallelHash;
  }
  destroy() {
    super.destroy.call(this);
    if (this.leafHash) this.leafHash.destroy();
  }
  clone(): ParallelHash {
    return this._cloneInto();
  }
}

function genPrl(
  blockLen: number,
  outputLen: number,
  leaf: ReturnType<typeof gencShake>,
  xof = false
) {
  const parallel = (message: Input, opts?: ParallelOpts): Uint8Array =>
    parallel.create(opts).update(message).digest();
  parallel.create = (opts: ParallelOpts = {}) =>
    new ParallelHash(
      blockLen,
      chooseLen(opts, outputLen),
      () => leaf.create({ dkLen: 2 * outputLen }),
      xof,
      opts
    );
  return parallel;
}

export const parallelhash128 = /* @__PURE__ */ (() => genPrl(168, 128 / 8, cshake128))();
export const parallelhash256 = /* @__PURE__ */ (() => genPrl(136, 256 / 8, cshake256))();
export const parallelhash128xof = /* @__PURE__ */ (() => genPrl(168, 128 / 8, cshake128, true))();
export const parallelhash256xof = /* @__PURE__ */ (() => genPrl(136, 256 / 8, cshake256, true))();

// Kangaroo
// Same as NIST rightEncode, but returns [0] for zero string
function rightEncodeK12(n: number): Uint8Array {
  const res = [];
  for (; n > 0; n >>= 8) res.unshift(n & 0xff);
  res.push(res.length);
  return new Uint8Array(res);
}

export type KangarooOpts = { dkLen?: number; personalization?: Input };
const EMPTY = new Uint8Array([]);

class KangarooTwelve extends Keccak implements HashXOF<KangarooTwelve> {
  readonly chunkLen = 8192;
  private leafHash?: Keccak;
  private personalization: Uint8Array;
  private chunkPos = 0; // Position of current block in chunk
  private chunksDone = 0; // How many chunks we already have
  constructor(
    blockLen: number,
    protected leafLen: number,
    outputLen: number,
    rounds: number,
    opts: KangarooOpts
  ) {
    super(blockLen, 0x07, outputLen, true, rounds);
    const { personalization } = opts;
    this.personalization = toBytesOptional(personalization);
  }
  update(data: Input) {
    data = toBytes(data);
    const { chunkLen, blockLen, leafLen, rounds } = this;
    for (let pos = 0, len = data.length; pos < len; ) {
      if (this.chunkPos == chunkLen) {
        if (this.leafHash) super.update(this.leafHash.digest());
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
      if (this.leafHash) this.leafHash.update(chunk);
      else super.update(chunk);
      this.chunkPos += take;
      pos += take;
    }
    return this;
  }
  protected finish() {
    if (this.finished) return;
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
    if (this.leafHash) this.leafHash.destroy();
    // We cannot zero personalization buffer since it is user provided and we don't want to mutate user input
    this.personalization = EMPTY;
  }
  _cloneInto(to?: KangarooTwelve): KangarooTwelve {
    const { blockLen, leafLen, leafHash, outputLen, rounds } = this;
    to ||= new KangarooTwelve(blockLen, leafLen, outputLen, rounds, {});
    super._cloneInto(to);
    if (leafHash) to.leafHash = leafHash._cloneInto(to.leafHash);
    to.personalization.set(this.personalization);
    to.leafLen = this.leafLen;
    to.chunkPos = this.chunkPos;
    to.chunksDone = this.chunksDone;
    return to;
  }
  clone(): KangarooTwelve {
    return this._cloneInto();
  }
}
// Default to 32 bytes, so it can be used without opts
export const k12 = /* @__PURE__ */ (() =>
  wrapConstructorWithOpts<KangarooTwelve, KangarooOpts>(
    (opts: KangarooOpts = {}) => new KangarooTwelve(168, 32, chooseLen(opts, 32), 12, opts)
  ))();
// MarsupilamiFourteen
export const m14 = /* @__PURE__ */ (() =>
  wrapConstructorWithOpts<KangarooTwelve, KangarooOpts>(
    (opts: KangarooOpts = {}) => new KangarooTwelve(136, 64, chooseLen(opts, 64), 14, opts)
  ))();

// https://keccak.team/files/CSF-0.1.pdf
// + https://github.com/XKCP/XKCP/tree/master/lib/high/Keccak/PRG
class KeccakPRG extends Keccak {
  protected rate: number;
  constructor(capacity: number) {
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
  update(data: Input) {
    super.update(data);
    this.posOut = this.blockLen;
    return this;
  }
  feed(data: Input) {
    return this.update(data);
  }
  protected finish() {}
  digestInto(_out: Uint8Array): Uint8Array {
    throw new Error('KeccakPRG: digest is not allowed, please use .fetch instead.');
  }
  fetch(bytes: number): Uint8Array {
    return this.xof(bytes);
  }
  // Ensure irreversibility (even if state leaked previous outputs cannot be computed)
  forget() {
    if (this.rate < 1600 / 2 + 1) throw new Error('KeccakPRG: rate too low to use forget');
    this.keccak();
    for (let i = 0; i < this.blockLen; i++) this.state[i] = 0;
    this.pos = this.blockLen;
    this.keccak();
    this.posOut = this.blockLen;
  }
  _cloneInto(to?: KeccakPRG): KeccakPRG {
    const { rate } = this;
    to ||= new KeccakPRG(1600 - rate);
    super._cloneInto(to);
    to.rate = rate;
    return to;
  }
  clone(): KeccakPRG {
    return this._cloneInto();
  }
}

export const keccakprg = (capacity = 254) => new KeccakPRG(capacity);
