import type {
    EventFragment, FunctionFragment, Result, Typed
} from "../abi/index.js";
import type {
    TransactionRequest, PreparedTransactionRequest, TopicFilter
} from "../providers/index.js";

import type { ContractTransactionResponse } from "./wrappers.js";


/**
 *  The name for an event used for subscribing to Contract events.
 *
 *  **``string``** - An event by name. The event must be non-ambiguous.
 *  The parameters will be dereferenced when passed into the listener.
 *
 *  [[ContractEvent]] - A filter from the ``contract.filters``, which will
 *  pass only the EventPayload as a single parameter, which includes a
 *  ``.signature`` property that can be used to further filter the event.
 *
 *  [[TopicFilter]] - A filter defined using the standard Ethereum API
 *  which provides the specific topic hash or topic hashes to watch for along
 *  with any additional values to filter by. This will only pass a single
 *  parameter to the listener, the EventPayload which will include additional
 *  details to refine by, such as the event name and signature.
 *
 *  [[DeferredTopicFilter]] - A filter created by calling a [[ContractEvent]]
 *  with parameters, which will create a filter for a specific event
 *  signature and dereference each parameter when calling the listener.
 */
export type ContractEventName = string | ContractEvent | TopicFilter | DeferredTopicFilter;

/**
 *  A Contract with no method constraints.
 */
export interface ContractInterface {
    [ name: string ]: BaseContractMethod;
};

/**
 *  When creating a filter using the ``contract.filters``, this is returned.
 */
export interface DeferredTopicFilter {
    getTopicFilter(): Promise<TopicFilter>;
    fragment: EventFragment;
}

/**
 *  When populating a transaction this type is returned.
 */
export interface ContractTransaction extends PreparedTransactionRequest {
    /**
     *  The target address.
     */
    to: string;

    /**
     *  The transaction data.
     */
    data: string;

    /**
     *  The from address, if any.
     */
    from?: string;
}

/**
 *  A deployment transaction for a contract.
 */
export interface ContractDeployTransaction extends Omit<ContractTransaction, "to"> { }

/**
 *  The overrides for a contract transaction.
 */
export interface Overrides extends Omit<TransactionRequest, "to" | "data"> { };


/**
 *  Arguments to a Contract method can always include an additional and
 *  optional overrides parameter.
 *
 *  @_ignore:
 */
export type PostfixOverrides<A extends Array<any>> = A | [ ...A, Overrides ];

/**
 *  Arguments to a Contract method can always include an additional and
 *  optional overrides parameter, and each parameter can optionally be
 *  [[Typed]].
 *
 *  @_ignore:
 */
export type ContractMethodArgs<A extends Array<any>> = PostfixOverrides<{ [ I in keyof A ]-?: A[I] | Typed }>;

// A = Arguments passed in as a tuple
// R = The result type of the call (i.e. if only one return type,
//     the qualified type, otherwise Result)
// D = The type the default call will return (i.e. R for view/pure,
//     TransactionResponse otherwise)

/**
 *  A Contract method can be called directly, or used in various ways.
 */
export interface BaseContractMethod<A extends Array<any> = Array<any>, R = any, D extends R | ContractTransactionResponse = R | ContractTransactionResponse> {
    (...args: ContractMethodArgs<A>): Promise<D>;

    /**
     *  The name of the Contract method.
     */
    name: string;

    /**
     *  The fragment of the Contract method. This will throw on ambiguous
     *  method names.
     */
    fragment: FunctionFragment;

    /**
     *  Returns the fragment constrained by %%args%%. This can be used to
     *  resolve ambiguous method names.
     */
    getFragment(...args: ContractMethodArgs<A>): FunctionFragment;

    /**
     *  Returns a populated transaction that can be used to perform the
     *  contract method with %%args%%.
     */
    populateTransaction(...args: ContractMethodArgs<A>): Promise<ContractTransaction>;

    /**
     *  Call the contract method with %%args%% and return the value.
     *
     *  If the return value is a single type, it will be dereferenced and
     *  returned directly, otherwise the full Result will be returned.
     */
    staticCall(...args: ContractMethodArgs<A>): Promise<R>;

    /**
     *  Send a transaction for the contract method with %%args%%.
     */
    send(...args: ContractMethodArgs<A>): Promise<ContractTransactionResponse>;

    /**
     *  Estimate the gas to send the contract method with %%args%%.
     */
    estimateGas(...args: ContractMethodArgs<A>): Promise<bigint>;

    /**
     *  Call the contract method with %%args%% and return the Result
     *  without any dereferencing.
     */
    staticCallResult(...args: ContractMethodArgs<A>): Promise<Result>;
}

/**
 *  A contract method on a Contract.
 */
export interface ContractMethod<
    A extends Array<any> = Array<any>,
    R = any,
    D extends R | ContractTransactionResponse = R | ContractTransactionResponse
> extends BaseContractMethod<A, R, D> { }

/**
 *  A pure of view method on a Contract.
 */
export interface ConstantContractMethod<
    A extends Array<any>,
    R = any
> extends ContractMethod<A, R, R> { }


/**
 *  Each argument of an event is nullable (to indicate matching //any//.
 *
 *  @_ignore:
 */
export type ContractEventArgs<A extends Array<any>> = { [ I in keyof A ]?: A[I] | Typed | null };

export interface ContractEvent<A extends Array<any> = Array<any>> {
    (...args: ContractEventArgs<A>): DeferredTopicFilter;

    /**
     *  The name of the Contract event.
     */
    name: string;

    /**
     *  The fragment of the Contract event. This will throw on ambiguous
     *  method names.
     */
    fragment: EventFragment;

    /**
     *  Returns the fragment constrained by %%args%%. This can be used to
     *  resolve ambiguous event names.
     */
    getFragment(...args: ContractEventArgs<A>): EventFragment;
};

/**
 *  A Fallback or Receive function on a Contract.
 */
export interface WrappedFallback {
    (overrides?: Omit<TransactionRequest, "to">): Promise<ContractTransactionResponse>;

    /**
     *  Returns a populated transaction that can be used to perform the
     *  fallback method.
     *
     *  For non-receive fallback, ``data`` may be overridden.
     */
    populateTransaction(overrides?: Omit<TransactionRequest, "to">): Promise<ContractTransaction>;

    /**
     *  Call the contract fallback and return the result.
     *
     *  For non-receive fallback, ``data`` may be overridden.
     */
    staticCall(overrides?: Omit<TransactionRequest, "to">): Promise<string>;

    /**
     *  Send a transaction to the contract fallback.
     *
     *  For non-receive fallback, ``data`` may be overridden.
     */
    send(overrides?: Omit<TransactionRequest, "to">): Promise<ContractTransactionResponse>;

    /**
     *  Estimate the gas to send a transaction to the contract fallback.
     *
     *  For non-receive fallback, ``data`` may be overridden.
     */
    estimateGas(overrides?: Omit<TransactionRequest, "to">): Promise<bigint>;
}
