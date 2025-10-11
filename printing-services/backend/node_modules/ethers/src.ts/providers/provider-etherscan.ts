/**
 *  [[link-etherscan]] provides a third-party service for connecting to
 *  various blockchains over a combination of JSON-RPC and custom API
 *  endpoints.
 *
 *  **Supported Networks**
 *
 *  - Ethereum Mainnet (``mainnet``)
 *  - Goerli Testnet (``goerli``)
 *  - Sepolia Testnet (``sepolia``)
 *  - Holesky Testnet (``holesky``)
 *  - Arbitrum (``arbitrum``)
 *  - Arbitrum Goerli Testnet (``arbitrum-goerli``)
 *  - Base (``base``)
 *  - Base Sepolia Testnet (``base-sepolia``)
 *  - BNB Smart Chain Mainnet (``bnb``)
 *  - BNB Smart Chain Testnet (``bnbt``)
 *  - Optimism (``optimism``)
 *  - Optimism Goerli Testnet (``optimism-goerli``)
 *  - Polygon (``matic``)
 *  - Polygon Mumbai Testnet (``matic-mumbai``)
 *  - Polygon Amoy Testnet (``matic-amoy``)
 *
 *  @_subsection api/providers/thirdparty:Etherscan  [providers-etherscan]
 */

import { AbiCoder } from "../abi/index.js";
import { Contract } from "../contract/index.js";
import { accessListify, Transaction } from "../transaction/index.js";
import {
    defineProperties,
    hexlify, toQuantity,
    FetchRequest,
    assert, assertArgument, isError,
//    parseUnits,
    toUtf8String
 } from "../utils/index.js";

import { AbstractProvider } from "./abstract-provider.js";
import { Network } from "./network.js";
import { NetworkPlugin } from "./plugins-network.js";
import { showThrottleMessage } from "./community.js";

import { PerformActionRequest } from "./abstract-provider.js";
import type { Networkish } from "./network.js";
//import type { } from "./pagination";
import type { TransactionRequest } from "./provider.js";

const THROTTLE = 2000;

function isPromise<T = any>(value: any): value is Promise<T> {
    return (value && typeof(value.then) === "function");
}


/**
 *  When subscribing to the ``"debug"`` event on an Etherscan-based
 *  provider, the events receive a **DebugEventEtherscanProvider**
 *  payload.
 *
 *  @_docloc: api/providers/thirdparty:Etherscan
 */
export type DebugEventEtherscanProvider = {
    action: "sendRequest",
    id: number,
    url: string,
    payload: Record<string, any>
} | {
    action: "receiveRequest",
    id: number,
    result: any
} | {
    action: "receiveError",
    id: number,
    error: any
};

const EtherscanPluginId = "org.ethers.plugins.provider.Etherscan";

/**
 *  A Network can include an **EtherscanPlugin** to provide
 *  a custom base URL.
 *
 *  @_docloc: api/providers/thirdparty:Etherscan
 */
export class EtherscanPlugin extends NetworkPlugin {
    /**
     *  The Etherscan API base URL.
     */
    readonly baseUrl!: string;

    /**
     *  Creates a new **EtherscanProvider** which will use
     *  %%baseUrl%%.
     */
    constructor(baseUrl: string) {
        super(EtherscanPluginId);
        defineProperties<EtherscanPlugin>(this, { baseUrl });
    }

    clone(): EtherscanPlugin {
        return new EtherscanPlugin(this.baseUrl);
    }
}

const skipKeys = [ "enableCcipRead" ];

let nextId = 1;

/**
 *  The **EtherscanBaseProvider** is the super-class of
 *  [[EtherscanProvider]], which should generally be used instead.
 *
 *  Since the **EtherscanProvider** includes additional code for
 *  [[Contract]] access, in //rare cases// that contracts are not
 *  used, this class can reduce code size.
 *
 *  @_docloc: api/providers/thirdparty:Etherscan
 */
export class EtherscanProvider extends AbstractProvider {

    /**
     *  The connected network.
     */
    readonly network!: Network;

    /**
     *  The API key or null if using the community provided bandwidth.
     */
    readonly apiKey!: null | string;

    readonly #plugin: null | EtherscanPlugin;

