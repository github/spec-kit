"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getCreate2Address = exports.getCreateAddress = void 0;
const index_js_1 = require("../crypto/index.js");
const index_js_2 = require("../utils/index.js");
const address_js_1 = require("./address.js");
// http://ethereum.stackexchange.com/questions/760/how-is-the-address-of-an-ethereum-contract-computed
/**
 *  Returns the address that would result from a ``CREATE`` for %%tx%%.
 *
 *  This can be used to compute the address a contract will be
 *  deployed to by an EOA when sending a deployment transaction (i.e.
 *  when the ``to`` address is ``null``).
 *
 *  This can also be used to compute the address a contract will be
 *  deployed to by a contract, by using the contract's address as the
 *  ``to`` and the contract's nonce.
 *
 *  @example
 *    from = "0x8ba1f109551bD432803012645Ac136ddd64DBA72";
 *    nonce = 5;
 *
 *    getCreateAddress({ from, nonce });
 *    //_result:
 */
function getCreateAddress(tx) {
    const from = (0, address_js_1.getAddress)(tx.from);
    const nonce = (0, index_js_2.getBigInt)(tx.nonce, "tx.nonce");
    let nonceHex = nonce.toString(16);
    if (nonceHex === "0") {
        nonceHex = "0x";
    }
    else if (nonceHex.length % 2) {
        nonceHex = "0x0" + nonceHex;
    }
    else {
        nonceHex = "0x" + nonceHex;
    }
    return (0, address_js_1.getAddress)((0, index_js_2.dataSlice)((0, index_js_1.keccak256)((0, index_js_2.encodeRlp)([from, nonceHex])), 12));
}
exports.getCreateAddress = getCreateAddress;
/**
 *  Returns the address that would result from a ``CREATE2`` operation
 *  with the given %%from%%, %%salt%% and %%initCodeHash%%.
 *
 *  To compute the %%initCodeHash%% from a contract's init code, use
 *  the [[keccak256]] function.
 *
 *  For a quick overview and example of ``CREATE2``, see [[link-ricmoo-wisps]].
 *
 *  @example
 *    // The address of the contract
 *    from = "0x8ba1f109551bD432803012645Ac136ddd64DBA72"
 *
 *    // The salt
 *    salt = id("HelloWorld")
 *
 *    // The hash of the initCode
 *    initCode = "0x6394198df16000526103ff60206004601c335afa6040516060f3";
 *    initCodeHash = keccak256(initCode)
 *
 *    getCreate2Address(from, salt, initCodeHash)
 *    //_result:
 */
function getCreate2Address(_from, _salt, _initCodeHash) {
    const from = (0, address_js_1.getAddress)(_from);
    const salt = (0, index_js_2.getBytes)(_salt, "salt");
    const initCodeHash = (0, index_js_2.getBytes)(_initCodeHash, "initCodeHash");
    (0, index_js_2.assertArgument)(salt.length === 32, "salt must be 32 bytes", "salt", _salt);
    (0, index_js_2.assertArgument)(initCodeHash.length === 32, "initCodeHash must be 32 bytes", "initCodeHash", _initCodeHash);
    return (0, address_js_1.getAddress)((0, index_js_2.dataSlice)((0, index_js_1.keccak256)((0, index_js_2.concat)(["0xff", from, salt, initCodeHash])), 12));
}
exports.getCreate2Address = getCreate2Address;
//# sourceMappingURL=contract-address.js.map