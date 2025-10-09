// Type definitions for Sinon 9.0
// Project: https://sinonjs.org
// Definitions by: William Sears <https://github.com/mrbigdog2u>
//                 Lukas Spieß <https://github.com/lumaxis>
//                 Nico Jansen <https://github.com/nicojs>
//                 James Garbutt <https://github.com/43081j>
//                 Josh Goldberg <https://github.com/joshuakgoldberg>
//                 Greg Jednaszewski <https://github.com/gjednaszewski>
//                 John Wood <https://github.com/johnjesse>
//                 Alec Flett <https://github.com/alecf>
//                 Simon Schick <https://github.com/SimonSchick>
//                 Roey Berman <https://github.com/bergundy>
// Definitions: https://github.com/DefinitelyTyped/DefinitelyTyped

import * as FakeTimers from '@sinonjs/fake-timers';

// sinon uses DOM dependencies which are absent in browser-less environment like node.js
// to avoid compiler errors this monkey patch is used
// see more details in https://github.com/DefinitelyTyped/DefinitelyTyped/issues/11351
interface Event {} // tslint:disable-line no-empty-interface
interface Document {} // tslint:disable-line no-empty-interface

declare namespace Sinon {
    type MatchArguments<T> = {
        [K in keyof T]: SinonMatcher | (T[K] extends object ? MatchArguments<T[K]> : never) | T[K];
    };

    interface SinonSpyCallApi<TArgs extends any[] = any[], TReturnValue = any> {
        // Properties
        /**
         * Array of received arguments.
         */
        args: TArgs;

        // Methods
        /**
         * Returns true if the spy was called at least once with @param obj as this.
         * calledOn also accepts a matcher spyCall.calledOn(sinon.match(fn)) (see matchers).
         * @param obj
         */
        calledOn(obj: any): boolean;
        /**
         * Returns true if spy was called at least once with the provided arguments.
         * Can be used for partial matching, Sinon only checks the provided arguments against actual arguments,
         * so a call that received the provided arguments (in the same spots) and possibly others as well will return true.
         * @param args
         */
        calledWith(...args: Partial<MatchArguments<TArgs>>[]): boolean;
        /**
         * Returns true if spy was called at least once with the provided arguments and no others.
         */
        calledWithExactly(...args: MatchArguments<TArgs>): boolean;
        /**
         * Returns true if spy/stub was called the new operator.
         * Beware that this is inferred based on the value of the this object and the spy function’s prototype,
         * so it may give false positives if you actively return the right kind of object.
         */
        calledWithNew(): boolean;
        /**
         * Returns true if spy was called at exactly once with the provided arguments.
         * @param args
         */
        calledOnceWith(...args: MatchArguments<TArgs>): boolean;
        calledOnceWithExactly(...args: MatchArguments<TArgs>): boolean;
        /**
         * Returns true if spy was called with matching arguments (and possibly others).
         * This behaves the same as spy.calledWith(sinon.match(arg1), sinon.match(arg2), ...).
         * @param args
         */
        calledWithMatch(...args: TArgs): boolean;
        /**
         * Returns true if call did not receive provided arguments.
         * @param args
         */
        notCalledWith(...args: MatchArguments<TArgs>): boolean;
        /**
         * Returns true if call did not receive matching arguments.
         * This behaves the same as spyCall.notCalledWith(sinon.match(arg1), sinon.match(arg2), ...).
         * @param args
         */
        notCalledWithMatch(...args: TArgs): boolean;
        /**
         * Returns true if spy returned the provided value at least once.
         * Uses deep comparison for objects and arrays. Use spy.returned(sinon.match.same(obj)) for strict comparison (see matchers).
         * @param value
         */
        returned(value: TReturnValue | SinonMatcher): boolean;
        /**
         * Returns true if spy threw an exception at least once.
         */
        threw(): boolean;
        /**
         * Returns true if spy threw an exception of the provided type at least once.
         */
        threw(type: string): boolean;
        /**
         * Returns true if spy threw the provided exception object at least once.
         */
        threw(obj: any): boolean;
        /**
         * Like yield, but with an explicit argument number specifying which callback to call.
         * Useful if a function is called with more than one callback, and simply calling the first callback is not desired.
         * @param pos
         */
        callArg(pos: number): void;
        callArgOn(pos: number, obj: any, ...args: any[]): void;
        /**
         * Like callArg, but with arguments.
         */
        callArgWith(pos: number, ...args: any[]): void;
        callArgOnWith(pos: number, obj: any, ...args: any[]): void;
        /**
         * Invoke callbacks passed to the stub with the given arguments.
         * If the stub was never called with a function argument, yield throws an error.
         * Returns an Array with all callbacks return values in the order they were called, if no error is thrown.
         * Also aliased as invokeCallback.
         */
        yield(...args: any[]): void;
        yieldOn(obj: any, ...args: any[]): void;
        /**
         * Invokes callbacks passed as a property of an object to the stub.
         * Like yield, yieldTo grabs the first matching argument, finds the callback and calls it with the (optional) arguments.
         */
        yieldTo(property: string, ...args: any[]): void;
        yieldToOn(property: string, obj: any, ...args: any[]): void;
    }

    interface SinonSpyCall<TArgs extends any[] = any[], TReturnValue = any>
        extends SinonSpyCallApi<TArgs, TReturnValue> {
        /**
         * The call’s this value.
         */
        thisValue: any;
        /**
         * Exception thrown, if any.
         */
        exception: any;
        /**
         * Return value.
         */
        returnValue: TReturnValue;
        /**
         * This property is a convenience for a call’s callback.
         * When the last argument in a call is a Function, then callback will reference that. Otherwise it will be undefined.
         */
        callback: Function | undefined;

        /**
         * This property is a convenience for the first argument of the call.
         */
        firstArg: any;

        /**
         * This property is a convenience for the last argument of the call.
         */
        lastArg: any;

        /**
         * Returns true if the spy call occurred before another spy call.
         * @param call
         *
         */
        calledBefore(call: SinonSpyCall<any>): boolean;
        /**
         * Returns true if the spy call occurred after another spy call.
         * @param call
         */
        calledAfter(call: SinonSpyCall<any>): boolean;
    }

