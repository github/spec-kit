import type { Provider, TransactionRequest, TransactionResponse } from "./provider.js";
/**
 *  A **ContractRunner** is a generic interface which defines an object
 *  capable of interacting with a Contract on the network.
 *
 *  The more operations supported, the more utility it is capable of.
 *
 *  The most common ContractRunners are [Providers](Provider) which enable
 *  read-only access and [Signers](Signer) which enable write-access.
 */
export interface ContractRunner {
    /**
     *  The provider used for necessary state querying operations.
     *
     *  This can also point to the **ContractRunner** itself, in the
     *  case of an [[AbstractProvider]].
     */
    provider: null | Provider;
    /**
     *  Required to estimate gas.
     */
    estimateGas?: (tx: TransactionRequest) => Promise<bigint>;
    /**
     * Required for pure, view or static calls to contracts.
     */
    call?: (tx: TransactionRequest) => Promise<string>;
    /**
     *  Required to support ENS names
     */
    resolveName?: (name: string) => Promise<null | string>;
    /**
     *  Required for state mutating calls
     */
    sendTransaction?: (tx: TransactionRequest) => Promise<TransactionResponse>;
}
//# sourceMappingURL=contracts.d.ts.map