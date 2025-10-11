import type { CodecSettings, Schema, SerdeFunctions, ShapeDeserializer } from "@smithy/types";
/**
 * This deserializer is a dispatcher that decides whether to use a string deserializer
 * or a codec deserializer based on HTTP traits.
 *
 * For example, in a JSON HTTP message, the deserialization of a field will differ depending on whether
 * it is bound to the HTTP header (string) or body (JSON).
 *
 * @alpha
 */
export declare class HttpInterceptingShapeDeserializer<CodecShapeDeserializer extends ShapeDeserializer<any>> implements ShapeDeserializer<string | Uint8Array> {
    private codecDeserializer;
    private stringDeserializer;
    private serdeContext;
    constructor(codecDeserializer: CodecShapeDeserializer, codecSettings: CodecSettings);
    setSerdeContext(serdeContext: SerdeFunctions): void;
    read(schema: Schema, data: string | Uint8Array): any | Promise<any>;
}