    interface SinonSpy<TArgs extends any[] = any[], TReturnValue = any>
        extends Pick<
            SinonSpyCallApi<TArgs, TReturnValue>,
            Exclude<keyof SinonSpyCallApi<TArgs, TReturnValue>, 'args'>
        > {
        // Properties
        /**
         * The number of recorded calls.
         */
        callCount: number;
        /**
         * true if the spy was called at least once
         */
        called: boolean;
        /**
         * true if the spy was not called
         */
        notCalled: boolean;
        /**
         * true if spy was called exactly once
         */
        calledOnce: boolean;
        /**
         * true if the spy was called exactly twice
         */
        calledTwice: boolean;
        /**
         * true if the spy was called exactly thrice
         */
        calledThrice: boolean;
        /**
         * The first call
         */
        firstCall: SinonSpyCall<TArgs, TReturnValue>;
        /**
         * The second call
         */
        secondCall: SinonSpyCall<TArgs, TReturnValue>;
        /**
         * The third call
         */
        thirdCall: SinonSpyCall<TArgs, TReturnValue>;
        /**
         * The last call
         */
        lastCall: SinonSpyCall<TArgs, TReturnValue>;
        /**
         * Array of this objects, spy.thisValues[0] is the this object for the first call.
         */
        thisValues: any[];
        /**
         * Array of arguments received, spy.args[0] is an array of arguments received in the first call.
         */
        args: TArgs[];
        /**
         * Array of exception objects thrown, spy.exceptions[0] is the exception thrown by the first call.
         * If the call did not throw an error, the value at the call’s location in .exceptions will be undefined.
         */
        exceptions: any[];
        /**
         * Array of return values, spy.returnValues[0] is the return value of the first call.
         * If the call did not explicitly return a value, the value at the call’s location in .returnValues will be undefined.
         */
        returnValues: TReturnValue[];

        /**
         * Holds a reference to the original method/function this stub has wrapped.
         */
        wrappedMethod: (...args: TArgs) => TReturnValue;

        // Methods
        (...args: TArgs): TReturnValue;

        /**
         * Returns true if the spy was called before @param anotherSpy
         * @param anotherSpy
         */
        calledBefore(anotherSpy: SinonSpy<any>): boolean;
        /**
         * Returns true if the spy was called after @param anotherSpy
         * @param anotherSpy
         */
        calledAfter(anotherSpy: SinonSpy<any>): boolean;
        /**
         * Returns true if spy was called before @param anotherSpy, and no spy calls occurred between spy and @param anotherSpy.
         * @param anotherSpy
         */
        calledImmediatelyBefore(anotherSpy: SinonSpy<any>): boolean;
        /**
         * Returns true if spy was called after @param anotherSpy, and no spy calls occurred between @param anotherSpy and spy.
         * @param anotherSpy
         */
        calledImmediatelyAfter(anotherSpy: SinonSpy<any>): boolean;

        /**
         * Creates a spy that only records calls when the received arguments match those passed to withArgs.
         * This is useful to be more expressive in your assertions, where you can access the spy with the same call.
         * @param args Expected args
         */
        withArgs(...args: MatchArguments<TArgs>): SinonSpy<TArgs, TReturnValue>;
        /**
         * Returns true if the spy was always called with @param obj as this.
         * @param obj
         */
        alwaysCalledOn(obj: any): boolean;
        /**
         * Returns true if spy was always called with the provided arguments (and possibly others).
         */
        alwaysCalledWith(...args: MatchArguments<TArgs>): boolean;
        /**
         * Returns true if spy was always called with the exact provided arguments.
         * @param args
         */
        alwaysCalledWithExactly(...args: MatchArguments<TArgs>): boolean;
        /**
         * Returns true if spy was always called with matching arguments (and possibly others).
         * This behaves the same as spy.alwaysCalledWith(sinon.match(arg1), sinon.match(arg2), ...).
         * @param args
         */
        alwaysCalledWithMatch(...args: TArgs): boolean;
        /**
         * Returns true if the spy/stub was never called with the provided arguments.
         * @param args
         */
        neverCalledWith(...args: MatchArguments<TArgs>): boolean;
        /**
         * Returns true if the spy/stub was never called with matching arguments.
         * This behaves the same as spy.neverCalledWith(sinon.match(arg1), sinon.match(arg2), ...).
         * @param args
         */
        neverCalledWithMatch(...args: TArgs): boolean;
        /**
         * Returns true if spy always threw an exception.
         */
        alwaysThrew(): boolean;
        /**
         * Returns true if spy always threw an exception of the provided type.
         */
        alwaysThrew(type: string): boolean;
        /**
         * Returns true if spy always threw the provided exception object.
         */
        alwaysThrew(obj: any): boolean;
        /**
         * Returns true if spy always returned the provided value.
         * @param obj
         */
        alwaysReturned(obj: any): boolean;
        /**
         * Invoke callbacks passed to the stub with the given arguments.
         * If the stub was never called with a function argument, yield throws an error.
         * Returns an Array with all callbacks return values in the order they were called, if no error is thrown.
         */
        invokeCallback(...args: TArgs): void;
        /**
         * Set the displayName of the spy or stub.
         * @param name
         */
        named(name: string): SinonSpy<TArgs, TReturnValue>;
        /**
         * Returns the nth call.
         * Accessing individual calls helps with more detailed behavior verification when the spy is called more than once.
         * @param n Zero based index of the spy call.
         */
        getCall(n: number): SinonSpyCall<TArgs, TReturnValue>;
        /**
         * Returns an Array of all calls recorded by the spy.
         */
        getCalls(): Array<SinonSpyCall<TArgs, TReturnValue>>;
        /**
         * Resets the state of a spy.
         */
        resetHistory(): void;
        /**
         * Returns the passed format string with the following replacements performed:
         * * %n - the name of the spy "spy" by default)
         * * %c - the number of times the spy was called, in words ("once", "twice", etc.)
         * * %C - a list of string representations of the calls to the spy, with each call prefixed by a newline and four spaces
         * * %t - a comma-delimited list of this values the spy was called on
         * * %n - the formatted value of the nth argument passed to printf
         * * %* - a comma-delimited list of the (non-format string) arguments passed to printf
         * * %D - a multi-line list of the arguments received by all calls to the spy
         * @param format
         * @param args
         */
        printf(format: string, ...args: any[]): string;
        /**
         * Replaces the spy with the original method. Only available if the spy replaced an existing method.
         */
        restore(): void;
    }

    interface SinonSpyStatic {
        /**
         * Creates an anonymous function that records arguments, this value, exceptions and return values for all calls.
         */
        (): SinonSpy;
        /**
         * Spies on the provided function
         */
        <F extends (...args: any[]) => any>(func: F): SinonSpy<Parameters<F>, ReturnType<F>>;
        /**
         * Creates a spy for object.method and replaces the original method with the spy.
         * An exception is thrown if the property is not already a function.
         * The spy acts exactly like the original method in all cases.
         * The original method can be restored by calling object.method.restore().
         * The returned spy is the function object which replaced the original method. spy === object.method.
         */
        <T, K extends keyof T>(obj: T, method: K): T[K] extends (...args: infer TArgs) => infer TReturnValue
            ? SinonSpy<TArgs, TReturnValue>
            : SinonSpy;

        <T, K extends keyof T>(obj: T, method: K, types: Array<'get' | 'set'>): PropertyDescriptor & {
            get: SinonSpy<[], T[K]>;
            set: SinonSpy<[T[K]], void>;
        };
    }

    interface SinonStub<TArgs extends any[] = any[], TReturnValue = any> extends SinonSpy<TArgs, TReturnValue> {
        /**
         * Resets the stub’s behaviour to the default behaviour
         * You can reset behaviour of all stubs using sinon.resetBehavior()
         */
        resetBehavior(): void;
        /**
         * Resets both behaviour and history of the stub.
         * This is equivalent to calling both stub.resetBehavior() and stub.resetHistory()
         * Updated in sinon@2.0.0
         * Since sinon@5.0.0
         * As a convenience, you can apply stub.reset() to all stubs using sinon.reset()
         */
        reset(): void;
        /**
         * Causes the stub to return promises using a specific Promise library instead of the global one when using stub.rejects or stub.resolves.
         * Returns the stub to allow chaining.
         */
        usingPromise(promiseLibrary: any): SinonStub<TArgs, TReturnValue>;

