import { Subscribable } from './subscribable.js';

type Listener = (focused: boolean) => void;
type SetupFn = (setFocused: (focused?: boolean) => void) => (() => void) | undefined;
declare class FocusManager extends Subscribable<Listener> {
    #private;
    constructor();
    protected onSubscribe(): void;
    protected onUnsubscribe(): void;
    setEventListener(setup: SetupFn): void;
    setFocused(focused?: boolean): void;
    onFocus(): void;
    isFocused(): boolean;
}
declare const focusManager: FocusManager;

export { FocusManager, focusManager };
