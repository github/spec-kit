import assertString from './util/assertString';
var bech32 = /^(bc1)[a-z0-9]{25,39}$/;
var base58 = /^(1|3)[A-HJ-NP-Za-km-z1-9]{25,39}$/;
export default function isBtcAddress(str) {
  assertString(str);
  return bech32.test(str) || base58.test(str);
}