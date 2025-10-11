//import { TypedDataDomain, TypedDataField } from "@ethersproject/providerabstract-signer";
import { getAddress } from "../address/index.js";
import { keccak256 } from "../crypto/index.js";
import { recoverAddress } from "../transaction/index.js";
import { concat, defineProperties, getBigInt, getBytes, hexlify, isHexString, mask, toBeHex, toQuantity, toTwos, zeroPadValue, assertArgument } from "../utils/index.js";
import { id } from "./id.js";
const padding = new Uint8Array(32);
padding.fill(0);
const BN__1 = BigInt(-1);
const BN_0 = BigInt(0);
const BN_1 = BigInt(1);
const BN_MAX_UINT256 = BigInt("0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff");
;
;
function hexPadRight(value) {
    const bytes = getBytes(value);
    const padOffset = bytes.length % 32;
    if (padOffset) {
        return concat([bytes, padding.slice(padOffset)]);
    }
    return hexlify(bytes);
}
const hexTrue = toBeHex(BN_1, 32);
const hexFalse = toBeHex(BN_0, 32);
const domainFieldTypes = {
    name: "string",
    version: "string",
    chainId: "uint256",
    verifyingContract: "address",
    salt: "bytes32"
};
const domainFieldNames = [
    "name", "version", "chainId", "verifyingContract", "salt"
];
function checkString(key) {
    return function (value) {
        assertArgument(typeof (value) === "string", `invalid domain value for ${JSON.stringify(key)}`, `domain.${key}`, value);
        return value;
    };
}
const domainChecks = {
    name: checkString("name"),
    version: checkString("version"),
    chainId: function (_value) {
        const value = getBigInt(_value, "domain.chainId");
        assertArgument(value >= 0, "invalid chain ID", "domain.chainId", _value);
        if (Number.isSafeInteger(value)) {
            return Number(value);
        }
        return toQuantity(value);
    },
    verifyingContract: function (value) {
        try {
            return getAddress(value).toLowerCase();
        }
        catch (error) { }
        assertArgument(false, `invalid domain value "verifyingContract"`, "domain.verifyingContract", value);
    },
    salt: function (value) {
        const bytes = getBytes(value, "domain.salt");
        assertArgument(bytes.length === 32, `invalid domain value "salt"`, "domain.salt", value);
        return hexlify(bytes);
    }
};
function getBaseEncoder(type) {
    // intXX and uintXX
    {
        const match = type.match(/^(u?)int(\d+)$/);
        if (match) {
            const signed = (match[1] === "");
            const width = parseInt(match[2]);
            assertArgument(width % 8 === 0 && width !== 0 && width <= 256 && match[2] === String(width), "invalid numeric width", "type", type);
            const boundsUpper = mask(BN_MAX_UINT256, signed ? (width - 1) : width);
            const boundsLower = signed ? ((boundsUpper + BN_1) * BN__1) : BN_0;
            return function (_value) {
                const value = getBigInt(_value, "value");
                assertArgument(value >= boundsLower && value <= boundsUpper, `value out-of-bounds for ${type}`, "value", value);
                return toBeHex(signed ? toTwos(value, 256) : value, 32);
            };
        }
    }
    // bytesXX
    {
        const match = type.match(/^bytes(\d+)$/);
        if (match) {
            const width = parseInt(match[1]);
            assertArgument(width !== 0 && width <= 32 && match[1] === String(width), "invalid bytes width", "type", type);
            return function (value) {
                const bytes = getBytes(value);
                assertArgument(bytes.length === width, `invalid length for ${type}`, "value", value);
                return hexPadRight(value);
            };
        }
    }
    switch (type) {
        case "address": return function (value) {
            return zeroPadValue(getAddress(value), 32);
        };
        case "bool": return function (value) {
            return ((!value) ? hexFalse : hexTrue);
        };
        case "bytes": return function (value) {
            return keccak256(value);
        };
        case "string": return function (value) {
            return id(value);
        };
    }
    return null;
}
function encodeType(name, fields) {
    return `${name}(${fields.map(({ name, type }) => (type + " " + name)).join(",")})`;
}
// foo[][3] => { base: "foo", index: "[][3]", array: {
//     base: "foo", prefix: "foo[]", count: 3 } }
function splitArray(type) {
    const match = type.match(/^([^\x5b]*)((\x5b\d*\x5d)*)(\x5b(\d*)\x5d)$/);
    if (match) {
        return {
            base: match[1],
            index: (match[2] + match[4]),
            array: {
                base: match[1],
                prefix: (match[1] + match[2]),
                count: (match[5] ? parseInt(match[5]) : -1),
            }
        };
    }
    return { base: type };
}
/**
 *  A **TypedDataEncode** prepares and encodes [[link-eip-712]] payloads
 *  for signed typed data.
 *
 *  This is useful for those that wish to compute various components of a
 *  typed data hash, primary types, or sub-components, but generally the
 *  higher level [[Signer-signTypedData]] is more useful.
 */
