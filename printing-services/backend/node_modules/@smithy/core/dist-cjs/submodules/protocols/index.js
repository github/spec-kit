var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/submodules/protocols/index.ts
var index_exports = {};
__export(index_exports, {
  FromStringShapeDeserializer: () => FromStringShapeDeserializer,
  HttpBindingProtocol: () => HttpBindingProtocol,
  HttpInterceptingShapeDeserializer: () => HttpInterceptingShapeDeserializer,
  HttpInterceptingShapeSerializer: () => HttpInterceptingShapeSerializer,
  HttpProtocol: () => HttpProtocol,
  RequestBuilder: () => RequestBuilder,
  RpcProtocol: () => RpcProtocol,
  ToStringShapeSerializer: () => ToStringShapeSerializer,
  collectBody: () => collectBody,
  determineTimestampFormat: () => determineTimestampFormat,
  extendedEncodeURIComponent: () => extendedEncodeURIComponent,
  requestBuilder: () => requestBuilder,
  resolvedPath: () => resolvedPath
});
module.exports = __toCommonJS(index_exports);

// src/submodules/protocols/collect-stream-body.ts
var import_util_stream = require("@smithy/util-stream");
var collectBody = async (streamBody = new Uint8Array(), context) => {
  if (streamBody instanceof Uint8Array) {
    return import_util_stream.Uint8ArrayBlobAdapter.mutate(streamBody);
  }
  if (!streamBody) {
    return import_util_stream.Uint8ArrayBlobAdapter.mutate(new Uint8Array());
  }
  const fromContext = context.streamCollector(streamBody);
  return import_util_stream.Uint8ArrayBlobAdapter.mutate(await fromContext);
};

// src/submodules/protocols/extended-encode-uri-component.ts
function extendedEncodeURIComponent(str) {
  return encodeURIComponent(str).replace(/[!'()*]/g, function(c) {
    return "%" + c.charCodeAt(0).toString(16).toUpperCase();
  });
}

// src/submodules/protocols/HttpBindingProtocol.ts
var import_schema2 = require("@smithy/core/schema");
var import_serde = require("@smithy/core/serde");
var import_protocol_http2 = require("@smithy/protocol-http");
var import_util_stream2 = require("@smithy/util-stream");

