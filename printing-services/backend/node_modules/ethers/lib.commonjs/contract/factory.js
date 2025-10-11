"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ContractFactory = void 0;
const index_js_1 = require("../abi/index.js");
const index_js_2 = require("../address/index.js");
const index_js_3 = require("../utils/index.js");
const contract_js_1 = require("./contract.js");
// A = Arguments to the constructor
// I = Interface of deployed contracts
/**
 *  A **ContractFactory** is used to deploy a Contract to the blockchain.
 */
class ContractFactory {
    /**
     *  The Contract Interface.
     */
    interface;
    /**
     *  The Contract deployment bytecode. Often called the initcode.
     */
    bytecode;
    /**
     *  The ContractRunner to deploy the Contract as.
     */
    runner;
    /**
     *  Create a new **ContractFactory** with %%abi%% and %%bytecode%%,
     *  optionally connected to %%runner%%.
     *
     *  The %%bytecode%% may be the ``bytecode`` property within the
     *  standard Solidity JSON output.
     */
    constructor(abi, bytecode, runner) {
        const iface = index_js_1.Interface.from(abi);
        // Dereference Solidity bytecode objects and allow a missing `0x`-prefix
        if (bytecode instanceof Uint8Array) {
            bytecode = (0, index_js_3.hexlify)((0, index_js_3.getBytes)(bytecode));
        }
        else {
            if (typeof (bytecode) === "object") {
                bytecode = bytecode.object;
            }
            if (!bytecode.startsWith("0x")) {
                bytecode = "0x" + bytecode;
            }
            bytecode = (0, index_js_3.hexlify)((0, index_js_3.getBytes)(bytecode));
        }
        (0, index_js_3.defineProperties)(this, {
            bytecode, interface: iface, runner: (runner || null)
        });
    }
    attach(target) {
        return new contract_js_1.BaseContract(target, this.interface, this.runner);
    }
    /**
     *  Resolves to the transaction to deploy the contract, passing %%args%%
     *  into the constructor.
     */
    async getDeployTransaction(...args) {
        let overrides = {};
        const fragment = this.interface.deploy;
        if (fragment.inputs.length + 1 === args.length) {
            overrides = await (0, contract_js_1.copyOverrides)(args.pop());
        }
        if (fragment.inputs.length !== args.length) {
            throw new Error("incorrect number of arguments to constructor");
        }
        const resolvedArgs = await (0, contract_js_1.resolveArgs)(this.runner, fragment.inputs, args);
        const data = (0, index_js_3.concat)([this.bytecode, this.interface.encodeDeploy(resolvedArgs)]);
        return Object.assign({}, overrides, { data });
    }
    /**
     *  Resolves to the Contract deployed by passing %%args%% into the
     *  constructor.
     *
     *  This will resolve to the Contract before it has been deployed to the
     *  network, so the [[BaseContract-waitForDeployment]] should be used before
     *  sending any transactions to it.
     */
    async deploy(...args) {
        const tx = await this.getDeployTransaction(...args);
        (0, index_js_3.assert)(this.runner && typeof (this.runner.sendTransaction) === "function", "factory runner does not support sending transactions", "UNSUPPORTED_OPERATION", {
            operation: "sendTransaction"
        });
        const sentTx = await this.runner.sendTransaction(tx);
        const address = (0, index_js_2.getCreateAddress)(sentTx);
        return new contract_js_1.BaseContract(address, this.interface, this.runner, sentTx);
    }
    /**
     *  Return a new **ContractFactory** with the same ABI and bytecode,
     *  but connected to %%runner%%.
     */
    connect(runner) {
        return new ContractFactory(this.interface, this.bytecode, runner);
    }
    /**
     *  Create a new **ContractFactory** from the standard Solidity JSON output.
     */
    static fromSolidity(output, runner) {
        (0, index_js_3.assertArgument)(output != null, "bad compiler output", "output", output);
        if (typeof (output) === "string") {
            output = JSON.parse(output);
        }
        const abi = output.abi;
        let bytecode = "";
        if (output.bytecode) {
            bytecode = output.bytecode;
        }
        else if (output.evm && output.evm.bytecode) {
            bytecode = output.evm.bytecode;
        }
        return new this(abi, bytecode, runner);
    }
}
exports.ContractFactory = ContractFactory;
//# sourceMappingURL=factory.js.map