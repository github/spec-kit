/**
 *  A fragment is a single item from an ABI, which may represent any of:
 *
 *  - [Functions](FunctionFragment)
 *  - [Events](EventFragment)
 *  - [Constructors](ConstructorFragment)
 *  - Custom [Errors](ErrorFragment)
 *  - [Fallback or Receive](FallbackFragment) functions
 *
 *  @_subsection api/abi/abi-coder:Fragments  [about-fragments]
 */
/**
 *  A Type description in a [JSON ABI format](link-solc-jsonabi).
 */
export interface JsonFragmentType {
    /**
     *  The parameter name.
     */
    readonly name?: string;
    /**
     *  If the parameter is indexed.
     */
    readonly indexed?: boolean;
    /**
     *  The type of the parameter.
     */
    readonly type?: string;
    /**
     *  The internal Solidity type.
     */
    readonly internalType?: string;
    /**
     *  The components for a tuple.
     */
    readonly components?: ReadonlyArray<JsonFragmentType>;
}
/**
 *  A fragment for a method, event or error in a [JSON ABI format](link-solc-jsonabi).
 */
export interface JsonFragment {
    /**
     *  The name of the error, event, function, etc.
     */
    readonly name?: string;
    /**
     *  The type of the fragment (e.g. ``event``, ``"function"``, etc.)
     */
    readonly type?: string;
    /**
     *  If the event is anonymous.
     */
    readonly anonymous?: boolean;
    /**
     *  If the function is payable.
     */
    readonly payable?: boolean;
    /**
     *  If the function is constant.
     */
    readonly constant?: boolean;
    /**
     *  The mutability state of the function.
     */
    readonly stateMutability?: string;
    /**
     *  The input parameters.
     */
    readonly inputs?: ReadonlyArray<JsonFragmentType>;
    /**
     *  The output parameters.
     */
    readonly outputs?: ReadonlyArray<JsonFragmentType>;
    /**
     *  The gas limit to use when sending a transaction for this function.
     */
    readonly gas?: string;
}
/**
 *  The format to serialize the output as.
 *
 *  **``"sighash"``** - the bare formatting, used to compute the selector
 *  or topic hash; this format cannot be reversed (as it discards ``indexed``)
 *  so cannot by used to export an [[Interface]].
 *
 *  **``"minimal"``** - Human-Readable ABI with minimal spacing and without
 *  names, so it is compact, but will result in Result objects that cannot
 *  be accessed by name.
 *
 *  **``"full"``** - Full Human-Readable ABI, with readable spacing and names
 *  intact; this is generally the recommended format.
 *
 *  **``"json"``** - The [JSON ABI format](link-solc-jsonabi).
 */
export type FormatType = "sighash" | "minimal" | "full" | "json";
/**
 *  When [walking](ParamType-walk) a [[ParamType]], this is called
 *  on each component.
 */
export type ParamTypeWalkFunc = (type: string, value: any) => any;
/**
 *  When [walking asynchronously](ParamType-walkAsync) a [[ParamType]],
 *  this is called on each component.
 */
export type ParamTypeWalkAsyncFunc = (type: string, value: any) => any | Promise<any>;
/**
 *  Each input and output of a [[Fragment]] is an Array of **ParamType**.
 */
