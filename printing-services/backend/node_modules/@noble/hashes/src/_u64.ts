const U32_MASK64 = /* @__PURE__ */ BigInt(2 ** 32 - 1);
const _32n = /* @__PURE__ */ BigInt(32);

// We are not using BigUint64Array, because they are extremely slow as per 2022
function fromBig(n: bigint, le = false) {
  if (le) return { h: Number(n & U32_MASK64), l: Number((n >> _32n) & U32_MASK64) };
  return { h: Number((n >> _32n) & U32_MASK64) | 0, l: Number(n & U32_MASK64) | 0 };
}

function split(lst: bigint[], le = false) {
  let Ah = new Uint32Array(lst.length);
  let Al = new Uint32Array(lst.length);
  for (let i = 0; i < lst.length; i++) {
    const { h, l } = fromBig(lst[i], le);
    [Ah[i], Al[i]] = [h, l];
  }
  return [Ah, Al];
}

const toBig = (h: number, l: number) => (BigInt(h >>> 0) << _32n) | BigInt(l >>> 0);
// for Shift in [0, 32)
const shrSH = (h: number, _l: number, s: number) => h >>> s;
const shrSL = (h: number, l: number, s: number) => (h << (32 - s)) | (l >>> s);
// Right rotate for Shift in [1, 32)
const rotrSH = (h: number, l: number, s: number) => (h >>> s) | (l << (32 - s));
const rotrSL = (h: number, l: number, s: number) => (h << (32 - s)) | (l >>> s);
// Right rotate for Shift in (32, 64), NOTE: 32 is special case.
const rotrBH = (h: number, l: number, s: number) => (h << (64 - s)) | (l >>> (s - 32));
const rotrBL = (h: number, l: number, s: number) => (h >>> (s - 32)) | (l << (64 - s));
// Right rotate for shift===32 (just swaps l&h)
const rotr32H = (_h: number, l: number) => l;
const rotr32L = (h: number, _l: number) => h;
// Left rotate for Shift in [1, 32)
const rotlSH = (h: number, l: number, s: number) => (h << s) | (l >>> (32 - s));
const rotlSL = (h: number, l: number, s: number) => (l << s) | (h >>> (32 - s));
// Left rotate for Shift in (32, 64), NOTE: 32 is special case.
const rotlBH = (h: number, l: number, s: number) => (l << (s - 32)) | (h >>> (64 - s));
const rotlBL = (h: number, l: number, s: number) => (h << (s - 32)) | (l >>> (64 - s));

// JS uses 32-bit signed integers for bitwise operations which means we cannot
// simple take carry out of low bit sum by shift, we need to use division.
function add(Ah: number, Al: number, Bh: number, Bl: number) {
  const l = (Al >>> 0) + (Bl >>> 0);
  return { h: (Ah + Bh + ((l / 2 ** 32) | 0)) | 0, l: l | 0 };
}
// Addition with more than 2 elements
const add3L = (Al: number, Bl: number, Cl: number) => (Al >>> 0) + (Bl >>> 0) + (Cl >>> 0);
const add3H = (low: number, Ah: number, Bh: number, Ch: number) =>
  (Ah + Bh + Ch + ((low / 2 ** 32) | 0)) | 0;
const add4L = (Al: number, Bl: number, Cl: number, Dl: number) =>
  (Al >>> 0) + (Bl >>> 0) + (Cl >>> 0) + (Dl >>> 0);
const add4H = (low: number, Ah: number, Bh: number, Ch: number, Dh: number) =>
  (Ah + Bh + Ch + Dh + ((low / 2 ** 32) | 0)) | 0;
const add5L = (Al: number, Bl: number, Cl: number, Dl: number, El: number) =>
  (Al >>> 0) + (Bl >>> 0) + (Cl >>> 0) + (Dl >>> 0) + (El >>> 0);
const add5H = (low: number, Ah: number, Bh: number, Ch: number, Dh: number, Eh: number) =>
  (Ah + Bh + Ch + Dh + Eh + ((low / 2 ** 32) | 0)) | 0;

// prettier-ignore
export {
  fromBig, split, toBig,
  shrSH, shrSL,
  rotrSH, rotrSL, rotrBH, rotrBL,
  rotr32H, rotr32L,
  rotlSH, rotlSL, rotlBH, rotlBL,
  add, add3L, add3H, add4L, add4H, add5H, add5L,
};
// prettier-ignore
const u64 = {
  fromBig, split, toBig,
  shrSH, shrSL,
  rotrSH, rotrSL, rotrBH, rotrBL,
  rotr32H, rotr32L,
  rotlSH, rotlSL, rotlBH, rotlBL,
  add, add3L, add3H, add4L, add4H, add5H, add5L,
};
export default u64;
