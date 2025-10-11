/*! noble-hashes - MIT License (c) 2022 Paul Miller (paulmillr.com) */

// We use WebCrypto aka globalThis.crypto, which exists in browsers and node.js 16+.
// node.js versions earlier than v19 don't declare it in global scope.
// For node.js, package.json#exports field mapping rewrites import
// from `crypto` to `cryptoNode`, which imports native module.
// Makes the utils un-importable in browsers without a bundler.
// Once node.js 18 is deprecated, we can just drop the import.
import { crypto } from '@noble/hashes/crypto';

// prettier-ignore
export type TypedArray = Int8Array | Uint8ClampedArray | Uint8Array |
  Uint16Array | Int16Array | Uint32Array | Int32Array;

const u8a = (a: any): a is Uint8Array => a instanceof Uint8Array;
// Cast array to different type
export const u8 = (arr: TypedArray) => new Uint8Array(arr.buffer, arr.byteOffset, arr.byteLength);
export const u32 = (arr: TypedArray) =>
  new Uint32Array(arr.buffer, arr.byteOffset, Math.floor(arr.byteLength / 4));

// Cast array to view
export const createView = (arr: TypedArray) =>
  new DataView(arr.buffer, arr.byteOffset, arr.byteLength);

// The rotate right (circular right shift) operation for uint32
export const rotr = (word: number, shift: number) => (word << (32 - shift)) | (word >>> shift);

// big-endian hardware is rare. Just in case someone still decides to run hashes:
// early-throw an error because we don't support BE yet.
export const isLE = new Uint8Array(new Uint32Array([0x11223344]).buffer)[0] === 0x44;
if (!isLE) throw new Error('Non little-endian hardware is not supported');

const hexes = /* @__PURE__ */ Array.from({ length: 256 }, (_, i) =>
  i.toString(16).padStart(2, '0')
);
/**
 * @example bytesToHex(Uint8Array.from([0xca, 0xfe, 0x01, 0x23])) // 'cafe0123'
 */
export function bytesToHex(bytes: Uint8Array): string {
  if (!u8a(bytes)) throw new Error('Uint8Array expected');
  // pre-caching improves the speed 6x
  let hex = '';
  for (let i = 0; i < bytes.length; i++) {
    hex += hexes[bytes[i]];
  }
  return hex;
}

/**
 * @example hexToBytes('cafe0123') // Uint8Array.from([0xca, 0xfe, 0x01, 0x23])
 */
export function hexToBytes(hex: string): Uint8Array {
  if (typeof hex !== 'string') throw new Error('hex string expected, got ' + typeof hex);
  const len = hex.length;
  if (len % 2) throw new Error('padded hex string expected, got unpadded hex of length ' + len);
  const array = new Uint8Array(len / 2);
  for (let i = 0; i < array.length; i++) {
    const j = i * 2;
    const hexByte = hex.slice(j, j + 2);
    const byte = Number.parseInt(hexByte, 16);
    if (Number.isNaN(byte) || byte < 0) throw new Error('Invalid byte sequence');
    array[i] = byte;
  }
  return array;
}

// There is no setImmediate in browser and setTimeout is slow.
// call of async fn will return Promise, which will be fullfiled only on
// next scheduler queue processing step and this is exactly what we need.
export const nextTick = async () => {};

// Returns control to thread each 'tick' ms to avoid blocking
export async function asyncLoop(iters: number, tick: number, cb: (i: number) => void) {
  let ts = Date.now();
  for (let i = 0; i < iters; i++) {
    cb(i);
    // Date.now() is not monotonic, so in case if clock goes backwards we return return control too
    const diff = Date.now() - ts;
    if (diff >= 0 && diff < tick) continue;
    await nextTick();
    ts += diff;
  }
}

// Global symbols in both browsers and Node.js since v11
// See https://github.com/microsoft/TypeScript/issues/31535
declare const TextEncoder: any;

/**
 * @example utf8ToBytes('abc') // new Uint8Array([97, 98, 99])
 */
export function utf8ToBytes(str: string): Uint8Array {
  if (typeof str !== 'string') throw new Error(`utf8ToBytes expected string, got ${typeof str}`);
  return new Uint8Array(new TextEncoder().encode(str)); // https://bugzil.la/1681809
}

export type Input = Uint8Array | string;
/**
 * Normalizes (non-hex) string or Uint8Array to Uint8Array.
 * Warning: when Uint8Array is passed, it would NOT get copied.
 * Keep in mind for future mutable operations.
 */