// src/submodules/protocols/HttpProtocol.ts
var import_schema = require("@smithy/core/schema");
var import_protocol_http = require("@smithy/protocol-http");
var HttpProtocol = class {
  constructor(options) {
    this.options = options;
  }
  getRequestType() {
    return import_protocol_http.HttpRequest;
  }
  getResponseType() {
    return import_protocol_http.HttpResponse;
  }
  setSerdeContext(serdeContext) {
    this.serdeContext = serdeContext;
    this.serializer.setSerdeContext(serdeContext);
    this.deserializer.setSerdeContext(serdeContext);
    if (this.getPayloadCodec()) {
      this.getPayloadCodec().setSerdeContext(serdeContext);
    }
  }
  updateServiceEndpoint(request, endpoint) {
    if ("url" in endpoint) {
      request.protocol = endpoint.url.protocol;
      request.hostname = endpoint.url.hostname;
      request.port = endpoint.url.port ? Number(endpoint.url.port) : void 0;
      request.path = endpoint.url.pathname;
      request.fragment = endpoint.url.hash || void 0;
      request.username = endpoint.url.username || void 0;
      request.password = endpoint.url.password || void 0;
      for (const [k, v] of endpoint.url.searchParams.entries()) {
        if (!request.query) {
          request.query = {};
        }
        request.query[k] = v;
      }
      return request;
    } else {
      request.protocol = endpoint.protocol;
      request.hostname = endpoint.hostname;
      request.port = endpoint.port ? Number(endpoint.port) : void 0;
      request.path = endpoint.path;
      request.query = {
        ...endpoint.query
      };
      return request;
    }
  }
  setHostPrefix(request, operationSchema, input) {
    const operationNs = import_schema.NormalizedSchema.of(operationSchema);
    const inputNs = import_schema.NormalizedSchema.of(operationSchema.input);
    if (operationNs.getMergedTraits().endpoint) {
      let hostPrefix = operationNs.getMergedTraits().endpoint?.[0];
      if (typeof hostPrefix === "string") {
        const hostLabelInputs = [...inputNs.structIterator()].filter(
          ([, member]) => member.getMergedTraits().hostLabel
        );
        for (const [name] of hostLabelInputs) {
          const replacement = input[name];
          if (typeof replacement !== "string") {
            throw new Error(`@smithy/core/schema - ${name} in input must be a string as hostLabel.`);
          }
          hostPrefix = hostPrefix.replace(`{${name}}`, replacement);
        }
        request.hostname = hostPrefix + request.hostname;
      }
    }
  }
  deserializeMetadata(output) {
    return {
      httpStatusCode: output.statusCode,
      requestId: output.headers["x-amzn-requestid"] ?? output.headers["x-amzn-request-id"] ?? output.headers["x-amz-request-id"],
      extendedRequestId: output.headers["x-amz-id-2"],
      cfId: output.headers["x-amz-cf-id"]
    };
  }
  /**
   * @param eventStream - the iterable provided by the caller.
   * @param requestSchema - the schema of the event stream container (struct).
   * @param [initialRequest] - only provided if the initial-request is part of the event stream (RPC).
   *
   * @returns a stream suitable for the HTTP body of a request.
   */
  async serializeEventStream({
    eventStream,
    requestSchema,
    initialRequest
  }) {
    const eventStreamSerde = await this.loadEventStreamCapability();
    return eventStreamSerde.serializeEventStream({
      eventStream,
      requestSchema,
      initialRequest
    });
  }
  /**
   * @param response - http response from which to read the event stream.
   * @param unionSchema - schema of the event stream container (struct).
   * @param [initialResponseContainer] - provided and written to only if the initial response is part of the event stream (RPC).
   *
   * @returns the asyncIterable of the event stream.
   */
  async deserializeEventStream({
    response,
    responseSchema,
    initialResponseContainer
  }) {
    const eventStreamSerde = await this.loadEventStreamCapability();
    return eventStreamSerde.deserializeEventStream({
      response,
      responseSchema,
      initialResponseContainer
    });
  }
  /**
   * Loads eventStream capability async (for chunking).
   */
  async loadEventStreamCapability() {
    const { EventStreamSerde } = await Promise.resolve().then(() => __toESM(require("@smithy/core/event-streams")));
    return new EventStreamSerde({
      marshaller: this.getEventStreamMarshaller(),
      serializer: this.serializer,
      deserializer: this.deserializer,
      serdeContext: this.serdeContext,
      defaultContentType: this.getDefaultContentType()
    });
  }
  /**
   * @returns content-type default header value for event stream events and other documents.
   */
  getDefaultContentType() {
    throw new Error(
      `@smithy/core/protocols - ${this.constructor.name} getDefaultContentType() implementation missing.`
    );
  }
  async deserializeHttpMessage(schema, context, response, arg4, arg5) {
    void schema;
    void context;
    void response;
    void arg4;
    void arg5;
    return [];
  }
  getEventStreamMarshaller() {
    const context = this.serdeContext;
    if (!context.eventStreamMarshaller) {
      throw new Error("@smithy/core - HttpProtocol: eventStreamMarshaller missing in serdeContext.");
    }
    return context.eventStreamMarshaller;
  }
};