        /**
         * Makes the stub return the provided @param obj value.
         * @param obj
         */
        returns(obj: TReturnValue): SinonStub<TArgs, TReturnValue>;
        /**
         * Causes the stub to return the argument at the provided @param index.
         * stub.returnsArg(0); causes the stub to return the first argument.
         * If the argument at the provided index is not available, prior to sinon@6.1.2, an undefined value will be returned;
         * starting from sinon@6.1.2, a TypeError will be thrown.
         * @param index
         */
        returnsArg(index: number): SinonStub<TArgs, TReturnValue>;
        /**
         * Causes the stub to return its this value.
         * Useful for stubbing jQuery-style fluent APIs.
         */
        returnsThis(): SinonStub<TArgs, TReturnValue>;
        /**
         * Causes the stub to return a Promise which resolves to the provided value.
         * When constructing the Promise, sinon uses the Promise.resolve method.
         * You are responsible for providing a polyfill in environments which do not provide Promise.
         * The Promise library can be overwritten using the usingPromise method.
         * Since sinon@2.0.0
         */
        resolves(
            value?: TReturnValue extends PromiseLike<infer TResolveValue> ? TResolveValue : any,
        ): SinonStub<TArgs, TReturnValue>;
        /**
         * Causes the stub to return a Promise which resolves to the argument at the provided index.
         * stub.resolvesArg(0); causes the stub to return a Promise which resolves to the first argument.
         * If the argument at the provided index is not available, a TypeError will be thrown.
         */
        resolvesArg(index: number): SinonStub<TArgs, TReturnValue>;
        /**
         * Causes the stub to return a Promise which resolves to its this value.
         */
        resolvesThis(): SinonStub<TArgs, TReturnValue>;
        /**
         * Causes the stub to throw an exception (Error).
         * @param type
         */
        throws(type?: string): SinonStub<TArgs, TReturnValue>;
        /**
         * Causes the stub to throw the provided exception object.
         */
        throws(obj: any): SinonStub<TArgs, TReturnValue>;
        /**
         * Causes the stub to throw the argument at the provided index.
         * stub.throwsArg(0); causes the stub to throw the first argument as the exception.
         * If the argument at the provided index is not available, a TypeError will be thrown.
         * Since sinon@2.3.0
         * @param index
         */
        throwsArg(index: number): SinonStub<TArgs, TReturnValue>;
        throwsException(type?: string): SinonStub<TArgs, TReturnValue>;
        throwsException(obj: any): SinonStub<TArgs, TReturnValue>;
        /**
         * Causes the stub to return a Promise which rejects with an exception (Error).
         * When constructing the Promise, sinon uses the Promise.reject method.
         * You are responsible for providing a polyfill in environments which do not provide Promise.
         * The Promise library can be overwritten using the usingPromise method.
         * Since sinon@2.0.0
         */
        rejects(): SinonStub<TArgs, TReturnValue>;
        /**
         * Causes the stub to return a Promise which rejects with an exception of the provided type.
         * Since sinon@2.0.0
         */
        rejects(errorType: string): SinonStub<TArgs, TReturnValue>;
        /**
         * Causes the stub to return a Promise which rejects with the provided exception object.
         * Since sinon@2.0.0
         */
        rejects(value: any): SinonStub<TArgs, TReturnValue>;
        /**
         * Causes the stub to call the argument at the provided index as a callback function.
         * stub.callsArg(0); causes the stub to call the first argument as a callback.
         * If the argument at the provided index is not available or is not a function, a TypeError will be thrown.
         */
        callsArg(index: number): SinonStub<TArgs, TReturnValue>;
        /**
         * Causes the original method wrapped into the stub to be called when none of the conditional stubs are matched.
         */
        callThrough(): SinonStub<TArgs, TReturnValue>;
        /**
         * Like stub.callsArg(index); but with an additional parameter to pass the this context.
         * @param index
         * @param context
         */
        callsArgOn(index: number, context: any): SinonStub<TArgs, TReturnValue>;
        /**
         * Like callsArg, but with arguments to pass to the callback.
         * @param index
         * @param args
         */
        callsArgWith(index: number, ...args: any[]): SinonStub<TArgs, TReturnValue>;
        /**
         * Like above but with an additional parameter to pass the this context.
         * @param index
         * @param context
         * @param args
         */
        callsArgOnWith(index: number, context: any, ...args: any[]): SinonStub<TArgs, TReturnValue>;
        /**
         * Same as their corresponding non-Async counterparts, but with callback being deferred at called after all instructions in the current call stack are processed.
         * In Node environment the callback is deferred with process.nextTick.
         * In a browser the callback is deferred with setTimeout(callback, 0).
         * @param index
         */
        callsArgAsync(index: number): SinonStub<TArgs, TReturnValue>;
        /**
         * Same as their corresponding non-Async counterparts, but with callback being deferred at called after all instructions in the current call stack are processed.
         * In Node environment the callback is deferred with process.nextTick.
         * In a browser the callback is deferred with setTimeout(callback, 0).
         * @param index
         * @param context
         */
        callsArgOnAsync(index: number, context: any): SinonStub<TArgs, TReturnValue>;
        /**
         * Same as their corresponding non-Async counterparts, but with callback being deferred at called after all instructions in the current call stack are processed.
         * In Node environment the callback is deferred with process.nextTick.
         * In a browser the callback is deferred with setTimeout(callback, 0).
         */
        callsArgWithAsync(index: number, ...args: any[]): SinonStub<TArgs, TReturnValue>;
        /**
         * Same as their corresponding non-Async counterparts, but with callback being deferred at called after all instructions in the current call stack are processed.
         * In Node environment the callback is deferred with process.nextTick.
         * In a browser the callback is deferred with setTimeout(callback, 0).
         */
        callsArgOnWithAsync(index: number, context: any, ...args: any[]): SinonStub<TArgs, TReturnValue>;
        /**
         * Makes the stub call the provided @param func when invoked.
         * @param func
         */
        callsFake(func: (...args: TArgs) => TReturnValue): SinonStub<TArgs, TReturnValue>;
        /**
         * Replaces a new getter for this stub.
         */
        get(func: () => any): SinonStub<TArgs, TReturnValue>;
        /**
         * Defines a new setter for this stub.
         * @param func
         */
        set(func: (v: any) => void): SinonStub<TArgs, TReturnValue>;
        /**
         * Defines the behavior of the stub on the @param n call. Useful for testing sequential interactions.
         * There are methods onFirstCall, onSecondCall,onThirdCall to make stub definitions read more naturally.
         * onCall can be combined with all of the behavior defining methods in this section. In particular, it can be used together with withArgs.
         * @param n
         */
        onCall(n: number): SinonStub<TArgs, TReturnValue>;
        /**
         * Alias for stub.onCall(0);
         */
        onFirstCall(): SinonStub<TArgs, TReturnValue>;
        /**
         * Alias for stub.onCall(1);
         */
        onSecondCall(): SinonStub<TArgs, TReturnValue>;
        /**
         * Alias for stub.onCall(2);
         */
        onThirdCall(): SinonStub<TArgs, TReturnValue>;
        /**
         * Defines a new value for this stub.
         * @param val
         */
        value(val: any): SinonStub<TArgs, TReturnValue>;
        /**
         * Set the displayName of the spy or stub.
         * @param name
         */
        named(name: string): SinonStub<TArgs, TReturnValue>;
        /**
         * Similar to callsArg.
         * Causes the stub to call the first callback it receives with the provided arguments (if any).
         * If a method accepts more than one callback, you need to use callsArg to have the stub invoke other callbacks than the first one.
         */
        yields(...args: any[]): SinonStub<TArgs, TReturnValue>;
        /**
         * Like above but with an additional parameter to pass the this context.
         */
        yieldsOn(context: any, ...args: any[]): SinonStub<TArgs, TReturnValue>;
        yieldsRight(...args: any[]): SinonStub<TArgs, TReturnValue>;
        /**
         * Causes the spy to invoke a callback passed as a property of an object to the spy.
         * Like yields, yieldsTo grabs the first matching argument, finds the callback and calls it with the (optional) arguments.
         * @param property
         * @param args
         */
        yieldsTo(property: string, ...args: any[]): SinonStub<TArgs, TReturnValue>;
        /**
         * Like above but with an additional parameter to pass the this context.
         */
        yieldsToOn(property: string, context: any, ...args: any[]): SinonStub<TArgs, TReturnValue>;
        /**
         * Same as their corresponding non-Async counterparts, but with callback being deferred at called after all instructions in the current call stack are processed.
         * In Node environment the callback is deferred with process.nextTick.
         * In a browser the callback is deferred with setTimeout(callback, 0).
         * @param args
         */
        yieldsAsync(...args: any[]): SinonStub<TArgs, TReturnValue>;
        /**
         * Same as their corresponding non-Async counterparts, but with callback being deferred at called after all instructions in the current call stack are processed.
         * In Node environment the callback is deferred with process.nextTick.
         * In a browser the callback is deferred with setTimeout(callback, 0).
         * @param context
         * @param args
         */
        yieldsOnAsync(context: any, ...args: any[]): SinonStub<TArgs, TReturnValue>;
        /**
         * Same as their corresponding non-Async counterparts, but with callback being deferred at called after all instructions in the current call stack are processed.
         * In Node environment the callback is deferred with process.nextTick.
         * In a browser the callback is deferred with setTimeout(callback, 0).
         * @param property
         * @param args
         */
        yieldsToAsync(property: string, ...args: any[]): SinonStub<TArgs, TReturnValue>;
        /**
         * Same as their corresponding non-Async counterparts, but with callback being deferred at called after all instructions in the current call stack are processed.
         * In Node environment the callback is deferred with process.nextTick.
         * In a browser the callback is deferred with setTimeout(callback, 0).
         * @param property
         * @param context
         * @param args
         */
        yieldsToOnAsync(property: string, context: any, ...args: any[]): SinonStub<TArgs, TReturnValue>;
        /**
         * Stubs the method only for the provided arguments.
         * This is useful to be more expressive in your assertions, where you can access the spy with the same call.
         * It is also useful to create a stub that can act differently in response to different arguments.
         * @param args
         */
        withArgs(...args: MatchArguments<TArgs>): SinonStub<TArgs, TReturnValue>;
    }

