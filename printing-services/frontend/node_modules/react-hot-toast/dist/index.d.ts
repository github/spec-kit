import * as react from 'react';
import { CSSProperties } from 'react';
import * as goober from 'goober';

type ToastType = 'success' | 'error' | 'loading' | 'blank' | 'custom';
type ToastPosition = 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right';
type Renderable = React.ReactElement | string | null;
interface IconTheme {
    primary: string;
    secondary: string;
}
type ValueFunction<TValue, TArg> = (arg: TArg) => TValue;
type ValueOrFunction<TValue, TArg> = TValue | ValueFunction<TValue, TArg>;
declare const resolveValue: <TValue, TArg>(valOrFunction: ValueOrFunction<TValue, TArg>, arg: TArg) => TValue;
interface Toast {
    type: ToastType;
    id: string;
    toasterId?: string;
    message: ValueOrFunction<Renderable, Toast>;
    icon?: Renderable;
    duration?: number;
    pauseDuration: number;
    position?: ToastPosition;
    removeDelay?: number;
    ariaProps: {
        role: 'status' | 'alert';
        'aria-live': 'assertive' | 'off' | 'polite';
    };
    style?: CSSProperties;
    className?: string;
    iconTheme?: IconTheme;
    createdAt: number;
    visible: boolean;
    dismissed: boolean;
    height?: number;
}
type ToastOptions = Partial<Pick<Toast, 'id' | 'icon' | 'duration' | 'ariaProps' | 'className' | 'style' | 'position' | 'iconTheme' | 'toasterId' | 'removeDelay'>>;
type DefaultToastOptions = ToastOptions & {
    [key in ToastType]?: ToastOptions;
};
interface ToasterProps {
    position?: ToastPosition;
    toastOptions?: DefaultToastOptions;
    reverseOrder?: boolean;
    gutter?: number;
    containerStyle?: React.CSSProperties;
    containerClassName?: string;
    toasterId?: string;
    children?: (toast: Toast) => React.ReactElement;
}

type Message = ValueOrFunction<Renderable, Toast>;
type ToastHandler = (message: Message, options?: ToastOptions) => string;
declare const toast: {
    (message: Message, opts?: ToastOptions): string;
    error: ToastHandler;
    success: ToastHandler;
    loading: ToastHandler;
    custom: ToastHandler;
    dismiss(toastId?: string, toasterId?: string): void;
    dismissAll(toasterId?: string): void;
    remove(toastId?: string, toasterId?: string): void;
    removeAll(toasterId?: string): void;
    promise<T>(promise: Promise<T> | (() => Promise<T>), msgs: {
        loading: Renderable;
        success?: ValueOrFunction<Renderable, T>;
        error?: ValueOrFunction<Renderable, any>;
    }, opts?: DefaultToastOptions): Promise<T>;
};

declare const useToaster: (toastOptions?: DefaultToastOptions, toasterId?: string) => {
    toasts: Toast[];
    handlers: {
        updateHeight: (toastId: string, height: number) => void;
        startPause: () => void;
        endPause: () => void;
        calculateOffset: (toast: Toast, opts?: {
            reverseOrder?: boolean;
            gutter?: number;
            defaultPosition?: ToastPosition;
        }) => number;
    };
};

interface ToasterSettings {
    toastLimit: number;
}
interface ToasterState {
    toasts: Toast[];
    settings: ToasterSettings;
    pausedAt: number | undefined;
}
declare const useStore: (toastOptions?: DefaultToastOptions, toasterId?: string) => ToasterState;

interface ToastBarProps {
    toast: Toast;
    position?: ToastPosition;
    style?: react.CSSProperties;
    children?: (components: {
        icon: Renderable;
        message: Renderable;
    }) => Renderable;
}
declare const ToastBar: react.FC<ToastBarProps>;

interface ErrorTheme {
    primary?: string;
    secondary?: string;
}
declare const ErrorIcon: goober.StyledVNode<Omit<react.ClassAttributes<HTMLDivElement> & react.HTMLAttributes<HTMLDivElement> & goober.DefaultTheme & ErrorTheme, never>>;

interface LoaderTheme {
    primary?: string;
    secondary?: string;
}
declare const LoaderIcon: goober.StyledVNode<Omit<react.ClassAttributes<HTMLDivElement> & react.HTMLAttributes<HTMLDivElement> & goober.DefaultTheme & LoaderTheme, never>>;

interface CheckmarkTheme {
    primary?: string;
    secondary?: string;
}
declare const CheckmarkIcon: goober.StyledVNode<Omit<react.ClassAttributes<HTMLDivElement> & react.HTMLAttributes<HTMLDivElement> & goober.DefaultTheme & CheckmarkTheme, never>>;

declare const ToastIcon: react.FC<{
    toast: Toast;
}>;

declare const Toaster: react.FC<ToasterProps>;

export { CheckmarkIcon, DefaultToastOptions, ErrorIcon, IconTheme, LoaderIcon, Renderable, Toast, ToastBar, ToastIcon, ToastOptions, ToastPosition, ToastType, Toaster, ToasterProps, ValueFunction, ValueOrFunction, toast as default, resolveValue, toast, useToaster, useStore as useToasterStore };