// src/submodules/protocols/HttpBindingProtocol.ts
var HttpBindingProtocol = class extends HttpProtocol {
  async serializeRequest(operationSchema, _input, context) {
    const input = {
      ..._input ?? {}
    };
    const serializer = this.serializer;
    const query = {};
    const headers = {};
    const endpoint = await context.endpoint();
    const ns = import_schema2.NormalizedSchema.of(operationSchema?.input);
    const schema = ns.getSchema();
    let hasNonHttpBindingMember = false;
    let payload;
    const request = new import_protocol_http2.HttpRequest({
      protocol: "",
      hostname: "",
      port: void 0,
      path: "",
      fragment: void 0,
      query,
      headers,
      body: void 0
    });
    if (endpoint) {
      this.updateServiceEndpoint(request, endpoint);
      this.setHostPrefix(request, operationSchema, input);
      const opTraits = import_schema2.NormalizedSchema.translateTraits(operationSchema.traits);
      if (opTraits.http) {
        request.method = opTraits.http[0];
        const [path, search] = opTraits.http[1].split("?");
        if (request.path == "/") {
          request.path = path;
        } else {
          request.path += path;
        }
        const traitSearchParams = new URLSearchParams(search ?? "");
        Object.assign(query, Object.fromEntries(traitSearchParams));
      }
    }
    for (const [memberName, memberNs] of ns.structIterator()) {
      const memberTraits = memberNs.getMergedTraits() ?? {};
      const inputMemberValue = input[memberName];
      if (inputMemberValue == null) {
        continue;
      }
      if (memberTraits.httpPayload) {
        const isStreaming = memberNs.isStreaming();
        if (isStreaming) {
          const isEventStream = memberNs.isStructSchema();
          if (isEventStream) {
            if (input[memberName]) {
              payload = await this.serializeEventStream({
                eventStream: input[memberName],
                requestSchema: ns
              });
            }
          } else {
            payload = inputMemberValue;
          }
        } else {
          serializer.write(memberNs, inputMemberValue);
          payload = serializer.flush();
        }
        delete input[memberName];
      } else if (memberTraits.httpLabel) {
        serializer.write(memberNs, inputMemberValue);
        const replacement = serializer.flush();
        if (request.path.includes(`{${memberName}+}`)) {
          request.path = request.path.replace(
            `{${memberName}+}`,
            replacement.split("/").map(extendedEncodeURIComponent).join("/")
          );
        } else if (request.path.includes(`{${memberName}}`)) {
          request.path = request.path.replace(`{${memberName}}`, extendedEncodeURIComponent(replacement));
        }
        delete input[memberName];
      } else if (memberTraits.httpHeader) {
        serializer.write(memberNs, inputMemberValue);
        headers[memberTraits.httpHeader.toLowerCase()] = String(serializer.flush());
        delete input[memberName];
      } else if (typeof memberTraits.httpPrefixHeaders === "string") {
        for (const [key, val] of Object.entries(inputMemberValue)) {
          const amalgam = memberTraits.httpPrefixHeaders + key;
          serializer.write([memberNs.getValueSchema(), { httpHeader: amalgam }], val);
          headers[amalgam.toLowerCase()] = serializer.flush();
        }
        delete input[memberName];
      } else if (memberTraits.httpQuery || memberTraits.httpQueryParams) {
        this.serializeQuery(memberNs, inputMemberValue, query);
        delete input[memberName];
      } else {
        hasNonHttpBindingMember = true;
      }
    }
    if (hasNonHttpBindingMember && input) {
      serializer.write(schema, input);
      payload = serializer.flush();
    }
    request.headers = headers;
    request.query = query;
    request.body = payload;
    return request;
  }
  serializeQuery(ns, data, query) {
    const serializer = this.serializer;
    const traits = ns.getMergedTraits();
    if (traits.httpQueryParams) {
      for (const [key, val] of Object.entries(data)) {
        if (!(key in query)) {
          const valueSchema = ns.getValueSchema();
          Object.assign(valueSchema.getMergedTraits(), {
            // We pass on the traits to the sub-schema
            // because we are still in the process of serializing the map itself.
            ...traits,
            httpQuery: key,
            httpQueryParams: void 0
          });
          this.serializeQuery(valueSchema, val, query);
        }
      }
      return;
    }
    if (ns.isListSchema()) {
      const sparse = !!ns.getMergedTraits().sparse;
      const buffer = [];
      for (const item of data) {
        serializer.write([ns.getValueSchema(), traits], item);
        const serializable = serializer.flush();
        if (sparse || serializable !== void 0) {
          buffer.push(serializable);
        }
      }
      query[traits.httpQuery] = buffer;
    } else {
      serializer.write([ns, traits], data);
      query[traits.httpQuery] = serializer.flush();
    }
  }
  async deserializeResponse(operationSchema, context, response) {
    const deserializer = this.deserializer;
    const ns = import_schema2.NormalizedSchema.of(operationSchema.output);
    const dataObject = {};
    if (response.statusCode >= 300) {
      const bytes = await collectBody(response.body, context);
      if (bytes.byteLength > 0) {
        Object.assign(dataObject, await deserializer.read(import_schema2.SCHEMA.DOCUMENT, bytes));
      }
      await this.handleError(operationSchema, context, response, dataObject, this.deserializeMetadata(response));
      throw new Error("@smithy/core/protocols - HTTP Protocol error handler failed to throw.");
    }
    for (const header in response.headers) {
      const value = response.headers[header];
      delete response.headers[header];
      response.headers[header.toLowerCase()] = value;
    }
    const nonHttpBindingMembers = await this.deserializeHttpMessage(ns, context, response, dataObject);
    if (nonHttpBindingMembers.length) {
      const bytes = await collectBody(response.body, context);
      if (bytes.byteLength > 0) {
        const dataFromBody = await deserializer.read(ns, bytes);
        for (const member of nonHttpBindingMembers) {
          dataObject[member] = dataFromBody[member];
        }
      }
    }
    dataObject.$metadata = this.deserializeMetadata(response);
    return dataObject;
  }
  async deserializeHttpMessage(schema, context, response, arg4, arg5) {
    let dataObject;
    if (arg4 instanceof Set) {
      dataObject = arg5;
    } else {
      dataObject = arg4;
    }
    const deserializer = this.deserializer;
    const ns = import_schema2.NormalizedSchema.of(schema);
    const nonHttpBindingMembers = [];
    for (const [memberName, memberSchema] of ns.structIterator()) {
      const memberTraits = memberSchema.getMemberTraits();
      if (memberTraits.httpPayload) {
        const isStreaming = memberSchema.isStreaming();
        if (isStreaming) {
          const isEventStream = memberSchema.isStructSchema();
          if (isEventStream) {
            dataObject[memberName] = await this.deserializeEventStream({
              response,
              responseSchema: ns
            });
          } else {
            dataObject[memberName] = (0, import_util_stream2.sdkStreamMixin)(response.body);
          }
        } else if (response.body) {
          const bytes = await collectBody(response.body, context);
          if (bytes.byteLength > 0) {
            dataObject[memberName] = await deserializer.read(memberSchema, bytes);
          }
        }
      } else if (memberTraits.httpHeader) {
        const key = String(memberTraits.httpHeader).toLowerCase();
        const value = response.headers[key];
        if (null != value) {
          if (memberSchema.isListSchema()) {
            const headerListValueSchema = memberSchema.getValueSchema();
            headerListValueSchema.getMergedTraits().httpHeader = key;
            let sections;
            if (headerListValueSchema.isTimestampSchema() && headerListValueSchema.getSchema() === import_schema2.SCHEMA.TIMESTAMP_DEFAULT) {
              sections = (0, import_serde.splitEvery)(value, ",", 2);
            } else {
              sections = (0, import_serde.splitHeader)(value);
            }
            const list = [];
            for (const section of sections) {
              list.push(await deserializer.read(headerListValueSchema, section.trim()));
            }
            dataObject[memberName] = list;
          } else {
            dataObject[memberName] = await deserializer.read(memberSchema, value);
          }
        }
      } else if (memberTraits.httpPrefixHeaders !== void 0) {
        dataObject[memberName] = {};
        for (const [header, value] of Object.entries(response.headers)) {
          if (header.startsWith(memberTraits.httpPrefixHeaders)) {
            const valueSchema = memberSchema.getValueSchema();
            valueSchema.getMergedTraits().httpHeader = header;
            dataObject[memberName][header.slice(memberTraits.httpPrefixHeaders.length)] = await deserializer.read(
              valueSchema,
              value
            );
          }
        }
      } else if (memberTraits.httpResponseCode) {
        dataObject[memberName] = response.statusCode;
      } else {
        nonHttpBindingMembers.push(memberName);
      }
    }
    return nonHttpBindingMembers;
  }
};

