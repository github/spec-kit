import { number as assertNumber } from './_assert.js';
import { sha256 } from './sha256.js';
import { pbkdf2 } from './pbkdf2.js';
import { asyncLoop, checkOpts, Input, u32 } from './utils.js';

// RFC 7914 Scrypt KDF

// Left rotate for uint32
const rotl = (a: number, b: number) => (a << b) | (a >>> (32 - b));

// The main Scrypt loop: uses Salsa extensively.
// Six versions of the function were tried, this is the fastest one.
// prettier-ignore
function XorAndSalsa(
  prev: Uint32Array,
  pi: number,
  input: Uint32Array,
  ii: number,
  out: Uint32Array,
  oi: number
) {
  // Based on https://cr.yp.to/salsa20.html
  // Xor blocks
  let y00 = prev[pi++] ^ input[ii++], y01 = prev[pi++] ^ input[ii++];
  let y02 = prev[pi++] ^ input[ii++], y03 = prev[pi++] ^ input[ii++];
  let y04 = prev[pi++] ^ input[ii++], y05 = prev[pi++] ^ input[ii++];
  let y06 = prev[pi++] ^ input[ii++], y07 = prev[pi++] ^ input[ii++];
  let y08 = prev[pi++] ^ input[ii++], y09 = prev[pi++] ^ input[ii++];
  let y10 = prev[pi++] ^ input[ii++], y11 = prev[pi++] ^ input[ii++];
  let y12 = prev[pi++] ^ input[ii++], y13 = prev[pi++] ^ input[ii++];
  let y14 = prev[pi++] ^ input[ii++], y15 = prev[pi++] ^ input[ii++];
  // Save state to temporary variables (salsa)
  let x00 = y00, x01 = y01, x02 = y02, x03 = y03,
      x04 = y04, x05 = y05, x06 = y06, x07 = y07,
      x08 = y08, x09 = y09, x10 = y10, x11 = y11,
      x12 = y12, x13 = y13, x14 = y14, x15 = y15;
  // Main loop (salsa)
  for (let i = 0; i < 8; i += 2) {
    x04 ^= rotl(x00 + x12 | 0,  7); x08 ^= rotl(x04 + x00 | 0,  9);
    x12 ^= rotl(x08 + x04 | 0, 13); x00 ^= rotl(x12 + x08 | 0, 18);
    x09 ^= rotl(x05 + x01 | 0,  7); x13 ^= rotl(x09 + x05 | 0,  9);
    x01 ^= rotl(x13 + x09 | 0, 13); x05 ^= rotl(x01 + x13 | 0, 18);
    x14 ^= rotl(x10 + x06 | 0,  7); x02 ^= rotl(x14 + x10 | 0,  9);
    x06 ^= rotl(x02 + x14 | 0, 13); x10 ^= rotl(x06 + x02 | 0, 18);
    x03 ^= rotl(x15 + x11 | 0,  7); x07 ^= rotl(x03 + x15 | 0,  9);
    x11 ^= rotl(x07 + x03 | 0, 13); x15 ^= rotl(x11 + x07 | 0, 18);
    x01 ^= rotl(x00 + x03 | 0,  7); x02 ^= rotl(x01 + x00 | 0,  9);
    x03 ^= rotl(x02 + x01 | 0, 13); x00 ^= rotl(x03 + x02 | 0, 18);
    x06 ^= rotl(x05 + x04 | 0,  7); x07 ^= rotl(x06 + x05 | 0,  9);
    x04 ^= rotl(x07 + x06 | 0, 13); x05 ^= rotl(x04 + x07 | 0, 18);
    x11 ^= rotl(x10 + x09 | 0,  7); x08 ^= rotl(x11 + x10 | 0,  9);
    x09 ^= rotl(x08 + x11 | 0, 13); x10 ^= rotl(x09 + x08 | 0, 18);
    x12 ^= rotl(x15 + x14 | 0,  7); x13 ^= rotl(x12 + x15 | 0,  9);
    x14 ^= rotl(x13 + x12 | 0, 13); x15 ^= rotl(x14 + x13 | 0, 18);
  }
  // Write output (salsa)
  out[oi++] = (y00 + x00) | 0; out[oi++] = (y01 + x01) | 0;
  out[oi++] = (y02 + x02) | 0; out[oi++] = (y03 + x03) | 0;
  out[oi++] = (y04 + x04) | 0; out[oi++] = (y05 + x05) | 0;
  out[oi++] = (y06 + x06) | 0; out[oi++] = (y07 + x07) | 0;
  out[oi++] = (y08 + x08) | 0; out[oi++] = (y09 + x09) | 0;
  out[oi++] = (y10 + x10) | 0; out[oi++] = (y11 + x11) | 0;
  out[oi++] = (y12 + x12) | 0; out[oi++] = (y13 + x13) | 0;
  out[oi++] = (y14 + x14) | 0; out[oi++] = (y15 + x15) | 0;
}

