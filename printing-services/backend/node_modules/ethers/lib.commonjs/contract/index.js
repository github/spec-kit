"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.UndecodedEventLog = exports.EventLog = exports.ContractTransactionResponse = exports.ContractTransactionReceipt = exports.ContractUnknownEventPayload = exports.ContractEventPayload = exports.ContractFactory = exports.Contract = exports.BaseContract = void 0;
/**
 *  A **Contract** object is a meta-class (a class whose definition is
 *  defined at runtime), which communicates with a deployed smart contract
 *  on the blockchain and provides a simple JavaScript interface to call
 *  methods, send transaction, query historic logs and listen for its events.
 *
 *  @_section: api/contract:Contracts  [about-contracts]
 */
var contract_js_1 = require("./contract.js");
Object.defineProperty(exports, "BaseContract", { enumerable: true, get: function () { return contract_js_1.BaseContract; } });
Object.defineProperty(exports, "Contract", { enumerable: true, get: function () { return contract_js_1.Contract; } });
var factory_js_1 = require("./factory.js");
Object.defineProperty(exports, "ContractFactory", { enumerable: true, get: function () { return factory_js_1.ContractFactory; } });
var wrappers_js_1 = require("./wrappers.js");
Object.defineProperty(exports, "ContractEventPayload", { enumerable: true, get: function () { return wrappers_js_1.ContractEventPayload; } });
Object.defineProperty(exports, "ContractUnknownEventPayload", { enumerable: true, get: function () { return wrappers_js_1.ContractUnknownEventPayload; } });
Object.defineProperty(exports, "ContractTransactionReceipt", { enumerable: true, get: function () { return wrappers_js_1.ContractTransactionReceipt; } });
Object.defineProperty(exports, "ContractTransactionResponse", { enumerable: true, get: function () { return wrappers_js_1.ContractTransactionResponse; } });
Object.defineProperty(exports, "EventLog", { enumerable: true, get: function () { return wrappers_js_1.EventLog; } });
Object.defineProperty(exports, "UndecodedEventLog", { enumerable: true, get: function () { return wrappers_js_1.UndecodedEventLog; } });
//# sourceMappingURL=index.js.map