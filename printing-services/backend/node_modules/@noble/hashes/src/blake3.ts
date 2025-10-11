import { bytes, exists, number, output } from './_assert.js';
import { fromBig } from './_u64.js';
import { BLAKE2 } from './_blake2.js';
import { compress, IV } from './blake2s.js';
import { Input, u8, u32, toBytes, HashXOF, wrapXOFConstructorWithOpts } from './utils.js';

// Blake3 is single-option Blake2 with reduced security (round count).

// Flag bitset
const enum Flags {
  CHUNK_START = 1 << 0,
  CHUNK_END = 1 << 1,
  PARENT = 1 << 2,
  ROOT = 1 << 3,
  KEYED_HASH = 1 << 4,
  DERIVE_KEY_CONTEXT = 1 << 5,
  DERIVE_KEY_MATERIAL = 1 << 6,
}

const SIGMA: Uint8Array = /* @__PURE__ */ (() => {
  const Id = Array.from({ length: 16 }, (_, i) => i);
  const permute = (arr: number[]) =>
    [2, 6, 3, 10, 7, 0, 4, 13, 1, 11, 12, 5, 9, 14, 15, 8].map((i) => arr[i]);
  const res: number[] = [];
  for (let i = 0, v = Id; i < 7; i++, v = permute(v)) res.push(...v);
  return Uint8Array.from(res);
})();

// - key: is 256-bit key
// - context: string should be hardcoded, globally unique, and application - specific.
//   A good default format for the context string is "[application] [commit timestamp] [purpose]"
// - Only one of 'key' (keyed mode) or 'context' (derive key mode) can be used at same time
export type Blake3Opts = { dkLen?: number; key?: Input; context?: Input };

// Why is this so slow? It should be 6x faster than blake2b.
// - There is only 30% reduction in number of rounds from blake2s
// - This function uses tree mode to achive parallelisation via SIMD and threading,
//   however in JS we don't have threads and SIMD, so we get only overhead from tree structure
// - It is possible to speed it up via Web Workers, hovewer it will make code singnificantly more
//   complicated, which we are trying to avoid, since this library is intended to be used
//   for cryptographic purposes. Also, parallelization happens only on chunk level (1024 bytes),
//   which won't really benefit small inputs.
class BLAKE3 extends BLAKE2<BLAKE3> implements HashXOF<BLAKE3> {
  private IV: Uint32Array;
  private flags = 0 | 0;
  private state: Uint32Array;
  private chunkPos = 0; // Position of current block in chunk
  private chunksDone = 0; // How many chunks we already have
  private stack: Uint32Array[] = [];
  // Output
  private posOut = 0;
  private bufferOut32 = new Uint32Array(16);
  private bufferOut: Uint8Array;
  private chunkOut = 0; // index of output chunk
  private enableXOF = true;

