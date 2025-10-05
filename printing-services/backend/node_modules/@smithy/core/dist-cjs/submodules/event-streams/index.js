var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
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
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/submodules/event-streams/index.ts
var index_exports = {};
__export(index_exports, {
  EventStreamSerde: () => EventStreamSerde
});
module.exports = __toCommonJS(index_exports);

// src/submodules/event-streams/EventStreamSerde.ts
var import_schema = require("@smithy/core/schema");
var import_util_utf8 = require("@smithy/util-utf8");
var EventStreamSerde = class {
  /**
   * Properties are injected by the HttpProtocol.
   */
  constructor({
    marshaller,
    serializer,
    deserializer,
    serdeContext,
    defaultContentType
  }) {
    this.marshaller = marshaller;
    this.serializer = serializer;
    this.deserializer = deserializer;
    this.serdeContext = serdeContext;
    this.defaultContentType = defaultContentType;
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
    const marshaller = this.marshaller;
    const eventStreamMember = requestSchema.getEventStreamMember();
    const unionSchema = requestSchema.getMemberSchema(eventStreamMember);
    const memberSchemas = unionSchema.getMemberSchemas();
    const serializer = this.serializer;
    const defaultContentType = this.defaultContentType;
    const initialRequestMarker = Symbol("initialRequestMarker");
    const eventStreamIterable = {
      async *[Symbol.asyncIterator]() {
        if (initialRequest) {
          const headers = {
            ":event-type": { type: "string", value: "initial-request" },
            ":message-type": { type: "string", value: "event" },
            ":content-type": { type: "string", value: defaultContentType }
          };
          serializer.write(requestSchema, initialRequest);
          const body = serializer.flush();
          yield {
            [initialRequestMarker]: true,
            headers,
            body
          };
        }
        for await (const page of eventStream) {
          yield page;
        }
      }
    };
    return marshaller.serialize(eventStreamIterable, (event) => {
      if (event[initialRequestMarker]) {
        return {
          headers: event.headers,
          body: event.body
        };
      }
      const unionMember = Object.keys(event).find((key) => {
        return key !== "__type";
      }) ?? "";
      const { additionalHeaders, body, eventType, explicitPayloadContentType } = this.writeEventBody(
        unionMember,
        unionSchema,
        event
      );
      const headers = {
        ":event-type": { type: "string", value: eventType },
        ":message-type": { type: "string", value: "event" },
        ":content-type": { type: "string", value: explicitPayloadContentType ?? defaultContentType },
        ...additionalHeaders
      };
      return {
        headers,
        body
      };
    });
  }
  /**
   * @param response - http response from which to read the event stream.
   * @param unionSchema - schema of the event stream container (struct).
   * @param [initialResponseContainer] - provided and written to only if the initial response is part of the event stream (RPC).
   *
   * @returns the asyncIterable of the event stream for the end-user.
   */
  async deserializeEventStream({
    response,
    responseSchema,
    initialResponseContainer
  }) {
    const marshaller = this.marshaller;
    const eventStreamMember = responseSchema.getEventStreamMember();
    const unionSchema = responseSchema.getMemberSchema(eventStreamMember);
    const memberSchemas = unionSchema.getMemberSchemas();
    const initialResponseMarker = Symbol("initialResponseMarker");
    const asyncIterable = marshaller.deserialize(response.body, async (event) => {
      const unionMember = Object.keys(event).find((key) => {
        return key !== "__type";
      }) ?? "";
      if (unionMember === "initial-response") {
        const dataObject = await this.deserializer.read(responseSchema, event[unionMember].body);
        delete dataObject[eventStreamMember];
        return {
          [initialResponseMarker]: true,
          ...dataObject
        };
      } else if (unionMember in memberSchemas) {
        const eventStreamSchema = memberSchemas[unionMember];
        return {
          [unionMember]: await this.deserializer.read(eventStreamSchema, event[unionMember].body)
        };
      } else {
        return {
          $unknown: event
        };
      }
    });
    const asyncIterator = asyncIterable[Symbol.asyncIterator]();
    const firstEvent = await asyncIterator.next();
    if (firstEvent.done) {
      return asyncIterable;
    }
    if (firstEvent.value?.[initialResponseMarker]) {
      if (!responseSchema) {
        throw new Error(
          "@smithy::core/protocols - initial-response event encountered in event stream but no response schema given."
        );
      }
      for (const [key, value] of Object.entries(firstEvent.value)) {
        initialResponseContainer[key] = value;
      }
    }
    return {
      async *[Symbol.asyncIterator]() {
        if (!firstEvent?.value?.[initialResponseMarker]) {
          yield firstEvent.value;
        }
        while (true) {
          const { done, value } = await asyncIterator.next();
          if (done) {
            break;
          }
          yield value;
        }
      }
    };
  }
  /**
   * @param unionMember - member name within the structure that contains an event stream union.
   * @param unionSchema - schema of the union.
   * @param event
   *
   * @returns the event body (bytes) and event type (string).
   */
  writeEventBody(unionMember, unionSchema, event) {
    const serializer = this.serializer;
    let eventType = unionMember;
    let explicitPayloadMember = null;
    let explicitPayloadContentType;
    const isKnownSchema = unionSchema.hasMemberSchema(unionMember);
    const additionalHeaders = {};
    if (!isKnownSchema) {
      const [type, value] = event[unionMember];
      eventType = type;
      serializer.write(import_schema.SCHEMA.DOCUMENT, value);
    } else {
      const eventSchema = unionSchema.getMemberSchema(unionMember);
      if (eventSchema.isStructSchema()) {
        for (const [memberName, memberSchema] of eventSchema.structIterator()) {
          const { eventHeader, eventPayload } = memberSchema.getMergedTraits();
          if (eventPayload) {
            explicitPayloadMember = memberName;
            break;
          } else if (eventHeader) {
            const value = event[unionMember][memberName];
            let type = "binary";
            if (memberSchema.isNumericSchema()) {
              if ((-2) ** 31 <= value && value <= 2 ** 31 - 1) {
                type = "integer";
              } else {
                type = "long";
              }
            } else if (memberSchema.isTimestampSchema()) {
              type = "timestamp";
            } else if (memberSchema.isStringSchema()) {
              type = "string";
            } else if (memberSchema.isBooleanSchema()) {
              type = "boolean";
            }
            if (value != null) {
              additionalHeaders[memberName] = {
                type,
                value
              };
              delete event[unionMember][memberName];
            }
          }
        }
        if (explicitPayloadMember !== null) {
          const payloadSchema = eventSchema.getMemberSchema(explicitPayloadMember);
          if (payloadSchema.isBlobSchema()) {
            explicitPayloadContentType = "application/octet-stream";
          } else if (payloadSchema.isStringSchema()) {
            explicitPayloadContentType = "text/plain";
          }
          serializer.write(payloadSchema, event[unionMember][explicitPayloadMember]);
        } else {
          serializer.write(eventSchema, event[unionMember]);
        }
      } else {
        throw new Error("@smithy/core/event-streams - non-struct member not supported in event stream union.");
      }
    }
    const messageSerialization = serializer.flush();
    const body = typeof messageSerialization === "string" ? (this.serdeContext?.utf8Decoder ?? import_util_utf8.fromUtf8)(messageSerialization) : messageSerialization;
    return {
      body,
      eventType,
      explicitPayloadContentType,
      additionalHeaders
    };
  }
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  EventStreamSerde
});
