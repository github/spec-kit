# noble-curves

Audited & minimal JS implementation of elliptic curve cryptography.

- 🔒 [**Audited**](#security) by an independent security firm
- 🔻 Tree-shaking-friendly: use only what's necessary, other code won't be included
- 🏎 Ultra-fast, hand-optimized for caveats of JS engines
- 🔍 Unique tests ensure correctness: property-based, cross-library and Wycheproof vectors, fuzzing
- ➰ Short Weierstrass, Edwards, Montgomery curves
- ✍️ ECDSA, EdDSA, Schnorr, BLS signature schemes, ECDH key agreement
- 🔖 SUF-CMA and SBS (non-repudiation) for ed25519, ed448 and others
- #️⃣ hash-to-curve for encoding or hashing an arbitrary string to an elliptic curve point
- 🧜‍♂️ Poseidon ZK-friendly hash

### This library belongs to _noble_ crypto

> **noble-crypto** — high-security, easily auditable set of contained cryptographic libraries and tools.

- No dependencies, protection against supply chain attacks
- Auditable TypeScript / JS code
- Supported on all major platforms
- Releases are signed with PGP keys and built transparently with NPM provenance
- Check out [homepage](https://paulmillr.com/noble/) & all libraries:
  [ciphers](https://github.com/paulmillr/noble-ciphers),
  [curves](https://github.com/paulmillr/noble-curves),
  [hashes](https://github.com/paulmillr/noble-hashes),
  4kb [secp256k1](https://github.com/paulmillr/noble-secp256k1) /
  [ed25519](https://github.com/paulmillr/noble-ed25519)

## Usage

> npm install @noble/curves

We support all major platforms and runtimes.
For [Deno](https://deno.land), ensure to use [npm specifier](https://deno.land/manual@v1.28.0/node/npm_specifiers).
For React Native, you may need a [polyfill for crypto.getRandomValues](https://github.com/LinusU/react-native-get-random-values).
If you don't like NPM, a standalone [noble-curves.js](https://github.com/paulmillr/noble-curves/releases) is also available.

- [Implementations](#implementations)
  - [ECDSA signature scheme](#ecdsa-signature-scheme)
  - [ECDSA public key recovery & extra entropy](#ecdsa-public-key-recovery--extra-entropy)
  - [ECDH (Elliptic Curve Diffie-Hellman)](#ecdh-elliptic-curve-diffie-hellman)
  - [Schnorr signatures over secp256k1, BIP340](#schnorr-signatures-over-secp256k1-bip340)
  - [ed25519, X25519, ristretto255](#ed25519-x25519-ristretto255)
  - [ed448, X448, decaf448](#ed448-x448-decaf448)
  - [bls12-381](#bls12-381)
  - [All available imports](#all-available-imports)
  - [Accessing a curve's variables](#accessing-a-curves-variables)
- [Abstract API](#abstract-api)
  - [abstract/weierstrass: Short Weierstrass curve](#abstractweierstrass-short-weierstrass-curve)
  - [abstract/edwards: Twisted Edwards curve](#abstractedwards-twisted-edwards-curve)
  - [abstract/montgomery: Montgomery curve](#abstractmontgomery-montgomery-curve)
  - [abstract/bls: Barreto-Lynn-Scott curves](#abstractbls-barreto-lynn-scott-curves)
  - [abstract/hash-to-curve: Hashing strings to curve points](#abstracthash-to-curve-hashing-strings-to-curve-points)
  - [abstract/poseidon: Poseidon hash](#abstractposeidon-poseidon-hash)
  - [abstract/modular: Modular arithmetics utilities](#abstractmodular-modular-arithmetics-utilities)
    - [Creating private keys from hashes](#creating-private-keys-from-hashes)
  - [abstract/utils: Useful utilities](#abstractutils-useful-utilities)
- [Security](#security)
- [Speed](#speed)
- [Contributing & testing](#contributing--testing)
- [Upgrading](#upgrading)
- [Resources](#resources)
  - [Demos](#demos)
  - [Projects using curves](#projects-using-curves)
- [License](#license)

### Implementations

Implementations are utilizing [noble-hashes](https://github.com/paulmillr/noble-hashes).
[Abstract API](#abstract-api) doesn't depend on them: you can use a different hashing library.

#### ECDSA signature scheme

Generic example that works for all curves, shown for secp256k1:

```ts
// import * from '@noble/curves'; // Error: use sub-imports, to ensure small app size
import { secp256k1 } from '@noble/curves/secp256k1'; // ESM and Common.js
// import { secp256k1 } from 'npm:@noble/curves@1.2.0/secp256k1'; // Deno
const priv = secp256k1.utils.randomPrivateKey();
const pub = secp256k1.getPublicKey(priv);
const msg = new Uint8Array(32).fill(1); // message hash (not message) in ecdsa
const sig = secp256k1.sign(msg, priv); // `{prehash: true}` option is available
const isValid = secp256k1.verify(sig, msg, pub) === true;

// hex strings are also supported besides Uint8Arrays:
const privHex = '46c930bc7bb4db7f55da20798697421b98c4175a52c630294d75a84b9c126236';
const pub2 = secp256k1.getPublicKey(privHex);
```

#### ECDSA public key recovery & extra entropy

```ts
sig.recoverPublicKey(msg).toRawBytes(); // === pub; // public key recovery

// extraEntropy https://moderncrypto.org/mail-archive/curves/2017/000925.html
const sigImprovedSecurity = secp256k1.sign(msg, priv, { extraEntropy: true });
```

#### ECDH (Elliptic Curve Diffie-Hellman)

```ts
// 1. The output includes parity byte. Strip it using shared.slice(1)
// 2. The output is not hashed. More secure way is sha256(shared) or hkdf(shared)
const someonesPub = secp256k1.getPublicKey(secp256k1.utils.randomPrivateKey());
const shared = secp256k1.getSharedSecret(priv, someonesPub);
```

#### Schnorr signatures over secp256k1 (BIP340)

```ts
import { schnorr } from '@noble/curves/secp256k1';
const priv = schnorr.utils.randomPrivateKey();
const pub = schnorr.getPublicKey(priv);
const msg = new TextEncoder().encode('hello');
const sig = schnorr.sign(msg, priv);
const isValid = schnorr.verify(sig, msg, pub);
```

#### ed25519, X25519, ristretto255

```ts
import { ed25519 } from '@noble/curves/ed25519';
const priv = ed25519.utils.randomPrivateKey();
const pub = ed25519.getPublicKey(priv);
const msg = new TextEncoder().encode('hello');
const sig = ed25519.sign(msg, priv);
ed25519.verify(sig, msg, pub); // Default mode: follows ZIP215
ed25519.verify(sig, msg, pub, { zip215: false }); // RFC8032 / FIPS 186-5
```

Default `verify` behavior follows [ZIP215](https://zips.z.cash/zip-0215) and
[can be used in consensus-critical applications](https://hdevalence.ca/blog/2020-10-04-its-25519am).
It has SUF-CMA (strong unforgeability under chosen message attacks).
`zip215: false` option switches verification criteria to strict
[RFC8032](https://www.rfc-editor.org/rfc/rfc8032) / [FIPS 186-5](https://csrc.nist.gov/publications/detail/fips/186/5/final)
and additionally provides non-repudiation with SBS [(Strongly Binding Signatures)](https://eprint.iacr.org/2020/1244).

X25519 follows [RFC7748](https://www.rfc-editor.org/rfc/rfc7748).

```ts
// Variants from RFC8032: with context, prehashed
import { ed25519ctx, ed25519ph } from '@noble/curves/ed25519';

// ECDH using curve25519 aka x25519
import { x25519 } from '@noble/curves/ed25519';
const priv = 'a546e36bf0527c9d3b16154b82465edd62144c0ac1fc5a18506a2244ba449ac4';
const pub = 'e6db6867583030db3594c1a424b15f7c726624ec26b3353b10a903a6d0ab1c4c';
x25519.getSharedSecret(priv, pub) === x25519.scalarMult(priv, pub); // aliases
x25519.getPublicKey(priv) === x25519.scalarMultBase(priv);
x25519.getPublicKey(x25519.utils.randomPrivateKey());

// ed25519 => x25519 conversion
import { edwardsToMontgomeryPub, edwardsToMontgomeryPriv } from '@noble/curves/ed25519';
edwardsToMontgomeryPub(ed25519.getPublicKey(ed25519.utils.randomPrivateKey()));
edwardsToMontgomeryPriv(ed25519.utils.randomPrivateKey());
```

ristretto255 follows [irtf draft](https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-ristretto255-decaf448).

```ts
// hash-to-curve, ristretto255
import { utf8ToBytes } from '@noble/hashes/utils';
import { sha512 } from '@noble/hashes/sha512';
import {
  hashToCurve,
  encodeToCurve,
  RistrettoPoint,
  hashToRistretto255,
} from '@noble/curves/ed25519';

const msg = utf8ToBytes('Ristretto is traditionally a short shot of espresso coffee');
hashToCurve(msg);

const rp = RistrettoPoint.fromHex(
  '6a493210f7499cd17fecb510ae0cea23a110e8d5b901f8acadd3095c73a3b919'
);
RistrettoPoint.BASE.multiply(2n).add(rp).subtract(RistrettoPoint.BASE).toRawBytes();
RistrettoPoint.ZERO.equals(dp) === false;
// pre-hashed hash-to-curve
RistrettoPoint.hashToCurve(sha512(msg));
// full hash-to-curve including domain separation tag
hashToRistretto255(msg, { DST: 'ristretto255_XMD:SHA-512_R255MAP_RO_' });
```

#### ed448, X448, decaf448

```ts
import { ed448 } from '@noble/curves/ed448';
const priv = ed448.utils.randomPrivateKey();
const pub = ed448.getPublicKey(priv);
const msg = new TextEncoder().encode('whatsup');
const sig = ed448.sign(msg, priv);
ed448.verify(sig, msg, pub);

// Variants from RFC8032: prehashed
import { ed448ph } from '@noble/curves/ed448';
```

ECDH using Curve448 aka X448, follows [RFC7748](https://www.rfc-editor.org/rfc/rfc7748).

```ts
import { x448 } from '@noble/curves/ed448';
x448.getSharedSecret(priv, pub) === x448.scalarMult(priv, pub); // aliases
x448.getPublicKey(priv) === x448.scalarMultBase(priv);

// ed448 => x448 conversion
import { edwardsToMontgomeryPub } from '@noble/curves/ed448';
edwardsToMontgomeryPub(ed448.getPublicKey(ed448.utils.randomPrivateKey()));
```

decaf448 follows [irtf draft](https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-ristretto255-decaf448).

```ts
import { utf8ToBytes } from '@noble/hashes/utils';
import { shake256 } from '@noble/hashes/sha3';
import { hashToCurve, encodeToCurve, DecafPoint, hashToDecaf448 } from '@noble/curves/ed448';

const msg = utf8ToBytes('Ristretto is traditionally a short shot of espresso coffee');
hashToCurve(msg);

const dp = DecafPoint.fromHex(
  'c898eb4f87f97c564c6fd61fc7e49689314a1f818ec85eeb3bd5514ac816d38778f69ef347a89fca817e66defdedce178c7cc709b2116e75'
);
DecafPoint.BASE.multiply(2n).add(dp).subtract(DecafPoint.BASE).toRawBytes();
DecafPoint.ZERO.equals(dp) === false;
// pre-hashed hash-to-curve
DecafPoint.hashToCurve(shake256(msg, { dkLen: 112 }));
// full hash-to-curve including domain separation tag
hashToDecaf448(msg, { DST: 'decaf448_XOF:SHAKE256_D448MAP_RO_' });
```

Same RFC7748 / RFC8032 / IRTF draft are followed.

#### bls12-381

See [abstract/bls](#abstractbls-barreto-lynn-scott-curves).

#### All available imports

```typescript
import { secp256k1, schnorr } from '@noble/curves/secp256k1';
import { ed25519, ed25519ph, ed25519ctx, x25519, RistrettoPoint } from '@noble/curves/ed25519';
import { ed448, ed448ph, ed448ctx, x448 } from '@noble/curves/ed448';
import { p256 } from '@noble/curves/p256';
import { p384 } from '@noble/curves/p384';
import { p521 } from '@noble/curves/p521';
import { pallas, vesta } from '@noble/curves/pasta';
import { bls12_381 } from '@noble/curves/bls12-381';
import { bn254 } from '@noble/curves/bn254'; // also known as alt_bn128
import { jubjub } from '@noble/curves/jubjub';
import { bytesToHex, hexToBytes, concatBytes, utf8ToBytes } from '@noble/curves/abstract/utils';
```

#### Accessing a curve's variables

```ts
import { secp256k1 } from '@noble/curves/secp256k1';
// Every curve has `CURVE` object that contains its parameters, field, and others
console.log(secp256k1.CURVE.p); // field modulus
console.log(secp256k1.CURVE.n); // curve order
console.log(secp256k1.CURVE.a, secp256k1.CURVE.b); // equation params
console.log(secp256k1.CURVE.Gx, secp256k1.CURVE.Gy); // base point coordinates
```

## Abstract API

Abstract API allows to define custom curves. All arithmetics is done with JS
bigints over finite fields, which is defined from `modular` sub-module. For
scalar multiplication, we use
[precomputed tables with w-ary non-adjacent form (wNAF)](https://paulmillr.com/posts/noble-secp256k1-fast-ecc/).
Precomputes are enabled for weierstrass and edwards BASE points of a curve. You
could precompute any other point (e.g. for ECDH) using `utils.precompute()`
method: check out examples.

### abstract/weierstrass: Short Weierstrass curve

```ts
import { weierstrass } from '@noble/curves/abstract/weierstrass';
import { Field } from '@noble/curves/abstract/modular'; // finite field for mod arithmetics
import { sha256 } from '@noble/hashes/sha256'; // 3rd-party sha256() of type utils.CHash
import { hmac } from '@noble/hashes/hmac'; // 3rd-party hmac() that will accept sha256()
import { concatBytes, randomBytes } from '@noble/hashes/utils'; // 3rd-party utilities
const secq256k1 = weierstrass({
  // secq256k1: cycle of secp256k1 with Fp/N flipped.
  // https://personaelabs.org/posts/spartan-ecdsa
  // https://zcash.github.io/halo2/background/curves.html#cycles-of-curves
  a: 0n,
  b: 7n,
  Fp: Field(2n ** 256n - 432420386565659656852420866394968145599n),
  n: 2n ** 256n - 2n ** 32n - 2n ** 9n - 2n ** 8n - 2n ** 7n - 2n ** 6n - 2n ** 4n - 1n,
  Gx: 55066263022277343669578718895168534326250603453777594175500187360389116729240n,
  Gy: 32670510020758816978083085130507043184471273380659243275938904335757337482424n,
  hash: sha256,
  hmac: (key: Uint8Array, ...msgs: Uint8Array[]) => hmac(sha256, key, concatBytes(...msgs)),
  randomBytes,
});

// Replace weierstrass() with weierstrassPoints() if you don't need ECDSA, hash, hmac, randomBytes
```

Short Weierstrass curve's formula is `y² = x³ + ax + b`. `weierstrass`
expects arguments `a`, `b`, field `Fp`, curve order `n`, cofactor `h`
and coordinates `Gx`, `Gy` of generator point.

**`k` generation** is done deterministically, following
[RFC6979](https://www.rfc-editor.org/rfc/rfc6979). For this you will need
`hmac` & `hash`, which in our implementations is provided by noble-hashes. If
you're using different hashing library, make sure to wrap it in the following interface:

```ts
type CHash = {
  (message: Uint8Array): Uint8Array;
  blockLen: number;
  outputLen: number;
  create(): any;
};
```

**Message hash** is expected instead of message itself:

- `sign(msgHash, privKey)` is default behavior, assuming you pre-hash msg with sha2, or other hash
- `sign(msg, privKey, {prehash: true})` option can be used if you want to pass the message itself

**Weierstrass points:**

1. Exported as `ProjectivePoint`
2. Represented in projective (homogeneous) coordinates: (x, y, z) ∋ (x=x/z, y=y/z)
3. Use complete exception-free formulas for addition and doubling
4. Can be decoded/encoded from/to Uint8Array / hex strings using
   `ProjectivePoint.fromHex` and `ProjectivePoint#toRawBytes()`
5. Have `assertValidity()` which checks for being on-curve
6. Have `toAffine()` and `x` / `y` getters which convert to 2d xy affine coordinates

```ts
// `weierstrassPoints()` returns `CURVE` and `ProjectivePoint`
// `weierstrass()` returns `CurveFn`
type SignOpts = { lowS?: boolean; prehash?: boolean; extraEntropy: boolean | Uint8Array };
type CurveFn = {
  CURVE: ReturnType<typeof validateOpts>;
  getPublicKey: (privateKey: PrivKey, isCompressed?: boolean) => Uint8Array;
  getSharedSecret: (privateA: PrivKey, publicB: Hex, isCompressed?: boolean) => Uint8Array;
  sign: (msgHash: Hex, privKey: PrivKey, opts?: SignOpts) => SignatureType;
  verify: (
    signature: Hex | SignatureType,
    msgHash: Hex,
    publicKey: Hex,
    opts?: { lowS?: boolean; prehash?: boolean }
  ) => boolean;
  ProjectivePoint: ProjectivePointConstructor;
  Signature: SignatureConstructor;
  utils: {
    normPrivateKeyToScalar: (key: PrivKey) => bigint;
    isValidPrivateKey(key: PrivKey): boolean;
    randomPrivateKey: () => Uint8Array;
    precompute: (windowSize?: number, point?: ProjPointType<bigint>) => ProjPointType<bigint>;
  };
};

// T is usually bigint, but can be something else like complex numbers in BLS curves
interface ProjPointType<T> extends Group<ProjPointType<T>> {
  readonly px: T;
  readonly py: T;
  readonly pz: T;
  get x(): bigint;
  get y(): bigint;
  multiply(scalar: bigint): ProjPointType<T>;
  multiplyUnsafe(scalar: bigint): ProjPointType<T>;
  multiplyAndAddUnsafe(Q: ProjPointType<T>, a: bigint, b: bigint): ProjPointType<T> | undefined;
  toAffine(iz?: T): AffinePoint<T>;
  isTorsionFree(): boolean;
  clearCofactor(): ProjPointType<T>;
  assertValidity(): void;
  hasEvenY(): boolean;
  toRawBytes(isCompressed?: boolean): Uint8Array;
  toHex(isCompressed?: boolean): string;
}
// Static methods for 3d XYZ points
interface ProjConstructor<T> extends GroupConstructor<ProjPointType<T>> {
  new (x: T, y: T, z: T): ProjPointType<T>;
  fromAffine(p: AffinePoint<T>): ProjPointType<T>;
  fromHex(hex: Hex): ProjPointType<T>;
  fromPrivateKey(privateKey: PrivKey): ProjPointType<T>;
}
```

**ECDSA signatures** are represented by `Signature` instances and can be
described by the interface:

```ts
interface SignatureType {
  readonly r: bigint;
  readonly s: bigint;
  readonly recovery?: number;
  assertValidity(): void;
  addRecoveryBit(recovery: number): SignatureType;
  hasHighS(): boolean;
  normalizeS(): SignatureType;
  recoverPublicKey(msgHash: Hex): ProjPointType<bigint>;
  toCompactRawBytes(): Uint8Array;
  toCompactHex(): string;
  // DER-encoded
  toDERRawBytes(): Uint8Array;
  toDERHex(): string;
}
type SignatureConstructor = {
  new (r: bigint, s: bigint): SignatureType;
  fromCompact(hex: Hex): SignatureType;
  fromDER(hex: Hex): SignatureType;
};
```

More examples:

```typescript
// All curves expose same generic interface.
const priv = secq256k1.utils.randomPrivateKey();
secq256k1.getPublicKey(priv); // Convert private key to public.
const sig = secq256k1.sign(msg, priv); // Sign msg with private key.
const sig2 = secq256k1.sign(msg, priv, { prehash: true }); // hash(msg)
secq256k1.verify(sig, msg, priv); // Verify if sig is correct.

const Point = secq256k1.ProjectivePoint;
const point = Point.BASE; // Elliptic curve Point class and BASE point static var.
point.add(point).equals(point.double()); // add(), equals(), double() methods
point.subtract(point).equals(Point.ZERO); // subtract() method, ZERO static var
point.negate(); // Flips point over x/y coordinate.
point.multiply(31415n); // Multiplication of Point by scalar.

point.assertValidity(); // Checks for being on-curve
point.toAffine(); // Converts to 2d affine xy coordinates

secq256k1.CURVE.n;
secq256k1.CURVE.p;
secq256k1.CURVE.Fp.mod();
secq256k1.CURVE.hash();

// precomputes
const fast = secq256k1.utils.precompute(8, Point.fromHex(someonesPubKey));
fast.multiply(privKey); // much faster ECDH now
```

### abstract/edwards: Twisted Edwards curve

```ts
import { twistedEdwards } from '@noble/curves/abstract/edwards';
import { Field } from '@noble/curves/abstract/modular';
import { sha512 } from '@noble/hashes/sha512';
import { randomBytes } from '@noble/hashes/utils';

const Fp = Field(2n ** 255n - 19n);
const ed25519 = twistedEdwards({
  a: Fp.create(-1n),
  d: Fp.div(-121665n, 121666n), // -121665n/121666n mod p
  Fp: Fp,
  n: 2n ** 252n + 27742317777372353535851937790883648493n,
  h: 8n,
  Gx: 15112221349535400772501151409588531511454012693041857206046113283949847762202n,
  Gy: 46316835694926478169428394003475163141307993866256225615783033603165251855960n,
  hash: sha512,
  randomBytes,
  adjustScalarBytes(bytes) {
    // optional; but mandatory in ed25519
    bytes[0] &= 248;
    bytes[31] &= 127;
    bytes[31] |= 64;
    return bytes;
  },
} as const);
```

Twisted Edwards curve's formula is `ax² + y² = 1 + dx²y²`. You must specify `a`, `d`, field `Fp`, order `n`, cofactor `h`
and coordinates `Gx`, `Gy` of generator point.

For EdDSA signatures, `hash` param required. `adjustScalarBytes` which instructs how to change private scalars could be specified.

**Edwards points:**

1. Exported as `ExtendedPoint`
2. Represented in extended coordinates: (x, y, z, t) ∋ (x=x/z, y=y/z)
3. Use complete exception-free formulas for addition and doubling
4. Can be decoded/encoded from/to Uint8Array / hex strings using `ExtendedPoint.fromHex` and `ExtendedPoint#toRawBytes()`
5. Have `assertValidity()` which checks for being on-curve
6. Have `toAffine()` and `x` / `y` getters which convert to 2d xy affine coordinates
7. Have `isTorsionFree()`, `clearCofactor()` and `isSmallOrder()` utilities to handle torsions

```ts
// `twistedEdwards()` returns `CurveFn` of following type:
type CurveFn = {
  CURVE: ReturnType<typeof validateOpts>;
  getPublicKey: (privateKey: Hex) => Uint8Array;
  sign: (message: Hex, privateKey: Hex, context?: Hex) => Uint8Array;
  verify: (sig: SigType, message: Hex, publicKey: Hex, context?: Hex) => boolean;
  ExtendedPoint: ExtPointConstructor;
  utils: {
    randomPrivateKey: () => Uint8Array;
    getExtendedPublicKey: (key: PrivKey) => {
      head: Uint8Array;
      prefix: Uint8Array;
      scalar: bigint;
      point: PointType;
      pointBytes: Uint8Array;
    };
  };
};

interface ExtPointType extends Group<ExtPointType> {
  readonly ex: bigint;
  readonly ey: bigint;
  readonly ez: bigint;
  readonly et: bigint;
  get x(): bigint;
  get y(): bigint;
  assertValidity(): void;
  multiply(scalar: bigint): ExtPointType;
  multiplyUnsafe(scalar: bigint): ExtPointType;
  isSmallOrder(): boolean;
  isTorsionFree(): boolean;
  clearCofactor(): ExtPointType;
  toAffine(iz?: bigint): AffinePoint<bigint>;
  toRawBytes(isCompressed?: boolean): Uint8Array;
  toHex(isCompressed?: boolean): string;
}
// Static methods of Extended Point with coordinates in X, Y, Z, T
interface ExtPointConstructor extends GroupConstructor<ExtPointType> {
  new (x: bigint, y: bigint, z: bigint, t: bigint): ExtPointType;
  fromAffine(p: AffinePoint<bigint>): ExtPointType;
  fromHex(hex: Hex): ExtPointType;
  fromPrivateKey(privateKey: Hex): ExtPointType;
}
```

### abstract/montgomery: Montgomery curve

```typescript
import { montgomery } from '@noble/curves/abstract/montgomery';
import { Field } from '@noble/curves/abstract/modular';

const x25519 = montgomery({
  a: 486662n,
  Gu: 9n,
  Fp: Field(2n ** 255n - 19n),
  montgomeryBits: 255,
  nByteLength: 32,
  // Optional param
  adjustScalarBytes(bytes) {
    bytes[0] &= 248;
    bytes[31] &= 127;
    bytes[31] |= 64;
    return bytes;
  },
});
```

The module contains methods for x-only ECDH on Curve25519 / Curve448 from RFC7748.
Proper Elliptic Curve Points are not implemented yet.

You must specify curve params `Fp`, `a`, `Gu` coordinate of u, `montgomeryBits` and `nByteLength`.

### abstract/bls: Barreto-Lynn-Scott curves

The module abstracts BLS (Barreto-Lynn-Scott) pairing-friendly elliptic curve construction.
They allow to construct [zk-SNARKs](https://z.cash/technology/zksnarks/) and
use aggregated, batch-verifiable
[threshold signatures](https://medium.com/snigirev.stepan/bls-signatures-better-than-schnorr-5a7fe30ea716),
using Boneh-Lynn-Shacham signature scheme.

The module doesn't expose `CURVE` property: use `G1.CURVE`, `G2.CURVE` instead.

Main methods and properties are:

- `getPublicKey(privateKey)`
- `sign(message, privateKey)`
- `verify(signature, message, publicKey)`
- `aggregatePublicKeys(publicKeys)`
- `aggregateSignatures(signatures)`
- `G1` and `G2` curves containing `CURVE` and `ProjectivePoint`
- `Signature` property with `fromHex`, `toHex` methods
- `fields` containing `Fp`, `Fp2`, `Fp6`, `Fp12`, `Fr`

Right now we only implement BLS12-381 (compatible with ETH and others),
but in theory defining BLS12-377, BLS24 should be straightforward. An example:

```ts
import { bls12_381 as bls } from '@noble/curves/bls12-381';
const privateKey = '67d53f170b908cabb9eb326c3c337762d59289a8fec79f7bc9254b584b73265c';
const message = '64726e3da8';
const publicKey = bls.getPublicKey(privateKey);
const signature = bls.sign(message, privateKey);
const isValid = bls.verify(signature, message, publicKey);
console.log({ publicKey, signature, isValid });

// Sign 1 msg with 3 keys
const privateKeys = [
  '18f020b98eb798752a50ed0563b079c125b0db5dd0b1060d1c1b47d4a193e1e4',
  'ed69a8c50cf8c9836be3b67c7eeff416612d45ba39a5c099d48fa668bf558c9c',
  '16ae669f3be7a2121e17d0c68c05a8f3d6bef21ec0f2315f1d7aec12484e4cf5',
];
const messages = ['d2', '0d98', '05caf3'];
const publicKeys = privateKeys.map(bls.getPublicKey);
const signatures2 = privateKeys.map((p) => bls.sign(message, p));
const aggPubKey2 = bls.aggregatePublicKeys(publicKeys);
const aggSignature2 = bls.aggregateSignatures(signatures2);
const isValid2 = bls.verify(aggSignature2, message, aggPubKey2);
console.log({ signatures2, aggSignature2, isValid2 });

// Sign 3 msgs with 3 keys
const signatures3 = privateKeys.map((p, i) => bls.sign(messages[i], p));
const aggSignature3 = bls.aggregateSignatures(signatures3);
const isValid3 = bls.verifyBatch(aggSignature3, messages, publicKeys);
console.log({ publicKeys, signatures3, aggSignature3, isValid3 });

// Pairings, with and without final exponentiation
// bls.pairing(PointG1, PointG2);
// bls.pairing(PointG1, PointG2, false);
// bls.fields.Fp12.finalExponentiate(bls.fields.Fp12.mul(eGS, ePHm));

// Others
// bls.G1.ProjectivePoint.BASE, bls.G2.ProjectivePoint.BASE
// bls.fields.Fp, bls.fields.Fp2, bls.fields.Fp12, bls.fields.Fr

// hash-to-curve examples can be seen below
```

Full types:

```ts
getPublicKey: (privateKey: PrivKey) => Uint8Array;
sign: {
  (message: Hex, privateKey: PrivKey): Uint8Array;
  (message: ProjPointType<Fp2>, privateKey: PrivKey): ProjPointType<Fp2>;
};
verify: (
  signature: Hex | ProjPointType<Fp2>,
  message: Hex | ProjPointType<Fp2>,
  publicKey: Hex | ProjPointType<Fp>
) => boolean;
verifyBatch: (
  signature: Hex | ProjPointType<Fp2>,
  messages: (Hex | ProjPointType<Fp2>)[],
  publicKeys: (Hex | ProjPointType<Fp>)[]
) => boolean;
aggregatePublicKeys: {
  (publicKeys: Hex[]): Uint8Array;
  (publicKeys: ProjPointType<Fp>[]): ProjPointType<Fp>;
};
aggregateSignatures: {
  (signatures: Hex[]): Uint8Array;
  (signatures: ProjPointType<Fp2>[]): ProjPointType<Fp2>;
};
millerLoop: (ell: [Fp2, Fp2, Fp2][], g1: [Fp, Fp]) => Fp12;
pairing: (P: ProjPointType<Fp>, Q: ProjPointType<Fp2>, withFinalExponent?: boolean) => Fp12;
G1: CurvePointsRes<Fp> & ReturnType<typeof htf.createHasher<Fp>>;
G2: CurvePointsRes<Fp2> & ReturnType<typeof htf.createHasher<Fp2>>;
Signature: SignatureCoder<Fp2>;
params: {
  x: bigint;
  r: bigint;
  G1b: bigint;
  G2b: Fp2;
};
fields: {
  Fp: IField<Fp>;
  Fp2: IField<Fp2>;
  Fp6: IField<Fp6>;
  Fp12: IField<Fp12>;
  Fr: IField<bigint>;
};
utils: {
  randomPrivateKey: () => Uint8Array;
  calcPairingPrecomputes: (p: AffinePoint<Fp2>) => [Fp2, Fp2, Fp2][];
};
```

### abstract/hash-to-curve: Hashing strings to curve points

The module allows to hash arbitrary strings to elliptic curve points. Implements [RFC 9380](https://www.rfc-editor.org/rfc/rfc9380).

Every curve has exported `hashToCurve` and `encodeToCurve` methods. You should always prefer `hashToCurve` for security:

```ts
import { hashToCurve, encodeToCurve } from '@noble/curves/secp256k1';
import { randomBytes } from '@noble/hashes/utils';
hashToCurve('0102abcd');
console.log(hashToCurve(randomBytes()));
console.log(encodeToCurve(randomBytes()));

import { bls12_381 } from '@noble/curves/bls12-381';
bls12_381.G1.hashToCurve(randomBytes(), { DST: 'another' });
bls12_381.G2.hashToCurve(randomBytes(), { DST: 'custom' });
```

Low-level methods from the spec:

```ts
// produces a uniformly random byte string using a cryptographic hash function H that outputs b bits.
function expand_message_xmd(
  msg: Uint8Array,
  DST: Uint8Array,
  lenInBytes: number,
  H: CHash // For CHash see abstract/weierstrass docs section
): Uint8Array;
// produces a uniformly random byte string using an extendable-output function (XOF) H.
function expand_message_xof(
  msg: Uint8Array,
  DST: Uint8Array,
  lenInBytes: number,
  k: number,
  H: CHash
): Uint8Array;
// Hashes arbitrary-length byte strings to a list of one or more elements of a finite field F
function hash_to_field(msg: Uint8Array, count: number, options: Opts): bigint[][];

/**
 * * `DST` is a domain separation tag, defined in section 2.2.5
 * * `p` characteristic of F, where F is a finite field of characteristic p and order q = p^m
 * * `m` is extension degree (1 for prime fields)
 * * `k` is the target security target in bits (e.g. 128), from section 5.1
 * * `expand` is `xmd` (SHA2, SHA3, BLAKE) or `xof` (SHAKE, BLAKE-XOF)
 * * `hash` conforming to `utils.CHash` interface, with `outputLen` / `blockLen` props
 */
type UnicodeOrBytes = string | Uint8Array;
type Opts = {
  DST: UnicodeOrBytes;
  p: bigint;
  m: number;
  k: number;
  expand?: 'xmd' | 'xof';
  hash: CHash;
};
```

### abstract/poseidon: Poseidon hash

Implements [Poseidon](https://www.poseidon-hash.info) ZK-friendly hash.

There are many poseidon variants with different constants.
We don't provide them: you should construct them manually.
Check out [micro-starknet](https://github.com/paulmillr/micro-starknet) package for a proper example.

```ts
import { poseidon } from '@noble/curves/abstract/poseidon';

type PoseidonOpts = {
  Fp: Field<bigint>;
  t: number;
  roundsFull: number;
  roundsPartial: number;
  sboxPower?: number;
  reversePartialPowIdx?: boolean;
  mds: bigint[][];
  roundConstants: bigint[][];
};
const instance = poseidon(opts: PoseidonOpts);
```

### abstract/modular: Modular arithmetics utilities

```ts
import * as mod from '@noble/curves/abstract/modular';
const fp = mod.Field(2n ** 255n - 19n); // Finite field over 2^255-19
fp.mul(591n, 932n); // multiplication
fp.pow(481n, 11024858120n); // exponentiation
fp.div(5n, 17n); // division: 5/17 mod 2^255-19 == 5 * invert(17)
fp.sqrt(21n); // square root

// Generic non-FP utils are also available
mod.mod(21n, 10n); // 21 mod 10 == 1n; fixed version of 21 % 10
mod.invert(17n, 10n); // invert(17) mod 10; modular multiplicative inverse
mod.invertBatch([1n, 2n, 4n], 21n); // => [1n, 11n, 16n] in one inversion
```

Field operations are not constant-time: they are using JS bigints, see [security](#security).
The fact is mostly irrelevant, but the important method to keep in mind is `pow`,
which may leak exponent bits, when used naïvely.

`mod.Field` is always **field over prime**. Non-prime fields aren't supported for now.
We don't test for prime-ness for speed and because algorithms are probabilistic anyway.
Initializing a non-prime field could make your app suspectible to
DoS (infilite loop) on Tonelli-Shanks square root calculation.

Unlike `mod.invert`, `mod.invertBatch` won't throw on `0`: make sure to throw an error yourself.

#### Creating private keys from hashes

You can't simply make a 32-byte private key from a 32-byte hash.
Doing so will make the key [biased](https://research.kudelskisecurity.com/2020/07/28/the-definitive-guide-to-modulo-bias-and-how-to-avoid-it/).

To make the bias negligible, we follow [FIPS 186-5 A.2](https://csrc.nist.gov/publications/detail/fips/186/5/final)
and [RFC 9380](https://www.rfc-editor.org/rfc/rfc9380#section-5.2).
This means, for 32-byte key, we would need 48-byte hash to get 2^-128 bias, which matches curve security level.

`hashToPrivateScalar()` that hashes to **private key** was created for this purpose.
Use [abstract/hash-to-curve](#abstracthash-to-curve-hashing-strings-to-curve-points)
if you need to hash to **public key**.

```ts
import { p256 } from '@noble/curves/p256';
import { sha256 } from '@noble/hashes/sha256';
import { hkdf } from '@noble/hashes/hkdf';
const someKey = new Uint8Array(32).fill(2); // Needs to actually be random, not .fill(2)
const derived = hkdf(sha256, someKey, undefined, 'application', 48); // 48 bytes for 32-byte priv
const validPrivateKey = mod.hashToPrivateScalar(derived, p256.CURVE.n);
```

### abstract/utils: Useful utilities

```ts
import * as utils from '@noble/curves/abstract/utils';

utils.bytesToHex(Uint8Array.from([0xde, 0xad, 0xbe, 0xef]));
utils.hexToBytes('deadbeef');
utils.numberToHexUnpadded(123n);
utils.hexToNumber();

utils.bytesToNumberBE(Uint8Array.from([0xde, 0xad, 0xbe, 0xef]));
utils.bytesToNumberLE(Uint8Array.from([0xde, 0xad, 0xbe, 0xef]));
utils.numberToBytesBE(123n, 32);
utils.numberToBytesLE(123n, 64);

utils.concatBytes(Uint8Array.from([0xde, 0xad]), Uint8Array.from([0xbe, 0xef]));
utils.nLength(255n);
utils.equalBytes(Uint8Array.from([0xde]), Uint8Array.from([0xde]));
```

## Security

1. The library has been independently audited:

- in Feb 2023 by [Trail of Bits](https://www.trailofbits.com):
  [PDF](https://github.com/trailofbits/publications/blob/master/reviews/2023-01-ryanshea-noblecurveslibrary-securityreview.pdf).
  The audit has been funded by [Ryan Shea](https://www.shea.io).
  Audit scope was abstract modules `curve`, `hash-to-curve`, `modular`, `poseidon`, `utils`, `weierstrass`,
  and top-level modules `_shortw_utils` and `secp256k1`.
  See [changes since v0.7.3 audit](https://github.com/paulmillr/noble-curves/compare/0.7.3..main).

2. The library has been fuzzed by [Guido Vranken's cryptofuzz](https://github.com/guidovranken/cryptofuzz).
   You can run the fuzzer by yourself to check it.
3. [Timing attack](https://en.wikipedia.org/wiki/Timing_attack) considerations:
   _JIT-compiler_ and _Garbage Collector_ make "constant time" extremely hard to
   achieve in a scripting language. Which means _any other JS library can't have
   constant-timeness_. Even statically typed Rust, a language without GC,
   [makes it harder to achieve constant-time](https://www.chosenplaintext.ca/open-source/rust-timing-shield/security)
   for some cases. If your goal is absolute security, don't use any JS lib — including bindings to native ones.
   Use low-level libraries & languages. Nonetheless we're targetting algorithmic constant time.

We consider infrastructure attacks like rogue NPM modules very important;
that's why it's crucial to minimize the amount of 3rd-party dependencies & native bindings.
If your app uses 500 dependencies, any dep could get hacked and you'll be
downloading malware with every `npm install`. Our goal is to minimize this attack vector.
As for devDependencies used by the library:

- `@scure` base, bip32, bip39 (used in tests), micro-bmark (benchmark), micro-should (testing)
  are developed by us and follow the same practices such as: minimal library size, auditability,
  signed releases
- prettier (linter), fast-check (property-based testing), typescript versions
  are locked and rarely updated. Every update is checked with `npm-diff`.
  The packages are big, which makes it hard to audit their source code thoroughly and fully.
- They are only used if you clone the git repo and want to add some feature to it. End-users won't use them.

As for key generation, we're deferring to built-in
[crypto.getRandomValues](https://developer.mozilla.org/en-US/docs/Web/API/Crypto/getRandomValues)
which is considered cryptographically secure (CSPRNG).

## Speed

Benchmark results on Apple M2 with node v20:

```
secp256k1
init x 68 ops/sec @ 14ms/op
getPublicKey x 6,750 ops/sec @ 148μs/op
sign x 5,206 ops/sec @ 192μs/op
verify x 880 ops/sec @ 1ms/op
getSharedSecret x 536 ops/sec @ 1ms/op
recoverPublicKey x 852 ops/sec @ 1ms/op
schnorr.sign x 685 ops/sec @ 1ms/op
schnorr.verify x 908 ops/sec @ 1ms/op

p256
init x 38 ops/sec @ 26ms/op
getPublicKey x 6,530 ops/sec @ 153μs/op
sign x 5,074 ops/sec @ 197μs/op
verify x 626 ops/sec @ 1ms/op

p384
init x 17 ops/sec @ 57ms/op
getPublicKey x 2,883 ops/sec @ 346μs/op
sign x 2,358 ops/sec @ 424μs/op
verify x 245 ops/sec @ 4ms/op

p521
init x 9 ops/sec @ 109ms/op
getPublicKey x 1,516 ops/sec @ 659μs/op
sign x 1,271 ops/sec @ 786μs/op
verify x 123 ops/sec @ 8ms/op

ed25519
init x 54 ops/sec @ 18ms/op
getPublicKey x 10,269 ops/sec @ 97μs/op
sign x 5,110 ops/sec @ 195μs/op
verify x 1,049 ops/sec @ 952μs/op

ed448
init x 19 ops/sec @ 51ms/op
getPublicKey x 3,775 ops/sec @ 264μs/op
sign x 1,771 ops/sec @ 564μs/op
verify x 351 ops/sec @ 2ms/op

ecdh
├─x25519 x 1,466 ops/sec @ 682μs/op
├─secp256k1 x 539 ops/sec @ 1ms/op
├─p256 x 511 ops/sec @ 1ms/op
├─p384 x 199 ops/sec @ 5ms/op
├─p521 x 103 ops/sec @ 9ms/op
└─x448 x 548 ops/sec @ 1ms/op

bls12-381
init x 36 ops/sec @ 27ms/op
getPublicKey 1-bit x 973 ops/sec @ 1ms/op
getPublicKey x 970 ops/sec @ 1ms/op
sign x 55 ops/sec @ 17ms/op
verify x 39 ops/sec @ 25ms/op
pairing x 106 ops/sec @ 9ms/op
aggregatePublicKeys/8 x 129 ops/sec @ 7ms/op
aggregatePublicKeys/32 x 34 ops/sec @ 28ms/op
aggregatePublicKeys/128 x 8 ops/sec @ 112ms/op
aggregatePublicKeys/512 x 2 ops/sec @ 446ms/op
aggregatePublicKeys/2048 x 0 ops/sec @ 1778ms/op
aggregateSignatures/8 x 50 ops/sec @ 19ms/op
aggregateSignatures/32 x 13 ops/sec @ 74ms/op
aggregateSignatures/128 x 3 ops/sec @ 296ms/op
aggregateSignatures/512 x 0 ops/sec @ 1180ms/op
aggregateSignatures/2048 x 0 ops/sec @ 4715ms/op

hash-to-curve
hash_to_field x 91,600 ops/sec @ 10μs/op
secp256k1 x 2,373 ops/sec @ 421μs/op
p256 x 4,310 ops/sec @ 231μs/op
p384 x 1,664 ops/sec @ 600μs/op
p521 x 807 ops/sec @ 1ms/op
ed25519 x 3,088 ops/sec @ 323μs/op
ed448 x 1,247 ops/sec @ 801μs/op
```

## Contributing & testing

1. Clone the repository
2. `npm install` to install build dependencies like TypeScript
3. `npm run build` to compile TypeScript code
4. `npm run test` will execute all main tests

## Upgrading

Previously, the library was split into single-feature packages
[noble-secp256k1](https://github.com/paulmillr/noble-secp256k1),
[noble-ed25519](https://github.com/paulmillr/noble-ed25519) and
[noble-bls12-381](https://github.com/paulmillr/noble-bls12-381).

Curves continue their original work. The single-feature packages changed their
direction towards providing minimal 4kb implementations of cryptography,
which means they have less features.

Upgrading from noble-secp256k1 2.0 or noble-ed25519 2.0: no changes, libraries are compatible.

Upgrading from noble-secp256k1 1.7:

- `getPublicKey`
  - now produce 33-byte compressed signatures by default
  - to use old behavior, which produced 65-byte uncompressed keys, set
    argument `isCompressed` to `false`: `getPublicKey(priv, false)`
- `sign`
  - is now sync; use `signAsync` for async version
  - now returns `Signature` instance with `{ r, s, recovery }` properties
  - `canonical` option was renamed to `lowS`
  - `recovered` option has been removed because recovery bit is always returned now
  - `der` option has been removed. There are 2 options:
    1. Use compact encoding: `fromCompact`, `toCompactRawBytes`, `toCompactHex`.
       Compact encoding is simply a concatenation of 32-byte r and 32-byte s.
    2. If you must use DER encoding, switch to noble-curves (see above).
- `verify`
  - `strict` option was renamed to `lowS`
- `getSharedSecret`
  - now produce 33-byte compressed signatures by default
  - to use old behavior, which produced 65-byte uncompressed keys, set
    argument `isCompressed` to `false`: `getSharedSecret(a, b, false)`
- `recoverPublicKey(msg, sig, rec)` was changed to `sig.recoverPublicKey(msg)`
- `number` type for private keys have been removed: use `bigint` instead
- `Point` (2d xy) has been changed to `ProjectivePoint` (3d xyz)
- `utils` were split into `utils` (same api as in noble-curves) and
  `etc` (`hmacSha256Sync` and others)

Upgrading from [@noble/ed25519](https://github.com/paulmillr/noble-ed25519) 1.7:

- Methods are now sync by default
- `bigint` is no longer allowed in `getPublicKey`, `sign`, `verify`. Reason: ed25519 is LE, can lead to bugs
- `Point` (2d xy) has been changed to `ExtendedPoint` (xyzt)
- `Signature` was removed: just use raw bytes or hex now
- `utils` were split into `utils` (same api as in noble-curves) and
  `etc` (`sha512Sync` and others)
- `getSharedSecret` was moved to `x25519` module
- `toX25519` has been moved to `edwardsToMontgomeryPub` and `edwardsToMontgomeryPriv` methods

Upgrading from [@noble/bls12-381](https://github.com/paulmillr/noble-bls12-381):

- Methods and classes were renamed:
  - PointG1 -> G1.Point, PointG2 -> G2.Point
  - PointG2.fromSignature -> Signature.decode, PointG2.toSignature -> Signature.encode
- Fp2 ORDER was corrected

## Resources

- [Learning fast elliptic-curve cryptography](https://paulmillr.com/posts/noble-secp256k1-fast-ecc/)
- EdDSA
  - [A Deep dive into Ed25519 Signatures](https://cendyne.dev/posts/2022-03-06-ed25519-signatures.html)
  - [Ed25519 Deep Dive Addendum](https://cendyne.dev/posts/2022-09-11-ed25519-deep-dive-addendum.html)
  - [It’s 255:19AM. Do you know what your validation criteria are?](https://hdevalence.ca/blog/2020-10-04-its-25519am)
  - [Taming the many EdDSAs](https://csrc.nist.gov/csrc/media/Presentations/2023/crclub-2023-03-08/images-media/20230308-crypto-club-slides--taming-the-many-EdDSAs.pdf)
    that describes concepts of Strong UnForgeability under Chosen Message Attacks and Strongly Binding Signatures
  - [Cofactor Explained: Clearing Elliptic Curves’ dirty little secret](https://loup-vaillant.fr/tutorials/cofactor)
  - [Surrounded by Elligators](https://loup-vaillant.fr/articles/implementing-elligator)
- Pairings and BLS
  - [BLS signatures for busy people](https://gist.github.com/paulmillr/18b802ad219b1aee34d773d08ec26ca2)
  - [BLS12-381 for the rest of us](https://hackmd.io/@benjaminion/bls12-381)
  - [Key concepts of pairings](https://medium.com/@alonmuroch_65570/bls-signatures-part-2-key-concepts-of-pairings-27a8a9533d0c)
  - Pairing over bls12-381:
    [fields](https://research.nccgroup.com/2020/07/06/pairing-over-bls12-381-part-1-fields/),
    [curves](https://research.nccgroup.com/2020/07/13/pairing-over-bls12-381-part-2-curves/),
    [pairings](https://research.nccgroup.com/2020/08/13/pairing-over-bls12-381-part-3-pairing/)
  - [Estimating the bit security of pairing-friendly curves](https://research.nccgroup.com/2022/02/03/estimating-the-bit-security-of-pairing-friendly-curves/)

### Demos

- [Elliptic Curve Calculator](https://paulmillr.com/noble): add / multiply points, sign messages
- [BLS threshold signatures](https://genthresh.com)

### Projects using curves

- HDkey libraries: [scure-bip32](https://github.com/paulmillr/scure-bip32), [bip32](https://github.com/bitcoinjs/bip32)
- Social networks: [nostr](https://github.com/nbd-wtf/nostr-tools), [bluesky](https://github.com/bluesky-social/atproto)
- Ethereum libraries:
  - [ethereum-cryptography](https://github.com/ethereum/js-ethereum-cryptography)
  - [micro-eth-signer](https://github.com/paulmillr/micro-eth-signer),
    [ethers](https://github.com/ethers-io/ethers.js) (old noble),
    [viem.sh](https://viem.sh),
    [@ethereumjs](https://github.com/ethereumjs/ethereumjs-monorepo)
  - [metamask's eth-sig-util](https://github.com/MetaMask/eth-sig-util)
  - [gridplus lattice sdk](https://github.com/GridPlus/lattice-eth2-utils)
- Bitcoin libraries:
  - [scure-btc-signer](https://github.com/paulmillr/scure-btc-signer)
  - [tapscript](https://github.com/cmdruid/tapscript)
- Solana libraries: [micro-sol-signer](https://github.com/paulmillr/micro-sol-signer), [solana-web3.js](https://github.com/solana-labs/solana-web3.js)
- Other web3 stuff:
  - [scure-starknet](https://github.com/paulmillr/scure-starknet)
  - [aztec](https://github.com/AztecProtocol/aztec-packages)
  - [polkadot.js](https://github.com/polkadot-js/common), [drand-client](https://github.com/drand/drand-client), [moneroj](https://github.com/beritani/moneroj), [tronlib](https://github.com/CoinSpace/tronlib)
- [protonmail](https://github.com/ProtonMail/WebClients) (old noble for now)
- [did-jwt](https://github.com/decentralized-identity/did-jwt), [hpke-js](https://github.com/dajiaji/hpke-js),
  [js-libp2p-noise](https://github.com/ChainSafe/js-libp2p-noise)
- [ed25519-keygen](https://github.com/paulmillr/ed25519-keygen) SSH, PGP, TOR key generation
- [secp256k1 compatibility layer](https://github.com/ethereum/js-ethereum-cryptography/blob/2.0.0/src/secp256k1-compat.ts)
  for users who want to switch from secp256k1-node or tiny-secp256k1. Allows to see which methods map to corresponding noble code.
- [BLS BBS signatures](https://github.com/Wind4Greg/BBS-Draft-Checks) following [draft-irtf-cfrg-bbs-signatures-latest](https://identity.foundation/bbs-signature/draft-irtf-cfrg-bbs-signatures.html)
- [KZG trusted setup ceremony](https://github.com/dsrvlabs/czg-keremony)
- See [full list of projects on GitHub](https://github.com/paulmillr/noble-curves/network/dependents).

## License

The MIT License (MIT)

Copyright (c) 2022 Paul Miller [(https://paulmillr.com)](https://paulmillr.com)

See LICENSE file.
