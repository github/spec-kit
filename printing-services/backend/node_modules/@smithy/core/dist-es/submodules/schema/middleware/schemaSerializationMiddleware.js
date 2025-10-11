import { getSmithyContext } from "@smithy/util-middleware";
export const schemaSerializationMiddleware = (config) => (next, context) => async (args) => {
    const { operationSchema } = getSmithyContext(context);
    const endpoint = context.endpointV2?.url && config.urlParser
        ? async () => config.urlParser(context.endpointV2.url)
        : config.endpoint;
    const request = await config.protocol.serializeRequest(operationSchema, args.input, {
        ...config,
        ...context,
        endpoint,
    });
    return next({
        ...args,
        request,
    });
};
