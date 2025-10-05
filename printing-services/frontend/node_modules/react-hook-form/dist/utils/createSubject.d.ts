import type { Noop } from '../types';
export type Observer<T> = {
    next: (value: T) => void;
};
export type Subscription = {
    unsubscribe: Noop;
};
export type Subject<T> = {
    readonly observers: Observer<T>[];
    subscribe: (value: Observer<T>) => Subscription;
    unsubscribe: Noop;
} & Observer<T>;
declare const _default: <T>() => Subject<T>;
export default _default;
//# sourceMappingURL=createSubject.d.ts.map