type NotifyCallback = () => void;
type NotifyFunction = (callback: () => void) => void;
type BatchNotifyFunction = (callback: () => void) => void;
type BatchCallsCallback<T extends Array<unknown>> = (...args: T) => void;
type ScheduleFunction = (callback: () => void) => void;
declare const defaultScheduler: ScheduleFunction;
declare function createNotifyManager(): {
    readonly batch: <T>(callback: () => T) => T;
    /**
     * All calls to the wrapped function will be batched.
     */
    readonly batchCalls: <T extends Array<unknown>>(callback: BatchCallsCallback<T>) => BatchCallsCallback<T>;
    readonly schedule: (callback: NotifyCallback) => void;
    /**
     * Use this method to set a custom notify function.
     * This can be used to for example wrap notifications with `React.act` while running tests.
     */
    readonly setNotifyFunction: (fn: NotifyFunction) => void;
    /**
     * Use this method to set a custom function to batch notifications together into a single tick.
     * By default React Query will use the batch function provided by ReactDOM or React Native.
     */
    readonly setBatchNotifyFunction: (fn: BatchNotifyFunction) => void;
    readonly setScheduler: (fn: ScheduleFunction) => void;
};
declare const notifyManager: {
    readonly batch: <T>(callback: () => T) => T;
    /**
     * All calls to the wrapped function will be batched.
     */
    readonly batchCalls: <T extends Array<unknown>>(callback: BatchCallsCallback<T>) => BatchCallsCallback<T>;
    readonly schedule: (callback: NotifyCallback) => void;
    /**
     * Use this method to set a custom notify function.
     * This can be used to for example wrap notifications with `React.act` while running tests.
     */
    readonly setNotifyFunction: (fn: NotifyFunction) => void;
    /**
     * Use this method to set a custom function to batch notifications together into a single tick.
     * By default React Query will use the batch function provided by ReactDOM or React Native.
     */
    readonly setBatchNotifyFunction: (fn: BatchNotifyFunction) => void;
    readonly setScheduler: (fn: ScheduleFunction) => void;
};

export { createNotifyManager, defaultScheduler, notifyManager };
