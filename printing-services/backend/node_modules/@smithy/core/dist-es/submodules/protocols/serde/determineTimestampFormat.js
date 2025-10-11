import { SCHEMA } from "@smithy/core/schema";
export function determineTimestampFormat(ns, settings) {
    if (settings.timestampFormat.useTrait) {
        if (ns.isTimestampSchema() &&
            (ns.getSchema() === SCHEMA.TIMESTAMP_DATE_TIME ||
                ns.getSchema() === SCHEMA.TIMESTAMP_HTTP_DATE ||
                ns.getSchema() === SCHEMA.TIMESTAMP_EPOCH_SECONDS)) {
            return ns.getSchema();
        }
    }
    const { httpLabel, httpPrefixHeaders, httpHeader, httpQuery } = ns.getMergedTraits();
    const bindingFormat = settings.httpBindings
        ? typeof httpPrefixHeaders === "string" || Boolean(httpHeader)
            ? SCHEMA.TIMESTAMP_HTTP_DATE
            : Boolean(httpQuery) || Boolean(httpLabel)
                ? SCHEMA.TIMESTAMP_DATE_TIME
                : undefined
        : undefined;
    return bindingFormat ?? settings.timestampFormat.default;
}
