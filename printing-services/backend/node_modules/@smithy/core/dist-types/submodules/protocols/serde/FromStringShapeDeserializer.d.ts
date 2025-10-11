import type { CodecSettings, Schema, SerdeFunctions, ShapeDeserializer } from "@smithy/types";
/**
 * This deserializer reads strings.
 *
 * @alpha
 */
export declare class FromStringShapeDeserializer implements ShapeDeserializer<string> {
    private settings;
    private serdeContext;
    constructor(settings: CodecSettings);
    setSerdeContext(serdeContext: SerdeFunctions): void;
    read(_schema: Schema, data: string): any;
    private base64ToUtf8;
}