export function toBytes(data: Input): Uint8Array {
  if (typeof data === 'string') data = utf8ToBytes(data);
  if (!u8a(data)) throw new Error(`expected Uint8Array, got ${typeof data}`);
  return data;
}

/**
 * Copies several Uint8Arrays into one.
 */
export function concatBytes(...arrays: Uint8Array[]): Uint8Array {
  const r = new Uint8Array(arrays.reduce((sum, a) => sum + a.length, 0));
  let pad = 0; // walk through each item, ensure they have proper type
  arrays.forEach((a) => {
    if (!u8a(a)) throw new Error('Uint8Array expected');
    r.set(a, pad);
    pad += a.length;
  });
  return r;
}

// For runtime check if class implements interface
export abstract class Hash<T extends Hash<T>> {
  abstract blockLen: number; // Bytes per block
  abstract outputLen: number; // Bytes in output
  abstract update(buf: Input): this;
  // Writes digest into buf
  abstract digestInto(buf: Uint8Array): void;
  abstract digest(): Uint8Array;
  /**
   * Resets internal state. Makes Hash instance unusable.
   * Reset is impossible for keyed hashes if key is consumed into state. If digest is not consumed
   * by user, they will need to manually call `destroy()` when zeroing is necessary.
   */
  abstract destroy(): void;
  /**
   * Clones hash instance. Unsafe: doesn't check whether `to` is valid. Can be used as `clone()`
   * when no options are passed.
   * Reasons to use `_cloneInto` instead of clone: 1) performance 2) reuse instance => all internal
   * buffers are overwritten => causes buffer overwrite which is used for digest in some cases.
   * There are no guarantees for clean-up because it's impossible in JS.
   */
  abstract _cloneInto(to?: T): T;
  // Safe version that clones internal state
  clone(): T {
    return this._cloneInto();
  }
}

/**
 * XOF: streaming API to read digest in chunks.
 * Same as 'squeeze' in keccak/k12 and 'seek' in blake3, but more generic name.
 * When hash used in XOF mode it is up to user to call '.destroy' afterwards, since we cannot
 * destroy state, next call can require more bytes.
 */
export type HashXOF<T extends Hash<T>> = Hash<T> & {
  xof(bytes: number): Uint8Array; // Read 'bytes' bytes from digest stream
  xofInto(buf: Uint8Array): Uint8Array; // read buf.length bytes from digest stream into buf
};

const toStr = {}.toString;
type EmptyObj = {};
export function checkOpts<T1 extends EmptyObj, T2 extends EmptyObj>(
  defaults: T1,
  opts?: T2
): T1 & T2 {
  if (opts !== undefined && toStr.call(opts) !== '[object Object]')
    throw new Error('Options should be object or undefined');
  const merged = Object.assign(defaults, opts);
  return merged as T1 & T2;
}

export type CHash = ReturnType<typeof wrapConstructor>;

export function wrapConstructor<T extends Hash<T>>(hashCons: () => Hash<T>) {
  const hashC = (msg: Input): Uint8Array => hashCons().update(toBytes(msg)).digest();
  const tmp = hashCons();
  hashC.outputLen = tmp.outputLen;
  hashC.blockLen = tmp.blockLen;
  hashC.create = () => hashCons();
  return hashC;
}

export function wrapConstructorWithOpts<H extends Hash<H>, T extends Object>(
  hashCons: (opts?: T) => Hash<H>
) {
  const hashC = (msg: Input, opts?: T): Uint8Array => hashCons(opts).update(toBytes(msg)).digest();
  const tmp = hashCons({} as T);
  hashC.outputLen = tmp.outputLen;
  hashC.blockLen = tmp.blockLen;
  hashC.create = (opts: T) => hashCons(opts);
  return hashC;
}

export function wrapXOFConstructorWithOpts<H extends HashXOF<H>, T extends Object>(
  hashCons: (opts?: T) => HashXOF<H>
) {
  const hashC = (msg: Input, opts?: T): Uint8Array => hashCons(opts).update(toBytes(msg)).digest();
  const tmp = hashCons({} as T);
  hashC.outputLen = tmp.outputLen;
  hashC.blockLen = tmp.blockLen;
  hashC.create = (opts: T) => hashCons(opts);
  return hashC;
}

/**
 * Secure PRNG. Uses `crypto.getRandomValues`, which defers to OS.
 */
export function randomBytes(bytesLength = 32): Uint8Array {
  if (crypto && typeof crypto.getRandomValues === 'function') {
    return crypto.getRandomValues(new Uint8Array(bytesLength));
  }
  throw new Error('crypto.getRandomValues must be defined');
}
