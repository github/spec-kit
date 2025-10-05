const Base64 = ")!@#$%^&*(ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_";

/**
 *  @_ignore
 */
export function decodeBits(width: number, data: string): Array<number> {
    const maxValue = (1 << width) - 1;
    const result: Array<number> = [ ];
    let accum = 0, bits = 0, flood = 0;
    for (let i = 0; i < data.length; i++) {

        // Accumulate 6 bits of data
        accum = ((accum << 6) | Base64.indexOf(data[i]));
        bits += 6;

        // While we have enough for a word...
        while (bits >= width) {
            // ...read the word
            const value = (accum >> (bits - width));
            accum &= (1 << (bits - width)) - 1;
            bits -= width;

            // A value of 0 indicates we exceeded maxValue, it
            // floods over into the next value
            if (value === 0) {
                flood += maxValue;
            } else {
                result.push(value + flood);
                flood = 0;
            }
        }
    }

    return result;
}
