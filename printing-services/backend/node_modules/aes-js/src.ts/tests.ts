import assert from "assert"
import fs from "fs";
import { join, resolve } from "path";

import * as aes from "./index.js";

interface TestCase {
  modeOfOperation: string;

  iv: Array<number>;
  key: Array<number>;

  plaintext: Array<Array<number>>;
  encrypted: Array<Array<number>>;

  segmentSize: number;
}

const root = (function() {
  let root = process.cwd();

  while (true) {
    if (fs.existsSync(join(root, "package.json"))) { return root; }
    const parent = join(root, "..");
    if (parent === root) { break; }
    root = parent;
  }

  throw new Error("could not find root");
})();

describe("Tests Encrypting and Decrypting", function() {
  const json = fs.readFileSync(resolve(root, "./test/test-vectors.json")).toString()
  const tests: Array<TestCase> = JSON.parse(json);

  function getCrypter(key: Uint8Array, test: TestCase): null | aes.ModeOfOperation {
    switch (test.modeOfOperation) {
      case "ctr":
        return new aes.CTR(key, 0);
      case "cbc":
        return new aes.CBC(key, Buffer.from(test.iv));
      case "cfb":
        return new aes.CFB(key, Buffer.from(test.iv), test.segmentSize * 8);
      case "ecb":
        return new aes.ECB(key);
      case "ofb":
        return new aes.OFB(key, Buffer.from(test.iv));
    }

    return null;
  }

  tests.forEach((test, index) => {

    it(`tests encrypting: ${ test. modeOfOperation}.${ index }`, function() {
      const encrypter = getCrypter(Buffer.from(test.key), test);
      if (!encrypter) { this.skip(); }

      for (let i = 0; i < test.plaintext.length; i++) {
        const plaintext = Buffer.from(test.plaintext[i]);
        const ciphertext = Buffer.from(test.encrypted[i]);

        const result = Buffer.from(encrypter.encrypt(plaintext));
        assert.ok(ciphertext.equals(result), "encrypting failed");
      }
    });

    it(`tests decrypting: ${ test. modeOfOperation}.${ index }`, function() {
      const decrypter = getCrypter(Buffer.from(test.key), test);
      if (!decrypter) { this.skip(); }

      for (let i = 0; i < test.plaintext.length; i++) {
        const plaintext = Buffer.from(test.plaintext[i]);
        const ciphertext = Buffer.from(test.encrypted[i]);

        const result = Buffer.from(decrypter.decrypt(ciphertext));
        assert.ok(plaintext.equals(result), "decrypting failed");
      }
    });
  });
});

describe("Tests Padding", function() {
  for (let size = 0; size < 100; size++) {
    it(`tests padding: length=${ size }`, function() {

      // Create a random piece of data
      const data = new Uint8Array(size);
      data.fill(42);

      // Pad it
      const padded = aes.pkcs7Pad(data);
      assert.ok((padded.length % 16) === 0, "Failed to pad to block size");
      assert.ok(data.length <= padded.length && padded.length <= data.length + 16, "Padding went awry");
      assert.ok(padded[padded.length - 1] >= 1 && padded[padded.length - 1] <= 16, "Failed to pad to block size");

      // Trim it
      const trimmed = aes.pkcs7Strip(padded);
      assert.ok(Buffer.from(data).equals(trimmed), "Failed to trim to original data");
    });
  }
});
