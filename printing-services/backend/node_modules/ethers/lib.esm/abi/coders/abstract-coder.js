import { defineProperties, concat, getBytesCopy, getNumber, hexlify, toBeArray, toBigInt, toNumber, assert, assertArgument
/*, isError*/
 } from "../../utils/index.js";
/**
 * @_ignore:
 */
export const WordSize = 32;
const Padding = new Uint8Array(WordSize);
// Properties used to immediate pass through to the underlying object
// - `then` is used to detect if an object is a Promise for await
const passProperties = ["then"];
const _guard = {};
const resultNames = new WeakMap();
function getNames(result) {
    return resultNames.get(result);
}
function setNames(result, names) {
    resultNames.set(result, names);
}
function throwError(name, error) {
    const wrapped = new Error(`deferred error during ABI decoding triggered accessing ${name}`);
    wrapped.error = error;
    throw wrapped;
}
function toObject(names, items, deep) {
    if (names.indexOf(null) >= 0) {
        return items.map((item, index) => {
            if (item instanceof Result) {
                return toObject(getNames(item), item, deep);
            }
            return item;
        });
    }
    return names.reduce((accum, name, index) => {
        let item = items.getValue(name);
        if (!(name in accum)) {
            if (deep && item instanceof Result) {
                item = toObject(getNames(item), item, deep);
            }
            accum[name] = item;
        }
        return accum;
    }, {});
}
/**
 *  A [[Result]] is a sub-class of Array, which allows accessing any
 *  of its values either positionally by its index or, if keys are
 *  provided by its name.
 *
 *  @_docloc: api/abi
 */
