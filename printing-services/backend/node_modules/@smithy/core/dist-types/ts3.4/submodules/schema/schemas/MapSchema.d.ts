import { MapSchema as IMapSchema, SchemaRef, SchemaTraits } from "@smithy/types";
import { Schema } from "./Schema";
/**
 * A schema with a key schema and value schema.
 * @alpha
 */
export declare class MapSchema extends Schema implements IMapSchema {
    static readonly symbol: unique symbol;
    name: string;
    traits: SchemaTraits;
    /**
     * This is expected to be StringSchema, but may have traits.
     */
    keySchema: SchemaRef;
    valueSchema: SchemaRef;
    protected readonly symbol: symbol;
}
/**
 * Factory for MapSchema.
 * @internal
 */
export declare const map: (namespace: string, name: string, traits: SchemaTraits, keySchema: SchemaRef, valueSchema: SchemaRef) => MapSchema;