    interface SinonStubStatic {
        /* tslint:disable:no-unnecessary-generics */

        /**
         * Creates an anonymous stub function
         */
        <TArgs extends any[] = any[], R = any>(): SinonStub<TArgs, R>;

        /* tslint:enable:no-unnecessary-generics */

        /**
         * Stubs all the object’s methods.
         * Note that it’s usually better practice to stub individual methods, particularly on objects that you don’t understand or control all the methods for (e.g. library dependencies).
         * Stubbing individual methods tests intent more precisely and is less susceptible to unexpected behavior as the object’s code evolves.
         * If you want to create a stub object of MyConstructor, but don’t want the constructor to be invoked, use this utility function.
         */
        <T>(obj: T): SinonStubbedInstance<T>;
        /**
         * Replaces obj.method with a stub function.
         * An exception is thrown if the property is not already a function.
         * The original function can be restored by calling object.method.restore(); (or stub.restore();).
         */
        <T, K extends keyof T>(obj: T, method: K): T[K] extends (...args: infer TArgs) => infer TReturnValue
            ? SinonStub<TArgs, TReturnValue>
            : SinonStub;
    }

    interface SinonExpectation extends SinonStub {
        /**
         * Specify the minimum amount of calls expected.
         */
        atLeast(n: number): SinonExpectation;
        /**
         * Specify the maximum amount of calls expected.
         * @param n
         */
        atMost(n: number): SinonExpectation;
        /**
         * Expect the method to never be called.
         */
        never(): SinonExpectation;
        /**
         * Expect the method to be called exactly once.
         */
        once(): SinonExpectation;
        /**
         * Expect the method to be called exactly twice.
         */
        twice(): SinonExpectation;
        /**
         * Expect the method to be called exactly thrice.
         */
        thrice(): SinonExpectation;
        /**
         * Expect the method to be called exactly @param n times.
         */
        exactly(n: number): SinonExpectation;
        /**
         * Expect the method to be called with the provided arguments and possibly others.
         * An expectation instance only holds onto a single set of arguments specified with withArgs.
         * Subsequent calls will overwrite the previously-specified set of arguments (even if they are different),
         * so it is generally not intended that this method be invoked more than once per test case.
         * @param args
         */
        withArgs(...args: any[]): SinonExpectation;
        /**
         * Expect the method to be called with the provided arguments and no others.
         * An expectation instance only holds onto a single set of arguments specified with withExactArgs.
         * Subsequent calls will overwrite the previously-specified set of arguments (even if they are different),
         * so it is generally not intended that this method be invoked more than once per test case.
         * @param args
         */
        withExactArgs(...args: any[]): SinonExpectation;
        on(obj: any): SinonExpectation;
        /**
         * Verifies all expectations on the mock.
         * If any expectation is not satisfied, an exception is thrown.
         * Also restores the mocked methods.
         */
        verify(): SinonExpectation;
        /**
         * Restores all mocked methods.
         */
        restore(): void;
    }

    interface SinonExpectationStatic {
        /**
         * Creates an expectation without a mock object, basically an anonymous mock function.
         * Method name is optional and is used in exception messages to make them more readable.
         * @param methodName
         */
        create(methodName?: string): SinonExpectation;
    }

    interface SinonMock {
        /**
         * Overrides obj.method with a mock function and returns it.
         */
        expects(method: string): SinonExpectation;
        /**
         * Restores all mocked methods.
         */
        restore(): void;
        /**
         * Verifies all expectations on the mock.
         * If any expectation is not satisfied, an exception is thrown.
         * Also restores the mocked methods.
         */
        verify(): void;
    }

    interface SinonMockStatic {
        (): SinonExpectation;
        /**
         * Creates a mock for the provided object.
         * Does not change the object, but returns a mock object to set expectations on the object’s methods.
         */
        (obj: any): SinonMock;
    }

    type SinonTimerId = FakeTimers.TimerId;

    type SinonFakeTimers = FakeTimers.InstalledMethods &
        FakeTimers.NodeClock &
        FakeTimers.BrowserClock & {
            /**
             * Restore the faked methods.
             * Call in e.g. tearDown.
             */
            restore(): void;
        };

    interface SinonFakeTimersConfig {
        now: number | Date;
        toFake: string[];
        shouldAdvanceTime: boolean;
    }

    interface SinonFakeUploadProgress {
        eventListeners: {
            progress: any[];
            load: any[];
            abort: any[];
            error: any[];
        };

        addEventListener(event: string, listener: (e: Event) => any): void;
        removeEventListener(event: string, listener: (e: Event) => any): void;
        dispatchEvent(event: Event): void;
    }

    interface SinonFakeXMLHttpRequest {
        // Properties
        /**
         * The URL set on the request object.
         */
        url: string;
        /**
         * The request method as a string.
         */
        method: string;
        /**
         * An object of all request headers, i.e.:
         */
        requestHeaders: any;
        /**
         * The request body
         */
        requestBody: string;
        /**
         * The request’s status code.
         * undefined if the request has not been handled (see respond below)
         */
        status: number;
        /**
         * Only populated if the respond method is called (see below).
         */
        statusText: string;
        /**
         * Whether or not the request is asynchronous.
         */
        async: boolean;
        /**
         * Username, if any.
         */
        username: string;
        /**
         * Password, if any.
         */
        password: string;
        withCredentials: boolean;
        upload: SinonFakeUploadProgress;
        /**
         * When using respond, this property is populated with a parsed document if response headers indicate as much (see the spec)
         */
        responseXML: Document;
        /**
         * The value of the given response header, if the request has been responded to (see respond).
         * @param header
         */
        getResponseHeader(header: string): string;
        /**
         * All response headers as an object.
         */
        getAllResponseHeaders(): any;

