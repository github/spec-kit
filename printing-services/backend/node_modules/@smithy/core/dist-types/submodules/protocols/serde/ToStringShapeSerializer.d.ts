import type { CodecSettings, Schema, SerdeFunctions, ShapeSerializer } from "@smithy/types";
/**
 * Serializes a shape to string.
 *
 * @alpha
 */
export declare class ToStringShapeSerializer implements ShapeSerializer<string> {
    private settings;
    private stringBuffer;
    private serdeContext;
    constructor(settings: CodecSettings);
    setSerdeContext(serdeContext: SerdeFunctions): void;
    write(schema: Schema, value: unknown): void;
    flush(): string;
}
