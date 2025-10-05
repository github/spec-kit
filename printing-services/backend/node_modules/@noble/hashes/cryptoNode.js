"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.crypto = void 0;
// We use WebCrypto aka globalThis.crypto, which exists in browsers and node.js 16+.
// See utils.ts for details.
// The file will throw on node.js 14 and earlier.
// @ts-ignore
const nc = require("node:crypto");
exports.crypto = nc && typeof nc === 'object' && 'webcrypto' in nc ? nc.webcrypto : undefined;
//# sourceMappingURL=cryptoNode.js.map