        // Methods
        /**
         * Sets response headers (e.g. { "Content-Type": "text/html", ... }, updates the readyState property and fires onreadystatechange.
         * @param headers
         */
        setResponseHeaders(headers: any): void;
        /**
         * Sets the respond body, updates the readyState property and fires onreadystatechange.
         * Additionally, populates responseXML with a parsed document if response headers indicate as much.
         */
        setResponseBody(body: string): void;
        /**
         * Calls the above three methods.
         */
        respond(status: number, headers: any, body: string): void;
        autoRespond(ms: number): void;
        /**
         * Simulates a network error on the request. The onerror handler will be called and the status will be 0.
         */
        error(): void;
        onerror(): void;
    }

    interface SinonFakeXMLHttpRequestStatic {
        new (): SinonFakeXMLHttpRequest;
        /**
         * Default false.
         * When set to true, Sinon will check added filters if certain requests should be “unfaked”
         */
        useFilters: boolean;
        /**
         * Add a filter that will decide whether or not to fake a request.
         * The filter will be called when xhr.open is called, with the exact same arguments (method, url, async, username, password).
         * If the filter returns true, the request will not be faked.
         * @param filter
         */
        addFilter(
            filter: (method: string, url: string, async: boolean, username: string, password: string) => boolean,
        ): void;
        /**
         * By assigning a function to the onCreate property of the returned object from useFakeXMLHttpRequest()
         * you can subscribe to newly created FakeXMLHttpRequest objects. See below for the fake xhr object API.
         * Using this observer means you can still reach objects created by e.g. jQuery.ajax (or other abstractions/frameworks).
         * @param xhr
         */
        onCreate(xhr: SinonFakeXMLHttpRequest): void;
        /**
         * Restore original function(s).
         */
        restore(): void;
    }

    interface SinonFakeServer extends SinonFakeServerOptions {
        // Properties
        /**
         * Used internally to determine the HTTP method used with the provided request.
         * By default this method simply returns request.method.
         * When server.fakeHTTPMethods is true, the method will return the value of the _method parameter if the method is “POST”.
         * This method can be overridden to provide custom behavior.
         * @param request
         */
        getHTTPMethod(request: SinonFakeXMLHttpRequest): string;
        /**
         * You can inspect the server.requests to verify request ordering, find unmatched requests or check that no requests has been done.
         * server.requests is an array of all the FakeXMLHttpRequest objects that have been created.
         */
        requests: SinonFakeXMLHttpRequest[];

        // Methods
        /**
         * Causes the server to respond to any request not matched by another response with the provided data. The default catch-all response is [404, {}, ""].
         * A String representing the response body
         * An Array with status, headers and response body, e.g. [200, { "Content-Type": "text/html", "Content-Length": 2 }, "OK"]
         * A Function.
         * Default status is 200 and default headers are none.
         * When the response is a Function, it will be passed the request object. You must manually call respond on it to complete the request.
         * @param body A String representing the response body
         */
        respondWith(body: string): void;
        /**
         * Causes the server to respond to any request not matched by another response with the provided data. The default catch-all response is [404, {}, ""].
         * Default status is 200 and default headers are none.
         * When the response is a Function, it will be passed the request object. You must manually call respond on it to complete the request.
         * @param response An Array with status, headers and response body, e.g. [200, { "Content-Type": "text/html", "Content-Length": 2 }, "OK"]
         */
        respondWith(response: any[]): void;
        /**
         * Causes the server to respond to any request not matched by another response with the provided data. The default catch-all response is [404, {}, ""].
         * Default status is 200 and default headers are none.
         * When the response is a Function, it will be passed the request object. You must manually call respond on it to complete the request.
         * @param fn A Function.
         */
        respondWith(fn: (xhr: SinonFakeXMLHttpRequest) => void): void;
        /**
         * Responds to all requests to given URL, e.g. /posts/1.
         */
        respondWith(url: string, body: string): void;
        /**
         * Responds to all requests to given URL, e.g. /posts/1.
         */
        respondWith(url: string, response: any[]): void;
        /**
         * Responds to all requests to given URL, e.g. /posts/1.
         */
        respondWith(url: string, fn: (xhr: SinonFakeXMLHttpRequest) => void): void;
        /**
         * Responds to all method requests to the given URL with the given response.
         * method is an HTTP verb.
         */
        respondWith(method: string, url: string, body: string): void;
        /**
         * Responds to all method requests to the given URL with the given response.
         * method is an HTTP verb.
         */
        respondWith(method: string, url: string, response: any[]): void;
        /**
         * Responds to all method requests to the given URL with the given response.
         * method is an HTTP verb.
         */
        respondWith(method: string, url: string, fn: (xhr: SinonFakeXMLHttpRequest) => void): void;
        /**
         * URL may be a regular expression, e.g. /\\/post\\//\\d+
         * If the response is a Function, it will be passed any capture groups from the regular expression along with the XMLHttpRequest object:
         */
        respondWith(url: RegExp, body: string): void;
        /**
         * URL may be a regular expression, e.g. /\\/post\\//\\d+
         * If the response is a Function, it will be passed any capture groups from the regular expression along with the XMLHttpRequest object:
         */
        respondWith(url: RegExp, response: any[]): void;
        /**
         * URL may be a regular expression, e.g. /\\/post\\//\\d+
         * If the response is a Function, it will be passed any capture groups from the regular expression along with the XMLHttpRequest object:
         */
        respondWith(url: RegExp, fn: (xhr: SinonFakeXMLHttpRequest) => void): void;
        /**
         * Responds to all method requests to URLs matching the regular expression.
         */
        respondWith(method: string, url: RegExp, body: string): void;
        /**
         * Responds to all method requests to URLs matching the regular expression.
         */
        respondWith(method: string, url: RegExp, response: any[]): void;
        /**
         * Responds to all method requests to URLs matching the regular expression.
         */
        respondWith(method: string, url: RegExp, fn: (xhr: SinonFakeXMLHttpRequest) => void): void;
        /**
         * Causes all queued asynchronous requests to receive a response.
         * If none of the responses added through respondWith match, the default response is [404, {}, ""].
         * Synchronous requests are responded to immediately, so make sure to call respondWith upfront.
         * If called with arguments, respondWith will be called with those arguments before responding to requests.
         */
        respond(): void;
        restore(): void;
    }

    interface SinonFakeServerOptions {
        /**
         * When set to true, causes the server to automatically respond to incoming requests after a timeout.
         * The default timeout is 10ms but you can control it through the autoRespondAfter property.
         * Note that this feature is intended to help during mockup development, and is not suitable for use in tests.
         */
        autoRespond: boolean;
        /**
         * When autoRespond is true, respond to requests after this number of milliseconds. Default is 10.
         */
        autoRespondAfter: number;
        /**
         * If set to true, server will find _method parameter in POST body and recognize that as the actual method.
         * Supports a pattern common to Ruby on Rails applications. For custom HTTP method faking, override server.getHTTPMethod(request).
         */
        fakeHTTPMethods: boolean;
        /**
         * If set, the server will respond to every request immediately and synchronously.
         * This is ideal for faking the server from within a test without having to call server.respond() after each request made in that test.
         * As this is synchronous and immediate, this is not suitable for simulating actual network latency in tests or mockups.
         * To simulate network latency with automatic responses, see server.autoRespond and server.autoRespondAfter.
         */
        respondImmediately: boolean;
    }

    interface SinonFakeServerStatic {
        create(options?: Partial<SinonFakeServerOptions>): SinonFakeServer;
    }

    interface SinonExposeOptions {
        prefix: string;
        includeFail: boolean;
    }

    interface SinonAssert {
        // Properties
        /**
         * Defaults to AssertError.
         */
        failException: string;
        /**
         * Every assertion fails by calling this method.
         * By default it throws an error of type sinon.assert.failException.
         * If the test framework looks for assertion errors by checking for a specific exception, you can simply override the kind of exception thrown.
         * If that does not fit with your testing framework of choice, override the fail method to do the right thing.
         */
        fail(message?: string): void; // Overridable
        /**
         * Called every time assertion passes.
         * Default implementation does nothing.
         */
        pass(assertion: any): void; // Overridable

