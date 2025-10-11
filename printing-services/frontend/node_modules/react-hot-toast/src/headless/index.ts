import { toast } from '../core/toast';

export type {
  DefaultToastOptions,
  IconTheme,
  Renderable,
  Toast,
  ToasterProps,
  ToastOptions,
  ToastPosition,
  ToastType,
  ValueFunction,
  ValueOrFunction,
} from '../core/types';

export { resolveValue } from '../core/types';
export { useToaster } from '../core/use-toaster';
export { useStore as useToasterStore } from '../core/store';

export { toast };
export default toast;
