import { NormalizedSchema, SCHEMA } from "@smithy/core/schema";
import { LazyJsonString, NumericValue, parseEpochTimestamp, parseRfc3339DateTimeWithOffset, parseRfc7231DateTime, splitHeader, } from "@smithy/core/serde";
import { fromBase64 } from "@smithy/util-base64";
import { toUtf8 } from "@smithy/util-utf8";
import { determineTimestampFormat } from "./determineTimestampFormat";
export class FromStringShapeDeserializer {
    constructor(settings) {
        this.settings = settings;
    }
    setSerdeContext(serdeContext) {
        this.serdeContext = serdeContext;
    }
    read(_schema, data) {
        const ns = NormalizedSchema.of(_schema);
        if (ns.isListSchema()) {
            return splitHeader(data).map((item) => this.read(ns.getValueSchema(), item));
        }
        if (ns.isBlobSchema()) {
            return (this.serdeContext?.base64Decoder ?? fromBase64)(data);
        }
        if (ns.isTimestampSchema()) {
            const format = determineTimestampFormat(ns, this.settings);
            switch (format) {
                case SCHEMA.TIMESTAMP_DATE_TIME:
                    return parseRfc3339DateTimeWithOffset(data);
                case SCHEMA.TIMESTAMP_HTTP_DATE:
                    return parseRfc7231DateTime(data);
                case SCHEMA.TIMESTAMP_EPOCH_SECONDS:
                    return parseEpochTimestamp(data);
                default:
                    console.warn("Missing timestamp format, parsing value with Date constructor:", data);
                    return new Date(data);
            }
        }
        if (ns.isStringSchema()) {
            const mediaType = ns.getMergedTraits().mediaType;
            let intermediateValue = data;
            if (mediaType) {
                if (ns.getMergedTraits().httpHeader) {
                    intermediateValue = this.base64ToUtf8(intermediateValue);
                }
                const isJson = mediaType === "application/json" || mediaType.endsWith("+json");
                if (isJson) {
                    intermediateValue = LazyJsonString.from(intermediateValue);
                }
                return intermediateValue;
            }
        }
        switch (true) {
            case ns.isNumericSchema():
                return Number(data);
            case ns.isBigIntegerSchema():
                return BigInt(data);
            case ns.isBigDecimalSchema():
                return new NumericValue(data, "bigDecimal");
            case ns.isBooleanSchema():
                return String(data).toLowerCase() === "true";
        }
        return data;
    }
    base64ToUtf8(base64String) {
        return (this.serdeContext?.utf8Encoder ?? toUtf8)((this.serdeContext?.base64Decoder ?? fromBase64)(base64String));
    }
}