function BlockMix(input: Uint32Array, ii: number, out: Uint32Array, oi: number, r: number) {
  // The block B is r 128-byte chunks (which is equivalent of 2r 64-byte chunks)
  let head = oi + 0;
  let tail = oi + 16 * r;
  for (let i = 0; i < 16; i++) out[tail + i] = input[ii + (2 * r - 1) * 16 + i]; // X ← B[2r−1]
  for (let i = 0; i < r; i++, head += 16, ii += 16) {
    // We write odd & even Yi at same time. Even: 0bXXXXX0 Odd:  0bXXXXX1
    XorAndSalsa(out, tail, input, ii, out, head); // head[i] = Salsa(blockIn[2*i] ^ tail[i-1])
    if (i > 0) tail += 16; // First iteration overwrites tmp value in tail
    XorAndSalsa(out, head, input, (ii += 16), out, tail); // tail[i] = Salsa(blockIn[2*i+1] ^ head[i])
  }
}

export type ScryptOpts = {
  N: number; // cost factor
  r: number; // block size
  p: number; // parallelization
  dkLen?: number; // key length
  asyncTick?: number; // block execution max time
  maxmem?: number;
  onProgress?: (progress: number) => void;
};

// Common prologue and epilogue for sync/async functions
function scryptInit(password: Input, salt: Input, _opts?: ScryptOpts) {
  // Maxmem - 1GB+1KB by default
  const opts = checkOpts(
    {
      dkLen: 32,
      asyncTick: 10,
      maxmem: 1024 ** 3 + 1024,
    },
    _opts
  );
  const { N, r, p, dkLen, asyncTick, maxmem, onProgress } = opts;
  assertNumber(N);
  assertNumber(r);
  assertNumber(p);
  assertNumber(dkLen);
  assertNumber(asyncTick);
  assertNumber(maxmem);
  if (onProgress !== undefined && typeof onProgress !== 'function')
    throw new Error('progressCb should be function');
  const blockSize = 128 * r;
  const blockSize32 = blockSize / 4;
  if (N <= 1 || (N & (N - 1)) !== 0 || N >= 2 ** (blockSize / 8) || N > 2 ** 32) {
    // NOTE: we limit N to be less than 2**32 because of 32 bit variant of Integrify function
    // There is no JS engines that allows alocate more than 4GB per single Uint8Array for now, but can change in future.
    throw new Error(
      'Scrypt: N must be larger than 1, a power of 2, less than 2^(128 * r / 8) and less than 2^32'
    );
  }
  if (p < 0 || p > ((2 ** 32 - 1) * 32) / blockSize) {
    throw new Error(
      'Scrypt: p must be a positive integer less than or equal to ((2^32 - 1) * 32) / (128 * r)'
    );
  }
  if (dkLen < 0 || dkLen > (2 ** 32 - 1) * 32) {
    throw new Error(
      'Scrypt: dkLen should be positive integer less than or equal to (2^32 - 1) * 32'
    );
  }
  const memUsed = blockSize * (N + p);
  if (memUsed > maxmem) {
    throw new Error(
      `Scrypt: parameters too large, ${memUsed} (128 * r * (N + p)) > ${maxmem} (maxmem)`
    );
  }
  // [B0...Bp−1] ← PBKDF2HMAC-SHA256(Passphrase, Salt, 1, blockSize*ParallelizationFactor)
  // Since it has only one iteration there is no reason to use async variant
  const B = pbkdf2(sha256, password, salt, { c: 1, dkLen: blockSize * p });
  const B32 = u32(B);
  // Re-used between parallel iterations. Array(iterations) of B
  const V = u32(new Uint8Array(blockSize * N));
  const tmp = u32(new Uint8Array(blockSize));
  let blockMixCb = () => {};
  if (onProgress) {
    const totalBlockMix = 2 * N * p;
    // Invoke callback if progress changes from 10.01 to 10.02
    // Allows to draw smooth progress bar on up to 8K screen
    const callbackPer = Math.max(Math.floor(totalBlockMix / 10000), 1);
    let blockMixCnt = 0;
    blockMixCb = () => {
      blockMixCnt++;
      if (onProgress && (!(blockMixCnt % callbackPer) || blockMixCnt === totalBlockMix))
        onProgress(blockMixCnt / totalBlockMix);
    };
  }
  return { N, r, p, dkLen, blockSize32, V, B32, B, tmp, blockMixCb, asyncTick };
}