        // Methods

        /**
         * Passes if spy was never called
         * @param spy
         */
        notCalled(spy: SinonSpy<any>): void;
        /**
         * Passes if spy was called at least once.
         */
        called(spy: SinonSpy<any>): void;
        /**
         * Passes if spy was called once and only once.
         */
        calledOnce(spy: SinonSpy<any>): void;
        /**
         * Passes if spy was called exactly twice.
         */
        calledTwice(spy: SinonSpy<any>): void;
        /**
         * Passes if spy was called exactly three times.
         */
        calledThrice(spy: SinonSpy<any>): void;
        /**
         * Passes if spy was called exactly num times.
         */
        callCount(spy: SinonSpy<any>, count: number): void;
        /**
         * Passes if provided spies were called in the specified order.
         * @param spies
         */
        callOrder(...spies: Array<SinonSpy<any>>): void;
        /**
         * Passes if spy was ever called with obj as its this value.
         * It’s possible to assert on a dedicated spy call: sinon.assert.calledOn(spy.firstCall, arg1, arg2, ...);.
         */
        calledOn(spyOrSpyCall: SinonSpy<any> | SinonSpyCall<any>, obj: any): void;
        /**
         * Passes if spy was always called with obj as its this value.
         */
        alwaysCalledOn(spy: SinonSpy<any>, obj: any): void;

        /**
         * Passes if spy was called with the provided arguments.
         * It’s possible to assert on a dedicated spy call: sinon.assert.calledWith(spy.firstCall, arg1, arg2, ...);.
         * @param spyOrSpyCall
         * @param args
         */
        calledWith<TArgs extends any[]>(
            spyOrSpyCall: SinonSpy<TArgs> | SinonSpyCall<TArgs>,
            ...args: MatchArguments<TArgs>
        ): void;
        /**
         * Passes if spy was always called with the provided arguments.
         * @param spy
         * @param args
         */
        alwaysCalledWith<TArgs extends any[]>(spy: SinonSpy<TArgs>, ...args: MatchArguments<TArgs>): void;
        /**
         * Passes if spy was never called with the provided arguments.
         * @param spy
         * @param args
         */
        neverCalledWith<TArgs extends any[]>(spy: SinonSpy<TArgs>, ...args: MatchArguments<TArgs>): void;
        /**
         * Passes if spy was called with the provided arguments and no others.
         * It’s possible to assert on a dedicated spy call: sinon.assert.calledWithExactly(spy.getCall(1), arg1, arg2, ...);.
         * @param spyOrSpyCall
         * @param args
         */
        calledWithExactly<TArgs extends any[]>(
            spyOrSpyCall: SinonSpy<TArgs> | SinonSpyCall<TArgs>,
            ...args: MatchArguments<TArgs>
        ): void;
        /**
         * Passes if spy was called at exactly once with the provided arguments and no others.
         * @param spyOrSpyCall
         * @param args
         */
        calledOnceWithExactly<TArgs extends any[]>(
            spyOrSpyCall: SinonSpy<TArgs> | SinonSpyCall<TArgs>,
            ...args: MatchArguments<TArgs>
        ): void;
        /**
         * Passes if spy was always called with the provided arguments and no others.
         */
        alwaysCalledWithExactly<TArgs extends any[]>(spy: SinonSpy<TArgs>, ...args: MatchArguments<TArgs>): void;
        /**
         * Passes if spy was called with matching arguments.
         * This behaves the same way as sinon.assert.calledWith(spy, sinon.match(arg1), sinon.match(arg2), ...).
         * It's possible to assert on a dedicated spy call: sinon.assert.calledWithMatch(spy.secondCall, arg1, arg2, ...);.
         */
        calledWithMatch<TArgs extends any[]>(spyOrSpyCall: SinonSpy<TArgs> | SinonSpyCall<TArgs>, ...args: TArgs): void;
        /**
         * Passes if spy was called once with matching arguments.
         * This behaves the same way as calling both sinon.assert.calledOnce(spy) and
         * sinon.assert.calledWithMatch(spy, ...).
         */
        calledOnceWithMatch<TArgs extends any[]>(
            spyOrSpyCall: SinonSpy<TArgs> | SinonSpyCall<TArgs>,
            ...args: TArgs
        ): void;
        /**
         * Passes if spy was always called with matching arguments.
         * This behaves the same way as sinon.assert.alwaysCalledWith(spy, sinon.match(arg1), sinon.match(arg2), ...).
         */
        alwaysCalledWithMatch<TArgs extends any[]>(spy: SinonSpy<TArgs>, ...args: TArgs): void;
        /**
         * Passes if spy was never called with matching arguments.
         * This behaves the same way as sinon.assert.neverCalledWith(spy, sinon.match(arg1), sinon.match(arg2), ...).
         * @param spy
         * @param args
         */
        neverCalledWithMatch<TArgs extends any[]>(spy: SinonSpy<TArgs>, ...args: TArgs): void;
        /**
         * Passes if spy was called with the new operator.
         * It’s possible to assert on a dedicated spy call: sinon.assert.calledWithNew(spy.secondCall, arg1, arg2, ...);.
         * @param spyOrSpyCall
         */
        calledWithNew(spyOrSpyCall: SinonSpy<any> | SinonSpyCall<any>): void;
        /**
         * Passes if spy threw any exception.
         */
        threw(spyOrSpyCall: SinonSpy<any> | SinonSpyCall<any>): void;
        /**
         * Passes if spy threw the given exception.
         * The exception is an actual object.
         * It’s possible to assert on a dedicated spy call: sinon.assert.threw(spy.thirdCall, exception);.
         */
        threw(spyOrSpyCall: SinonSpy<any> | SinonSpyCall<any>, exception: string): void;
        /**
         * Passes if spy threw the given exception.
         * The exception is a String denoting its type.
         * It’s possible to assert on a dedicated spy call: sinon.assert.threw(spy.thirdCall, exception);.
         */
        threw(spyOrSpyCall: SinonSpy<any> | SinonSpyCall<any>, exception: any): void;

        /**
         * Like threw, only required for all calls to the spy.
         */
        alwaysThrew(spy: SinonSpy<any>): void;
        /**
         * Like threw, only required for all calls to the spy.
         */
        alwaysThrew(spy: SinonSpy<any>, exception: string): void;
        /**
         * Like threw, only required for all calls to the spy.
         */
        alwaysThrew(spy: SinonSpy<any>, exception: any): void;

        /**
         * Uses sinon.match to test if the arguments can be considered a match.
         */
        match(actual: any, expected: any): void;
        /**
         * Exposes assertions into another object, to better integrate with the test framework.
         * For instance, JsTestDriver uses global assertions, and to make Sinon.JS assertions appear alongside them, you can do.
         * @example sinon.assert.expose(this);
         * This will give you assertCalled(spy),assertCallOrder(spy1, spy2, ...) and so on.
         * The method accepts an optional options object with two options.
         */
        expose(obj: any, options?: Partial<SinonExposeOptions>): void;
    }

    interface SinonMatcher {
        /**
         * All matchers implement and and or. This allows to logically combine mutliple matchers.
         * The result is a new matchers that requires both (and) or one of the matchers (or) to return true.
         * @example var stringOrNumber = sinon.match.string.or(sinon.match.number);
         * var bookWithPages = sinon.match.instanceOf(Book).and(sinon.match.has("pages"));
         */
        and(expr: SinonMatcher): SinonMatcher;
        /**
         * All matchers implement and and or. This allows to logically combine mutliple matchers.
         * The result is a new matchers that requires both (and) or one of the matchers (or) to return true.
         * @example var stringOrNumber = sinon.match.string.or(sinon.match.number);
         * var bookWithPages = sinon.match.instanceOf(Book).and(sinon.match.has("pages"));
         */
        or(expr: SinonMatcher): SinonMatcher;
        test(val: any): boolean;
    }