// src/submodules/protocols/RpcProtocol.ts
var import_schema3 = require("@smithy/core/schema");
var import_protocol_http3 = require("@smithy/protocol-http");
var RpcProtocol = class extends HttpProtocol {
  async serializeRequest(operationSchema, input, context) {
    const serializer = this.serializer;
    const query = {};
    const headers = {};
    const endpoint = await context.endpoint();
    const ns = import_schema3.NormalizedSchema.of(operationSchema?.input);
    const schema = ns.getSchema();
    let payload;
    const request = new import_protocol_http3.HttpRequest({
      protocol: "",
      hostname: "",
      port: void 0,
      path: "/",
      fragment: void 0,
      query,
      headers,
      body: void 0
    });
    if (endpoint) {
      this.updateServiceEndpoint(request, endpoint);
      this.setHostPrefix(request, operationSchema, input);
    }
    const _input = {
      ...input
    };
    if (input) {
      const eventStreamMember = ns.getEventStreamMember();
      if (eventStreamMember) {
        if (_input[eventStreamMember]) {
          const initialRequest = {};
          for (const [memberName, memberSchema] of ns.structIterator()) {
            if (memberName !== eventStreamMember && _input[memberName]) {
              serializer.write(memberSchema, _input[memberName]);
              initialRequest[memberName] = serializer.flush();
            }
          }
          payload = await this.serializeEventStream({
            eventStream: _input[eventStreamMember],
            requestSchema: ns,
            initialRequest
          });
        }
      } else {
        serializer.write(schema, _input);
        payload = serializer.flush();
      }
    }
    request.headers = headers;
    request.query = query;
    request.body = payload;
    request.method = "POST";
    return request;
  }
  async deserializeResponse(operationSchema, context, response) {
    const deserializer = this.deserializer;
    const ns = import_schema3.NormalizedSchema.of(operationSchema.output);
    const dataObject = {};
    if (response.statusCode >= 300) {
      const bytes = await collectBody(response.body, context);
      if (bytes.byteLength > 0) {
        Object.assign(dataObject, await deserializer.read(import_schema3.SCHEMA.DOCUMENT, bytes));
      }
      await this.handleError(operationSchema, context, response, dataObject, this.deserializeMetadata(response));
      throw new Error("@smithy/core/protocols - RPC Protocol error handler failed to throw.");
    }
    for (const header in response.headers) {
      const value = response.headers[header];
      delete response.headers[header];
      response.headers[header.toLowerCase()] = value;
    }
    const eventStreamMember = ns.getEventStreamMember();
    if (eventStreamMember) {
      dataObject[eventStreamMember] = await this.deserializeEventStream({
        response,
        responseSchema: ns,
        initialResponseContainer: dataObject
      });
    } else {
      const bytes = await collectBody(response.body, context);
      if (bytes.byteLength > 0) {
        Object.assign(dataObject, await deserializer.read(ns, bytes));
      }
    }
    dataObject.$metadata = this.deserializeMetadata(response);
    return dataObject;
  }
};

