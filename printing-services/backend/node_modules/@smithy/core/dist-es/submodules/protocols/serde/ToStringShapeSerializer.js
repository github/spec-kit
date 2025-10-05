import { NormalizedSchema, SCHEMA } from "@smithy/core/schema";
import { dateToUtcString, LazyJsonString, quoteHeader } from "@smithy/core/serde";
import { toBase64 } from "@smithy/util-base64";
import { determineTimestampFormat } from "./determineTimestampFormat";
export class ToStringShapeSerializer {
    constructor(settings) {
        this.settings = settings;
        this.stringBuffer = "";
        this.serdeContext = undefined;
    }
    setSerdeContext(serdeContext) {
        this.serdeContext = serdeContext;
    }
    write(schema, value) {
        const ns = NormalizedSchema.of(schema);
        switch (typeof value) {
            case "object":
                if (value === null) {
                    this.stringBuffer = "null";
                    return;
                }
                if (ns.isTimestampSchema()) {
                    if (!(value instanceof Date)) {
                        throw new Error(`@smithy/core/protocols - received non-Date value ${value} when schema expected Date in ${ns.getName(true)}`);
                    }
                    const format = determineTimestampFormat(ns, this.settings);
                    switch (format) {
                        case SCHEMA.TIMESTAMP_DATE_TIME:
                            this.stringBuffer = value.toISOString().replace(".000Z", "Z");
                            break;
                        case SCHEMA.TIMESTAMP_HTTP_DATE:
                            this.stringBuffer = dateToUtcString(value);
                            break;
                        case SCHEMA.TIMESTAMP_EPOCH_SECONDS:
                            this.stringBuffer = String(value.getTime() / 1000);
                            break;
                        default:
                            console.warn("Missing timestamp format, using epoch seconds", value);
                            this.stringBuffer = String(value.getTime() / 1000);
                    }
                    return;
                }
                if (ns.isBlobSchema() && "byteLength" in value) {
                    this.stringBuffer = (this.serdeContext?.base64Encoder ?? toBase64)(value);
                    return;
                }
                if (ns.isListSchema() && Array.isArray(value)) {
                    let buffer = "";
                    for (const item of value) {
                        this.write([ns.getValueSchema(), ns.getMergedTraits()], item);
                        const headerItem = this.flush();
                        const serialized = ns.getValueSchema().isTimestampSchema() ? headerItem : quoteHeader(headerItem);
                        if (buffer !== "") {
                            buffer += ", ";
                        }
                        buffer += serialized;
                    }
                    this.stringBuffer = buffer;
                    return;
                }
                this.stringBuffer = JSON.stringify(value, null, 2);
                break;
            case "string":
                const mediaType = ns.getMergedTraits().mediaType;
                let intermediateValue = value;
                if (mediaType) {
                    const isJson = mediaType === "application/json" || mediaType.endsWith("+json");
                    if (isJson) {
                        intermediateValue = LazyJsonString.from(intermediateValue);
                    }
                    if (ns.getMergedTraits().httpHeader) {
                        this.stringBuffer = (this.serdeContext?.base64Encoder ?? toBase64)(intermediateValue.toString());
                        return;
                    }
                }
                this.stringBuffer = value;
                break;
            default:
                this.stringBuffer = String(value);
        }
    }
    flush() {
        const buffer = this.stringBuffer;
        this.stringBuffer = "";
        return buffer;
    }
}
