/*! noble-curves - MIT License (c) 2022 Paul Miller (paulmillr.com) */
import type { Group, GroupConstructor, AffinePoint } from './curve.js';
import { mod, IField } from './modular.js';
import { bytesToNumberBE, CHash, concatBytes, utf8ToBytes, validateObject } from './utils.js';

/**
 * * `DST` is a domain separation tag, defined in section 2.2.5
 * * `p` characteristic of F, where F is a finite field of characteristic p and order q = p^m
 * * `m` is extension degree (1 for prime fields)
 * * `k` is the target security target in bits (e.g. 128), from section 5.1
 * * `expand` is `xmd` (SHA2, SHA3, BLAKE) or `xof` (SHAKE, BLAKE-XOF)
 * * `hash` conforming to `utils.CHash` interface, with `outputLen` / `blockLen` props
 */
type UnicodeOrBytes = string | Uint8Array;
export type Opts = {
  DST: UnicodeOrBytes;
  p: bigint;
  m: number;
  k: number;
  expand: 'xmd' | 'xof';
  hash: CHash;
};

function validateDST(dst: UnicodeOrBytes): Uint8Array {
  if (dst instanceof Uint8Array) return dst;
  if (typeof dst === 'string') return utf8ToBytes(dst);
  throw new Error('DST must be Uint8Array or string');
}

// Octet Stream to Integer. "spec" implementation of os2ip is 2.5x slower vs bytesToNumberBE.
const os2ip = bytesToNumberBE;

// Integer to Octet Stream (numberToBytesBE)
function i2osp(value: number, length: number): Uint8Array {
  if (value < 0 || value >= 1 << (8 * length)) {
    throw new Error(`bad I2OSP call: value=${value} length=${length}`);
  }
  const res = Array.from({ length }).fill(0) as number[];
  for (let i = length - 1; i >= 0; i--) {
    res[i] = value & 0xff;
    value >>>= 8;
  }
  return new Uint8Array(res);
}

function strxor(a: Uint8Array, b: Uint8Array): Uint8Array {
  const arr = new Uint8Array(a.length);
  for (let i = 0; i < a.length; i++) {
    arr[i] = a[i] ^ b[i];
  }
  return arr;
}

function isBytes(item: unknown): void {
  if (!(item instanceof Uint8Array)) throw new Error('Uint8Array expected');
}
function isNum(item: unknown): void {
  if (!Number.isSafeInteger(item)) throw new Error('number expected');
}

// Produces a uniformly random byte string using a cryptographic hash function H that outputs b bits
// https://www.rfc-editor.org/rfc/rfc9380#section-5.3.1
export function expand_message_xmd(
  msg: Uint8Array,
  DST: Uint8Array,
  lenInBytes: number,
  H: CHash
): Uint8Array {
  isBytes(msg);
  isBytes(DST);
  isNum(lenInBytes);
  // https://www.rfc-editor.org/rfc/rfc9380#section-5.3.3
  if (DST.length > 255) DST = H(concatBytes(utf8ToBytes('H2C-OVERSIZE-DST-'), DST));
  const { outputLen: b_in_bytes, blockLen: r_in_bytes } = H;
  const ell = Math.ceil(lenInBytes / b_in_bytes);
  if (ell > 255) throw new Error('Invalid xmd length');
  const DST_prime = concatBytes(DST, i2osp(DST.length, 1));
  const Z_pad = i2osp(0, r_in_bytes);
  const l_i_b_str = i2osp(lenInBytes, 2); // len_in_bytes_str
  const b = new Array<Uint8Array>(ell);
  const b_0 = H(concatBytes(Z_pad, msg, l_i_b_str, i2osp(0, 1), DST_prime));
  b[0] = H(concatBytes(b_0, i2osp(1, 1), DST_prime));
  for (let i = 1; i <= ell; i++) {
    const args = [strxor(b_0, b[i - 1]), i2osp(i + 1, 1), DST_prime];
    b[i] = H(concatBytes(...args));
  }
  const pseudo_random_bytes = concatBytes(...b);
  return pseudo_random_bytes.slice(0, lenInBytes);
}

// Produces a uniformly random byte string using an extendable-output function (XOF) H.
// 1. The collision resistance of H MUST be at least k bits.
// 2. H MUST be an XOF that has been proved indifferentiable from
//    a random oracle under a reasonable cryptographic assumption.
// https://www.rfc-editor.org/rfc/rfc9380#section-5.3.2
export function expand_message_xof(
  msg: Uint8Array,
  DST: Uint8Array,
  lenInBytes: number,
  k: number,
  H: CHash
): Uint8Array {
  isBytes(msg);
  isBytes(DST);
  isNum(lenInBytes);
  // https://www.rfc-editor.org/rfc/rfc9380#section-5.3.3
  // DST = H('H2C-OVERSIZE-DST-' || a_very_long_DST, Math.ceil((lenInBytes * k) / 8));
  if (DST.length > 255) {
    const dkLen = Math.ceil((2 * k) / 8);
    DST = H.create({ dkLen }).update(utf8ToBytes('H2C-OVERSIZE-DST-')).update(DST).digest();
  }
  if (lenInBytes > 65535 || DST.length > 255)
    throw new Error('expand_message_xof: invalid lenInBytes');
  return (
    H.create({ dkLen: lenInBytes })
      .update(msg)
      .update(i2osp(lenInBytes, 2))
      // 2. DST_prime = DST || I2OSP(len(DST), 1)
      .update(DST)
      .update(i2osp(DST.length, 1))
      .digest()
  );
}

