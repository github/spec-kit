import { Interface } from "../abi/index.js";
import { BaseContract } from "./contract.js";
import type { InterfaceAbi } from "../abi/index.js";
import type { Addressable } from "../address/index.js";
import type { ContractRunner } from "../providers/index.js";
import type { BytesLike } from "../utils/index.js";
import type { ContractInterface, ContractMethodArgs, ContractDeployTransaction } from "./types.js";
import type { ContractTransactionResponse } from "./wrappers.js";
/**
 *  A **ContractFactory** is used to deploy a Contract to the blockchain.
 */
export declare class ContractFactory<A extends Array<any> = Array<any>, I = BaseContract> {
    /**
     *  The Contract Interface.
     */
    readonly interface: Interface;
    /**
     *  The Contract deployment bytecode. Often called the initcode.
     */
    readonly bytecode: string;
    /**
     *  The ContractRunner to deploy the Contract as.
     */
    readonly runner: null | ContractRunner;
    /**
     *  Create a new **ContractFactory** with %%abi%% and %%bytecode%%,
     *  optionally connected to %%runner%%.
     *
     *  The %%bytecode%% may be the ``bytecode`` property within the
     *  standard Solidity JSON output.
     */
    constructor(abi: Interface | InterfaceAbi, bytecode: BytesLike | {
        object: string;
    }, runner?: null | ContractRunner);
    attach(target: string | Addressable): BaseContract & Omit<I, keyof BaseContract>;
    /**
     *  Resolves to the transaction to deploy the contract, passing %%args%%
     *  into the constructor.
     */
    getDeployTransaction(...args: ContractMethodArgs<A>): Promise<ContractDeployTransaction>;
    /**
     *  Resolves to the Contract deployed by passing %%args%% into the
     *  constructor.
     *
     *  This will resolve to the Contract before it has been deployed to the
     *  network, so the [[BaseContract-waitForDeployment]] should be used before
     *  sending any transactions to it.
     */
    deploy(...args: ContractMethodArgs<A>): Promise<BaseContract & {
        deploymentTransaction(): ContractTransactionResponse;
    } & Omit<I, keyof BaseContract>>;
    /**
     *  Return a new **ContractFactory** with the same ABI and bytecode,
     *  but connected to %%runner%%.
     */
    connect(runner: null | ContractRunner): ContractFactory<A, I>;
    /**
     *  Create a new **ContractFactory** from the standard Solidity JSON output.
     */
    static fromSolidity<A extends Array<any> = Array<any>, I = ContractInterface>(output: any, runner?: ContractRunner): ContractFactory<A, I>;
}
//# sourceMappingURL=factory.d.ts.map