export declare class ParamType {
    #private;
    /**
     *  The local name of the parameter (or ``""`` if unbound)
     */
    readonly name: string;
    /**
     *  The fully qualified type (e.g. ``"address"``, ``"tuple(address)"``,
     *  ``"uint256[3][]"``)
     */
    readonly type: string;
    /**
     *  The base type (e.g. ``"address"``, ``"tuple"``, ``"array"``)
     */
    readonly baseType: string;
    /**
     *  True if the parameters is indexed.
     *
     *  For non-indexable types this is ``null``.
     */
    readonly indexed: null | boolean;
    /**
     *  The components for the tuple.
     *
     *  For non-tuple types this is ``null``.
     */
    readonly components: null | ReadonlyArray<ParamType>;
    /**
     *  The array length, or ``-1`` for dynamic-lengthed arrays.
     *
     *  For non-array types this is ``null``.
     */
    readonly arrayLength: null | number;
    /**
     *  The type of each child in the array.
     *
     *  For non-array types this is ``null``.
     */
    readonly arrayChildren: null | ParamType;
    /**
     *  @private
     */
    constructor(guard: any, name: string, type: string, baseType: string, indexed: null | boolean, components: null | ReadonlyArray<ParamType>, arrayLength: null | number, arrayChildren: null | ParamType);
    /**
     *  Return a string representation of this type.
     *
     *  For example,
     *
     *  ``sighash" => "(uint256,address)"``
     *
     *  ``"minimal" => "tuple(uint256,address) indexed"``
     *
     *  ``"full" => "tuple(uint256 foo, address bar) indexed baz"``
     */
    format(format?: FormatType): string;
    /**
     *  Returns true if %%this%% is an Array type.
     *
     *  This provides a type gaurd ensuring that [[arrayChildren]]
     *  and [[arrayLength]] are non-null.
     */
    isArray(): this is (ParamType & {
        arrayChildren: ParamType;
        arrayLength: number;
    });
    /**
     *  Returns true if %%this%% is a Tuple type.
     *
     *  This provides a type gaurd ensuring that [[components]]
     *  is non-null.
     */
    isTuple(): this is (ParamType & {
        components: ReadonlyArray<ParamType>;
    });
    /**
     *  Returns true if %%this%% is an Indexable type.
     *
     *  This provides a type gaurd ensuring that [[indexed]]
     *  is non-null.
     */
    isIndexable(): this is (ParamType & {
        indexed: boolean;
    });
    /**
     *  Walks the **ParamType** with %%value%%, calling %%process%%
     *  on each type, destructing the %%value%% recursively.
     */
    walk(value: any, process: ParamTypeWalkFunc): any;
    /**
     *  Walks the **ParamType** with %%value%%, asynchronously calling
     *  %%process%% on each type, destructing the %%value%% recursively.
     *
     *  This can be used to resolve ENS names by walking and resolving each
     *  ``"address"`` type.
     */
    walkAsync(value: any, process: ParamTypeWalkAsyncFunc): Promise<any>;
    /**
     *  Creates a new **ParamType** for %%obj%%.
     *
     *  If %%allowIndexed%% then the ``indexed`` keyword is permitted,
     *  otherwise the ``indexed`` keyword will throw an error.
     */
    static from(obj: any, allowIndexed?: boolean): ParamType;
    /**
     *  Returns true if %%value%% is a **ParamType**.
     */
    static isParamType(value: any): value is ParamType;
}
/**
 *  The type of a [[Fragment]].
 */
export type FragmentType = "constructor" | "error" | "event" | "fallback" | "function" | "struct";
/**
 *  An abstract class to represent An individual fragment from a parse ABI.
 */
export declare abstract class Fragment {
    /**
     *  The type of the fragment.
     */
    readonly type: FragmentType;
    /**
     *  The inputs for the fragment.
     */
    readonly inputs: ReadonlyArray<ParamType>;
    /**
     *  @private
     */
    constructor(guard: any, type: FragmentType, inputs: ReadonlyArray<ParamType>);
    /**
     *  Returns a string representation of this fragment as %%format%%.
     */
    abstract format(format?: FormatType): string;
    /**
     *  Creates a new **Fragment** for %%obj%%, wich can be any supported
     *  ABI frgament type.
     */
    static from(obj: any): Fragment;
    /**
     *  Returns true if %%value%% is a [[ConstructorFragment]].
     */
    static isConstructor(value: any): value is ConstructorFragment;
    /**
     *  Returns true if %%value%% is an [[ErrorFragment]].
     */
    static isError(value: any): value is ErrorFragment;
    /**
     *  Returns true if %%value%% is an [[EventFragment]].
     */
    static isEvent(value: any): value is EventFragment;
    /**
     *  Returns true if %%value%% is a [[FunctionFragment]].
     */
    static isFunction(value: any): value is FunctionFragment;
    /**
     *  Returns true if %%value%% is a [[StructFragment]].
     */
    static isStruct(value: any): value is StructFragment;
}
/**
 *  An abstract class to represent An individual fragment
 *  which has a name from a parse ABI.
 */
export declare abstract class NamedFragment extends Fragment {
    /**
     *  The name of the fragment.
     */
    readonly name: string;
    /**
     *  @private
     */
    constructor(guard: any, type: FragmentType, name: string, inputs: ReadonlyArray<ParamType>);
}
/**
 *  A Fragment which represents a //Custom Error//.
 */
export declare class ErrorFragment extends NamedFragment {
    /**
     *  @private
     */
    constructor(guard: any, name: string, inputs: ReadonlyArray<ParamType>);
    /**
     *  The Custom Error selector.
     */
    get selector(): string;
    /**
     *  Returns a string representation of this fragment as %%format%%.
     */
    format(format?: FormatType): string;
    /**
     *  Returns a new **ErrorFragment** for %%obj%%.
     */
    static from(obj: any): ErrorFragment;
    /**
     *  Returns ``true`` and provides a type guard if %%value%% is an
     *  **ErrorFragment**.
     */
    static isFragment(value: any): value is ErrorFragment;
}
/**
 *  A Fragment which represents an Event.
 */
