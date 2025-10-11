import { hash as assertHash, bytes as assertBytes, exists as assertExists } from './_assert.js';
import { Hash, CHash, Input, toBytes } from './utils.js';
// HMAC (RFC 2104)
export class HMAC<T extends Hash<T>> extends Hash<HMAC<T>> {
  oHash: T;
  iHash: T;
  blockLen: number;
  outputLen: number;
  private finished = false;
  private destroyed = false;

  constructor(hash: CHash, _key: Input) {
    super();
    assertHash(hash);
    const key = toBytes(_key);
    this.iHash = hash.create() as T;
    if (typeof this.iHash.update !== 'function')
      throw new Error('Expected instance of class which extends utils.Hash');
    this.blockLen = this.iHash.blockLen;
    this.outputLen = this.iHash.outputLen;
    const blockLen = this.blockLen;
    const pad = new Uint8Array(blockLen);
    // blockLen can be bigger than outputLen
    pad.set(key.length > blockLen ? hash.create().update(key).digest() : key);
    for (let i = 0; i < pad.length; i++) pad[i] ^= 0x36;
    this.iHash.update(pad);
    // By doing update (processing of first block) of outer hash here we can re-use it between multiple calls via clone
    this.oHash = hash.create() as T;
    // Undo internal XOR && apply outer XOR
    for (let i = 0; i < pad.length; i++) pad[i] ^= 0x36 ^ 0x5c;
    this.oHash.update(pad);
    pad.fill(0);
  }
  update(buf: Input) {
    assertExists(this);
    this.iHash.update(buf);
    return this;
  }
  digestInto(out: Uint8Array) {
    assertExists(this);
    assertBytes(out, this.outputLen);
    this.finished = true;
    this.iHash.digestInto(out);
    this.oHash.update(out);
    this.oHash.digestInto(out);
    this.destroy();
  }
  digest() {
    const out = new Uint8Array(this.oHash.outputLen);
    this.digestInto(out);
    return out;
  }
  _cloneInto(to?: HMAC<T>): HMAC<T> {
    // Create new instance without calling constructor since key already in state and we don't know it.
    to ||= Object.create(Object.getPrototypeOf(this), {});
    const { oHash, iHash, finished, destroyed, blockLen, outputLen } = this;
    to = to as this;
    to.finished = finished;
    to.destroyed = destroyed;
    to.blockLen = blockLen;
    to.outputLen = outputLen;
    to.oHash = oHash._cloneInto(to.oHash);
    to.iHash = iHash._cloneInto(to.iHash);
    return to;
  }
  destroy() {
    this.destroyed = true;
    this.oHash.destroy();
    this.iHash.destroy();
  }
}

/**
 * HMAC: RFC2104 message authentication code.
 * @param hash - function that would be used e.g. sha256
 * @param key - message key
 * @param message - message data
 */
export const hmac = (hash: CHash, key: Input, message: Input): Uint8Array =>
  new HMAC<any>(hash, key).update(message).digest();
hmac.create = (hash: CHash, key: Input) => new HMAC<any>(hash, key);