    interface SinonArrayMatcher extends SinonMatcher {
        /**
         * Requires an Array to be deep equal another one.
         */
        deepEquals(expected: any[]): SinonMatcher;
        /**
         * Requires an Array to start with the same values as another one.
         */
        startsWith(expected: any[]): SinonMatcher;
        /**
         * Requires an Array to end with the same values as another one.
         */
        endsWith(expected: any[]): SinonMatcher;
        /**
         * Requires an Array to contain each one of the values the given array has.
         */
        contains(expected: any[]): SinonMatcher;
    }

    interface SimplifiedSet {
        has(el: any): boolean;
    }

    interface SimplifiedMap extends SimplifiedSet {
        get(key: any): any;
    }

    interface SinonMapMatcher extends SinonMatcher {
        /**
         * Requires a Map to be deep equal another one.
         */
        deepEquals(expected: SimplifiedMap): SinonMatcher;
        /**
         * Requires a Map to contain each one of the items the given map has.
         */
        contains(expected: SimplifiedMap): SinonMatcher;
    }

    interface SinonSetMatcher extends SinonMatcher {
        /**
         *  Requires a Set to be deep equal another one.
         */
        deepEquals(expected: SimplifiedSet): SinonMatcher;
        /**
         * Requires a Set to contain each one of the items the given set has.
         */
        contains(expected: SimplifiedSet): SinonMatcher;
    }

    interface SinonMatch {
        /**
         * Requires the value to be == to the given number.
         */
        (value: number): SinonMatcher;
        /**
         * Requires the value to be a string and have the expectation as a substring.
         */
        (value: string): SinonMatcher;
        /**
         * Requires the value to be a string and match the given regular expression.
         */
        (expr: RegExp): SinonMatcher;
        /**
         * See custom matchers.
         */
        (callback: (value: any) => boolean, message?: string): SinonMatcher;
        /**
         * Requires the value to be not null or undefined and have at least the same properties as expectation.
         * This supports nested matchers.
         */
        (obj: object): SinonMatcher;
        /**
         * Matches anything.
         */
        any: SinonMatcher;
        /**
         * Requires the value to be defined.
         */
        defined: SinonMatcher;
        /**
         * Requires the value to be truthy.
         */
        truthy: SinonMatcher;
        /**
         * Requires the value to be falsy.
         */
        falsy: SinonMatcher;
        /**
         * Requires the value to be a Boolean
         */
        bool: SinonMatcher;
        /**
         * Requires the value to be a Number.
         */
        number: SinonMatcher;
        /**
         * Requires the value to be a String.
         */
        string: SinonMatcher;
        /**
         * Requires the value to be an Object.
         */
        object: SinonMatcher;
        /**
         * Requires the value to be a Function.
         */
        func: SinonMatcher;
        /**
         * Requires the value to be a Map.
         */
        map: SinonMapMatcher;
        /**
         * Requires the value to be a Set.
         */
        set: SinonSetMatcher;
        /**
         * Requires the value to be an Array.
         */
        array: SinonArrayMatcher;
        /**
         * Requires the value to be a regular expression.
         */
        regexp: SinonMatcher;
        /**
         * Requires the value to be a Date object.
         */
        date: SinonMatcher;
        /**
         * Requires the value to be a Symbol.
         */
        symbol: SinonMatcher;
        /**
         * Requires the value to be in the specified array.
         */
        in(allowed: any[]): SinonMatcher;
        /**
         * Requires the value to strictly equal ref.
         */
        same(obj: any): SinonMatcher;
        /**
         * Requires the value to be of the given type, where type can be one of "undefined", "null", "boolean", "number", "string", "object", "function", "array", "regexp", "date" or "symbol".
         */
        typeOf(type: string): SinonMatcher;
        /**
         * Requires the value to be an instance of the given type.
         */
        instanceOf(type: any): SinonMatcher;
        /**
         * Requires the value to define the given property.
         * The property might be inherited via the prototype chain.
         * If the optional expectation is given, the value of the property is deeply compared with the expectation.
         * The expectation can be another matcher.
         * @param property
         * @param expect
         */
        has(property: string, expect?: any): SinonMatcher;
        /**
         * Same as sinon.match.has but the property must be defined by the value itself. Inherited properties are ignored.
         * @param property
         * @param expect
         */
        hasOwn(property: string, expect?: any): SinonMatcher;
        /**
         * Requires the value to define the given propertyPath. Dot (prop.prop) and bracket (prop[0]) notations are supported as in Lodash.get.
         * The propertyPath might be inherited via the prototype chain.
         * If the optional expectation is given, the value at the propertyPath is deeply compared with the expectation.
         * The expectation can be another matcher.
         */
        hasNested(path: string, expect?: any): SinonMatcher;
        /**
         * Requires every element of an Array, Set or Map, or alternatively every value of an Object to match the given matcher.
         */
        every(matcher: SinonMatcher): SinonMatcher;
        /**
         * Requires any element of an Array, Set or Map, or alternatively any value of an Object to match the given matcher.
         */
        some(matcher: SinonMatcher): SinonMatcher;
    }

    interface SinonSandboxConfig {
        /**
         * The sandbox’s methods can be injected into another object for convenience.
         * The injectInto configuration option can name an object to add properties to.
         */
        injectInto: object | null;
        /**
         * What properties to inject.
         * Note that simply naming “server” here is not sufficient to have a server property show up in the target object,
         * you also have to set useFakeServer to true.
         */
        properties: string[];
        /**
         * If set to true, the sandbox will have a clock property.
         * You can optionally pass in a configuration object that follows the specification for fake timers, such as { toFake: ["setTimeout", "setInterval"] }.
         */
        useFakeTimers: boolean | Partial<SinonFakeTimersConfig>;
        /**
         * If true, server and requests properties are added to the sandbox. Can also be an object to use for fake server.
         * The default one is sinon.fakeServer, but if you’re using jQuery 1.3.x or some other library that does not set the XHR’s onreadystatechange handler,
         * you might want to do:
         */
        useFakeServer: boolean | SinonFakeServer;
    }

    /**
     * Stubbed type of an object with members replaced by stubs.
     *
     * @template TType Type being stubbed.
     */
    type StubbableType<TType> = Function & { prototype: TType };

    /**
     * An instance of a stubbed object type with functions replaced by stubs.
     *
     * @template TType Object type being stubbed.
     */
    type SinonStubbedInstance<TType> = {
        [P in keyof TType]: SinonStubbedMember<TType[P]>;
    };

    /**
     * Replaces a type with a Sinon stub if it's a function.
     */
    type SinonStubbedMember<T> = T extends (...args: infer TArgs) => infer TReturnValue
        ? SinonStub<TArgs, TReturnValue>
        : T;

    interface SinonFake {
        /**
         * Creates a basic fake, with no behavior
         */
        (): SinonSpy;
        /**
         * Wraps an existing Function to record all interactions, while leaving it up to the func to provide the behavior.
         * This is useful when complex behavior not covered by the sinon.fake.* methods is required or when wrapping an existing function or method.
         */
        (fn: Function): SinonSpy;
        /**
         * Creates a fake that returns the val argument
         * @param val Returned value
         */
        returns(val: any): SinonSpy;
        /**
         * Creates a fake that throws an Error with the provided value as the message property.
         * If an Error is passed as the val argument, then that will be the thrown value. If any other value is passed, then that will be used for the message property of the thrown Error.
         * @param val Returned value or throw value if an Error
         */
        throws(val: Error | string): SinonSpy;
        /**
         * Creates a fake that returns a resolved Promise for the passed value.
         * @param val Resolved promise
         */
        resolves(val: any): SinonSpy;
        /**
         * Creates a fake that returns a rejected Promise for the passed value.
         * If an Error is passed as the value argument, then that will be the value of the promise.
         * If any other value is passed, then that will be used for the message property of the Error returned by the promise.
         * @param val Rejected promise
         */
        rejects(val: any): SinonSpy;
        /**
         * fake expects the last argument to be a callback and will invoke it with the given arguments.
         */
        yields(...args: any[]): SinonSpy;
        /**
         * fake expects the last argument to be a callback and will invoke it asynchronously with the given arguments.
         */
        yieldsAsync(...args: any[]): SinonSpy;
    }

