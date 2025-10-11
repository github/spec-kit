import { useEffect, useState, useRef } from 'react';
import { DefaultToastOptions, Toast, ToastType } from './types';

export const TOAST_EXPIRE_DISMISS_DELAY = 1000;
export const TOAST_LIMIT = 20;
export const DEFAULT_TOASTER_ID = 'default';

interface ToasterSettings {
  toastLimit: number;
}

export enum ActionType {
  ADD_TOAST,
  UPDATE_TOAST,
  UPSERT_TOAST,
  DISMISS_TOAST,
  REMOVE_TOAST,
  START_PAUSE,
  END_PAUSE,
}

export type Action =
  | {
      type: ActionType.ADD_TOAST;
      toast: Toast;
    }
  | {
      type: ActionType.UPSERT_TOAST;
      toast: Toast;
    }
  | {
      type: ActionType.UPDATE_TOAST;
      toast: Partial<Toast>;
    }
  | {
      type: ActionType.DISMISS_TOAST;
      toastId?: string;
    }
  | {
      type: ActionType.REMOVE_TOAST;
      toastId?: string;
    }
  | {
      type: ActionType.START_PAUSE;
      time: number;
    }
  | {
      type: ActionType.END_PAUSE;
      time: number;
    };

interface ToasterState {
  toasts: Toast[];
  settings: ToasterSettings;
  pausedAt: number | undefined;
}

interface State {
  [toasterId: string]: ToasterState;
}

export const reducer = (state: ToasterState, action: Action): ToasterState => {
  const { toastLimit } = state.settings;

  switch (action.type) {
    case ActionType.ADD_TOAST:
      return {
        ...state,
        toasts: [action.toast, ...state.toasts].slice(0, toastLimit),
      };

    case ActionType.UPDATE_TOAST:
      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === action.toast.id ? { ...t, ...action.toast } : t
        ),
      };

    case ActionType.UPSERT_TOAST:
      const { toast } = action;
      return reducer(state, {
        type: state.toasts.find((t) => t.id === toast.id)
          ? ActionType.UPDATE_TOAST
          : ActionType.ADD_TOAST,
        toast,
      });

    case ActionType.DISMISS_TOAST:
      const { toastId } = action;

      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === toastId || toastId === undefined
            ? {
                ...t,
                dismissed: true,
                visible: false,
              }
            : t
        ),
      };
    case ActionType.REMOVE_TOAST:
      if (action.toastId === undefined) {
        return {
          ...state,
          toasts: [],
        };
      }
      return {
        ...state,
        toasts: state.toasts.filter((t) => t.id !== action.toastId),
      };

    case ActionType.START_PAUSE:
      return {
        ...state,
        pausedAt: action.time,
      };

    case ActionType.END_PAUSE:
      const diff = action.time - (state.pausedAt || 0);

      return {
        ...state,
        pausedAt: undefined,
        toasts: state.toasts.map((t) => ({
          ...t,
          pauseDuration: t.pauseDuration + diff,
        })),
      };
  }
};

const listeners: Array<
  [toasterId: string, reducer: (state: ToasterState) => void]
> = [];

const defaultToasterState: ToasterState = {
  toasts: [],
  pausedAt: undefined,
  settings: {
    toastLimit: TOAST_LIMIT,
  },
};
let memoryState: State = {};

export const dispatch = (action: Action, toasterId = DEFAULT_TOASTER_ID) => {
  memoryState[toasterId] = reducer(
    memoryState[toasterId] || defaultToasterState,
    action
  );
  listeners.forEach(([id, listener]) => {
    if (id === toasterId) {
      listener(memoryState[toasterId]);
    }
  });
};

export const dispatchAll = (action: Action) =>
  Object.keys(memoryState).forEach((toasterId) => dispatch(action, toasterId));

export const getToasterIdFromToastId = (toastId: string) =>
  Object.keys(memoryState).find((toasterId) =>
    memoryState[toasterId].toasts.some((t) => t.id === toastId)
  );

export const createDispatch =
  (toasterId = DEFAULT_TOASTER_ID) =>
  (action: Action) => {
    dispatch(action, toasterId);
  };

export const defaultTimeouts: {
  [key in ToastType]: number;
} = {
  blank: 4000,
  error: 4000,
  success: 2000,
  loading: Infinity,
  custom: 4000,
};

export const useStore = (
  toastOptions: DefaultToastOptions = {},
  toasterId: string = DEFAULT_TOASTER_ID
): ToasterState => {
  const [state, setState] = useState<ToasterState>(
    memoryState[toasterId] || defaultToasterState
  );
  const initial = useRef(memoryState[toasterId]);

  // TODO: Switch to useSyncExternalStore when targeting React 18+
  useEffect(() => {
    if (initial.current !== memoryState[toasterId]) {
      setState(memoryState[toasterId]);
    }
    listeners.push([toasterId, setState]);
    return () => {
      const index = listeners.findIndex(([id]) => id === toasterId);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    };
  }, [toasterId]);

  const mergedToasts = state.toasts.map((t) => ({
    ...toastOptions,
    ...toastOptions[t.type],
    ...t,
    removeDelay:
      t.removeDelay ||
      toastOptions[t.type]?.removeDelay ||
      toastOptions?.removeDelay,
    duration:
      t.duration ||
      toastOptions[t.type]?.duration ||
      toastOptions?.duration ||
      defaultTimeouts[t.type],
    style: {
      ...toastOptions.style,
      ...toastOptions[t.type]?.style,
      ...t.style,
    },
  }));

  return {
    ...state,
    toasts: mergedToasts,
  };
};