// src/submodules/protocols/requestBuilder.ts
var import_protocol_http4 = require("@smithy/protocol-http");

// src/submodules/protocols/resolve-path.ts
var resolvedPath = (resolvedPath2, input, memberName, labelValueProvider, uriLabel, isGreedyLabel) => {
  if (input != null && input[memberName] !== void 0) {
    const labelValue = labelValueProvider();
    if (labelValue.length <= 0) {
      throw new Error("Empty value provided for input HTTP label: " + memberName + ".");
    }
    resolvedPath2 = resolvedPath2.replace(
      uriLabel,
      isGreedyLabel ? labelValue.split("/").map((segment) => extendedEncodeURIComponent(segment)).join("/") : extendedEncodeURIComponent(labelValue)
    );
  } else {
    throw new Error("No value provided for input HTTP label: " + memberName + ".");
  }
  return resolvedPath2;
};

// src/submodules/protocols/requestBuilder.ts
function requestBuilder(input, context) {
  return new RequestBuilder(input, context);
}
var RequestBuilder = class {
  constructor(input, context) {
    this.input = input;
    this.context = context;
    this.query = {};
    this.method = "";
    this.headers = {};
    this.path = "";
    this.body = null;
    this.hostname = "";
    this.resolvePathStack = [];
  }
  async build() {
    const { hostname, protocol = "https", port, path: basePath } = await this.context.endpoint();
    this.path = basePath;
    for (const resolvePath of this.resolvePathStack) {
      resolvePath(this.path);
    }
    return new import_protocol_http4.HttpRequest({
      protocol,
      hostname: this.hostname || hostname,
      port,
      method: this.method,
      path: this.path,
      query: this.query,
      body: this.body,
      headers: this.headers
    });
  }
  /**
   * Brevity setter for "hostname".
   */
  hn(hostname) {
    this.hostname = hostname;
    return this;
  }
  /**
   * Brevity initial builder for "basepath".
   */
  bp(uriLabel) {
    this.resolvePathStack.push((basePath) => {
      this.path = `${basePath?.endsWith("/") ? basePath.slice(0, -1) : basePath || ""}` + uriLabel;
    });
    return this;
  }
  /**
   * Brevity incremental builder for "path".
   */
  p(memberName, labelValueProvider, uriLabel, isGreedyLabel) {
    this.resolvePathStack.push((path) => {
      this.path = resolvedPath(path, this.input, memberName, labelValueProvider, uriLabel, isGreedyLabel);
    });
    return this;
  }
  /**
   * Brevity setter for "headers".
   */
  h(headers) {
    this.headers = headers;
    return this;
  }
  /**
   * Brevity setter for "query".
   */
  q(query) {
    this.query = query;
    return this;
  }
  /**
   * Brevity setter for "body".
   */
  b(body) {
    this.body = body;
    return this;
  }
  /**
   * Brevity setter for "method".
   */
  m(method) {
    this.method = method;
    return this;
  }
};

