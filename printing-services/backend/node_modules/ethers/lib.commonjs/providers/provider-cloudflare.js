"use strict";
/**
 *  About Cloudflare
 *
 *  @_subsection: api/providers/thirdparty:Cloudflare  [providers-cloudflare]
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.CloudflareProvider = void 0;
const index_js_1 = require("../utils/index.js");
const network_js_1 = require("./network.js");
const provider_jsonrpc_js_1 = require("./provider-jsonrpc.js");
/**
 *  About Cloudflare...
 */
class CloudflareProvider extends provider_jsonrpc_js_1.JsonRpcProvider {
    constructor(_network) {
        if (_network == null) {
            _network = "mainnet";
        }
        const network = network_js_1.Network.from(_network);
        (0, index_js_1.assertArgument)(network.name === "mainnet", "unsupported network", "network", _network);
        super("https:/\/cloudflare-eth.com/", network, { staticNetwork: network });
    }
}
exports.CloudflareProvider = CloudflareProvider;
//# sourceMappingURL=provider-cloudflare.js.map