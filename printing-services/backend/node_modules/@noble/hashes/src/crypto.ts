// We use WebCrypto aka globalThis.crypto, which exists in browsers and node.js 16+.
// See utils.ts for details.
declare const globalThis: Record<string, any> | undefined;
export const crypto =
  typeof globalThis === 'object' && 'crypto' in globalThis ? globalThis.crypto : undefined;
