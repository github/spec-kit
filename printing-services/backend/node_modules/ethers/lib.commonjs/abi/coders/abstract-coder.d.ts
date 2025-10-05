import type { BigNumberish, BytesLike } from "../../utils/index.js";
/**
 * @_ignore:
 */
export declare const WordSize: number;
/**
 *  A [[Result]] is a sub-class of Array, which allows accessing any
 *  of its values either positionally by its index or, if keys are
 *  provided by its name.
 *
 *  @_docloc: api/abi
 */
export declare class Result extends Array<any> {
    #private;
    [K: string | number]: any;
    /**
     *  @private
     */
    constructor(...args: Array<any>);
    /**
     *  Returns the Result as a normal Array. If %%deep%%, any children
     *  which are Result objects are also converted to a normal Array.
     *
     *  This will throw if there are any outstanding deferred
     *  errors.
     */
    toArray(deep?: boolean): Array<any>;
    /**
     *  Returns the Result as an Object with each name-value pair. If
     *  %%deep%%, any children which are Result objects are also
     *  converted to an Object.
     *
     *  This will throw if any value is unnamed, or if there are
     *  any outstanding deferred errors.
     */
    toObject(deep?: boolean): Record<string, any>;
    /**
     *  @_ignore
     */
    slice(start?: number | undefined, end?: number | undefined): Result;
    /**
     *  @_ignore
     */
    filter(callback: (el: any, index: number, array: Result) => boolean, thisArg?: any): Result;
    /**
     *  @_ignore
     */
    map<T extends any = any>(callback: (el: any, index: number, array: Result) => T, thisArg?: any): Array<T>;
    /**
     *  Returns the value for %%name%%.
     *
     *  Since it is possible to have a key whose name conflicts with
     *  a method on a [[Result]] or its superclass Array, or any
     *  JavaScript keyword, this ensures all named values are still
     *  accessible by name.
     */
    getValue(name: string): any;
    /**
     *  Creates a new [[Result]] for %%items%% with each entry
     *  also accessible by its corresponding name in %%keys%%.
     */
    static fromItems(items: Array<any>, keys?: Array<null | string>): Result;
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
export declare function checkResultErrors(result: Result): Array<{
    path: Array<string | number>;
    error: Error;
}>;
/**
 *  @_ignore
 */
export declare abstract class Coder {
    readonly name: string;
    readonly type: string;
    readonly localName: string;
    readonly dynamic: boolean;
    constructor(name: string, type: string, localName: string, dynamic: boolean);
    _throwError(message: string, value: any): never;
    abstract encode(writer: Writer, value: any): number;
    abstract decode(reader: Reader): any;
    abstract defaultValue(): any;
}
/**
 *  @_ignore
 */
export declare class Writer {
    #private;
    constructor();
    get data(): string;
    get length(): number;
    appendWriter(writer: Writer): number;
    writeBytes(value: BytesLike): number;
    writeValue(value: BigNumberish): number;
    writeUpdatableValue(): (value: BigNumberish) => void;
}
/**
 *  @_ignore
 */
export declare class Reader {
    #private;
    readonly allowLoose: boolean;
    constructor(data: BytesLike, allowLoose?: boolean, maxInflation?: number);
    get data(): string;
    get dataLength(): number;
    get consumed(): number;
    get bytes(): Uint8Array;
    subReader(offset: number): Reader;
    readBytes(length: number, loose?: boolean): Uint8Array;
    readValue(): bigint;
    readIndex(): number;
}
//# sourceMappingURL=abstract-coder.d.ts.map