"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getUrl = exports.createGetUrl = void 0;
const tslib_1 = require("tslib");
const http_1 = tslib_1.__importDefault(require("http"));
const https_1 = tslib_1.__importDefault(require("https"));
const zlib_1 = require("zlib");
const errors_js_1 = require("./errors.js");
const data_js_1 = require("./data.js");
/**
 *  @_ignore:
 */
function createGetUrl(options) {
    async function getUrl(req, signal) {
        // Make sure we weren't cancelled before sending
        (0, errors_js_1.assert)(signal == null || !signal.cancelled, "request cancelled before sending", "CANCELLED");
        const protocol = req.url.split(":")[0].toLowerCase();
        (0, errors_js_1.assert)(protocol === "http" || protocol === "https", `unsupported protocol ${protocol}`, "UNSUPPORTED_OPERATION", {
            info: { protocol },
            operation: "request"
        });
        (0, errors_js_1.assert)(protocol === "https" || !req.credentials || req.allowInsecureAuthentication, "insecure authorized connections unsupported", "UNSUPPORTED_OPERATION", {
            operation: "request"
        });
        const method = req.method;
        const headers = Object.assign({}, req.headers);
        const reqOptions = { method, headers };
        if (options) {
            if (options.agent) {
                reqOptions.agent = options.agent;
            }
        }
        // Create a Node-specific AbortController, if available
        let abort = null;
        try {
            abort = new AbortController();
            reqOptions.abort = abort.signal;
        }
        catch (e) {
            console.log(e);
        }
        const request = ((protocol === "http") ? http_1.default : https_1.default).request(req.url, reqOptions);
        request.setTimeout(req.timeout);
        const body = req.body;
        if (body) {
            request.write(Buffer.from(body));
        }
        request.end();
        return new Promise((resolve, reject) => {
            if (signal) {
                signal.addListener(() => {
                    if (abort) {
                        abort.abort();
                    }
                    reject((0, errors_js_1.makeError)("request cancelled", "CANCELLED"));
                });
            }
            request.on("timeout", () => {
                reject((0, errors_js_1.makeError)("request timeout", "TIMEOUT"));
            });
            request.once("response", (resp) => {
                const statusCode = resp.statusCode || 0;
                const statusMessage = resp.statusMessage || "";
                const headers = Object.keys(resp.headers || {}).reduce((accum, name) => {
                    let value = resp.headers[name] || "";
                    if (Array.isArray(value)) {
                        value = value.join(", ");
                    }
                    accum[name] = value;
                    return accum;
                }, {});
                let body = null;
                //resp.setEncoding("utf8");
                resp.on("data", (chunk) => {
                    if (signal) {
                        try {
                            signal.checkSignal();
                        }
                        catch (error) {
                            return reject(error);
                        }
                    }
                    if (body == null) {
                        body = chunk;
                    }
                    else {
                        const newBody = new Uint8Array(body.length + chunk.length);
                        newBody.set(body, 0);
                        newBody.set(chunk, body.length);
                        body = newBody;
                    }
                });
                resp.on("end", () => {
                    try {
                        if (headers["content-encoding"] === "gzip" && body) {
                            body = (0, data_js_1.getBytes)((0, zlib_1.gunzipSync)(body));
                        }
                        resolve({ statusCode, statusMessage, headers, body });
                    }
                    catch (error) {
                        reject((0, errors_js_1.makeError)("bad response data", "SERVER_ERROR", {
                            request: req, info: { response: resp, error }
                        }));
                    }
                });
                resp.on("error", (error) => {
                    //@TODO: Should this just return nornal response with a server error?
                    error.response = { statusCode, statusMessage, headers, body };
                    reject(error);
                });
            });
            request.on("error", (error) => { reject(error); });
        });
    }
    return getUrl;
}
exports.createGetUrl = createGetUrl;
// @TODO: remove in v7; provided for backwards compat
const defaultGetUrl = createGetUrl({});
/**
 *  @_ignore:
 */
async function getUrl(req, signal) {
    return defaultGetUrl(req, signal);
}
exports.getUrl = getUrl;
//# sourceMappingURL=geturl.js.map