import type { SignatureLike } from "../crypto/index.js";
import type { BigNumberish, BytesLike } from "../utils/index.js";
/**
 *  The domain for an [[link-eip-712]] payload.
 */
export interface TypedDataDomain {
    /**
     *  The human-readable name of the signing domain.
     */
    name?: null | string;
    /**
     *  The major version of the signing domain.
     */
    version?: null | string;
    /**
     *  The chain ID of the signing domain.
     */
    chainId?: null | BigNumberish;
    /**
     *  The the address of the contract that will verify the signature.
     */
    verifyingContract?: null | string;
    /**
     *  A salt used for purposes decided by the specific domain.
     */
    salt?: null | BytesLike;
}
/**
 *  A specific field of a structured [[link-eip-712]] type.
 */
export interface TypedDataField {
    /**
     *  The field name.
     */
    name: string;
    /**
     *  The type of the field.
     */
    type: string;
}
/**
 *  A **TypedDataEncode** prepares and encodes [[link-eip-712]] payloads
 *  for signed typed data.
 *
 *  This is useful for those that wish to compute various components of a
 *  typed data hash, primary types, or sub-components, but generally the
 *  higher level [[Signer-signTypedData]] is more useful.
 */
export declare class TypedDataEncoder {
    #private;
    /**
     *  The primary type for the structured [[types]].
     *
     *  This is derived automatically from the [[types]], since no
     *  recursion is possible, once the DAG for the types is consturcted
     *  internally, the primary type must be the only remaining type with
     *  no parent nodes.
     */
    readonly primaryType: string;
    /**
     *  The types.
     */
    get types(): Record<string, Array<TypedDataField>>;
    /**
     *  Create a new **TypedDataEncoder** for %%types%%.
     *
     *  This performs all necessary checking that types are valid and
     *  do not violate the [[link-eip-712]] structural constraints as
     *  well as computes the [[primaryType]].
     */
    constructor(_types: Record<string, Array<TypedDataField>>);
    /**
     *  Returnthe encoder for the specific %%type%%.
     */
    getEncoder(type: string): (value: any) => string;
    /**
     *  Return the full type for %%name%%.
     */
    encodeType(name: string): string;
    /**
     *  Return the encoded %%value%% for the %%type%%.
     */
    encodeData(type: string, value: any): string;
    /**
     *  Returns the hash of %%value%% for the type of %%name%%.
     */
    hashStruct(name: string, value: Record<string, any>): string;
    /**
     *  Return the fulled encoded %%value%% for the [[types]].
     */
    encode(value: Record<string, any>): string;
    /**
     *  Return the hash of the fully encoded %%value%% for the [[types]].
     */
    hash(value: Record<string, any>): string;
    /**
     *  @_ignore:
     */
    _visit(type: string, value: any, callback: (type: string, data: any) => any): any;
    /**
     *  Call %%calback%% for each value in %%value%%, passing the type and
     *  component within %%value%%.
     *
     *  This is useful for replacing addresses or other transformation that
     *  may be desired on each component, based on its type.
     */
    visit(value: Record<string, any>, callback: (type: string, data: any) => any): any;
    /**
     *  Create a new **TypedDataEncoder** for %%types%%.
     */
    static from(types: Record<string, Array<TypedDataField>>): TypedDataEncoder;
    /**
     *  Return the primary type for %%types%%.
     */
    static getPrimaryType(types: Record<string, Array<TypedDataField>>): string;
    /**
     *  Return the hashed struct for %%value%% using %%types%% and %%name%%.
     */
    static hashStruct(name: string, types: Record<string, Array<TypedDataField>>, value: Record<string, any>): string;
    /**
     *  Return the domain hash for %%domain%%.
     */
    static hashDomain(domain: TypedDataDomain): string;
    /**
     *  Return the fully encoded [[link-eip-712]] %%value%% for %%types%% with %%domain%%.
     */
    static encode(domain: TypedDataDomain, types: Record<string, Array<TypedDataField>>, value: Record<string, any>): string;
    /**
     *  Return the hash of the fully encoded [[link-eip-712]] %%value%% for %%types%% with %%domain%%.
     */
    static hash(domain: TypedDataDomain, types: Record<string, Array<TypedDataField>>, value: Record<string, any>): string;
    /**
     * Resolves to the value from resolving all addresses in %%value%% for
     * %%types%% and the %%domain%%.
     */
    static resolveNames(domain: TypedDataDomain, types: Record<string, Array<TypedDataField>>, value: Record<string, any>, resolveName: (name: string) => Promise<string>): Promise<{
        domain: TypedDataDomain;
        value: any;
    }>;
    /**
     *  Returns the JSON-encoded payload expected by nodes which implement
     *  the JSON-RPC [[link-eip-712]] method.
     */
    static getPayload(domain: TypedDataDomain, types: Record<string, Array<TypedDataField>>, value: Record<string, any>): any;
}
/**
 *  Compute the address used to sign the typed data for the %%signature%%.
 */
export declare function verifyTypedData(domain: TypedDataDomain, types: Record<string, Array<TypedDataField>>, value: Record<string, any>, signature: SignatureLike): string;
//# sourceMappingURL=typed-data.d.ts.map