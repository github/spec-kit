// Type definitions for @sinonjs/fake-timers 8.1
// Project: https://github.com/sinonjs/fake-timers
// Definitions by: Wim Looman <https://github.com/Nemo157>
//                 Rogier Schouten <https://github.com/rogierschouten>
//                 Yishai Zehavi <https://github.com/zyishai>
//                 Remco Haszing <https://github.com/remcohaszing>
//                 Jaden Simon <https://github.com/JadenSimon>
// Definitions: https://github.com/DefinitelyTyped/DefinitelyTyped
// TypeScript Version: 2.3

/**
 * Names of clock methods that may be faked by install.
 */
export type FakeMethod =
    | 'setTimeout'
    | 'clearTimeout'
    | 'setImmediate'
    | 'clearImmediate'
    | 'setInterval'
    | 'clearInterval'
    | 'Date'
    | 'nextTick'
    | 'hrtime'
    | 'requestAnimationFrame'
    | 'cancelAnimationFrame'
    | 'requestIdleCallback'
    | 'cancelIdleCallback'
    | 'performance';

/**
 * Global methods avaliable to every clock and also as standalone methods (inside `timers` global object).
 */
export interface GlobalTimers<TTimerId extends TimerId> {
    /**
     * Schedules a callback to be fired once timeout milliseconds have ticked by.
     *
     * @param callback   Callback to be fired.
     * @param timeout   How many ticks to wait to run the callback.
     * @param args   Any extra arguments to pass to the callback.
     * @returns Time identifier for cancellation.
     */
    setTimeout: (callback: (...args: any[]) => void, timeout: number, ...args: any[]) => TTimerId;

    /**
     * Clears a timer, as long as it was created using setTimeout.
     *
     * @param id   Timer ID or object.
     */
    clearTimeout: (id: TTimerId) => void;

    /**
     * Schedules a callback to be fired every time timeout milliseconds have ticked by.
     *
     * @param callback   Callback to be fired.
     * @param timeout   How many ticks to wait between callbacks.
     * @param args   Any extra arguments to pass to the callback.
     * @returns Time identifier for cancellation.
     */
    setInterval: (callback: (...args: any[]) => void, timeout: number, ...args: any[]) => TTimerId;

    /**
     * Clears a timer, as long as it was created using setInterval.
     *
     * @param id   Timer ID or object.
     */
    clearInterval: (id: TTimerId) => void;

    /**
     * Schedules the callback to be fired once 0 milliseconds have ticked by.
     *
     * @param callback   Callback to be fired.
     * @param args   Any extra arguments to pass to the callback.
     * @remarks You'll still have to call clock.tick() for the callback to fire.
     * @remarks If called during a tick the callback won't fire until 1 millisecond has ticked by.
     */
    setImmediate: (callback: (...args: any[]) => void, ...args: any[]) => TTimerId;

    /**
     * Clears a timer, as long as it was created using setImmediate.
     *
     * @param id   Timer ID or object.
     */
    clearImmediate: (id: TTimerId) => void;

    /**
     * Implements the Date object but using this clock to provide the correct time.
     */
    Date: typeof Date;
}

/**
 * Timer object used in node.
 */
export interface NodeTimer {
    /**
     * Stub method call. Does nothing.
     */
    ref(): NodeTimer;

    /**
     * Stub method call. Does nothing.
     */
    unref(): NodeTimer;

    /**
     * Refreshes the timer.
     */
    refresh(): NodeTimer;
}

/**
 * Timer identifier for clock scheduling.
 */
export type TimerId = number | NodeTimer;

/**
 * Controls the flow of time.
 */
export interface FakeClock<TTimerId extends TimerId> extends GlobalTimers<TTimerId> {
    /**
     * Current clock time.
     */
    now: number;

    /**
     * Mimics performance.now().
     */
    performance: {
        now: () => number;
    };

