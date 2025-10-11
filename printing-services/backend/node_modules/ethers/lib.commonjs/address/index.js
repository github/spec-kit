"use strict";
/**
 *  Addresses are a fundamental part of interacting with Ethereum. They
 *  represent the global identity of Externally Owned Accounts (accounts
 *  backed by a private key) and contracts.
 *
 *  The Ethereum Naming Service (ENS) provides an interconnected ecosystem
 *  of contracts, standards and libraries which enable looking up an
 *  address for an ENS name.
 *
 *  These functions help convert between various formats, validate
 *  addresses and safely resolve ENS names.
 *
 *  @_section: api/address:Addresses  [about-addresses]
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.resolveAddress = exports.isAddress = exports.isAddressable = exports.getCreate2Address = exports.getCreateAddress = exports.getIcapAddress = exports.getAddress = void 0;
null;
var address_js_1 = require("./address.js");
Object.defineProperty(exports, "getAddress", { enumerable: true, get: function () { return address_js_1.getAddress; } });
Object.defineProperty(exports, "getIcapAddress", { enumerable: true, get: function () { return address_js_1.getIcapAddress; } });
var contract_address_js_1 = require("./contract-address.js");
Object.defineProperty(exports, "getCreateAddress", { enumerable: true, get: function () { return contract_address_js_1.getCreateAddress; } });
Object.defineProperty(exports, "getCreate2Address", { enumerable: true, get: function () { return contract_address_js_1.getCreate2Address; } });
var checks_js_1 = require("./checks.js");
Object.defineProperty(exports, "isAddressable", { enumerable: true, get: function () { return checks_js_1.isAddressable; } });
Object.defineProperty(exports, "isAddress", { enumerable: true, get: function () { return checks_js_1.isAddress; } });
Object.defineProperty(exports, "resolveAddress", { enumerable: true, get: function () { return checks_js_1.resolveAddress; } });
//# sourceMappingURL=index.js.map