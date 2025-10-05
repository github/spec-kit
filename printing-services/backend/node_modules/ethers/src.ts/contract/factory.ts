
import { Interface } from "../abi/index.js";
import { getCreateAddress } from "../address/index.js";
import {
    concat, defineProperties, getBytes, hexlify,
    assert, assertArgument
} from "../utils/index.js";

import { BaseContract, copyOverrides, resolveArgs } from "./contract.js";

import type { InterfaceAbi } from "../abi/index.js";
import type { Addressable } from "../address/index.js";
import type { ContractRunner } from "../providers/index.js";
import type { BytesLike } from "../utils/index.js";

import type {
    ContractInterface, ContractMethodArgs, ContractDeployTransaction,
} from "./types.js";
import type { ContractTransactionResponse } from "./wrappers.js";


// A = Arguments to the constructor
// I = Interface of deployed contracts

/**
 *  A **ContractFactory** is used to deploy a Contract to the blockchain.
 */
export class ContractFactory<A extends Array<any> = Array<any>, I = BaseContract> {

    /**
     *  The Contract Interface.
     */
    readonly interface!: Interface;

    /**
     *  The Contract deployment bytecode. Often called the initcode.
     */
    readonly bytecode!: string;

    /**
     *  The ContractRunner to deploy the Contract as.
     */
    readonly runner!: null | ContractRunner;

    /**
     *  Create a new **ContractFactory** with %%abi%% and %%bytecode%%,
     *  optionally connected to %%runner%%.
     *
     *  The %%bytecode%% may be the ``bytecode`` property within the
     *  standard Solidity JSON output.
     */
    constructor(abi: Interface | InterfaceAbi, bytecode: BytesLike | { object: string }, runner?: null | ContractRunner) {
        const iface = Interface.from(abi);

        // Dereference Solidity bytecode objects and allow a missing `0x`-prefix
        if (bytecode instanceof Uint8Array) {
            bytecode = hexlify(getBytes(bytecode));
        } else {
            if (typeof(bytecode) === "object") { bytecode = bytecode.object; }
            if (!bytecode.startsWith("0x")) { bytecode = "0x" + bytecode; }
            bytecode = hexlify(getBytes(bytecode));
        }

        defineProperties<ContractFactory>(this, {
            bytecode, interface: iface, runner: (runner || null)
        });
    }

    attach(target: string | Addressable): BaseContract & Omit<I, keyof BaseContract> {
        return new (<any>BaseContract)(target, this.interface, this.runner);
    }

    /**
     *  Resolves to the transaction to deploy the contract, passing %%args%%
     *  into the constructor.
     */
    async getDeployTransaction(...args: ContractMethodArgs<A>): Promise<ContractDeployTransaction> {
        let overrides: Omit<ContractDeployTransaction, "data"> = { };

        const fragment = this.interface.deploy;

        if (fragment.inputs.length + 1 === args.length) {
            overrides = await copyOverrides(args.pop());
        }

        if (fragment.inputs.length !== args.length) {
            throw new Error("incorrect number of arguments to constructor");
        }

        const resolvedArgs = await resolveArgs(this.runner, fragment.inputs, args);

        const data = concat([ this.bytecode, this.interface.encodeDeploy(resolvedArgs) ]);
        return Object.assign({ }, overrides, { data });
    }

    /**
     *  Resolves to the Contract deployed by passing %%args%% into the
     *  constructor.
     *
     *  This will resolve to the Contract before it has been deployed to the
     *  network, so the [[BaseContract-waitForDeployment]] should be used before
     *  sending any transactions to it.
     */
    async deploy(...args: ContractMethodArgs<A>): Promise<BaseContract & { deploymentTransaction(): ContractTransactionResponse } & Omit<I, keyof BaseContract>> {
        const tx = await this.getDeployTransaction(...args);

        assert(this.runner && typeof(this.runner.sendTransaction) === "function",
            "factory runner does not support sending transactions", "UNSUPPORTED_OPERATION", {
            operation: "sendTransaction" });

        const sentTx = await this.runner.sendTransaction(tx);
        const address = getCreateAddress(sentTx);
        return new (<any>BaseContract)(address, this.interface, this.runner, sentTx);
    }

    /**
     *  Return a new **ContractFactory** with the same ABI and bytecode,
     *  but connected to %%runner%%.
     */
    connect(runner: null | ContractRunner): ContractFactory<A, I> {
        return new ContractFactory(this.interface, this.bytecode, runner);
    }

    /**
     *  Create a new **ContractFactory** from the standard Solidity JSON output.
     */
    static fromSolidity<A extends Array<any> = Array<any>, I = ContractInterface>(output: any, runner?: ContractRunner): ContractFactory<A, I> {
        assertArgument(output != null, "bad compiler output", "output", output);

        if (typeof(output) === "string") { output = JSON.parse(output); }

        const abi = output.abi;

        let bytecode = "";
        if (output.bytecode) {
            bytecode = output.bytecode;
        } else if (output.evm && output.evm.bytecode) {
            bytecode = output.evm.bytecode;
        }

        return new this(abi, bytecode, runner);
    }
}