    /**
     * Don't know what this prop is for, but it was included in the clocks that `createClock` or
     * `install` return (it is never used in the code, for now).
     */
    timeouts: {};

    /**
     * Maximum number of timers that will be run when calling runAll().
     */
    loopLimit: number;

    /**
     * Schedule callback to run in the next animation frame.
     *
     * @param callback   Callback to be fired.
     * @returns Request id.
     */
    requestAnimationFrame: (callback: (time: number) => void) => TTimerId;

    /**
     * Cancel animation frame request.
     *
     * @param id   The id returned from requestAnimationFrame method.
     */
    cancelAnimationFrame: (id: TTimerId) => void;

    /**
     * Queues the callback to be fired during idle periods to perform background and low priority work on the main event loop.
     *
     * @param callback   Callback to be fired.
     * @param timeout   The maximum number of ticks before the callback must be fired.
     * @remarks Callbacks which have a timeout option will be fired no later than time in milliseconds.
     */
    requestIdleCallback: (callback: () => void, timeout?: number) => TTimerId;

    /**
     * Clears a timer, as long as it was created using requestIdleCallback.
     *
     * @param id   Timer ID or object.
     */
    cancelIdleCallback: (id: TTimerId) => void;

    /**
     * Get the number of waiting timers.
     *
     * @returns number of waiting timers.
     */
    countTimers: () => number;

    /**
     * Advances the clock to the the moment of the first scheduled timer, firing it.
     * @returns Fake milliseconds since the unix epoch.
     */
    next: () => number;

    /**
     * Advances the clock to the the moment of the first scheduled timer, firing it.
     *
     * Also breaks the event loop, allowing any scheduled promise callbacks to execute _before_ running the timers.
     * @returns Fake milliseconds since the unix epoch.
     */
    nextAsync: () => Promise<number>;

    /**
     * Advance the clock, firing callbacks if necessary.
     *
     * @param time   How many ticks to advance by.
     * @returns Fake milliseconds since the unix epoch.
     */
    tick: (time: number | string) => number;

    /**
     * Advance the clock, firing callbacks if necessary.
     *
     * Also breaks the event loop, allowing any scheduled promise callbacks to execute _before_ running the timers.
     *
     * @param time   How many ticks to advance by.
     * @returns Fake milliseconds since the unix epoch.
     */
    tickAsync: (time: number | string) => Promise<number>;

    /**
     * Removes all timers and tick without firing them and restore now to its original value.
     */
    reset: () => void;

    /**
     * Runs all pending timers until there are none remaining.
     *
     * @remarks  If new timers are added while it is executing they will be run as well.
     * @returns Fake milliseconds since the unix epoch.
     */
    runAll: () => number;

    /**
     * Runs all pending timers until there are none remaining.
     *
     * Also breaks the event loop, allowing any scheduled promise callbacks to execute _before_ running the timers.
     *
     * @remarks  If new timers are added while it is executing they will be run as well.
     * @returns Fake milliseconds since the unix epoch.
     */
    runAllAsync: () => Promise<number>;

    /**
     * Advanced the clock to the next animation frame while firing all scheduled callbacks.
     * @returns Fake milliseconds since the unix epoch.
     */
    runToFrame: () => number;

    /**
     * Takes note of the last scheduled timer when it is run, and advances the clock to
     * that time firing callbacks as necessary.
     * @returns Fake milliseconds since the unix epoch.
     */
    runToLast: () => number;

    /**
     * Takes note of the last scheduled timer when it is run, and advances the clock to
     * that time firing callbacks as necessary.
     *
     * Also breaks the event loop, allowing any scheduled promise callbacks to execute _before_ running the timers.
     * @returns Fake milliseconds since the unix epoch.
     */
    runToLastAsync: () => Promise<number>;

    /**
     * Simulates a user changing the system clock.
     *
     * @param now   New system time.
     * @remarks This affects the current time but it does not in itself cause timers to fire.
     */
    setSystemTime: (now?: number | Date) => void;
}