export class TypedDataEncoder {
    /**
     *  The primary type for the structured [[types]].
     *
     *  This is derived automatically from the [[types]], since no
     *  recursion is possible, once the DAG for the types is consturcted
     *  internally, the primary type must be the only remaining type with
     *  no parent nodes.
     */
    primaryType;
    #types;
    /**
     *  The types.
     */
    get types() {
        return JSON.parse(this.#types);
    }
    #fullTypes;
    #encoderCache;
    /**
     *  Create a new **TypedDataEncoder** for %%types%%.
     *
     *  This performs all necessary checking that types are valid and
     *  do not violate the [[link-eip-712]] structural constraints as
     *  well as computes the [[primaryType]].
     */
    constructor(_types) {
        this.#fullTypes = new Map();
        this.#encoderCache = new Map();
        // Link struct types to their direct child structs
        const links = new Map();
        // Link structs to structs which contain them as a child
        const parents = new Map();
        // Link all subtypes within a given struct
        const subtypes = new Map();
        const types = {};
        Object.keys(_types).forEach((type) => {
            types[type] = _types[type].map(({ name, type }) => {
                // Normalize the base type (unless name conflict)
                let { base, index } = splitArray(type);
                if (base === "int" && !_types["int"]) {
                    base = "int256";
                }
                if (base === "uint" && !_types["uint"]) {
                    base = "uint256";
                }
                return { name, type: (base + (index || "")) };
            });
            links.set(type, new Set());
            parents.set(type, []);
            subtypes.set(type, new Set());
        });
        this.#types = JSON.stringify(types);
        for (const name in types) {
            const uniqueNames = new Set();
            for (const field of types[name]) {
                // Check each field has a unique name
                assertArgument(!uniqueNames.has(field.name), `duplicate variable name ${JSON.stringify(field.name)} in ${JSON.stringify(name)}`, "types", _types);
                uniqueNames.add(field.name);
                // Get the base type (drop any array specifiers)
                const baseType = splitArray(field.type).base;
                assertArgument(baseType !== name, `circular type reference to ${JSON.stringify(baseType)}`, "types", _types);
                // Is this a base encoding type?
                const encoder = getBaseEncoder(baseType);
                if (encoder) {
                    continue;
                }
                assertArgument(parents.has(baseType), `unknown type ${JSON.stringify(baseType)}`, "types", _types);
                // Add linkage
                parents.get(baseType).push(name);
                links.get(name).add(baseType);
            }
        }
        // Deduce the primary type
        const primaryTypes = Array.from(parents.keys()).filter((n) => (parents.get(n).length === 0));
        assertArgument(primaryTypes.length !== 0, "missing primary type", "types", _types);
        assertArgument(primaryTypes.length === 1, `ambiguous primary types or unused types: ${primaryTypes.map((t) => (JSON.stringify(t))).join(", ")}`, "types", _types);
        defineProperties(this, { primaryType: primaryTypes[0] });
        // Check for circular type references
        function checkCircular(type, found) {
            assertArgument(!found.has(type), `circular type reference to ${JSON.stringify(type)}`, "types", _types);
            found.add(type);
            for (const child of links.get(type)) {
                if (!parents.has(child)) {
                    continue;
                }
                // Recursively check children
                checkCircular(child, found);
                // Mark all ancestors as having this decendant
                for (const subtype of found) {
                    subtypes.get(subtype).add(child);
                }
            }
            found.delete(type);
        }
        checkCircular(this.primaryType, new Set());
        // Compute each fully describe type
        for (const [name, set] of subtypes) {
            const st = Array.from(set);
            st.sort();
            this.#fullTypes.set(name, encodeType(name, types[name]) + st.map((t) => encodeType(t, types[t])).join(""));
        }
    }
    /**
     *  Returnthe encoder for the specific %%type%%.
     */
    getEncoder(type) {
        let encoder = this.#encoderCache.get(type);
        if (!encoder) {
            encoder = this.#getEncoder(type);
            this.#encoderCache.set(type, encoder);
        }
        return encoder;
    }
    #getEncoder(type) {
        // Basic encoder type (address, bool, uint256, etc)
        {
            const encoder = getBaseEncoder(type);
            if (encoder) {
                return encoder;
            }
        }
        // Array
        const array = splitArray(type).array;
        if (array) {
            const subtype = array.prefix;
            const subEncoder = this.getEncoder(subtype);
            return (value) => {
                assertArgument(array.count === -1 || array.count === value.length, `array length mismatch; expected length ${array.count}`, "value", value);
                let result = value.map(subEncoder);
                if (this.#fullTypes.has(subtype)) {
                    result = result.map(keccak256);
                }
                return keccak256(concat(result));
            };
        }
        // Struct
        const fields = this.types[type];
        if (fields) {
            const encodedType = id(this.#fullTypes.get(type));
            return (value) => {
                const values = fields.map(({ name, type }) => {
                    const result = this.getEncoder(type)(value[name]);
                    if (this.#fullTypes.has(type)) {
                        return keccak256(result);
                    }
                    return result;
                });
                values.unshift(encodedType);
                return concat(values);
            };
        }
        assertArgument(false, `unknown type: ${type}`, "type", type);
    }
    /**
     *  Return the full type for %%name%%.
     */
    encodeType(name) {
        const result = this.#fullTypes.get(name);
        assertArgument(result, `unknown type: ${JSON.stringify(name)}`, "name", name);
        return result;
    }
    /**
     *  Return the encoded %%value%% for the %%type%%.
     */
    encodeData(type, value) {
        return this.getEncoder(type)(value);
    }
    /**
     *  Returns the hash of %%value%% for the type of %%name%%.
     */
    hashStruct(name, value) {
        return keccak256(this.encodeData(name, value));
    }
    /**
     *  Return the fulled encoded %%value%% for the [[types]].
     */
    encode(value) {
        return this.encodeData(this.primaryType, value);
    }
    /**
     *  Return the hash of the fully encoded %%value%% for the [[types]].
     */
    hash(value) {
        return this.hashStruct(this.primaryType, value);
    }
    /**
     *  @_ignore:
     */
    _visit(type, value, callback) {
        // Basic encoder type (address, bool, uint256, etc)
        {
            const encoder = getBaseEncoder(type);
            if (encoder) {
                return callback(type, value);
            }
        }
        // Array
        const array = splitArray(type).array;
        if (array) {
            assertArgument(array.count === -1 || array.count === value.length, `array length mismatch; expected length ${array.count}`, "value", value);
            return value.map((v) => this._visit(array.prefix, v, callback));
        }
        // Struct
        const fields = this.types[type];
        if (fields) {
            return fields.reduce((accum, { name, type }) => {
                accum[name] = this._visit(type, value[name], callback);
                return accum;
            }, {});
        }
        assertArgument(false, `unknown type: ${type}`, "type", type);
    }
    /**
     *  Call %%calback%% for each value in %%value%%, passing the type and
     *  component within %%value%%.
     *
     *  This is useful for replacing addresses or other transformation that
     *  may be desired on each component, based on its type.
     */
    visit(value, callback) {
        return this._visit(this.primaryType, value, callback);
    }
    /**
     *  Create a new **TypedDataEncoder** for %%types%%.
     */
    static from(types) {
        return new TypedDataEncoder(types);
    }
    /**
     *  Return the primary type for %%types%%.
     */
    static getPrimaryType(types) {
        return TypedDataEncoder.from(types).primaryType;
    }
    /**
     *  Return the hashed struct for %%value%% using %%types%% and %%name%%.
     */
    static hashStruct(name, types, value) {
        return TypedDataEncoder.from(types).hashStruct(name, value);
    }
    /**
     *  Return the domain hash for %%domain%%.
     */
    static hashDomain(domain) {
        const domainFields = [];
        for (const name in domain) {
            if (domain[name] == null) {
                continue;
            }
            const type = domainFieldTypes[name];
            assertArgument(type, `invalid typed-data domain key: ${JSON.stringify(name)}`, "domain", domain);
            domainFields.push({ name, type });
        }
        domainFields.sort((a, b) => {
            return domainFieldNames.indexOf(a.name) - domainFieldNames.indexOf(b.name);
        });
        return TypedDataEncoder.hashStruct("EIP712Domain", { EIP712Domain: domainFields }, domain);
    }
    /**
     *  Return the fully encoded [[link-eip-712]] %%value%% for %%types%% with %%domain%%.
     */
    static encode(domain, types, value) {
        return concat([
            "0x1901",
            TypedDataEncoder.hashDomain(domain),
            TypedDataEncoder.from(types).hash(value)
        ]);
    }
    /**
     *  Return the hash of the fully encoded [[link-eip-712]] %%value%% for %%types%% with %%domain%%.
     */
    static hash(domain, types, value) {
        return keccak256(TypedDataEncoder.encode(domain, types, value));
    }
    // Replaces all address types with ENS names with their looked up address
    /**
     * Resolves to the value from resolving all addresses in %%value%% for
     * %%types%% and the %%domain%%.
     */
    static async resolveNames(domain, types, value, resolveName) {
        // Make a copy to isolate it from the object passed in
        domain = Object.assign({}, domain);
        // Allow passing null to ignore value
        for (const key in domain) {
            if (domain[key] == null) {
                delete domain[key];
            }
        }
        // Look up all ENS names
        const ensCache = {};
        // Do we need to look up the domain's verifyingContract?
        if (domain.verifyingContract && !isHexString(domain.verifyingContract, 20)) {
            ensCache[domain.verifyingContract] = "0x";
        }
        // We are going to use the encoder to visit all the base values
        const encoder = TypedDataEncoder.from(types);
        // Get a list of all the addresses
        encoder.visit(value, (type, value) => {
            if (type === "address" && !isHexString(value, 20)) {
                ensCache[value] = "0x";
            }
            return value;
        });
        // Lookup each name
        for (const name in ensCache) {
            ensCache[name] = await resolveName(name);
        }
        // Replace the domain verifyingContract if needed
        if (domain.verifyingContract && ensCache[domain.verifyingContract]) {
            domain.verifyingContract = ensCache[domain.verifyingContract];
        }
        // Replace all ENS names with their address
        value = encoder.visit(value, (type, value) => {
            if (type === "address" && ensCache[value]) {
                return ensCache[value];
            }
            return value;
        });
        return { domain, value };
    }
    /**
     *  Returns the JSON-encoded payload expected by nodes which implement
     *  the JSON-RPC [[link-eip-712]] method.
     */
    static getPayload(domain, types, value) {
        // Validate the domain fields
        TypedDataEncoder.hashDomain(domain);
        // Derive the EIP712Domain Struct reference type
        const domainValues = {};
        const domainTypes = [];
        domainFieldNames.forEach((name) => {
            const value = domain[name];
            if (value == null) {
                return;
            }
            domainValues[name] = domainChecks[name](value);
            domainTypes.push({ name, type: domainFieldTypes[name] });
        });
        const encoder = TypedDataEncoder.from(types);
        // Get the normalized types
        types = encoder.types;
        const typesWithDomain = Object.assign({}, types);
        assertArgument(typesWithDomain.EIP712Domain == null, "types must not contain EIP712Domain type", "types.EIP712Domain", types);
        typesWithDomain.EIP712Domain = domainTypes;
        // Validate the data structures and types
        encoder.encode(value);
        return {
            types: typesWithDomain,
            domain: domainValues,
            primaryType: encoder.primaryType,
            message: encoder.visit(value, (type, value) => {
                // bytes
                if (type.match(/^bytes(\d*)/)) {
                    return hexlify(getBytes(value));
                }
                // uint or int
                if (type.match(/^u?int/)) {
                    return getBigInt(value).toString();
                }
                switch (type) {
                    case "address":
                        return value.toLowerCase();
                    case "bool":
                        return !!value;
                    case "string":
                        assertArgument(typeof (value) === "string", "invalid string", "value", value);
                        return value;
                }
                assertArgument(false, "unsupported type", "type", type);
            })
        };
    }
}
/**
 *  Compute the address used to sign the typed data for the %%signature%%.
 */
export function verifyTypedData(domain, types, value, signature) {
    return recoverAddress(TypedDataEncoder.hash(domain, types, value), signature);
}
//# sourceMappingURL=typed-data.js.map