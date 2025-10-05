/**
 *  A **Contract** object is a meta-class (a class whose definition is
 *  defined at runtime), which communicates with a deployed smart contract
 *  on the blockchain and provides a simple JavaScript interface to call
 *  methods, send transaction, query historic logs and listen for its events.
 *
 *  @_section: api/contract:Contracts  [about-contracts]
 */
export { BaseContract, Contract } from "./contract.js";
export { ContractFactory } from "./factory.js";
export { ContractEventPayload, ContractUnknownEventPayload, ContractTransactionReceipt, ContractTransactionResponse, EventLog, UndecodedEventLog } from "./wrappers.js";
//# sourceMappingURL=index.js.map