/**
 * {@link TimeoutManager} does not support passing arguments to the callback.
 *
 * `(_: void)` is the argument type inferred by TypeScript's default typings for
 * `setTimeout(cb, number)`.
 * If we don't accept a single void argument, then
 * `new Promise(resolve => timeoutManager.setTimeout(resolve, N))` is a type error.
 */
type TimeoutCallback = (_: void) => void;
/**
 * Wrapping `setTimeout` is awkward from a typing perspective because platform
 * typings may extend the return type of `setTimeout`. For example, NodeJS
 * typings add `NodeJS.Timeout`; but a non-default `timeoutManager` may not be
 * able to return such a type.
 */
type ManagedTimerId = number | {
    [Symbol.toPrimitive]: () => number;
};
/**
 * Backend for timer functions.
 */
type TimeoutProvider<TTimerId extends ManagedTimerId = ManagedTimerId> = {
    readonly setTimeout: (callback: TimeoutCallback, delay: number) => TTimerId;
    readonly clearTimeout: (timeoutId: TTimerId | undefined) => void;
    readonly setInterval: (callback: TimeoutCallback, delay: number) => TTimerId;
    readonly clearInterval: (intervalId: TTimerId | undefined) => void;
};
declare const defaultTimeoutProvider: TimeoutProvider<ReturnType<typeof setTimeout>>;
/**
 * Allows customization of how timeouts are created.
 *
 * @tanstack/query-core makes liberal use of timeouts to implement `staleTime`
 * and `gcTime`. The default TimeoutManager provider uses the platform's global
 * `setTimeout` implementation, which is known to have scalability issues with
 * thousands of timeouts on the event loop.
 *
 * If you hit this limitation, consider providing a custom TimeoutProvider that
 * coalesces timeouts.
 */
declare class TimeoutManager implements Omit<TimeoutProvider, 'name'> {
    #private;
    setTimeoutProvider<TTimerId extends ManagedTimerId>(provider: TimeoutProvider<TTimerId>): void;
    setTimeout(callback: TimeoutCallback, delay: number): ManagedTimerId;
    clearTimeout(timeoutId: ManagedTimerId | undefined): void;
    setInterval(callback: TimeoutCallback, delay: number): ManagedTimerId;
    clearInterval(intervalId: ManagedTimerId | undefined): void;
}
declare const timeoutManager: TimeoutManager;
/**
 * In many cases code wants to delay to the next event loop tick; this is not
 * mediated by {@link timeoutManager}.
 *
 * This function is provided to make auditing the `tanstack/query-core` for
 * incorrect use of system `setTimeout` easier.
 */
declare function systemSetTimeoutZero(callback: TimeoutCallback): void;

export { type ManagedTimerId, type TimeoutCallback, TimeoutManager, type TimeoutProvider, defaultTimeoutProvider, systemSetTimeoutZero, timeoutManager };
