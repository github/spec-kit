
export function pkcs7Pad(data: Uint8Array): Uint8Array {
    const padder = 16 - (data.length % 16);

    const result = new Uint8Array(data.length + padder);
    result.set(data);

    for (let i = data.length; i < result.length; i++) {
        result[i] = padder;
    }

    return result;
}

export function pkcs7Strip(data: Uint8Array): Uint8Array {
    if (data.length < 16) { throw new TypeError('PKCS#7 invalid length'); }

    const padder = data[data.length - 1];
    if (padder > 16) { throw new TypeError('PKCS#7 padding byte out of range'); }

    const length = data.length - padder;
    for (let i = 0; i < padder; i++) {
        if (data[length + i] !== padder) {
            throw new TypeError('PKCS#7 invalid padding byte');
        }
    }

    return new Uint8Array(data.subarray(0, length));
}
