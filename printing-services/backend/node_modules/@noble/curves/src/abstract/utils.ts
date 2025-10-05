/*! noble-curves - MIT License (c) 2022 Paul Miller (paulmillr.com) */
// 100 lines of code in the file are duplicated from noble-hashes (utils).
// This is OK: `abstract` directory does not use noble-hashes.
// User may opt-in into using different hashing library. This way, noble-hashes
// won't be included into their bundle.
const _0n = BigInt(0);
const _1n = BigInt(1);
const _2n = BigInt(2);
const u8a = (a: any): a is Uint8Array => a instanceof Uint8Array;
export type Hex = Uint8Array | string; // hex strings are accepted for simplicity
export type PrivKey = Hex | bigint; // bigints are accepted to ease learning curve
export type CHash = {
  (message: Uint8Array | string): Uint8Array;
  blockLen: number;
  outputLen: number;
  create(opts?: { dkLen?: number }): any; // For shake
};
export type FHash = (message: Uint8Array | string) => Uint8Array;

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

export function numberToHexUnpadded(num: number | bigint): string {
  const hex = num.toString(16);
  return hex.length & 1 ? `0${hex}` : hex;
}

export function hexToNumber(hex: string): bigint {
  if (typeof hex !== 'string') throw new Error('hex string expected, got ' + typeof hex);
  // Big Endian
  return BigInt(hex === '' ? '0' : `0x${hex}`);
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

// BE: Big Endian, LE: Little Endian
export function bytesToNumberBE(bytes: Uint8Array): bigint {
  return hexToNumber(bytesToHex(bytes));
}
export function bytesToNumberLE(bytes: Uint8Array): bigint {
  if (!u8a(bytes)) throw new Error('Uint8Array expected');
  return hexToNumber(bytesToHex(Uint8Array.from(bytes).reverse()));
}

export function numberToBytesBE(n: number | bigint, len: number): Uint8Array {
  return hexToBytes(n.toString(16).padStart(len * 2, '0'));
}
export function numberToBytesLE(n: number | bigint, len: number): Uint8Array {
  return numberToBytesBE(n, len).reverse();
}
// Unpadded, rarely used
export function numberToVarBytesBE(n: number | bigint): Uint8Array {
  return hexToBytes(numberToHexUnpadded(n));
}

/**
 * Takes hex string or Uint8Array, converts to Uint8Array.
 * Validates output length.
 * Will throw error for other types.
 * @param title descriptive title for an error e.g. 'private key'
 * @param hex hex string or Uint8Array
 * @param expectedLength optional, will compare to result array's length
 * @returns
 */
export function ensureBytes(title: string, hex: Hex, expectedLength?: number): Uint8Array {
  let res: Uint8Array;
  if (typeof hex === 'string') {
    try {
      res = hexToBytes(hex);
    } catch (e) {
      throw new Error(`${title} must be valid hex string, got "${hex}". Cause: ${e}`);
    }
  } else if (u8a(hex)) {
    // Uint8Array.from() instead of hash.slice() because node.js Buffer
    // is instance of Uint8Array, and its slice() creates **mutable** copy
    res = Uint8Array.from(hex);
  } else {
    throw new Error(`${title} must be hex string or Uint8Array`);
  }
  const len = res.length;
  if (typeof expectedLength === 'number' && len !== expectedLength)
    throw new Error(`${title} expected ${expectedLength} bytes, got ${len}`);
  return res;
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

export function equalBytes(b1: Uint8Array, b2: Uint8Array) {
  // We don't care about timing attacks here
  if (b1.length !== b2.length) return false;
  for (let i = 0; i < b1.length; i++) if (b1[i] !== b2[i]) return false;
  return true;
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

// Bit operations

/**
 * Calculates amount of bits in a bigint.
 * Same as `n.toString(2).length`
 */
export function bitLen(n: bigint) {
  let len;
  for (len = 0; n > _0n; n >>= _1n, len += 1);
  return len;
}

/**
 * Gets single bit at position.
 * NOTE: first bit position is 0 (same as arrays)
 * Same as `!!+Array.from(n.toString(2)).reverse()[pos]`
 */
export function bitGet(n: bigint, pos: number) {
  return (n >> BigInt(pos)) & _1n;
}

/**
 * Sets single bit at position.
 */
export const bitSet = (n: bigint, pos: number, value: boolean) => {
  return n | ((value ? _1n : _0n) << BigInt(pos));
};

/**
 * Calculate mask for N bits. Not using ** operator with bigints because of old engines.
 * Same as BigInt(`0b${Array(i).fill('1').join('')}`)
 */
export const bitMask = (n: number) => (_2n << BigInt(n - 1)) - _1n;

// DRBG

const u8n = (data?: any) => new Uint8Array(data); // creates Uint8Array
const u8fr = (arr: any) => Uint8Array.from(arr); // another shortcut
type Pred<T> = (v: Uint8Array) => T | undefined;
/**
 * Minimal HMAC-DRBG from NIST 800-90 for RFC6979 sigs.
 * @returns function that will call DRBG until 2nd arg returns something meaningful
 * @example
 *   const drbg = createHmacDRBG<Key>(32, 32, hmac);
 *   drbg(seed, bytesToKey); // bytesToKey must return Key or undefined
 */
export function createHmacDrbg<T>(
  hashLen: number,
  qByteLen: number,
  hmacFn: (key: Uint8Array, ...messages: Uint8Array[]) => Uint8Array
): (seed: Uint8Array, predicate: Pred<T>) => T {
  if (typeof hashLen !== 'number' || hashLen < 2) throw new Error('hashLen must be a number');
  if (typeof qByteLen !== 'number' || qByteLen < 2) throw new Error('qByteLen must be a number');
  if (typeof hmacFn !== 'function') throw new Error('hmacFn must be a function');
  // Step B, Step C: set hashLen to 8*ceil(hlen/8)
  let v = u8n(hashLen); // Minimal non-full-spec HMAC-DRBG from NIST 800-90 for RFC6979 sigs.
  let k = u8n(hashLen); // Steps B and C of RFC6979 3.2: set hashLen, in our case always same
  let i = 0; // Iterations counter, will throw when over 1000
  const reset = () => {
    v.fill(1);
    k.fill(0);
    i = 0;
  };
  const h = (...b: Uint8Array[]) => hmacFn(k, v, ...b); // hmac(k)(v, ...values)
  const reseed = (seed = u8n()) => {
    // HMAC-DRBG reseed() function. Steps D-G
    k = h(u8fr([0x00]), seed); // k = hmac(k || v || 0x00 || seed)
    v = h(); // v = hmac(k || v)
    if (seed.length === 0) return;
    k = h(u8fr([0x01]), seed); // k = hmac(k || v || 0x01 || seed)
    v = h(); // v = hmac(k || v)
  };
  const gen = () => {
    // HMAC-DRBG generate() function
    if (i++ >= 1000) throw new Error('drbg: tried 1000 values');
    let len = 0;
    const out: Uint8Array[] = [];
    while (len < qByteLen) {
      v = h();
      const sl = v.slice();
      out.push(sl);
      len += v.length;
    }
    return concatBytes(...out);
  };
  const genUntil = (seed: Uint8Array, pred: Pred<T>): T => {
    reset();
    reseed(seed); // Steps D-G
    let res: T | undefined = undefined; // Step H: grind until k is in [1..n-1]
    while (!(res = pred(gen()))) reseed();
    reset();
    return res;
  };
  return genUntil;
}

// Validating curves and fields

const validatorFns = {
  bigint: (val: any) => typeof val === 'bigint',
  function: (val: any) => typeof val === 'function',
  boolean: (val: any) => typeof val === 'boolean',
  string: (val: any) => typeof val === 'string',
  stringOrUint8Array: (val: any) => typeof val === 'string' || val instanceof Uint8Array,
  isSafeInteger: (val: any) => Number.isSafeInteger(val),
  array: (val: any) => Array.isArray(val),
  field: (val: any, object: any) => (object as any).Fp.isValid(val),
  hash: (val: any) => typeof val === 'function' && Number.isSafeInteger(val.outputLen),
} as const;
type Validator = keyof typeof validatorFns;
type ValMap<T extends Record<string, any>> = { [K in keyof T]?: Validator };
// type Record<K extends string | number | symbol, T> = { [P in K]: T; }

export function validateObject<T extends Record<string, any>>(
  object: T,
  validators: ValMap<T>,
  optValidators: ValMap<T> = {}
) {
  const checkField = (fieldName: keyof T, type: Validator, isOptional: boolean) => {
    const checkVal = validatorFns[type];
    if (typeof checkVal !== 'function')
      throw new Error(`Invalid validator "${type}", expected function`);

    const val = object[fieldName as keyof typeof object];
    if (isOptional && val === undefined) return;
    if (!checkVal(val, object)) {
      throw new Error(
        `Invalid param ${String(fieldName)}=${val} (${typeof val}), expected ${type}`
      );
    }
  };
  for (const [fieldName, type] of Object.entries(validators)) checkField(fieldName, type!, false);
  for (const [fieldName, type] of Object.entries(optValidators)) checkField(fieldName, type!, true);
  return object;
}
// validate type tests
// const o: { a: number; b: number; c: number } = { a: 1, b: 5, c: 6 };
// const z0 = validateObject(o, { a: 'isSafeInteger' }, { c: 'bigint' }); // Ok!
// // Should fail type-check
// const z1 = validateObject(o, { a: 'tmp' }, { c: 'zz' });
// const z2 = validateObject(o, { a: 'isSafeInteger' }, { c: 'zz' });
// const z3 = validateObject(o, { test: 'boolean', z: 'bug' });
// const z4 = validateObject(o, { a: 'boolean', z: 'bug' });