export class Result extends Array {
    // No longer used; but cannot be removed as it will remove the
    // #private field from the .d.ts which may break backwards
    // compatibility
    #names;
    /**
     *  @private
     */
    constructor(...args) {
        // To properly sub-class Array so the other built-in
        // functions work, the constructor has to behave fairly
        // well. So, in the event we are created via fromItems()
        // we build the read-only Result object we want, but on
        // any other input, we use the default constructor
        // constructor(guard: any, items: Array<any>, keys?: Array<null | string>);
        const guard = args[0];
        let items = args[1];
        let names = (args[2] || []).slice();
        let wrap = true;
        if (guard !== _guard) {
            items = args;
            names = [];
            wrap = false;
        }
        // Can't just pass in ...items since an array of length 1
        // is a special case in the super.
        super(items.length);
        items.forEach((item, index) => { this[index] = item; });
        // Find all unique keys
        const nameCounts = names.reduce((accum, name) => {
            if (typeof (name) === "string") {
                accum.set(name, (accum.get(name) || 0) + 1);
            }
            return accum;
        }, (new Map()));
        // Remove any key thats not unique
        setNames(this, Object.freeze(items.map((item, index) => {
            const name = names[index];
            if (name != null && nameCounts.get(name) === 1) {
                return name;
            }
            return null;
        })));
        // Dummy operations to prevent TypeScript from complaining
        this.#names = [];
        if (this.#names == null) {
            void (this.#names);
        }
        if (!wrap) {
            return;
        }
        // A wrapped Result is immutable
        Object.freeze(this);
        // Proxy indices and names so we can trap deferred errors
        const proxy = new Proxy(this, {
            get: (target, prop, receiver) => {
                if (typeof (prop) === "string") {
                    // Index accessor
                    if (prop.match(/^[0-9]+$/)) {
                        const index = getNumber(prop, "%index");
                        if (index < 0 || index >= this.length) {
                            throw new RangeError("out of result range");
                        }
                        const item = target[index];
                        if (item instanceof Error) {
                            throwError(`index ${index}`, item);
                        }
                        return item;
                    }
                    // Pass important checks (like `then` for Promise) through
                    if (passProperties.indexOf(prop) >= 0) {
                        return Reflect.get(target, prop, receiver);
                    }
                    const value = target[prop];
                    if (value instanceof Function) {
                        // Make sure functions work with private variables
                        // See: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Proxy#no_private_property_forwarding
                        return function (...args) {
                            return value.apply((this === receiver) ? target : this, args);
                        };
                    }
                    else if (!(prop in target)) {
                        // Possible name accessor
                        return target.getValue.apply((this === receiver) ? target : this, [prop]);
                    }
                }
                return Reflect.get(target, prop, receiver);
            }
        });
        setNames(proxy, getNames(this));
        return proxy;
    }
    /**
     *  Returns the Result as a normal Array. If %%deep%%, any children
     *  which are Result objects are also converted to a normal Array.
     *
     *  This will throw if there are any outstanding deferred
     *  errors.
     */
    toArray(deep) {
        const result = [];
        this.forEach((item, index) => {
            if (item instanceof Error) {
                throwError(`index ${index}`, item);
            }
            if (deep && item instanceof Result) {
                item = item.toArray(deep);
            }
            result.push(item);
        });
        return result;
    }
    /**
     *  Returns the Result as an Object with each name-value pair. If
     *  %%deep%%, any children which are Result objects are also
     *  converted to an Object.
     *
     *  This will throw if any value is unnamed, or if there are
     *  any outstanding deferred errors.
     */
    toObject(deep) {
        const names = getNames(this);
        return names.reduce((accum, name, index) => {
            assert(name != null, `value at index ${index} unnamed`, "UNSUPPORTED_OPERATION", {
                operation: "toObject()"
            });
            return toObject(names, this, deep);
        }, {});
    }
    /**
     *  @_ignore
     */
    slice(start, end) {
        if (start == null) {
            start = 0;
        }
        if (start < 0) {
            start += this.length;
            if (start < 0) {
                start = 0;
            }
        }
        if (end == null) {
            end = this.length;
        }
        if (end < 0) {
            end += this.length;
            if (end < 0) {
                end = 0;
            }
        }
        if (end > this.length) {
            end = this.length;
        }
        const _names = getNames(this);
        const result = [], names = [];
        for (let i = start; i < end; i++) {
            result.push(this[i]);
            names.push(_names[i]);
        }
        return new Result(_guard, result, names);
    }
    /**
     *  @_ignore
     */
    filter(callback, thisArg) {
        const _names = getNames(this);
        const result = [], names = [];
        for (let i = 0; i < this.length; i++) {
            const item = this[i];
            if (item instanceof Error) {
                throwError(`index ${i}`, item);
            }
            if (callback.call(thisArg, item, i, this)) {
                result.push(item);
                names.push(_names[i]);
            }
        }
        return new Result(_guard, result, names);
    }
    /**
     *  @_ignore
     */
    map(callback, thisArg) {
        const result = [];
        for (let i = 0; i < this.length; i++) {
            const item = this[i];
            if (item instanceof Error) {
                throwError(`index ${i}`, item);
            }
            result.push(callback.call(thisArg, item, i, this));
        }
        return result;
    }
    /**
     *  Returns the value for %%name%%.
     *
     *  Since it is possible to have a key whose name conflicts with
     *  a method on a [[Result]] or its superclass Array, or any
     *  JavaScript keyword, this ensures all named values are still
     *  accessible by name.
     */
    getValue(name) {
        const index = getNames(this).indexOf(name);
        if (index === -1) {
            return undefined;
        }
        const value = this[index];
        if (value instanceof Error) {
            throwError(`property ${JSON.stringify(name)}`, value.error);
        }
        return value;
    }
    /**
     *  Creates a new [[Result]] for %%items%% with each entry
     *  also accessible by its corresponding name in %%keys%%.
     */
    static fromItems(items, keys) {
        return new Result(_guard, items, keys);
    }
}
/**
 *  Returns all errors found in a [[Result]].
 *
 *  Since certain errors encountered when creating a [[Result]] do
 *  not impact the ability to continue parsing data, they are
 *  deferred until they are actually accessed. Hence a faulty string
 *  in an Event that is never used does not impact the program flow.
 *
 *  However, sometimes it may be useful to access, identify or
 *  validate correctness of a [[Result]].
 *
 *  @_docloc api/abi
 */
export function checkResultErrors(result) {
    // Find the first error (if any)
    const errors = [];
    const checkErrors = function (path, object) {
        if (!Array.isArray(object)) {
            return;
        }
        for (let key in object) {
            const childPath = path.slice();
            childPath.push(key);
            try {
                checkErrors(childPath, object[key]);
            }
            catch (error) {
                errors.push({ path: childPath, error: error });
            }
        }
    };
    checkErrors([], result);
    return errors;
}
function getValue(value) {
    let bytes = toBeArray(value);
    assert(bytes.length <= WordSize, "value out-of-bounds", "BUFFER_OVERRUN", { buffer: bytes, length: WordSize, offset: bytes.length });
    if (bytes.length !== WordSize) {
        bytes = getBytesCopy(concat([Padding.slice(bytes.length % WordSize), bytes]));
    }
    return bytes;
}
/**
 *  @_ignore
 */
export class Coder {
    // The coder name:
    //   - address, uint256, tuple, array, etc.
    name;
    // The fully expanded type, including composite types:
    //   - address, uint256, tuple(address,bytes), uint256[3][4][],  etc.
    type;
    // The localName bound in the signature, in this example it is "baz":
    //   - tuple(address foo, uint bar) baz
    localName;
    // Whether this type is dynamic:
    //  - Dynamic: bytes, string, address[], tuple(boolean[]), etc.
    //  - Not Dynamic: address, uint256, boolean[3], tuple(address, uint8)
    dynamic;
    constructor(name, type, localName, dynamic) {
        defineProperties(this, { name, type, localName, dynamic }, {
            name: "string", type: "string", localName: "string", dynamic: "boolean"
        });
    }
    _throwError(message, value) {
        assertArgument(false, message, this.localName, value);
    }
}
/**
 *  @_ignore
 */
export class Writer {
    // An array of WordSize lengthed objects to concatenation
    #data;
    #dataLength;
    constructor() {
        this.#data = [];
        this.#dataLength = 0;
    }
    get data() {
        return concat(this.#data);
    }
    get length() { return this.#dataLength; }
    #writeData(data) {
        this.#data.push(data);
        this.#dataLength += data.length;
        return data.length;
    }
    appendWriter(writer) {
        return this.#writeData(getBytesCopy(writer.data));
    }
    // Arrayish item; pad on the right to *nearest* WordSize
    writeBytes(value) {
        let bytes = getBytesCopy(value);
        const paddingOffset = bytes.length % WordSize;
        if (paddingOffset) {
            bytes = getBytesCopy(concat([bytes, Padding.slice(paddingOffset)]));
        }
        return this.#writeData(bytes);
    }
    // Numeric item; pad on the left *to* WordSize
    writeValue(value) {
        return this.#writeData(getValue(value));
    }
    // Inserts a numeric place-holder, returning a callback that can
    // be used to asjust the value later
    writeUpdatableValue() {
        const offset = this.#data.length;
        this.#data.push(Padding);
        this.#dataLength += WordSize;
        return (value) => {
            this.#data[offset] = getValue(value);
        };
    }
}
/**
 *  @_ignore
 */
export class Reader {
    // Allows incomplete unpadded data to be read; otherwise an error
    // is raised if attempting to overrun the buffer. This is required
    // to deal with an old Solidity bug, in which event data for
    // external (not public thoguh) was tightly packed.
    allowLoose;
    #data;
    #offset;
    #bytesRead;
    #parent;
    #maxInflation;
    constructor(data, allowLoose, maxInflation) {
        defineProperties(this, { allowLoose: !!allowLoose });
        this.#data = getBytesCopy(data);
        this.#bytesRead = 0;
        this.#parent = null;
        this.#maxInflation = (maxInflation != null) ? maxInflation : 1024;
        this.#offset = 0;
    }
    get data() { return hexlify(this.#data); }
    get dataLength() { return this.#data.length; }
    get consumed() { return this.#offset; }
    get bytes() { return new Uint8Array(this.#data); }
    #incrementBytesRead(count) {
        if (this.#parent) {
            return this.#parent.#incrementBytesRead(count);
        }
        this.#bytesRead += count;
        // Check for excessive inflation (see: #4537)
        assert(this.#maxInflation < 1 || this.#bytesRead <= this.#maxInflation * this.dataLength, `compressed ABI data exceeds inflation ratio of ${this.#maxInflation} ( see: https:/\/github.com/ethers-io/ethers.js/issues/4537 )`, "BUFFER_OVERRUN", {
            buffer: getBytesCopy(this.#data), offset: this.#offset,
            length: count, info: {
                bytesRead: this.#bytesRead,
                dataLength: this.dataLength
            }
        });
    }
    #peekBytes(offset, length, loose) {
        let alignedLength = Math.ceil(length / WordSize) * WordSize;
        if (this.#offset + alignedLength > this.#data.length) {
            if (this.allowLoose && loose && this.#offset + length <= this.#data.length) {
                alignedLength = length;
            }
            else {
                assert(false, "data out-of-bounds", "BUFFER_OVERRUN", {
                    buffer: getBytesCopy(this.#data),
                    length: this.#data.length,
                    offset: this.#offset + alignedLength
                });
            }
        }
        return this.#data.slice(this.#offset, this.#offset + alignedLength);
    }
    // Create a sub-reader with the same underlying data, but offset
    subReader(offset) {
        const reader = new Reader(this.#data.slice(this.#offset + offset), this.allowLoose, this.#maxInflation);
        reader.#parent = this;
        return reader;
    }
    // Read bytes
    readBytes(length, loose) {
        let bytes = this.#peekBytes(0, length, !!loose);
        this.#incrementBytesRead(length);
        this.#offset += bytes.length;
        // @TODO: Make sure the length..end bytes are all 0?
        return bytes.slice(0, length);
    }
    // Read a numeric values
    readValue() {
        return toBigInt(this.readBytes(WordSize));
    }
    readIndex() {
        return toNumber(this.readBytes(WordSize));
    }
}
//# sourceMappingURL=abstract-coder.js.map