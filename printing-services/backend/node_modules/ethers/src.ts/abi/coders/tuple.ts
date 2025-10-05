import { defineProperties } from "../../utils/properties.js";

import { Typed } from "../typed.js";
import { Coder } from "./abstract-coder.js";

import { pack, unpack } from "./array.js";

import type { Reader, Writer } from "./abstract-coder.js";

/**
 *  @_ignore
 */
export class TupleCoder extends Coder {
    readonly coders!: ReadonlyArray<Coder>;

    constructor(coders: Array<Coder>, localName: string) {
        let dynamic = false;
        const types: Array<string> = [];
        coders.forEach((coder) => {
            if (coder.dynamic) { dynamic = true; }
            types.push(coder.type);
        });
        const type = ("tuple(" + types.join(",") + ")");

        super("tuple", type, localName, dynamic);
        defineProperties<TupleCoder>(this, { coders: Object.freeze(coders.slice()) });
    }

    defaultValue(): any {
        const values: any = [ ];
        this.coders.forEach((coder) => {
            values.push(coder.defaultValue());
        });

        // We only output named properties for uniquely named coders
        const uniqueNames = this.coders.reduce((accum, coder) => {
            const name = coder.localName;
            if (name) {
                if (!accum[name]) { accum[name] = 0; }
                accum[name]++;
            }
            return accum;
        }, <{ [ name: string ]: number }>{ });

        // Add named values
        this.coders.forEach((coder: Coder, index: number) => {
            let name = coder.localName;
            if (!name || uniqueNames[name] !== 1) { return; }

            if (name === "length") { name = "_length"; }

            if (values[name] != null) { return; }

            values[name] = values[index];
        });

        return Object.freeze(values);
    }

    encode(writer: Writer, _value: Array<any> | { [ name: string ]: any } | Typed): number {
        const value = Typed.dereference(_value, "tuple");
        return pack(writer, this.coders, value);
    }

    decode(reader: Reader): any {
        return unpack(reader, this.coders);
    }
}

