import type React from 'react';
import type { Control, FieldError, FieldPath, FieldPathValue, FieldValues, Noop, RefCallBack, UseFormStateReturn } from './';
import type { RegisterOptions } from './validator';
export type ControllerFieldState = {
    invalid: boolean;
    isTouched: boolean;
    isDirty: boolean;
    isValidating: boolean;
    error?: FieldError;
};
export type ControllerRenderProps<TFieldValues extends FieldValues = FieldValues, TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>> = {
    onChange: (...event: any[]) => void;
    onBlur: Noop;
    value: FieldPathValue<TFieldValues, TName>;
    disabled?: boolean;
    name: TName;
    ref: RefCallBack;
};
export type UseControllerProps<TFieldValues extends FieldValues = FieldValues, TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>, TTransformedValues = TFieldValues> = {
    name: TName;
    rules?: Omit<RegisterOptions<TFieldValues, TName>, 'valueAsNumber' | 'valueAsDate' | 'setValueAs' | 'disabled'>;
    shouldUnregister?: boolean;
    defaultValue?: FieldPathValue<TFieldValues, TName>;
    control?: Control<TFieldValues, any, TTransformedValues>;
    disabled?: boolean;
};
export type UseControllerReturn<TFieldValues extends FieldValues = FieldValues, TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>> = {
    field: ControllerRenderProps<TFieldValues, TName>;
    formState: UseFormStateReturn<TFieldValues>;
    fieldState: ControllerFieldState;
};
/**
 * Render function to provide the control for the field.
 *
 * @returns all the event handlers, and relevant field and form state.
 *
 * @example
 * ```tsx
 * const { field, fieldState, formState } = useController();
 *
 * <Controller
 *   render={({ field, formState, fieldState }) => ({
 *     <input
 *       onChange={field.onChange}
 *       onBlur={field.onBlur}
 *       name={field.name}
 *       ref={field.ref} // optional for focus management
 *     />
 *   })}
 * />
 * ```
 */
export type ControllerProps<TFieldValues extends FieldValues = FieldValues, TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>, TTransformedValues = TFieldValues> = {
    render: ({ field, fieldState, formState, }: {
        field: ControllerRenderProps<TFieldValues, TName>;
        fieldState: ControllerFieldState;
        formState: UseFormStateReturn<TFieldValues>;
    }) => React.ReactElement;
} & UseControllerProps<TFieldValues, TName, TTransformedValues>;
//# sourceMappingURL=controller.d.ts.map