import { Subscribable } from './subscribable.cjs';

type Listener = (online: boolean) => void;
type SetupFn = (setOnline: Listener) => (() => void) | undefined;
declare class OnlineManager extends Subscribable<Listener> {
    #private;
    constructor();
    protected onSubscribe(): void;
    protected onUnsubscribe(): void;
    setEventListener(setup: SetupFn): void;
    setOnline(online: boolean): void;
    isOnline(): boolean;
}
declare const onlineManager: OnlineManager;

export { OnlineManager, onlineManager };
