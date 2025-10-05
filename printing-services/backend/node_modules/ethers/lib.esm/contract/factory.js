import { Interface } from "../abi/index.js";
import { getCreateAddress } from "../address/index.js";
import { concat, defineProperties, getBytes, hexlify, assert, assertArgument } from "../utils/index.js";
import { BaseContract, copyOverrides, resolveArgs } from "./contract.js";
// A = Arguments to the constructor
// I = Interface of deployed contracts
/**
 *  A **ContractFactory** is used to deploy a Contract to the blockchain.
 */
export class ContractFactory {
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
        const iface = Interface.from(abi);
        // Dereference Solidity bytecode objects and allow a missing `0x`-prefix
        if (bytecode instanceof Uint8Array) {
            bytecode = hexlify(getBytes(bytecode));
        }
        else {
            if (typeof (bytecode) === "object") {
                bytecode = bytecode.object;
            }
            if (!bytecode.startsWith("0x")) {
                bytecode = "0x" + bytecode;
            }
            bytecode = hexlify(getBytes(bytecode));
        }
        defineProperties(this, {
            bytecode, interface: iface, runner: (runner || null)
        });
    }
    attach(target) {
        return new BaseContract(target, this.interface, this.runner);
    }
    /**
     *  Resolves to the transaction to deploy the contract, passing %%args%%
     *  into the constructor.
     */
    async getDeployTransaction(...args) {
        let overrides = {};
        const fragment = this.interface.deploy;
        if (fragment.inputs.length + 1 === args.length) {
            overrides = await copyOverrides(args.pop());
        }
        if (fragment.inputs.length !== args.length) {
            throw new Error("incorrect number of arguments to constructor");
        }
        const resolvedArgs = await resolveArgs(this.runner, fragment.inputs, args);
        const data = concat([this.bytecode, this.interface.encodeDeploy(resolvedArgs)]);
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
        assert(this.runner && typeof (this.runner.sendTransaction) === "function", "factory runner does not support sending transactions", "UNSUPPORTED_OPERATION", {
            operation: "sendTransaction"
        });
        const sentTx = await this.runner.sendTransaction(tx);
        const address = getCreateAddress(sentTx);
        return new BaseContract(address, this.interface, this.runner, sentTx);
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
        assertArgument(output != null, "bad compiler output", "output", output);
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
//# sourceMappingURL=factory.js.map