function scryptOutput(
  password: Input,
  dkLen: number,
  B: Uint8Array,
  V: Uint32Array,
  tmp: Uint32Array
) {
  const res = pbkdf2(sha256, password, B, { c: 1, dkLen });
  B.fill(0);
  V.fill(0);
  tmp.fill(0);
  return res;
}

/**
 * Scrypt KDF from RFC 7914.
 * @param password - pass
 * @param salt - salt
 * @param opts - parameters
 * - `N` is cpu/mem work factor (power of 2 e.g. 2**18)
 * - `r` is block size (8 is common), fine-tunes sequential memory read size and performance
 * - `p` is parallelization factor (1 is common)
 * - `dkLen` is output key length in bytes e.g. 32.
 * - `asyncTick` - (default: 10) max time in ms for which async function can block execution
 * - `maxmem` - (default: `1024 ** 3 + 1024` aka 1GB+1KB). A limit that the app could use for scrypt
 * - `onProgress` - callback function that would be executed for progress report
 * @returns Derived key
 */
export function scrypt(password: Input, salt: Input, opts: ScryptOpts) {
  const { N, r, p, dkLen, blockSize32, V, B32, B, tmp, blockMixCb } = scryptInit(
    password,
    salt,
    opts
  );
  for (let pi = 0; pi < p; pi++) {
    const Pi = blockSize32 * pi;
    for (let i = 0; i < blockSize32; i++) V[i] = B32[Pi + i]; // V[0] = B[i]
    for (let i = 0, pos = 0; i < N - 1; i++) {
      BlockMix(V, pos, V, (pos += blockSize32), r); // V[i] = BlockMix(V[i-1]);
      blockMixCb();
    }
    BlockMix(V, (N - 1) * blockSize32, B32, Pi, r); // Process last element
    blockMixCb();
    for (let i = 0; i < N; i++) {
      // First u32 of the last 64-byte block (u32 is LE)
      const j = B32[Pi + blockSize32 - 16] % N; // j = Integrify(X) % iterations
      for (let k = 0; k < blockSize32; k++) tmp[k] = B32[Pi + k] ^ V[j * blockSize32 + k]; // tmp = B ^ V[j]
      BlockMix(tmp, 0, B32, Pi, r); // B = BlockMix(B ^ V[j])
      blockMixCb();
    }
  }
  return scryptOutput(password, dkLen, B, V, tmp);
}

/**
 * Scrypt KDF from RFC 7914.
 */
export async function scryptAsync(password: Input, salt: Input, opts: ScryptOpts) {
  const { N, r, p, dkLen, blockSize32, V, B32, B, tmp, blockMixCb, asyncTick } = scryptInit(
    password,
    salt,
    opts
  );
  for (let pi = 0; pi < p; pi++) {
    const Pi = blockSize32 * pi;
    for (let i = 0; i < blockSize32; i++) V[i] = B32[Pi + i]; // V[0] = B[i]
    let pos = 0;
    await asyncLoop(N - 1, asyncTick, () => {
      BlockMix(V, pos, V, (pos += blockSize32), r); // V[i] = BlockMix(V[i-1]);
      blockMixCb();
    });
    BlockMix(V, (N - 1) * blockSize32, B32, Pi, r); // Process last element
    blockMixCb();
    await asyncLoop(N, asyncTick, () => {
      // First u32 of the last 64-byte block (u32 is LE)
      const j = B32[Pi + blockSize32 - 16] % N; // j = Integrify(X) % iterations
      for (let k = 0; k < blockSize32; k++) tmp[k] = B32[Pi + k] ^ V[j * blockSize32 + k]; // tmp = B ^ V[j]
      BlockMix(tmp, 0, B32, Pi, r); // B = BlockMix(B ^ V[j])
      blockMixCb();
    });
  }
  return scryptOutput(password, dkLen, B, V, tmp);
}