    interface SinonSandbox {
        /**
         * A convenience reference for sinon.assert
         * Since sinon@2.0.0
         */
        assert: SinonAssert;
        clock: SinonFakeTimers;
        requests: SinonFakeXMLHttpRequest[];
        server: SinonFakeServer;
        match: SinonMatch;
        /**
         * Works exactly like sinon.spy
         */
        spy: SinonSpyStatic;
        /**
         * Works exactly like sinon.stub.
         */
        stub: SinonStubStatic;
        /**
         * Works exactly like sinon.mock
         */
        mock: SinonMockStatic;

        fake: SinonFake;

        /**
         * * No param : Causes Sinon to replace the global setTimeout, clearTimeout, setInterval, clearInterval, setImmediate, clearImmediate, process.hrtime, performance.now(when available)
         * and Date with a custom implementation which is bound to the returned clock object.
         * Starts the clock at the UNIX epoch (timestamp of 0).
         * * Now : As above, but rather than starting the clock with a timestamp of 0, start at the provided timestamp now.
         * Since sinon@2.0.0
         * You can also pass in a Date object, and its getTime() will be used for the starting timestamp.
         * * Config : As above, but allows further configuration options, some of which are:
         * * config.now - Number/Date - installs lolex with the specified unix epoch (default: 0)
         * * config.toFake - String[ ] - an array with explicit function names to fake.
         * By default lolex will automatically fake all methods except process.nextTick. You could, however, still fake nextTick by providing it explicitly
         * * config.shouldAdvanceTime - Boolean - tells lolex to increment mocked time automatically based on the real system time shift (default: false)
         * * Please visit the lolex.install documentation for the full feature set.
         * * Important note: when faking nextTick, normal calls to process.nextTick() would not execute automatically as they would during normal event-loop phases.
         * You would have to call either clock.next(), clock.tick(), clock.runAll() or clock.runToLast() (see example below). Please refer to the lolex documentation for more information.
         * @param config
         */
        useFakeTimers(config?: number | Date | Partial<SinonFakeTimersConfig>): SinonFakeTimers;
        /**
         * Causes Sinon to replace the native XMLHttpRequest object in browsers that support it with a custom implementation which does not send actual requests.
         * In browsers that support ActiveXObject, this constructor is replaced, and fake objects are returned for XMLHTTP progIds.
         * Other progIds, such as XMLDOM are left untouched.
         * The native XMLHttpRequest object will be available at sinon.xhr.XMLHttpRequest
         */
        useFakeXMLHttpRequest(): SinonFakeXMLHttpRequestStatic;
        /**
         * Fakes XHR and binds a server object to the sandbox such that it too is restored when calling sandbox.restore().
         * Access requests through sandbox.requests and server through sandbox.server
         */
        useFakeServer(): SinonFakeServer;
        /**
         * Restores all fakes created through sandbox.
         */
        restore(): void;
        /**
         * Resets the internal state of all fakes created through sandbox.
         */
        reset(): void;
        /**
         * Resets the history of all stubs created through the sandbox.
         * Since sinon@2.0.0
         */
        resetHistory(): void;
        /**
         * Resets the behaviour of all stubs created through the sandbox.
         * Since sinon@2.0.0
         */
        resetBehavior(): void;
        /**
         * Causes all stubs created from the sandbox to return promises using a specific Promise library instead of the global one when using stub.rejects or stub.resolves.
         * Returns the stub to allow chaining.
         * Since sinon@2.0.0
         */
        usingPromise(promiseLibrary: any): SinonSandbox;
        /**
         * Verifies all mocks created through the sandbox.
         */
        verify(): void;
        /**
         * Verifies all mocks and restores all fakes created through the sandbox.
         */
        verifyAndRestore(): void;

        /**
         * Replaces property on object with replacement argument. Attempts to replace an already replaced value cause an exception.
         * replacement can be any value, including spies, stubs and fakes.
         * This method only works on non-accessor properties, for replacing accessors, use sandbox.replaceGetter() and sandbox.replaceSetter().
         */
        replace<T, TKey extends keyof T>(obj: T, prop: TKey, replacement: T[TKey]): T[TKey];
        /**
         * Replaces getter for property on object with replacement argument. Attempts to replace an already replaced getter cause an exception.
         * replacement must be a Function, and can be instances of spies, stubs and fakes.
         * @param obj
         * @param prop
         * @param replacement
         */
        replaceGetter<T, TKey extends keyof T>(obj: T, prop: TKey, replacement: () => T[TKey]): () => T[TKey];
        /**
         * Replaces setter for property on object with replacement argument. Attempts to replace an already replaced setter cause an exception.
         * replacement must be a Function, and can be instances of spies, stubs and fakes.
         * @param obj
         * @param prop
         * @param replacement
         */
        replaceSetter<T, TKey extends keyof T>(
            obj: T,
            prop: TKey,
            replacement: (val: T[TKey]) => void,
        ): (val: T[TKey]) => void;

        /**
         * Creates a new object with the given functions as the prototype and stubs all implemented functions.
         *
         * @template TType Type being stubbed.
         * @param constructor   Object or class to stub.
         * @param overrides     An optional map overriding created stubs
         * @returns A stubbed version of the constructor.
         * @remarks The given constructor function is not invoked. See also the stub API.
         */
        createStubInstance<TType>(
            constructor: StubbableType<TType>,
            overrides?: {
                [K in keyof TType]?:
                    | SinonStubbedMember<TType[K]>
                    | (TType[K] extends (...args: any[]) => infer R ? R : TType[K]);
            },
        ): SinonStubbedInstance<TType>;
    }

    interface SinonApi {
        expectation: SinonExpectationStatic;

        clock: {
            create(now: number | Date): SinonFakeTimers;
        };

        FakeXMLHttpRequest: SinonFakeXMLHttpRequestStatic;

        fakeServer: SinonFakeServerStatic;
        fakeServerWithClock: SinonFakeServerStatic;

        /**
         * Creates a new sandbox object with spies, stubs, and mocks.
         * @param config
         */
        createSandbox(config?: Partial<SinonSandboxConfig>): SinonSandbox;
        defaultConfig: Partial<SinonSandboxConfig>;

        /**
         * Add a custom behavior.
         * The name will be available as a function on stubs, and the chaining mechanism
         * will be set up for you (e.g. no need to return anything from your function,
         * its return value will be ignored). The fn will be passed the fake instance
         * as its first argument, and then the user's arguments.
         */
        addBehavior: (name: string, fn: (fake: SinonStub, ...userArgs: any[]) => void) => void;

        /**
         * Replace the default formatter used when formatting ECMAScript object
         * An example converts a basic object, such as  {id: 42 }, to a string
         * on a format of your choosing, such as "{ id: 42 }"
         */
        setFormatter: (customFormatter: (...args: any[]) => string) => void;
    }

    type SinonStatic = SinonSandbox & SinonApi;
}

declare const Sinon: Sinon.SinonStatic;

export = Sinon;
export as namespace sinon;
