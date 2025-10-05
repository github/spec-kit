/**
 *  ENS is a service which allows easy-to-remember names to map to
 *  network addresses.
 *
 *  @_section: api/providers/ens-resolver:ENS Resolver  [about-ens-rsolver]
 */
import { getAddress } from "../address/index.js";
import { ZeroAddress } from "../constants/index.js";
import { Contract } from "../contract/index.js";
import { dnsEncode, namehash } from "../hash/index.js";
import { hexlify, isHexString, toBeHex, defineProperties, encodeBase58, assert, assertArgument, isError, FetchRequest } from "../utils/index.js";
// @TODO: This should use the fetch-data:ipfs gateway
// Trim off the ipfs:// prefix and return the default gateway URL
function getIpfsLink(link) {
    if (link.match(/^ipfs:\/\/ipfs\//i)) {
        link = link.substring(12);
    }
    else if (link.match(/^ipfs:\/\//i)) {
        link = link.substring(7);
    }
    else {
        assertArgument(false, "unsupported IPFS format", "link", link);
    }
    return `https:/\/gateway.ipfs.io/ipfs/${link}`;
}
;
;
/**
 *  A provider plugin super-class for processing multicoin address types.
 */
export class MulticoinProviderPlugin {
    /**
     *  The name.
     */
    name;
    /**
     *  Creates a new **MulticoinProviderPluing** for %%name%%.
     */
    constructor(name) {
        defineProperties(this, { name });
    }
    connect(proivder) {
        return this;
    }
    /**
     *  Returns ``true`` if %%coinType%% is supported by this plugin.
     */
    supportsCoinType(coinType) {
        return false;
    }
    /**
     *  Resolves to the encoded %%address%% for %%coinType%%.
     */
    async encodeAddress(coinType, address) {
        throw new Error("unsupported coin");
    }
    /**
     *  Resolves to the decoded %%data%% for %%coinType%%.
     */
    async decodeAddress(coinType, data) {
        throw new Error("unsupported coin");
    }
}
const BasicMulticoinPluginId = "org.ethers.plugins.provider.BasicMulticoin";
/**
 *  A **BasicMulticoinProviderPlugin** provides service for common
 *  coin types, which do not require additional libraries to encode or
 *  decode.
 */
export class BasicMulticoinProviderPlugin extends MulticoinProviderPlugin {
    /**
     *  Creates a new **BasicMulticoinProviderPlugin**.
     */
    constructor() {
        super(BasicMulticoinPluginId);
    }
}
const matcherIpfs = new RegExp("^(ipfs):/\/(.*)$", "i");
const matchers = [
    new RegExp("^(https):/\/(.*)$", "i"),
    new RegExp("^(data):(.*)$", "i"),
    matcherIpfs,
    new RegExp("^eip155:[0-9]+/(erc[0-9]+):(.*)$", "i"),
];
/**
 *  A connected object to a resolved ENS name resolver, which can be
 *  used to query additional details.
 */
export class EnsResolver {
    /**
     *  The connected provider.
     */
    provider;
    /**
     *  The address of the resolver.
     */
    address;
    /**
     *  The name this resolver was resolved against.
     */
    name;
    // For EIP-2544 names, the ancestor that provided the resolver
    #supports2544;
    #resolver;
    constructor(provider, address, name) {
        defineProperties(this, { provider, address, name });
        this.#supports2544 = null;
        this.#resolver = new Contract(address, [
            "function supportsInterface(bytes4) view returns (bool)",
            "function resolve(bytes, bytes) view returns (bytes)",
            "function addr(bytes32) view returns (address)",
            "function addr(bytes32, uint) view returns (bytes)",
            "function text(bytes32, string) view returns (string)",
            "function contenthash(bytes32) view returns (bytes)",
        ], provider);
    }
    /**
     *  Resolves to true if the resolver supports wildcard resolution.
     */
    async supportsWildcard() {
        if (this.#supports2544 == null) {
            this.#supports2544 = (async () => {
                try {
                    return await this.#resolver.supportsInterface("0x9061b923");
                }
                catch (error) {
                    // Wildcard resolvers must understand supportsInterface
                    // and return true.
                    if (isError(error, "CALL_EXCEPTION")) {
                        return false;
                    }
                    // Let future attempts try again...
                    this.#supports2544 = null;
                    throw error;
                }
            })();
        }
        return await this.#supports2544;
    }
    async #fetch(funcName, params) {
        params = (params || []).slice();
        const iface = this.#resolver.interface;
        // The first parameters is always the nodehash
        params.unshift(namehash(this.name));
        let fragment = null;
        if (await this.supportsWildcard()) {
            fragment = iface.getFunction(funcName);
            assert(fragment, "missing fragment", "UNKNOWN_ERROR", {
                info: { funcName }
            });
            params = [
                dnsEncode(this.name, 255),
                iface.encodeFunctionData(fragment, params)
            ];
            funcName = "resolve(bytes,bytes)";
        }
        params.push({
            enableCcipRead: true
        });
        try {
            const result = await this.#resolver[funcName](...params);
            if (fragment) {
                return iface.decodeFunctionResult(fragment, result)[0];
            }
            return result;
        }
        catch (error) {
            if (!isError(error, "CALL_EXCEPTION")) {
                throw error;
            }
        }
        return null;
    }
    /**
     *  Resolves to the address for %%coinType%% or null if the
     *  provided %%coinType%% has not been configured.
     */
    async getAddress(coinType) {
        if (coinType == null) {
            coinType = 60;
        }
        if (coinType === 60) {
            try {
                const result = await this.#fetch("addr(bytes32)");
                // No address
                if (result == null || result === ZeroAddress) {
                    return null;
                }
                return result;
            }
            catch (error) {
                if (isError(error, "CALL_EXCEPTION")) {
                    return null;
                }
                throw error;
            }
        }
        // Try decoding its EVM canonical chain as an EVM chain address first
        if (coinType >= 0 && coinType < 0x80000000) {
            let ethCoinType = coinType + 0x80000000;
            const data = await this.#fetch("addr(bytes32,uint)", [ethCoinType]);
            if (isHexString(data, 20)) {
                return getAddress(data);
            }
        }
        let coinPlugin = null;
        for (const plugin of this.provider.plugins) {
            if (!(plugin instanceof MulticoinProviderPlugin)) {
                continue;
            }
            if (plugin.supportsCoinType(coinType)) {
                coinPlugin = plugin;
                break;
            }
        }
        if (coinPlugin == null) {
            return null;
        }
        // keccak256("addr(bytes32,uint256")
        const data = await this.#fetch("addr(bytes32,uint)", [coinType]);
        // No address
        if (data == null || data === "0x") {
            return null;
        }
        // Compute the address
        const address = await coinPlugin.decodeAddress(coinType, data);
        if (address != null) {
            return address;
        }
        assert(false, `invalid coin data`, "UNSUPPORTED_OPERATION", {
            operation: `getAddress(${coinType})`,
            info: { coinType, data }
        });
    }
    /**
     *  Resolves to the EIP-634 text record for %%key%%, or ``null``
     *  if unconfigured.
     */
    async getText(key) {
        const data = await this.#fetch("text(bytes32,string)", [key]);
        if (data == null || data === "0x") {
            return null;
        }
        return data;
    }
    /**
     *  Rsolves to the content-hash or ``null`` if unconfigured.
     */
    async getContentHash() {
        // keccak256("contenthash()")
        const data = await this.#fetch("contenthash(bytes32)");
        // No contenthash
        if (data == null || data === "0x") {
            return null;
        }
        // IPFS (CID: 1, Type: 70=DAG-PB, 72=libp2p-key)
        const ipfs = data.match(/^0x(e3010170|e5010172)(([0-9a-f][0-9a-f])([0-9a-f][0-9a-f])([0-9a-f]*))$/);
        if (ipfs) {
            const scheme = (ipfs[1] === "e3010170") ? "ipfs" : "ipns";
            const length = parseInt(ipfs[4], 16);
            if (ipfs[5].length === length * 2) {
                return `${scheme}:/\/${encodeBase58("0x" + ipfs[2])}`;
            }
        }
        // Swarm (CID: 1, Type: swarm-manifest; hash/length hard-coded to keccak256/32)
        const swarm = data.match(/^0xe40101fa011b20([0-9a-f]*)$/);
        if (swarm && swarm[1].length === 64) {
            return `bzz:/\/${swarm[1]}`;
        }
        assert(false, `invalid or unsupported content hash data`, "UNSUPPORTED_OPERATION", {
            operation: "getContentHash()",
            info: { data }
        });
    }
    /**
     *  Resolves to the avatar url or ``null`` if the avatar is either
     *  unconfigured or incorrectly configured (e.g. references an NFT
     *  not owned by the address).
     *
     *  If diagnosing issues with configurations, the [[_getAvatar]]
     *  method may be useful.
     */
    async getAvatar() {
        const avatar = await this._getAvatar();
        return avatar.url;
    }
    /**
     *  When resolving an avatar, there are many steps involved, such
     *  fetching metadata and possibly validating ownership of an
     *  NFT.
     *
     *  This method can be used to examine each step and the value it
     *  was working from.
     */
    async _getAvatar() {
        const linkage = [{ type: "name", value: this.name }];
        try {
            // test data for ricmoo.eth
            //const avatar = "eip155:1/erc721:0x265385c7f4132228A0d54EB1A9e7460b91c0cC68/29233";
            const avatar = await this.getText("avatar");
            if (avatar == null) {
                linkage.push({ type: "!avatar", value: "" });
                return { url: null, linkage };
            }
            linkage.push({ type: "avatar", value: avatar });
            for (let i = 0; i < matchers.length; i++) {
                const match = avatar.match(matchers[i]);
                if (match == null) {
                    continue;
                }
                const scheme = match[1].toLowerCase();
                switch (scheme) {
                    case "https":
                    case "data":
                        linkage.push({ type: "url", value: avatar });
                        return { linkage, url: avatar };
                    case "ipfs": {
                        const url = getIpfsLink(avatar);
                        linkage.push({ type: "ipfs", value: avatar });
                        linkage.push({ type: "url", value: url });
                        return { linkage, url };
                    }
                    case "erc721":
                    case "erc1155": {
                        // Depending on the ERC type, use tokenURI(uint256) or url(uint256)
                        const selector = (scheme === "erc721") ? "tokenURI(uint256)" : "uri(uint256)";
                        linkage.push({ type: scheme, value: avatar });
                        // The owner of this name
                        const owner = await this.getAddress();
                        if (owner == null) {
                            linkage.push({ type: "!owner", value: "" });
                            return { url: null, linkage };
                        }
                        const comps = (match[2] || "").split("/");
                        if (comps.length !== 2) {
                            linkage.push({ type: `!${scheme}caip`, value: (match[2] || "") });
                            return { url: null, linkage };
                        }
                        const tokenId = comps[1];
                        const contract = new Contract(comps[0], [
                            // ERC-721
                            "function tokenURI(uint) view returns (string)",
                            "function ownerOf(uint) view returns (address)",
                            // ERC-1155
                            "function uri(uint) view returns (string)",
                            "function balanceOf(address, uint256) view returns (uint)"
                        ], this.provider);
                        // Check that this account owns the token
                        if (scheme === "erc721") {
                            const tokenOwner = await contract.ownerOf(tokenId);
                            if (owner !== tokenOwner) {
                                linkage.push({ type: "!owner", value: tokenOwner });
                                return { url: null, linkage };
                            }
                            linkage.push({ type: "owner", value: tokenOwner });
                        }
                        else if (scheme === "erc1155") {
                            const balance = await contract.balanceOf(owner, tokenId);
                            if (!balance) {
                                linkage.push({ type: "!balance", value: "0" });
                                return { url: null, linkage };
                            }
                            linkage.push({ type: "balance", value: balance.toString() });
                        }
                        // Call the token contract for the metadata URL
                        let metadataUrl = await contract[selector](tokenId);
                        if (metadataUrl == null || metadataUrl === "0x") {
                            linkage.push({ type: "!metadata-url", value: "" });
                            return { url: null, linkage };
                        }
                        linkage.push({ type: "metadata-url-base", value: metadataUrl });
                        // ERC-1155 allows a generic {id} in the URL
                        if (scheme === "erc1155") {
                            metadataUrl = metadataUrl.replace("{id}", toBeHex(tokenId, 32).substring(2));
                            linkage.push({ type: "metadata-url-expanded", value: metadataUrl });
                        }
                        // Transform IPFS metadata links
                        if (metadataUrl.match(/^ipfs:/i)) {
                            metadataUrl = getIpfsLink(metadataUrl);
                        }
                        linkage.push({ type: "metadata-url", value: metadataUrl });
                        // Get the token metadata
                        let metadata = {};
                        const response = await (new FetchRequest(metadataUrl)).send();
                        response.assertOk();
                        try {
                            metadata = response.bodyJson;
                        }
                        catch (error) {
                            try {
                                linkage.push({ type: "!metadata", value: response.bodyText });
                            }
                            catch (error) {
                                const bytes = response.body;
                                if (bytes) {
                                    linkage.push({ type: "!metadata", value: hexlify(bytes) });
                                }
                                return { url: null, linkage };
                            }
                            return { url: null, linkage };
                        }
                        if (!metadata) {
                            linkage.push({ type: "!metadata", value: "" });
                            return { url: null, linkage };
                        }
                        linkage.push({ type: "metadata", value: JSON.stringify(metadata) });
                        // Pull the image URL out
                        let imageUrl = metadata.image;
                        if (typeof (imageUrl) !== "string") {
                            linkage.push({ type: "!imageUrl", value: "" });
                            return { url: null, linkage };
                        }
                        if (imageUrl.match(/^(https:\/\/|data:)/i)) {
                            // Allow
                        }
                        else {
                            // Transform IPFS link to gateway
                            const ipfs = imageUrl.match(matcherIpfs);
                            if (ipfs == null) {
                                linkage.push({ type: "!imageUrl-ipfs", value: imageUrl });
                                return { url: null, linkage };
                            }
                            linkage.push({ type: "imageUrl-ipfs", value: imageUrl });
                            imageUrl = getIpfsLink(imageUrl);
                        }
                        linkage.push({ type: "url", value: imageUrl });
                        return { linkage, url: imageUrl };
                    }
                }
            }
        }
        catch (error) { }
        return { linkage, url: null };
    }
    static async getEnsAddress(provider) {
        const network = await provider.getNetwork();
        const ensPlugin = network.getPlugin("org.ethers.plugins.network.Ens");
        // No ENS...
        assert(ensPlugin, "network does not support ENS", "UNSUPPORTED_OPERATION", {
            operation: "getEnsAddress", info: { network }
        });
        return ensPlugin.address;
    }
    static async #getResolver(provider, name) {
        const ensAddr = await EnsResolver.getEnsAddress(provider);
        try {
            const contract = new Contract(ensAddr, [
                "function resolver(bytes32) view returns (address)"
            ], provider);
            const addr = await contract.resolver(namehash(name), {
                enableCcipRead: true
            });
            if (addr === ZeroAddress) {
                return null;
            }
            return addr;
        }
        catch (error) {
            // ENS registry cannot throw errors on resolver(bytes32),
            // so probably a link error
            throw error;
        }
        return null;
    }
    /**
     *  Resolve to the ENS resolver for %%name%% using %%provider%% or
     *  ``null`` if unconfigured.
     */
    static async fromName(provider, name) {
        let currentName = name;
        while (true) {
            if (currentName === "" || currentName === ".") {
                return null;
            }
            // Optimization since the eth node cannot change and does
            // not have a wildcard resolver
            if (name !== "eth" && currentName === "eth") {
                return null;
            }
            // Check the current node for a resolver
            const addr = await EnsResolver.#getResolver(provider, currentName);
            // Found a resolver!
            if (addr != null) {
                const resolver = new EnsResolver(provider, addr, name);
                // Legacy resolver found, using EIP-2544 so it isn't safe to use
                if (currentName !== name && !(await resolver.supportsWildcard())) {
                    return null;
                }
                return resolver;
            }
            // Get the parent node
            currentName = currentName.split(".").slice(1).join(".");
        }
    }
}
//# sourceMappingURL=ens-resolver.js.map