    /**
     *  Creates a new **EtherscanBaseProvider**.
     */
    constructor(_network?: Networkish, _apiKey?: string) {
        const apiKey = (_apiKey != null) ? _apiKey: null;

        super();

        const network = Network.from(_network);

        this.#plugin = network.getPlugin<EtherscanPlugin>(EtherscanPluginId);

        defineProperties<EtherscanProvider>(this, { apiKey, network });
    }

    /**
     *  Returns the base URL.
     *
     *  If an [[EtherscanPlugin]] is configured on the
     *  [[EtherscanBaseProvider_network]], returns the plugin's
     *  baseUrl.
     *
     *  Deprecated; for Etherscan v2 the base is no longer a simply
     *  host, but instead a URL including a chainId parameter. Changing
     *  this to return a URL prefix could break some libraries, so it
     *  is left intact but will be removed in the future as it is unused.
     */
    getBaseUrl(): string {
        if (this.#plugin) { return this.#plugin.baseUrl; }

        switch(this.network.name) {
            case "mainnet":
                return "https:/\/api.etherscan.io";
            case "goerli":
                return "https:/\/api-goerli.etherscan.io";
            case "sepolia":
                return "https:/\/api-sepolia.etherscan.io";
            case "holesky":
                return "https:/\/api-holesky.etherscan.io";

            case "arbitrum":
                return "https:/\/api.arbiscan.io";
            case "arbitrum-goerli":
                return "https:/\/api-goerli.arbiscan.io";
           case "base":
                return "https:/\/api.basescan.org";
            case "base-sepolia":
                return "https:/\/api-sepolia.basescan.org";
            case "bnb":
                return "https:/\/api.bscscan.com";
            case "bnbt":
                return "https:/\/api-testnet.bscscan.com";
            case "matic":
                return "https:/\/api.polygonscan.com";
            case "matic-amoy":
                return "https:/\/api-amoy.polygonscan.com";
            case "matic-mumbai":
                return "https:/\/api-testnet.polygonscan.com";
            case "optimism":
                return "https:/\/api-optimistic.etherscan.io";
            case "optimism-goerli":
                return "https:/\/api-goerli-optimistic.etherscan.io";

            default:
        }

        assertArgument(false, "unsupported network", "network", this.network);
    }

    /**
     *  Returns the URL for the %%module%% and %%params%%.
     */
    getUrl(module: string, params: Record<string, string>): string {
        let query = Object.keys(params).reduce((accum, key) => {
            const value = params[key];
            if (value != null) {
                accum += `&${ key }=${ value }`
            }
            return accum
        }, "");
        if (this.apiKey) { query += `&apikey=${ this.apiKey }`; }
        return `https:/\/api.etherscan.io/v2/api?chainid=${ this.network.chainId }&module=${ module }${ query }`;
    }

    /**
     *  Returns the URL for using POST requests.
     */
    getPostUrl(): string {
        return `https:/\/api.etherscan.io/v2/api?chainid=${ this.network.chainId }`;
    }

    /**
     *  Returns the parameters for using POST requests.
     */
    getPostData(module: string, params: Record<string, any>): Record<string, any> {
        params.module = module;
        params.apikey = this.apiKey;
        params.chainid = this.network.chainId;
        return params;
    }

    async detectNetwork(): Promise<Network> {
        return this.network;
    }

    /**
     *  Resolves to the result of calling %%module%% with %%params%%.
     *
     *  If %%post%%, the request is made as a POST request.
     */
    async fetch(module: string, params: Record<string, any>, post?: boolean): Promise<any> {
        const id = nextId++;

        const url = (post ? this.getPostUrl(): this.getUrl(module, params));
        const payload = (post ? this.getPostData(module, params): null);

        this.emit("debug", { action: "sendRequest", id, url, payload: payload });

        const request = new FetchRequest(url);
        request.setThrottleParams({ slotInterval: 1000 });
        request.retryFunc = (req, resp, attempt: number) => {
            if (this.isCommunityResource()) {
                showThrottleMessage("Etherscan");
            }
            return Promise.resolve(true);
        };
        request.processFunc = async (request, response) => {
            const result = response.hasBody() ? JSON.parse(toUtf8String(response.body)): { };
            const throttle = ((typeof(result.result) === "string") ? result.result: "").toLowerCase().indexOf("rate limit") >= 0;
            if (module === "proxy") {
                // This JSON response indicates we are being throttled
                if (result && result.status == 0 && result.message == "NOTOK" && throttle) {
                    this.emit("debug", { action: "receiveError", id, reason: "proxy-NOTOK", error: result });
                    response.throwThrottleError(result.result, THROTTLE);
                }
            } else {
                if (throttle) {
                    this.emit("debug", { action: "receiveError", id, reason: "null result", error: result.result });
                    response.throwThrottleError(result.result, THROTTLE);
                }
            }
            return response;
        };

        if (payload) {
            request.setHeader("content-type", "application/x-www-form-urlencoded; charset=UTF-8");
            request.body = Object.keys(payload).map((k) => `${ k }=${ payload[k] }`).join("&");
        }

        const response = await request.send();
        try {
            response.assertOk();
        } catch (error) {
            this.emit("debug", { action: "receiveError", id, error, reason: "assertOk" });
            assert(false, "response error", "SERVER_ERROR", { request, response });
        }

        if (!response.hasBody()) {
            this.emit("debug", { action: "receiveError", id, error: "missing body", reason: "null body" });
            assert(false, "missing response", "SERVER_ERROR", { request, response });
        }

        const result = JSON.parse(toUtf8String(response.body));
        if (module === "proxy") {
            if (result.jsonrpc != "2.0") {
                this.emit("debug", { action: "receiveError", id, result, reason: "invalid JSON-RPC" });
                assert(false, "invalid JSON-RPC response (missing jsonrpc='2.0')", "SERVER_ERROR", { request, response, info: { result } });
            }

            if (result.error) {
                this.emit("debug", { action: "receiveError", id, result, reason: "JSON-RPC error" });
                assert(false, "error response", "SERVER_ERROR", { request, response, info: { result } });
            }

            this.emit("debug", { action: "receiveRequest", id, result });

            return result.result;

        } else {
            // getLogs, getHistory have weird success responses
            if (result.status == 0 && (result.message === "No records found" || result.message === "No transactions found")) {
                this.emit("debug", { action: "receiveRequest", id, result });
                return result.result;
            }

            if (result.status != 1 || (typeof(result.message) === "string" && !result.message.match(/^OK/))) {
                this.emit("debug", { action: "receiveError", id, result });
                assert(false, "error response", "SERVER_ERROR", { request, response, info: { result } });
            }

            this.emit("debug", { action: "receiveRequest", id, result });

            return result.result;
        }
    }

    /**
     *  Returns %%transaction%% normalized for the Etherscan API.
     */
    _getTransactionPostData(transaction: TransactionRequest): Record<string, string> {
        const result: Record<string, string> = { };
        for (let key in transaction) {
            if (skipKeys.indexOf(key) >= 0) { continue; }

            if ((<any>transaction)[key] == null) { continue; }
            let value = (<any>transaction)[key];
            if (key === "type" && value === 0) { continue; }
            if (key === "blockTag" && value === "latest") { continue; }

            // Quantity-types require no leading zero, unless 0
            if ((<any>{ type: true, gasLimit: true, gasPrice: true, maxFeePerGs: true, maxPriorityFeePerGas: true, nonce: true, value: true })[key]) {
                value = toQuantity(value);

            } else if (key === "accessList") {
                value = "[" + accessListify(value).map((set) => {
                    return `{address:"${ set.address }",storageKeys:["${ set.storageKeys.join('","') }"]}`;
                }).join(",") + "]";

            } else if (key === "blobVersionedHashes") {
                if (value.length === 0) { continue; }

                // @TODO: update this once the API supports blobs
                assert(false, "Etherscan API does not support blobVersionedHashes", "UNSUPPORTED_OPERATION", {
                    operation: "_getTransactionPostData",
                    info: { transaction }
                });

            } else {
                value = hexlify(value);
            }
            result[key] = value;
        }
        return result;
    }

    /**
     *  Throws the normalized Etherscan error.
     */
    _checkError(req: PerformActionRequest, error: Error, transaction: any): never {
        // Pull any message out if, possible
        let message = "";
        if (isError(error, "SERVER_ERROR")) {
            // Check for an error emitted by a proxy call
            try {
                message = (<any>error).info.result.error.message;
            } catch (e) { }

            if (!message) {
                try {
                    message = (<any>error).info.message;
                } catch (e) { }
            }
        }

        if (req.method === "estimateGas") {
            if (!message.match(/revert/i) && message.match(/insufficient funds/i)) {
                assert(false, "insufficient funds", "INSUFFICIENT_FUNDS", {
                    transaction: req.transaction
                });
            }
        }

        if (req.method === "call" || req.method === "estimateGas") {
            if (message.match(/execution reverted/i)) {
                let data = "";
                try {
                    data = (<any>error).info.result.error.data;
                } catch (error) { }

                const e = AbiCoder.getBuiltinCallException(req.method, <any>req.transaction, data);
                e.info = { request: req, error }
                throw e;
            }
        }

        if (message) {
            if (req.method === "broadcastTransaction") {
                const transaction = Transaction.from(req.signedTransaction);
                if (message.match(/replacement/i) && message.match(/underpriced/i)) {
                    assert(false, "replacement fee too low", "REPLACEMENT_UNDERPRICED", {
                        transaction
                    });
                }

                if (message.match(/insufficient funds/)) {
                    assert(false, "insufficient funds for intrinsic transaction cost", "INSUFFICIENT_FUNDS", {
                       transaction
                    });
                }

                if (message.match(/same hash was already imported|transaction nonce is too low|nonce too low/)) {
                    assert(false, "nonce has already been used", "NONCE_EXPIRED", {
                       transaction
                    });
                }
            }
        }

        // Something we could not process
        throw error;
    }

    async _detectNetwork(): Promise<Network> {
        return this.network;
    }

    async _perform(req: PerformActionRequest): Promise<any> {
        switch (req.method) {
            case "chainId":
                return this.network.chainId;

            case "getBlockNumber":
                return this.fetch("proxy", { action: "eth_blockNumber" });

            case "getGasPrice":
                return this.fetch("proxy", { action: "eth_gasPrice" });

            case "getPriorityFee":
                // This is temporary until Etherscan completes support
                if (this.network.name === "mainnet") {
                    return "1000000000";
                } else if (this.network.name === "optimism") {
                    return "1000000";
                } else {
                    throw new Error("fallback onto the AbstractProvider default");
                }
                /* Working with Etherscan to get this added:
                try {
                    const test = await this.fetch("proxy", {
                        action: "eth_maxPriorityFeePerGas"
                    });
                    console.log(test);
                    return test;
                } catch (e) {
                    console.log("DEBUG", e);
                    throw e;
                }
                */
                /* This might be safe; but due to rounding neither myself
                   or Etherscan are necessarily comfortable with this. :)
                try {
                    const result = await this.fetch("gastracker", { action: "gasoracle" });
                    console.log(result);
                    const gasPrice = parseUnits(result.SafeGasPrice, "gwei");
                    const baseFee = parseUnits(result.suggestBaseFee, "gwei");
                    const priorityFee = gasPrice - baseFee;
                    if (priorityFee < 0) { throw new Error("negative priority fee; defer to abstract provider default"); }
                    return priorityFee;
                } catch (error) {
                    console.log("DEBUG", error);
                    throw error;
                }
                */

            case "getBalance":
                // Returns base-10 result
                return this.fetch("account", {
                    action: "balance",
                    address: req.address,
                    tag: req.blockTag
                });

           case "getTransactionCount":
                return this.fetch("proxy", {
                    action: "eth_getTransactionCount",
                    address: req.address,
                    tag: req.blockTag
                });

            case "getCode":
                return this.fetch("proxy", {
                    action: "eth_getCode",
                    address: req.address,
                    tag: req.blockTag
                });

            case "getStorage":
                return this.fetch("proxy", {
                    action: "eth_getStorageAt",
                    address: req.address,
                    position: req.position,
                    tag: req.blockTag
                });

            case "broadcastTransaction":
                return this.fetch("proxy", {
                    action: "eth_sendRawTransaction",
                    hex: req.signedTransaction
                }, true).catch((error) => {
                    return this._checkError(req, <Error>error, req.signedTransaction);
                });

            case "getBlock":
                if ("blockTag" in req) {
                    return this.fetch("proxy", {
                        action: "eth_getBlockByNumber",
                        tag: req.blockTag,
                        boolean: (req.includeTransactions ? "true": "false")
                    });
                }

                assert(false, "getBlock by blockHash not supported by Etherscan", "UNSUPPORTED_OPERATION", {
                    operation: "getBlock(blockHash)"
                });

            case "getTransaction":
                return this.fetch("proxy", {
                    action: "eth_getTransactionByHash",
                    txhash: req.hash
                });

            case "getTransactionReceipt":
                return this.fetch("proxy", {
                    action: "eth_getTransactionReceipt",
                    txhash: req.hash
                });

            case "call": {
                if (req.blockTag !== "latest") {
                    throw new Error("EtherscanProvider does not support blockTag for call");
                }

                const postData = this._getTransactionPostData(req.transaction);
                postData.module = "proxy";
                postData.action = "eth_call";

                try {
                    return await this.fetch("proxy", postData, true);
                } catch (error) {
                    return this._checkError(req, <Error>error, req.transaction);
                }
            }

            case "estimateGas": {
                const postData = this._getTransactionPostData(req.transaction);
                postData.module = "proxy";
                postData.action = "eth_estimateGas";

                try {
                    return await this.fetch("proxy", postData, true);
                } catch (error) {
                    return this._checkError(req, <Error>error, req.transaction);
                }
            }
/*
            case "getLogs": {
                // Needs to complain if more than one address is passed in
                const args: Record<string, any> = { action: "getLogs" }

                if (params.filter.fromBlock) {
                    args.fromBlock = checkLogTag(params.filter.fromBlock);
                }

                if (params.filter.toBlock) {
                    args.toBlock = checkLogTag(params.filter.toBlock);
                }

                if (params.filter.address) {
                    args.address = params.filter.address;
                }

                // @TODO: We can handle slightly more complicated logs using the logs API
                if (params.filter.topics && params.filter.topics.length > 0) {
                    if (params.filter.topics.length > 1) {
                        logger.throwError("unsupported topic count", Logger.Errors.UNSUPPORTED_OPERATION, { topics: params.filter.topics });
                    }
                    if (params.filter.topics.length === 1) {
                        const topic0 = params.filter.topics[0];
                        if (typeof(topic0) !== "string" || topic0.length !== 66) {
                            logger.throwError("unsupported topic format", Logger.Errors.UNSUPPORTED_OPERATION, { topic0: topic0 });
                        }
                        args.topic0 = topic0;
                    }
                }

                const logs: Array<any> = await this.fetch("logs", args);

                // Cache txHash => blockHash
                let blocks: { [tag: string]: string } = {};

                // Add any missing blockHash to the logs
                for (let i = 0; i < logs.length; i++) {
                    const log = logs[i];
                    if (log.blockHash != null) { continue; }
                    if (blocks[log.blockNumber] == null) {
                        const block = await this.getBlock(log.blockNumber);
                        if (block) {
                            blocks[log.blockNumber] = block.hash;
                        }
                    }

                    log.blockHash = blocks[log.blockNumber];
                }

                return logs;
            }
*/
            default:
                break;
        }

        return super._perform(req);
    }

    async getNetwork(): Promise<Network> {
        return this.network;
    }

    /**
     *  Resolves to the current price of ether.
     *
     *  This returns ``0`` on any network other than ``mainnet``.
     */
    async getEtherPrice(): Promise<number> {
        if (this.network.name !== "mainnet") { return 0.0; }
        return parseFloat((await this.fetch("stats", { action: "ethprice" })).ethusd);
    }

    /**
     *  Resolves to a [Contract]] for %%address%%, using the
     *  Etherscan API to retreive the Contract ABI.
     */
    async getContract(_address: string): Promise<null | Contract> {
        let address = this._getAddress(_address);
        if (isPromise(address)) { address = await address; }

        try {
            const resp = await this.fetch("contract", {
            action: "getabi", address });
            const abi = JSON.parse(resp);
            return new Contract(address, abi, this);
        } catch (error) {
            return null;
        }
    }

    isCommunityResource(): boolean {
        return (this.apiKey == null);
    }
}