// src/submodules/protocols/serde/FromStringShapeDeserializer.ts
var import_schema5 = require("@smithy/core/schema");
var import_serde2 = require("@smithy/core/serde");
var import_util_base64 = require("@smithy/util-base64");
var import_util_utf8 = require("@smithy/util-utf8");

// src/submodules/protocols/serde/determineTimestampFormat.ts
var import_schema4 = require("@smithy/core/schema");
function determineTimestampFormat(ns, settings) {
  if (settings.timestampFormat.useTrait) {
    if (ns.isTimestampSchema() && (ns.getSchema() === import_schema4.SCHEMA.TIMESTAMP_DATE_TIME || ns.getSchema() === import_schema4.SCHEMA.TIMESTAMP_HTTP_DATE || ns.getSchema() === import_schema4.SCHEMA.TIMESTAMP_EPOCH_SECONDS)) {
      return ns.getSchema();
    }
  }
  const { httpLabel, httpPrefixHeaders, httpHeader, httpQuery } = ns.getMergedTraits();
  const bindingFormat = settings.httpBindings ? typeof httpPrefixHeaders === "string" || Boolean(httpHeader) ? import_schema4.SCHEMA.TIMESTAMP_HTTP_DATE : Boolean(httpQuery) || Boolean(httpLabel) ? import_schema4.SCHEMA.TIMESTAMP_DATE_TIME : void 0 : void 0;
  return bindingFormat ?? settings.timestampFormat.default;
}