/**
 * Hashes arbitrary-length byte strings to a list of one or more elements of a finite field F
 * https://www.rfc-editor.org/rfc/rfc9380#section-5.2
 * @param msg a byte string containing the message to hash
 * @param count the number of elements of F to output
 * @param options `{DST: string, p: bigint, m: number, k: number, expand: 'xmd' | 'xof', hash: H}`, see above
 * @returns [u_0, ..., u_(count - 1)], a list of field elements.
 */
export function hash_to_field(msg: Uint8Array, count: number, options: Opts): bigint[][] {
  validateObject(options, {
    DST: 'stringOrUint8Array',
    p: 'bigint',
    m: 'isSafeInteger',
    k: 'isSafeInteger',
    hash: 'hash',
  });
  const { p, k, m, hash, expand, DST: _DST } = options;
  isBytes(msg);
  isNum(count);
  const DST = validateDST(_DST);
  const log2p = p.toString(2).length;
  const L = Math.ceil((log2p + k) / 8); // section 5.1 of ietf draft link above
  const len_in_bytes = count * m * L;
  let prb; // pseudo_random_bytes
  if (expand === 'xmd') {
    prb = expand_message_xmd(msg, DST, len_in_bytes, hash);
  } else if (expand === 'xof') {
    prb = expand_message_xof(msg, DST, len_in_bytes, k, hash);
  } else if (expand === '_internal_pass') {
    // for internal tests only
    prb = msg;
  } else {
    throw new Error('expand must be "xmd" or "xof"');
  }
  const u = new Array(count);
  for (let i = 0; i < count; i++) {
    const e = new Array(m);
    for (let j = 0; j < m; j++) {
      const elm_offset = L * (j + i * m);
      const tv = prb.subarray(elm_offset, elm_offset + L);
      e[j] = mod(os2ip(tv), p);
    }
    u[i] = e;
  }
  return u;
}

export function isogenyMap<T, F extends IField<T>>(field: F, map: [T[], T[], T[], T[]]) {
  // Make same order as in spec
  const COEFF = map.map((i) => Array.from(i).reverse());
  return (x: T, y: T) => {
    const [xNum, xDen, yNum, yDen] = COEFF.map((val) =>
      val.reduce((acc, i) => field.add(field.mul(acc, x), i))
    );
    x = field.div(xNum, xDen); // xNum / xDen
    y = field.mul(y, field.div(yNum, yDen)); // y * (yNum / yDev)
    return { x, y };
  };
}

export interface H2CPoint<T> extends Group<H2CPoint<T>> {
  add(rhs: H2CPoint<T>): H2CPoint<T>;
  toAffine(iz?: bigint): AffinePoint<T>;
  clearCofactor(): H2CPoint<T>;
  assertValidity(): void;
}

export interface H2CPointConstructor<T> extends GroupConstructor<H2CPoint<T>> {
  fromAffine(ap: AffinePoint<T>): H2CPoint<T>;
}

export type MapToCurve<T> = (scalar: bigint[]) => AffinePoint<T>;

// Separated from initialization opts, so users won't accidentally change per-curve parameters
// (changing DST is ok!)
export type htfBasicOpts = { DST: UnicodeOrBytes };

export function createHasher<T>(
  Point: H2CPointConstructor<T>,
  mapToCurve: MapToCurve<T>,
  def: Opts & { encodeDST?: UnicodeOrBytes }
) {
  if (typeof mapToCurve !== 'function') throw new Error('mapToCurve() must be defined');
  return {
    // Encodes byte string to elliptic curve.
    // hash_to_curve from https://www.rfc-editor.org/rfc/rfc9380#section-3
    hashToCurve(msg: Uint8Array, options?: htfBasicOpts) {
      const u = hash_to_field(msg, 2, { ...def, DST: def.DST, ...options } as Opts);
      const u0 = Point.fromAffine(mapToCurve(u[0]));
      const u1 = Point.fromAffine(mapToCurve(u[1]));
      const P = u0.add(u1).clearCofactor();
      P.assertValidity();
      return P;
    },

    // Encodes byte string to elliptic curve.
    // encode_to_curve from https://www.rfc-editor.org/rfc/rfc9380#section-3
    encodeToCurve(msg: Uint8Array, options?: htfBasicOpts) {
      const u = hash_to_field(msg, 1, { ...def, DST: def.encodeDST, ...options } as Opts);
      const P = Point.fromAffine(mapToCurve(u[0])).clearCofactor();
      P.assertValidity();
      return P;
    },
  };
}
