"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const assert_1 = __importDefault(require("assert"));
const fs_1 = __importDefault(require("fs"));
const path_1 = require("path");
const aes = __importStar(require("./index.js"));
const root = (function () {
    let root = process.cwd();
    while (true) {
        if (fs_1.default.existsSync((0, path_1.join)(root, "package.json"))) {
            return root;
        }
        const parent = (0, path_1.join)(root, "..");
        if (parent === root) {
            break;
        }
        root = parent;
    }
    throw new Error("could not find root");
})();
describe("Tests Encrypting and Decrypting", function () {
    const json = fs_1.default.readFileSync((0, path_1.resolve)(root, "./test/test-vectors.json")).toString();
    const tests = JSON.parse(json);
    function getCrypter(key, test) {
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
        it(`tests encrypting: ${test.modeOfOperation}.${index}`, function () {
            const encrypter = getCrypter(Buffer.from(test.key), test);
            if (!encrypter) {
                this.skip();
            }
            for (let i = 0; i < test.plaintext.length; i++) {
                const plaintext = Buffer.from(test.plaintext[i]);
                const ciphertext = Buffer.from(test.encrypted[i]);
                const result = Buffer.from(encrypter.encrypt(plaintext));
                assert_1.default.ok(ciphertext.equals(result), "encrypting failed");
            }
        });
        it(`tests decrypting: ${test.modeOfOperation}.${index}`, function () {
            const decrypter = getCrypter(Buffer.from(test.key), test);
            if (!decrypter) {
                this.skip();
            }
            for (let i = 0; i < test.plaintext.length; i++) {
                const plaintext = Buffer.from(test.plaintext[i]);
                const ciphertext = Buffer.from(test.encrypted[i]);
                const result = Buffer.from(decrypter.decrypt(ciphertext));
                assert_1.default.ok(plaintext.equals(result), "decrypting failed");
            }
        });
    });
});
describe("Tests Padding", function () {
    for (let size = 0; size < 100; size++) {
        it(`tests padding: length=${size}`, function () {
            // Create a random piece of data
            const data = new Uint8Array(size);
            data.fill(42);
            // Pad it
            const padded = aes.pkcs7Pad(data);
            assert_1.default.ok((padded.length % 16) === 0, "Failed to pad to block size");
            assert_1.default.ok(data.length <= padded.length && padded.length <= data.length + 16, "Padding went awry");
            assert_1.default.ok(padded[padded.length - 1] >= 1 && padded[padded.length - 1] <= 16, "Failed to pad to block size");
            // Trim it
            const trimmed = aes.pkcs7Strip(padded);
            assert_1.default.ok(Buffer.from(data).equals(trimmed), "Failed to trim to original data");
        });
    }
});
//# sourceMappingURL=tests.js.map