/**
 * Fake clock for a browser environment.
 */
export type BrowserClock = FakeClock<number>;

/**
 * Fake clock for a Node environment.
 */
export type NodeClock = FakeClock<NodeTimer> & {
    /**
     * Mimicks process.hrtime().
     *
     * @param prevTime   Previous system time to calculate time elapsed.
     * @returns High resolution real time as [seconds, nanoseconds].
     */
    hrtime(prevTime?: [number, number]): [number, number];

    /**
     * Mimics process.nextTick() explicitly dropping additional arguments.
     */
    queueMicrotask: (callback: () => void) => void;

    /**
     * Simulates process.nextTick().
     */
    nextTick: (callback: (...args: any[]) => void, ...args: any[]) => void;

    /**
     * Run all pending microtasks scheduled with nextTick.
     */
    runMicrotasks: () => void;
};

/**
 * Clock object created by @sinonjs/fake-timers.
 */
export type Clock = BrowserClock | NodeClock;

/**
 * Additional methods that installed clock have.
 */
export interface InstalledMethods {
    /**
     * Restores the original methods on the context that was passed to FakeTimers.install,
     * or the native timers if no context was given.
     */
    uninstall: () => void;

    methods: FakeMethod[];
}

/**
 * Clock object created by calling `install();`.
 */
export type InstalledClock = Clock & InstalledMethods;

/**
 * Creates a clock.
 *
 * @param now   Current time for the clock.
 * @param loopLimit    Maximum number of timers that will be run when calling runAll()
 *                     before assuming that we have an infinite loop and throwing an error
 *                     (by default, 1000).
 * @remarks The default epoch is 0.
 */
export function createClock(now?: number | Date, loopLimit?: number): Clock;

export interface FakeTimerInstallOpts {
    /**
     * Installs fake timers with the specified unix epoch (default: 0)
     */
    now?: number | Date | undefined;

    /**
     * An array with explicit function names to hijack. When not set, @sinonjs/fake-timers will automatically fake all methods except nextTick
     * e.g., FakeTimers.install({ toFake: ["setTimeout", "nextTick"]}) will fake only setTimeout and nextTick
     */
    toFake?: FakeMethod[] | undefined;

    /**
     * The maximum number of timers that will be run when calling runAll() (default: 1000)
     */
    loopLimit?: number | undefined;

    /**
     * Tells @sinonjs/fake-timers to increment mocked time automatically based on the real system time shift (e.g. the mocked time will be incremented by
     * 20ms for every 20ms change in the real system time) (default: false)
     */
    shouldAdvanceTime?: boolean | undefined;

    /**
     * Relevant only when using with shouldAdvanceTime: true. increment mocked time by advanceTimeDelta ms every advanceTimeDelta ms change
     * in the real system time (default: 20)
     */
    advanceTimeDelta?: number | undefined;

    /**
     * Tells FakeTimers to clear 'native' (i.e. not fake) timers by delegating to their respective handlers. These are not cleared by
     * default, leading to potentially unexpected behavior if timers existed prior to installing FakeTimers. (default: false)
     */
    shouldClearNativeTimers?: boolean | undefined;
}

/**
 * Creates a clock and installs it globally.
 *
 * @param [opts]   Options for the fake timer.
 */
export function install(opts?: FakeTimerInstallOpts): InstalledClock;

export interface FakeTimerWithContext {
    timers: GlobalTimers<TimerId>;
    createClock: (now?: number | Date, loopLimit?: number) => Clock;
    install: (opts?: FakeTimerInstallOpts) => InstalledClock;
    withGlobal: (global: object) => FakeTimerWithContext;
}

/**
 * Apply new context to fake timers.
 *
 * @param global   New context to apply like `window` (in browsers) or `global` (in node).
 */
export function withGlobal(global: object): FakeTimerWithContext;

export const timers: GlobalTimers<TimerId>;