// src/submodules/protocols/serde/FromStringShapeDeserializer.ts
var FromStringShapeDeserializer = class {
  constructor(settings) {
    this.settings = settings;
  }
  setSerdeContext(serdeContext) {
    this.serdeContext = serdeContext;
  }
  read(_schema, data) {
    const ns = import_schema5.NormalizedSchema.of(_schema);
    if (ns.isListSchema()) {
      return (0, import_serde2.splitHeader)(data).map((item) => this.read(ns.getValueSchema(), item));
    }
    if (ns.isBlobSchema()) {
      return (this.serdeContext?.base64Decoder ?? import_util_base64.fromBase64)(data);
    }
    if (ns.isTimestampSchema()) {
      const format = determineTimestampFormat(ns, this.settings);
      switch (format) {
        case import_schema5.SCHEMA.TIMESTAMP_DATE_TIME:
          return (0, import_serde2.parseRfc3339DateTimeWithOffset)(data);
        case import_schema5.SCHEMA.TIMESTAMP_HTTP_DATE:
          return (0, import_serde2.parseRfc7231DateTime)(data);
        case import_schema5.SCHEMA.TIMESTAMP_EPOCH_SECONDS:
          return (0, import_serde2.parseEpochTimestamp)(data);
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
          intermediateValue = import_serde2.LazyJsonString.from(intermediateValue);
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
        return new import_serde2.NumericValue(data, "bigDecimal");
      case ns.isBooleanSchema():
        return String(data).toLowerCase() === "true";
    }
    return data;
  }
  base64ToUtf8(base64String) {
    return (this.serdeContext?.utf8Encoder ?? import_util_utf8.toUtf8)((this.serdeContext?.base64Decoder ?? import_util_base64.fromBase64)(base64String));
  }
};

// src/submodules/protocols/serde/HttpInterceptingShapeDeserializer.ts
var import_schema6 = require("@smithy/core/schema");
var import_util_utf82 = require("@smithy/util-utf8");
var HttpInterceptingShapeDeserializer = class {
  constructor(codecDeserializer, codecSettings) {
    this.codecDeserializer = codecDeserializer;
    this.stringDeserializer = new FromStringShapeDeserializer(codecSettings);
  }
  setSerdeContext(serdeContext) {
    this.stringDeserializer.setSerdeContext(serdeContext);
    this.codecDeserializer.setSerdeContext(serdeContext);
    this.serdeContext = serdeContext;
  }
  read(schema, data) {
    const ns = import_schema6.NormalizedSchema.of(schema);
    const traits = ns.getMergedTraits();
    const toString = this.serdeContext?.utf8Encoder ?? import_util_utf82.toUtf8;
    if (traits.httpHeader || traits.httpResponseCode) {
      return this.stringDeserializer.read(ns, toString(data));
    }
    if (traits.httpPayload) {
      if (ns.isBlobSchema()) {
        const toBytes = this.serdeContext?.utf8Decoder ?? import_util_utf82.fromUtf8;
        if (typeof data === "string") {
          return toBytes(data);
        }
        return data;
      } else if (ns.isStringSchema()) {
        if ("byteLength" in data) {
          return toString(data);
        }
        return data;
      }
    }
    return this.codecDeserializer.read(ns, data);
  }
};

// src/submodules/protocols/serde/HttpInterceptingShapeSerializer.ts
var import_schema8 = require("@smithy/core/schema");

// src/submodules/protocols/serde/ToStringShapeSerializer.ts
var import_schema7 = require("@smithy/core/schema");
var import_serde3 = require("@smithy/core/serde");
var import_util_base642 = require("@smithy/util-base64");
var ToStringShapeSerializer = class {
  constructor(settings) {
    this.settings = settings;
    this.stringBuffer = "";
    this.serdeContext = void 0;
  }
  setSerdeContext(serdeContext) {
    this.serdeContext = serdeContext;
  }
  write(schema, value) {
    const ns = import_schema7.NormalizedSchema.of(schema);
    switch (typeof value) {
      case "object":
        if (value === null) {
          this.stringBuffer = "null";
          return;
        }
        if (ns.isTimestampSchema()) {
          if (!(value instanceof Date)) {
            throw new Error(
              `@smithy/core/protocols - received non-Date value ${value} when schema expected Date in ${ns.getName(
                true
              )}`
            );
          }
          const format = determineTimestampFormat(ns, this.settings);
          switch (format) {
            case import_schema7.SCHEMA.TIMESTAMP_DATE_TIME:
              this.stringBuffer = value.toISOString().replace(".000Z", "Z");
              break;
            case import_schema7.SCHEMA.TIMESTAMP_HTTP_DATE:
              this.stringBuffer = (0, import_serde3.dateToUtcString)(value);
              break;
            case import_schema7.SCHEMA.TIMESTAMP_EPOCH_SECONDS:
              this.stringBuffer = String(value.getTime() / 1e3);
              break;
            default:
              console.warn("Missing timestamp format, using epoch seconds", value);
              this.stringBuffer = String(value.getTime() / 1e3);
          }
          return;
        }
        if (ns.isBlobSchema() && "byteLength" in value) {
          this.stringBuffer = (this.serdeContext?.base64Encoder ?? import_util_base642.toBase64)(value);
          return;
        }
        if (ns.isListSchema() && Array.isArray(value)) {
          let buffer = "";
          for (const item of value) {
            this.write([ns.getValueSchema(), ns.getMergedTraits()], item);
            const headerItem = this.flush();
            const serialized = ns.getValueSchema().isTimestampSchema() ? headerItem : (0, import_serde3.quoteHeader)(headerItem);
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
            intermediateValue = import_serde3.LazyJsonString.from(intermediateValue);
          }
          if (ns.getMergedTraits().httpHeader) {
            this.stringBuffer = (this.serdeContext?.base64Encoder ?? import_util_base642.toBase64)(intermediateValue.toString());
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
};

// src/submodules/protocols/serde/HttpInterceptingShapeSerializer.ts
var HttpInterceptingShapeSerializer = class {
  constructor(codecSerializer, codecSettings, stringSerializer = new ToStringShapeSerializer(codecSettings)) {
    this.codecSerializer = codecSerializer;
    this.stringSerializer = stringSerializer;
  }
  setSerdeContext(serdeContext) {
    this.codecSerializer.setSerdeContext(serdeContext);
    this.stringSerializer.setSerdeContext(serdeContext);
  }
  write(schema, value) {
    const ns = import_schema8.NormalizedSchema.of(schema);
    const traits = ns.getMergedTraits();
    if (traits.httpHeader || traits.httpLabel || traits.httpQuery) {
      this.stringSerializer.write(ns, value);
      this.buffer = this.stringSerializer.flush();
      return;
    }
    return this.codecSerializer.write(ns, value);
  }
  flush() {
    if (this.buffer !== void 0) {
      const buffer = this.buffer;
      this.buffer = void 0;
      return buffer;
    }
    return this.codecSerializer.flush();
  }
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  FromStringShapeDeserializer,
  HttpBindingProtocol,
  HttpInterceptingShapeDeserializer,
  HttpInterceptingShapeSerializer,
  HttpProtocol,
  RequestBuilder,
  RpcProtocol,
  ToStringShapeSerializer,
  collectBody,
  determineTimestampFormat,
  extendedEncodeURIComponent,
  requestBuilder,
  resolvedPath
});
