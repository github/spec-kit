import {
  Renderable,
  Toast,
  ToastOptions,
  ToastType,
  DefaultToastOptions,
  ValueOrFunction,
  resolveValue,
} from './types';
import { genId } from './utils';
import {
  createDispatch,
  Action,
  ActionType,
  dispatchAll,
  getToasterIdFromToastId,
} from './store';

type Message = ValueOrFunction<Renderable, Toast>;

type ToastHandler = (message: Message, options?: ToastOptions) => string;

const createToast = (
  message: Message,
  type: ToastType = 'blank',
  opts?: ToastOptions
): Toast => ({
  createdAt: Date.now(),
  visible: true,
  dismissed: false,
  type,
  ariaProps: {
    role: 'status',
    'aria-live': 'polite',
  },
  message,
  pauseDuration: 0,
  ...opts,
  id: opts?.id || genId(),
});

const createHandler =
  (type?: ToastType): ToastHandler =>
  (message, options) => {
    const toast = createToast(message, type, options);

    const dispatch = createDispatch(
      toast.toasterId || getToasterIdFromToastId(toast.id)
    );

    dispatch({ type: ActionType.UPSERT_TOAST, toast });
    return toast.id;
  };

const toast = (message: Message, opts?: ToastOptions) =>
  createHandler('blank')(message, opts);

toast.error = createHandler('error');
toast.success = createHandler('success');
toast.loading = createHandler('loading');
toast.custom = createHandler('custom');

/**
 * Dismisses the toast with the given id. If no id is given, dismisses all toasts.
 * The toast will transition out and then be removed from the DOM.
 * Applies to all toasters, except when a `toasterId` is given.
 */
toast.dismiss = (toastId?: string, toasterId?: string) => {
  const action: Action = {
    type: ActionType.DISMISS_TOAST,
    toastId,
  };

  if (toasterId) {
    createDispatch(toasterId)(action);
  } else {
    dispatchAll(action);
  }
};

/**
 * Dismisses all toasts.
 */
toast.dismissAll = (toasterId?: string) => toast.dismiss(undefined, toasterId);

/**
 * Removes the toast with the given id.
 * The toast will be removed from the DOM without any transition.
 */
toast.remove = (toastId?: string, toasterId?: string) => {
  const action: Action = {
    type: ActionType.REMOVE_TOAST,
    toastId,
  };
  if (toasterId) {
    createDispatch(toasterId)(action);
  } else {
    dispatchAll(action);
  }
};

/**
 * Removes all toasts.
 */
toast.removeAll = (toasterId?: string) => toast.remove(undefined, toasterId);

/**
 * Create a loading toast that will automatically updates with the promise.
 */
toast.promise = <T>(
  promise: Promise<T> | (() => Promise<T>),
  msgs: {
    loading: Renderable;
    success?: ValueOrFunction<Renderable, T>;
    error?: ValueOrFunction<Renderable, any>;
  },
  opts?: DefaultToastOptions
) => {
  const id = toast.loading(msgs.loading, { ...opts, ...opts?.loading });

  if (typeof promise === 'function') {
    promise = promise();
  }

  promise
    .then((p) => {
      const successMessage = msgs.success
        ? resolveValue(msgs.success, p)
        : undefined;

      if (successMessage) {
        toast.success(successMessage, {
          id,
          ...opts,
          ...opts?.success,
        });
      } else {
        toast.dismiss(id);
      }
      return p;
    })
    .catch((e) => {
      const errorMessage = msgs.error ? resolveValue(msgs.error, e) : undefined;

      if (errorMessage) {
        toast.error(errorMessage, {
          id,
          ...opts,
          ...opts?.error,
        });
      } else {
        toast.dismiss(id);
      }
    });

  return promise;
};

export { toast };
