import http from "http";
import https from "https";
import { gunzipSync } from "zlib";

import { assert, makeError } from "./errors.js";
import { getBytes } from "./data.js";

import type {
    FetchGetUrlFunc, FetchRequest, FetchCancelSignal, GetUrlResponse
} from "./fetch.js";

/**
 *  @_ignore:
 */
export function createGetUrl(options?: Record<string, any>): FetchGetUrlFunc {

    async function getUrl(req: FetchRequest, signal?: FetchCancelSignal): Promise<GetUrlResponse> {
        // Make sure we weren't cancelled before sending
        assert(signal == null || !signal.cancelled, "request cancelled before sending", "CANCELLED");

        const protocol = req.url.split(":")[0].toLowerCase();

        assert(protocol === "http" || protocol === "https", `unsupported protocol ${ protocol }`, "UNSUPPORTED_OPERATION", {
            info: { protocol },
            operation: "request"
        });

        assert(protocol === "https" || !req.credentials || req.allowInsecureAuthentication, "insecure authorized connections unsupported", "UNSUPPORTED_OPERATION", {
            operation: "request"
        });

        const method = req.method;
        const headers = Object.assign({ }, req.headers);

        const reqOptions: any = { method, headers };
        if (options) {
            if (options.agent) { reqOptions.agent = options.agent; }
        }

        // Create a Node-specific AbortController, if available
        let abort: null | AbortController = null;
        try {
            abort = new AbortController();
            reqOptions.abort = abort.signal;
        } catch (e) { console.log(e); }

        const request = ((protocol === "http") ? http: https).request(req.url, reqOptions);

        request.setTimeout(req.timeout);

        const body = req.body;
        if (body) { request.write(Buffer.from(body)); }

        request.end();

        return new Promise((resolve, reject) => {

            if (signal) {
                signal.addListener(() => {
                    if (abort) { abort.abort(); }
                    reject(makeError("request cancelled", "CANCELLED"));
                });
            }

            request.on("timeout", () => {
                reject(makeError("request timeout", "TIMEOUT"));
            });

            request.once("response", (resp: http.IncomingMessage) => {
                const statusCode = resp.statusCode || 0;
                const statusMessage = resp.statusMessage || "";
                const headers = Object.keys(resp.headers || {}).reduce((accum, name) => {
                    let value = resp.headers[name] || "";
                    if (Array.isArray(value)) {
                        value = value.join(", ");
                    }
                    accum[name] = value;
                    return accum;
                }, <{ [ name: string ]: string }>{ });

                let body: null | Uint8Array = null;
                //resp.setEncoding("utf8");

                resp.on("data", (chunk: Uint8Array) => {
                    if (signal) {
                        try {
                            signal.checkSignal();
                        } catch (error) {
                            return reject(error);
                        }
                    }

                    if (body == null) {
                        body = chunk;
                    } else {
                        const newBody = new Uint8Array(body.length + chunk.length);
                        newBody.set(body, 0);
                        newBody.set(chunk, body.length);
                        body = newBody;
                    }
                });

                resp.on("end", () => {
                    try {
                        if (headers["content-encoding"] === "gzip" && body) {
                            body = getBytes(gunzipSync(body));
                        }

                        resolve({ statusCode, statusMessage, headers, body });

                    } catch (error) {
                        reject(makeError("bad response data", "SERVER_ERROR", {
                            request: req, info: { response: resp, error }
                        }));
                    }
                });

                resp.on("error", (error) => {
                //@TODO: Should this just return nornal response with a server error?
                    (<any>error).response = { statusCode, statusMessage, headers, body };
                    reject(error);
                });
            });

            request.on("error", (error) => { reject(error); });
        });
    }

    return getUrl;
}

// @TODO: remove in v7; provided for backwards compat
const defaultGetUrl: FetchGetUrlFunc = createGetUrl({ });

/**
 *  @_ignore:
 */
export async function getUrl(req: FetchRequest, signal?: FetchCancelSignal): Promise<GetUrlResponse> {
    return defaultGetUrl(req, signal);
}