  constructor(opts: Blake3Opts = {}, flags = 0) {
    super(64, opts.dkLen === undefined ? 32 : opts.dkLen, {}, Number.MAX_SAFE_INTEGER, 0, 0);
    this.outputLen = opts.dkLen === undefined ? 32 : opts.dkLen;
    number(this.outputLen);
    if (opts.key !== undefined && opts.context !== undefined)
      throw new Error('Blake3: only key or context can be specified at same time');
    else if (opts.key !== undefined) {
      const key = toBytes(opts.key).slice();
      if (key.length !== 32) throw new Error('Blake3: key should be 32 byte');
      this.IV = u32(key);
      this.flags = flags | Flags.KEYED_HASH;
    } else if (opts.context !== undefined) {
      const context_key = new BLAKE3({ dkLen: 32 }, Flags.DERIVE_KEY_CONTEXT)
        .update(opts.context)
        .digest();
      this.IV = u32(context_key);
      this.flags = flags | Flags.DERIVE_KEY_MATERIAL;
    } else {
      this.IV = IV.slice();
      this.flags = flags;
    }
    this.state = this.IV.slice();
    this.bufferOut = u8(this.bufferOut32);
  }
  // Unused
  protected get() {
    return [];
  }
  protected set() {}
  private b2Compress(counter: number, flags: number, buf: Uint32Array, bufPos: number = 0) {
    const { state: s, pos } = this;
    const { h, l } = fromBig(BigInt(counter), true);
    // prettier-ignore
    const { v0, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15 } =
      compress(
        SIGMA, bufPos, buf, 7,
        s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7],
        IV[0], IV[1], IV[2], IV[3], h, l, pos, flags
      );
    s[0] = v0 ^ v8;
    s[1] = v1 ^ v9;
    s[2] = v2 ^ v10;
    s[3] = v3 ^ v11;
    s[4] = v4 ^ v12;
    s[5] = v5 ^ v13;
    s[6] = v6 ^ v14;
    s[7] = v7 ^ v15;
  }
  protected compress(buf: Uint32Array, bufPos: number = 0, isLast: boolean = false) {
    // Compress last block
    let flags = this.flags;
    if (!this.chunkPos) flags |= Flags.CHUNK_START;
    if (this.chunkPos === 15 || isLast) flags |= Flags.CHUNK_END;
    if (!isLast) this.pos = this.blockLen;
    this.b2Compress(this.chunksDone, flags, buf, bufPos);
    this.chunkPos += 1;
    // If current block is last in chunk (16 blocks), then compress chunks
    if (this.chunkPos === 16 || isLast) {
      let chunk = this.state;
      this.state = this.IV.slice();
      // If not the last one, compress only when there are trailing zeros in chunk counter
      // chunks used as binary tree where current stack is path. Zero means current leaf is finished and can be compressed.
      // 1 (001) - leaf not finished (just push current chunk to stack)
      // 2 (010) - leaf finished at depth=1 (merge with last elm on stack and push back)
      // 3 (011) - last leaf not finished
      // 4 (100) - leafs finished at depth=1 and depth=2
      for (let last, chunks = this.chunksDone + 1; isLast || !(chunks & 1); chunks >>= 1) {
        if (!(last = this.stack.pop())) break;
        this.buffer32.set(last, 0);
        this.buffer32.set(chunk, 8);
        this.pos = this.blockLen;
        this.b2Compress(0, this.flags | Flags.PARENT, this.buffer32, 0);
        chunk = this.state;
        this.state = this.IV.slice();
      }
      this.chunksDone++;
      this.chunkPos = 0;
      this.stack.push(chunk);
    }
    this.pos = 0;
  }
  _cloneInto(to?: BLAKE3): BLAKE3 {
    to = super._cloneInto(to) as BLAKE3;
    const { IV, flags, state, chunkPos, posOut, chunkOut, stack, chunksDone } = this;
    to.state.set(state.slice());
    to.stack = stack.map((i) => Uint32Array.from(i));
    to.IV.set(IV);
    to.flags = flags;
    to.chunkPos = chunkPos;
    to.chunksDone = chunksDone;
    to.posOut = posOut;
    to.chunkOut = chunkOut;
    to.enableXOF = this.enableXOF;
    to.bufferOut32.set(this.bufferOut32);
    return to;
  }
  destroy() {
    this.destroyed = true;
    this.state.fill(0);
    this.buffer32.fill(0);
    this.IV.fill(0);
    this.bufferOut32.fill(0);
    for (let i of this.stack) i.fill(0);
  }
  // Same as b2Compress, but doesn't modify state and returns 16 u32 array (instead of 8)
  private b2CompressOut() {
    const { state: s, pos, flags, buffer32, bufferOut32: out32 } = this;
    const { h, l } = fromBig(BigInt(this.chunkOut++));
    // prettier-ignore
    const { v0, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15 } =
      compress(
        SIGMA, 0, buffer32, 7,
        s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7],
        IV[0], IV[1], IV[2], IV[3], l, h, pos, flags
      );
    out32[0] = v0 ^ v8;
    out32[1] = v1 ^ v9;
    out32[2] = v2 ^ v10;
    out32[3] = v3 ^ v11;
    out32[4] = v4 ^ v12;
    out32[5] = v5 ^ v13;
    out32[6] = v6 ^ v14;
    out32[7] = v7 ^ v15;
    out32[8] = s[0] ^ v8;
    out32[9] = s[1] ^ v9;
    out32[10] = s[2] ^ v10;
    out32[11] = s[3] ^ v11;
    out32[12] = s[4] ^ v12;
    out32[13] = s[5] ^ v13;
    out32[14] = s[6] ^ v14;
    out32[15] = s[7] ^ v15;
    this.posOut = 0;
  }
  protected finish() {
    if (this.finished) return;
    this.finished = true;
    // Padding
    this.buffer.fill(0, this.pos);
    // Process last chunk
    let flags = this.flags | Flags.ROOT;
    if (this.stack.length) {
      flags |= Flags.PARENT;
      this.compress(this.buffer32, 0, true);
      this.chunksDone = 0;
      this.pos = this.blockLen;
    } else {
      flags |= (!this.chunkPos ? Flags.CHUNK_START : 0) | Flags.CHUNK_END;
    }
    this.flags = flags;
    this.b2CompressOut();
  }
  private writeInto(out: Uint8Array) {
    exists(this, false);
    bytes(out);
    this.finish();
    const { blockLen, bufferOut } = this;
    for (let pos = 0, len = out.length; pos < len; ) {
      if (this.posOut >= blockLen) this.b2CompressOut();
      const take = Math.min(blockLen - this.posOut, len - pos);
      out.set(bufferOut.subarray(this.posOut, this.posOut + take), pos);
      this.posOut += take;
      pos += take;
    }
    return out;
  }
  xofInto(out: Uint8Array): Uint8Array {
    if (!this.enableXOF) throw new Error('XOF is not possible after digest call');
    return this.writeInto(out);
  }
  xof(bytes: number): Uint8Array {
    number(bytes);
    return this.xofInto(new Uint8Array(bytes));
  }
  digestInto(out: Uint8Array) {
    output(out, this);
    if (this.finished) throw new Error('digest() was already called');
    this.enableXOF = false;
    this.writeInto(out);
    this.destroy();
    return out;
  }
  digest() {
    return this.digestInto(new Uint8Array(this.outputLen));
  }
}

/**
 * BLAKE3 hash function.
 * @param msg - message that would be hashed
 * @param opts - dkLen, key, context
 */
export const blake3 = /* @__PURE__ */ wrapXOFConstructorWithOpts<BLAKE3, Blake3Opts>(
  (opts) => new BLAKE3(opts)
);