export declare class EventFragment extends NamedFragment {
    /**
     *  Whether this event is anonymous.
     */
    readonly anonymous: boolean;
    /**
     *  @private
     */
    constructor(guard: any, name: string, inputs: ReadonlyArray<ParamType>, anonymous: boolean);
    /**
     *  The Event topic hash.
     */
    get topicHash(): string;
    /**
     *  Returns a string representation of this event as %%format%%.
     */
    format(format?: FormatType): string;
    /**
     *  Return the topic hash for an event with %%name%% and %%params%%.
     */
    static getTopicHash(name: string, params?: Array<any>): string;
    /**
     *  Returns a new **EventFragment** for %%obj%%.
     */
    static from(obj: any): EventFragment;
    /**
     *  Returns ``true`` and provides a type guard if %%value%% is an
     *  **EventFragment**.
     */
    static isFragment(value: any): value is EventFragment;
}
/**
 *  A Fragment which represents a constructor.
 */
export declare class ConstructorFragment extends Fragment {
    /**
     *  Whether the constructor can receive an endowment.
     */
    readonly payable: boolean;
    /**
     *  The recommended gas limit for deployment or ``null``.
     */
    readonly gas: null | bigint;
    /**
     *  @private
     */
    constructor(guard: any, type: FragmentType, inputs: ReadonlyArray<ParamType>, payable: boolean, gas: null | bigint);
    /**
     *  Returns a string representation of this constructor as %%format%%.
     */
    format(format?: FormatType): string;
    /**
     *  Returns a new **ConstructorFragment** for %%obj%%.
     */
    static from(obj: any): ConstructorFragment;
    /**
     *  Returns ``true`` and provides a type guard if %%value%% is a
     *  **ConstructorFragment**.
     */
    static isFragment(value: any): value is ConstructorFragment;
}
/**
 *  A Fragment which represents a method.
 */
export declare class FallbackFragment extends Fragment {
    /**
     *  If the function can be sent value during invocation.
     */
    readonly payable: boolean;
    constructor(guard: any, inputs: ReadonlyArray<ParamType>, payable: boolean);
    /**
     *  Returns a string representation of this fallback as %%format%%.
     */
    format(format?: FormatType): string;
    /**
     *  Returns a new **FallbackFragment** for %%obj%%.
     */
    static from(obj: any): FallbackFragment;
    /**
     *  Returns ``true`` and provides a type guard if %%value%% is a
     *  **FallbackFragment**.
     */
    static isFragment(value: any): value is FallbackFragment;
}
/**
 *  A Fragment which represents a method.
 */
export declare class FunctionFragment extends NamedFragment {
    /**
     *  If the function is constant (e.g. ``pure`` or ``view`` functions).
     */
    readonly constant: boolean;
    /**
     *  The returned types for the result of calling this function.
     */
    readonly outputs: ReadonlyArray<ParamType>;
    /**
     *  The state mutability (e.g. ``payable``, ``nonpayable``, ``view``
     *  or ``pure``)
     */
    readonly stateMutability: "payable" | "nonpayable" | "view" | "pure";
    /**
     *  If the function can be sent value during invocation.
     */
    readonly payable: boolean;
    /**
     *  The recommended gas limit to send when calling this function.
     */
    readonly gas: null | bigint;
    /**
     *  @private
     */
    constructor(guard: any, name: string, stateMutability: "payable" | "nonpayable" | "view" | "pure", inputs: ReadonlyArray<ParamType>, outputs: ReadonlyArray<ParamType>, gas: null | bigint);
    /**
     *  The Function selector.
     */
    get selector(): string;
    /**
     *  Returns a string representation of this function as %%format%%.
     */
    format(format?: FormatType): string;
    /**
     *  Return the selector for a function with %%name%% and %%params%%.
     */
    static getSelector(name: string, params?: Array<any>): string;
    /**
     *  Returns a new **FunctionFragment** for %%obj%%.
     */
    static from(obj: any): FunctionFragment;
    /**
     *  Returns ``true`` and provides a type guard if %%value%% is a
     *  **FunctionFragment**.
     */
    static isFragment(value: any): value is FunctionFragment;
}
/**
 *  A Fragment which represents a structure.
 */
export declare class StructFragment extends NamedFragment {
    /**
     *  @private
     */
    constructor(guard: any, name: string, inputs: ReadonlyArray<ParamType>);
    /**
     *  Returns a string representation of this struct as %%format%%.
     */
    format(): string;
    /**
     *  Returns a new **StructFragment** for %%obj%%.
     */
    static from(obj: any): StructFragment;
    /**
     *  Returns ``true`` and provides a type guard if %%value%% is a
     *  **StructFragment**.
     */
    static isFragment(value: any): value is FunctionFragment;
}
//# sourceMappingURL=fragments.d.ts.map