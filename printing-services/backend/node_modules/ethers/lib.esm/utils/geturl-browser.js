import { assert, makeError } from "./errors.js";
export function createGetUrl(options) {
    async function getUrl(req, _signal) {
        assert(_signal == null || !_signal.cancelled, "request cancelled before sending", "CANCELLED");
        const protocol = req.url.split(":")[0].toLowerCase();
        assert(protocol === "http" || protocol === "https", `unsupported protocol ${protocol}`, "UNSUPPORTED_OPERATION", {
            info: { protocol },
            operation: "request"
        });
        assert(protocol === "https" || !req.credentials || req.allowInsecureAuthentication, "insecure authorized connections unsupported", "UNSUPPORTED_OPERATION", {
            operation: "request"
        });
        let error = null;
        const controller = new AbortController();
        const timer = setTimeout(() => {
            error = makeError("request timeout", "TIMEOUT");
            controller.abort();
        }, req.timeout);
        if (_signal) {
            _signal.addListener(() => {
                error = makeError("request cancelled", "CANCELLED");
                controller.abort();
            });
        }
        const init = Object.assign({}, options, {
            method: req.method,
            headers: new Headers(Array.from(req)),
            body: req.body || undefined,
            signal: controller.signal
        });
        let resp;
        try {
            resp = await fetch(req.url, init);
        }
        catch (_error) {
            clearTimeout(timer);
            if (error) {
                throw error;
            }
            throw _error;
        }
        clearTimeout(timer);
        const headers = {};
        resp.headers.forEach((value, key) => {
            headers[key.toLowerCase()] = value;
        });
        const respBody = await resp.arrayBuffer();
        const body = (respBody == null) ? null : new Uint8Array(respBody);
        return {
            statusCode: resp.status,
            statusMessage: resp.statusText,
            headers, body
        };
    }
    return getUrl;
}
// @TODO: remove in v7; provided for backwards compat
const defaultGetUrl = createGetUrl({});
export async function getUrl(req, _signal) {
    return defaultGetUrl(req, _signal);
}
//# sourceMappingURL=geturl-browser.js.map