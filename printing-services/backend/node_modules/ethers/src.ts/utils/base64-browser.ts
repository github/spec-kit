
// utils/base64-browser

import { getBytes } from "./data.js";

import type { BytesLike } from "./data.js";


export function decodeBase64(textData: string): Uint8Array {
    textData = atob(textData);
    const data = new Uint8Array(textData.length);
    for (let i = 0; i < textData.length; i++) {
        data[i] = textData.charCodeAt(i);
    }
    return getBytes(data);
}

export function encodeBase64(_data: BytesLike): string {
    const data = getBytes(_data);
    let textData = "";
    for (let i = 0; i < data.length; i++) {
        textData += String.fromCharCode(data[i]);
    }
    return btoa(textData);
}
