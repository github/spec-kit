import type React from 'react';
import type { VALIDATION_MODE } from '../constants';
import type { Subject, Subscription } from '../utils/createSubject';
import type { ErrorOption, FieldError, FieldErrors } from './errors';
import type { EventType } from './events';
import type { FieldArray } from './fieldArray';
import type { FieldName, FieldRefs, FieldValue, FieldValues, InternalFieldName } from './fields';
import type { FieldArrayPath, FieldPath, FieldPathValue, FieldPathValues } from './path';
import type { Resolver } from './resolvers';
import type { DeepMap, DeepPartial, Noop } from './utils';
import type { RegisterOptions } from './validator';
declare const $NestedValue: unique symbol;
/**
 * @deprecated to be removed in the next major version
 */
export type NestedValue<TValue extends object = object> = {
    [$NestedValue]: never;
} & TValue;
export type DefaultValues<TFieldValues> = TFieldValues extends AsyncDefaultValues<TFieldValues> ? DeepPartial<Awaited<TFieldValues>> : DeepPartial<TFieldValues>;
export type InternalNameSet = Set<InternalFieldName>;
export type ValidationMode = typeof VALIDATION_MODE;
export type Mode = keyof ValidationMode;
export type ValidationModeFlags = {
    isOnSubmit: boolean;
    isOnBlur: boolean;
    isOnChange: boolean;
    isOnAll: boolean;
    isOnTouch: boolean;
};
export type CriteriaMode = 'firstError' | 'all';
export type SubmitHandler<T> = (data: T, event?: React.BaseSyntheticEvent) => unknown | Promise<unknown>;
export type FormSubmitHandler<TTransformedValues> = (payload: {
    data: TTransformedValues;
    event?: React.BaseSyntheticEvent;
    formData: FormData;
    formDataJson: string;
    method?: 'post' | 'put' | 'delete';
}) => unknown | Promise<unknown>;
export type SubmitErrorHandler<TFieldValues extends FieldValues> = (errors: FieldErrors<TFieldValues>, event?: React.BaseSyntheticEvent) => unknown | Promise<unknown>;
export type SetValueConfig = Partial<{
    shouldValidate: boolean;
    shouldDirty: boolean;
    shouldTouch: boolean;
}>;
export type TriggerConfig = Partial<{
    shouldFocus: boolean;
}>;
export type ResetFieldConfig<TFieldValues extends FieldValues, TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>> = Partial<{
    keepDirty: boolean;
    keepTouched: boolean;
    keepError: boolean;
    defaultValue: FieldPathValue<TFieldValues, TFieldName>;
}>;
export type ChangeHandler = (event: {
    target: any;
    type?: any;
}) => Promise<void | boolean>;
export type DelayCallback = (wait: number) => void;
type AsyncDefaultValues<TFieldValues> = (payload?: unknown) => Promise<TFieldValues>;
export type UseFormProps<TFieldValues extends FieldValues = FieldValues, TContext = any, TTransformedValues = TFieldValues> = Partial<{
    mode: Mode;
    disabled: boolean;
    reValidateMode: Exclude<Mode, 'onTouched' | 'all'>;
    defaultValues: DefaultValues<TFieldValues> | AsyncDefaultValues<TFieldValues>;
    values: TFieldValues;
    errors: FieldErrors<TFieldValues>;
    resetOptions: Parameters<UseFormReset<TFieldValues>>[1];
    resolver: Resolver<TFieldValues, TContext, TTransformedValues>;
    context: TContext;
    shouldFocusError: boolean;
    shouldUnregister: boolean;
    shouldUseNativeValidation: boolean;
    progressive: boolean;
    criteriaMode: CriteriaMode;
    delayError: number;
    formControl?: Omit<UseFormReturn<TFieldValues, TContext, TTransformedValues>, 'formState'>;
}>;
export type FieldNamesMarkedBoolean<TFieldValues extends FieldValues> = DeepMap<DeepPartial<TFieldValues>, boolean>;
export type FormStateProxy<TFieldValues extends FieldValues = FieldValues> = {
    isDirty: boolean;
    isValidating: boolean;
    dirtyFields: FieldNamesMarkedBoolean<TFieldValues>;
    touchedFields: FieldNamesMarkedBoolean<TFieldValues>;
    validatingFields: FieldNamesMarkedBoolean<TFieldValues>;
    errors: boolean;
    isValid: boolean;
};
export type ReadFormState = {
    [K in keyof FormStateProxy]: boolean | 'all';
} & {
    values?: boolean;
};
export type FormState<TFieldValues extends FieldValues> = {
    isDirty: boolean;
    isLoading: boolean;
    isSubmitted: boolean;
    isSubmitSuccessful: boolean;
    isSubmitting: boolean;
    isValidating: boolean;
    isValid: boolean;
    disabled: boolean;
    submitCount: number;
    defaultValues?: undefined | Readonly<DeepPartial<TFieldValues>>;
    dirtyFields: Partial<Readonly<FieldNamesMarkedBoolean<TFieldValues>>>;
    touchedFields: Partial<Readonly<FieldNamesMarkedBoolean<TFieldValues>>>;
    validatingFields: Partial<Readonly<FieldNamesMarkedBoolean<TFieldValues>>>;
    errors: FieldErrors<TFieldValues>;
    isReady: boolean;
};
export type KeepStateOptions = Partial<{
    keepDirtyValues: boolean;
    keepErrors: boolean;
    keepDirty: boolean;
    keepValues: boolean;
    keepDefaultValues: boolean;
    keepIsSubmitted: boolean;
    keepIsSubmitSuccessful: boolean;
    keepTouched: boolean;
    keepIsValidating: boolean;
    keepIsValid: boolean;
    keepSubmitCount: boolean;
    keepFieldsRef: boolean;
}>;
export type SetFieldValue<TFieldValues extends FieldValues> = FieldValue<TFieldValues>;
export type RefCallBack = (instance: any) => void;
export type UseFormRegisterReturn<TFieldName extends InternalFieldName = InternalFieldName> = {
    onChange: ChangeHandler;
    onBlur: ChangeHandler;
    ref: RefCallBack;
    name: TFieldName;
    min?: string | number;
    max?: string | number;
    maxLength?: number;
    minLength?: number;
    pattern?: string;
    required?: boolean;
    disabled?: boolean;
};
/**
 * Register field into hook form with or without the actual DOM ref. You can invoke register anywhere in the component including at `useEffect`.
 *
 * @remarks
 * [API](https://react-hook-form.com/docs/useform/register) • [Demo](https://codesandbox.io/s/react-hook-form-register-ts-ip2j3) • [Video](https://www.youtube.com/watch?v=JFIpCoajYkA)
 *
 * @param name - the path name to the form field value, name is required and unique
 * @param options - register options include validation, disabled, unregister, value as and dependent validation
 *
 * @returns onChange, onBlur, name, ref, and native contribute attribute if browser validation is enabled.
 *
 * @example
 * ```tsx
 * // Register HTML native input
 * <input {...register("input")} />
 * <select {...register("select")} />
 *
 * // Register options
 * <textarea {...register("textarea", { required: "This is required.", maxLength: 20 })} />
 * <input type="number" {...register("name2", { valueAsNumber: true })} />
 * <input {...register("name3", { deps: ["name2"] })} />
 *
 * // Register custom field at useEffect
 * useEffect(() => {
 *   register("name4");
 *   register("name5", { value: "hiddenValue" });
 * }, [register])
 *
 * // Register without ref
 * const { onChange, onBlur, name } = register("name6")
 * <input onChange={onChange} onBlur={onBlur} name={name} />
 * ```
 */
export type UseFormRegister<TFieldValues extends FieldValues> = <TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>>(name: TFieldName, options?: RegisterOptions<TFieldValues, TFieldName>) => UseFormRegisterReturn<TFieldName>;
export type SetFocusOptions = Partial<{
    shouldSelect: boolean;
}>;
/**
 * Set focus on a registered field. You can start to invoke this method after all fields are mounted to the DOM.
 *
 * @remarks
 * [API](https://react-hook-form.com/docs/useform/setfocus) • [Demo](https://codesandbox.io/s/setfocus-rolus)
 *
 * @param name - the path name to the form field value.
 * @param options - input focus behavior options
 *
 * @example
 * ```tsx
 * useEffect(() => {
 *   setFocus("name");
 * }, [setFocus])
 * // shouldSelect allows to select input's content on focus
 * <button onClick={() => setFocus("name", { shouldSelect: true })}>Focus</button>
 * ```
 */
export type UseFormSetFocus<TFieldValues extends FieldValues> = <TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>>(name: TFieldName, options?: SetFocusOptions) => void;
type EitherOption<T> = {
    [K in keyof T]: {
        [P in K]: T[P];
    } & Partial<Record<Exclude<keyof T, K>, never>>;
}[keyof T];
export type GetValuesConfig = EitherOption<{
    dirtyFields: boolean;
    touchedFields: boolean;
}>;
export type UseFormGetValues<TFieldValues extends FieldValues> = {
    /**
     * Get the entire form values when no argument is supplied to this function.
     *
     * @remarks
     * [API](https://react-hook-form.com/docs/useform/getvalues) • [Demo](https://codesandbox.io/s/react-hook-form-v7-ts-getvalues-txsfg)
     *
     * @returns form values
     *
     * @example
     * ```tsx
     * <button onClick={() => getValues()}>getValues</button>
     *
     * <input {...register("name", {
     *   validate: (value, formValues) => formValues.otherField === value;
     * })} />
     * ```
     */
    (name?: undefined, config?: GetValuesConfig): TFieldValues;
    /**
     * Get a single field value.
     *
     * @remarks
     * [API](https://react-hook-form.com/docs/useform/getvalues) • [Demo](https://codesandbox.io/s/react-hook-form-v7-ts-getvalues-txsfg)
     *
     * @param name - the path name to the form field value.
     * @param config - return touched or dirty fields
     *
     * @returns the single field value
     *
     * @example
     * ```tsx
     * <button onClick={() => getValues("name")}>getValues</button>
     *
     * <input {...register("name", {
     *   validate: () => getValues('otherField') === "test";
     * })} />
     * ```
     */
    <TFieldName extends FieldPath<TFieldValues>>(name: TFieldName, config?: GetValuesConfig): FieldPathValue<TFieldValues, TFieldName>;
    /**
     * Get an array of field values.
     *
     * @remarks
     * [API](https://react-hook-form.com/docs/useform/getvalues) • [Demo](https://codesandbox.io/s/react-hook-form-v7-ts-getvalues-txsfg)
     *
     * @param names - an array of field names
     * @param config - return touched or dirty fields
     *
     * @returns An array of field values
     *
     * @example
     * ```tsx
     * <button onClick={() => getValues(["name", "name1"])}>getValues</button>
     *
     * <input {...register("name", {
     *   validate: () => getValues(["fieldA", "fieldB"]).includes("test");
     * })} />
     * ```
     */
    <TFieldNames extends FieldPath<TFieldValues>[]>(names: readonly [...TFieldNames], config?: GetValuesConfig): [...FieldPathValues<TFieldValues, TFieldNames>];
};
/**
 * This method will return individual field states. It will be useful when you are trying to retrieve the nested value field state in a typesafe approach.
 *
 * @remarks
 * [API](https://react-hook-form.com/docs/useform/getfieldstate) • [Demo](https://codesandbox.io/s/getfieldstate-jvekk)
 *
 * @param name - the path name to the form field value.
 *
 * @returns invalid, isDirty, isTouched and error object
 *
 * @example
 * ```tsx
 * // those formState has to be subscribed
 * const { formState: { dirtyFields, errors, touchedFields } } = formState();
 * getFieldState('name')
 * // Get field state when form state is not subscribed yet
 * getFieldState('name', formState)
 *
 * // It's ok to combine with useFormState
 * const formState = useFormState();
 * getFieldState('name')
 * getFieldState('name', formState)
 * ```
 */
export type UseFormGetFieldState<TFieldValues extends FieldValues> = <TFieldName extends FieldPath<TFieldValues>>(name: TFieldName, formState?: FormState<TFieldValues>) => {
    invalid: boolean;
    isDirty: boolean;
    isTouched: boolean;
    isValidating: boolean;
    error?: FieldError;
};
/**
 * This method will allow you to subscribe to formState without component render
 *
 * @remarks
 * [API](https://react-hook-form.com/docs/useform/subscribe) • [Demo](https://codesandbox.io/s/subscribe)
 *
 * @param options - subscription options on which formState subscribe to
 *
 * @example
 * ```tsx
const { subscribe } = useForm()

useEffect(() => {
 subscribe({
   formState: { isDirty: true },
   callback: () => {}
 })
})
 * ```
 */
export type UseFormSubscribe<TFieldValues extends FieldValues> = <TFieldNames extends readonly FieldPath<TFieldValues>[]>(payload: {
    name?: readonly [...TFieldNames] | TFieldNames[number];
    formState?: Partial<ReadFormState>;
    callback: (data: Partial<FormState<TFieldValues>> & {
        values: TFieldValues;
        name?: InternalFieldName;
        type?: EventType;
    }) => void;
    exact?: boolean;
}) => () => void;
export type UseFormWatch<TFieldValues extends FieldValues> = {
    /**
     * Watch and subscribe to the entire form update/change based on onChange and re-render at the useForm.
     *
     * @remarks
     * [API](https://react-hook-form.com/docs/useform/watch) • [Demo](https://codesandbox.io/s/react-hook-form-watch-v7-ts-8et1d) • [Video](https://www.youtube.com/watch?v=3qLd69WMqKk)
     *
     * @returns return the entire form values
     *
     * @example
     * ```tsx
     * const formValues = watch();
     * ```
     */
    (): TFieldValues;
    /**
     * Watch and subscribe to an array of fields used outside of render.
     *
     * @remarks
     * [API](https://react-hook-form.com/docs/useform/watch) • [Demo](https://codesandbox.io/s/react-hook-form-watch-v7-ts-8et1d) • [Video](https://www.youtube.com/watch?v=3qLd69WMqKk)
     *
     * @param names - an array of field names
     * @param defaultValue - defaultValues for the entire form
     *
     * @returns return an array of field values
     *
     * @example
     * ```tsx
     * const [name, name1] = watch(["name", "name1"]);
     * ```
     */
    <TFieldNames extends readonly FieldPath<TFieldValues>[]>(names: readonly [...TFieldNames], defaultValue?: DeepPartial<TFieldValues>): FieldPathValues<TFieldValues, TFieldNames>;
    /**
     * Watch and subscribe to a single field used outside of render.
     *
     * @remarks
     * [API](https://react-hook-form.com/docs/useform/watch) • [Demo](https://codesandbox.io/s/react-hook-form-watch-v7-ts-8et1d) • [Video](https://www.youtube.com/watch?v=3qLd69WMqKk)
     *
     * @param name - the path name to the form field value.
     * @param defaultValue - defaultValues for the entire form
     *
     * @returns return the single field value
     *
     * @example
     * ```tsx
     * const name = watch("name");
     * ```
     */
    <TFieldName extends FieldPath<TFieldValues>>(name: TFieldName, defaultValue?: FieldPathValue<TFieldValues, TFieldName>): FieldPathValue<TFieldValues, TFieldName>;
    /**
     * Subscribe to field update/change without trigger re-render
     *
     * @remarks
     * [API](https://react-hook-form.com/docs/useform/watch) • [Demo](https://codesandbox.io/s/react-hook-form-watch-v7-ts-8et1d) • [Video](https://www.youtube.com/watch?v=3qLd69WMqKk)
     *
     * @param callback - call back function to subscribe all fields change and return unsubscribe function
     * @param defaultValues - defaultValues for the entire form
     *
     * @returns unsubscribe function
     *
     * @example
     * ```tsx
     * useEffect(() => {
     *   const { unsubscribe } = watch((value) => {
     *     console.log(value);
     *   });
     *   return () => unsubscribe();
     * }, [watch])
     * ```
     */
    (callback: WatchObserver<TFieldValues>, defaultValues?: DeepPartial<TFieldValues>): Subscription;
};
/**
 * Trigger field or form validation
 *
 * @remarks
 * [API](https://react-hook-form.com/docs/useform/trigger) • [Demo](https://codesandbox.io/s/react-hook-form-v7-ts-triggervalidation-forked-xs7hl) • [Video](https://www.youtube.com/watch?v=-bcyJCDjksE)
 *
 * @param name - provide empty argument will trigger the entire form validation, an array of field names will validate an array of fields, and a single field name will only trigger that field's validation.
 * @param options - should focus on the error field
 *
 * @returns validation result
 *
 * @example
 * ```tsx
 * useEffect(() => {
 *   trigger();
 * }, [trigger])
 *
 * <button onClick={async () => {
 *   const result = await trigger(); // result will be a boolean value
 * }}>
 *  trigger
 *  </button>
 * ```
 */
export type UseFormTrigger<TFieldValues extends FieldValues> = (name?: FieldPath<TFieldValues> | FieldPath<TFieldValues>[] | readonly FieldPath<TFieldValues>[], options?: TriggerConfig) => Promise<boolean>;
/**
 * Clear the entire form errors.
 *
 * @remarks
 * [API](https://react-hook-form.com/docs/useform/clearerrors) • [Demo](https://codesandbox.io/s/react-hook-form-v7-ts-clearerrors-w3ymx)
 *
 * @param name - the path name to the form field value.
 *
 * @example
 * Clear all errors
 * ```tsx
 * clearErrors(); // clear the entire form error
 * clearErrors(["name", "name1"]) // clear an array of fields' error
 * clearErrors("name2"); // clear a single field error
 * ```
 */
export type UseFormClearErrors<TFieldValues extends FieldValues> = (name?: FieldPath<TFieldValues> | FieldPath<TFieldValues>[] | readonly FieldPath<TFieldValues>[] | `root.${string}` | 'root') => void;
/**
 * Set a single field value, or a group of fields value.
 *
 * @remarks
 * [API](https://react-hook-form.com/docs/useform/setvalue) • [Demo](https://codesandbox.io/s/react-hook-form-v7-ts-setvalue-8z9hx) • [Video](https://www.youtube.com/watch?v=qpv51sCH3fI)
 *
 * @param name - the path name to the form field value.
 * @param value - field value
 * @param options - should validate or update form state
 *
 * @example
 * ```tsx
 * // Update a single field
 * setValue('name', 'value', {
 *   shouldValidate: true, // trigger validation
 *   shouldTouch: true, // update touched fields form state
 *   shouldDirty: true, // update dirty and dirty fields form state
 * });
 *
 * // Update a group fields
 * setValue('root', {
 *   a: 'test', // setValue('root.a', 'data')
 *   b: 'test1', // setValue('root.b', 'data')
 * });
 *
 * // Update a nested object field
 * setValue('select', { label: 'test', value: 'Test' });
 * ```
 */
export type UseFormSetValue<TFieldValues extends FieldValues> = <TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>>(name: TFieldName, value: FieldPathValue<TFieldValues, TFieldName>, options?: SetValueConfig) => void;
/**
 * Set an error for the field. When set an error which is not associated to a field then manual `clearErrors` invoke is required.
 *
 * @remarks
 * [API](https://react-hook-form.com/docs/useform/seterror) • [Demo](https://codesandbox.io/s/react-hook-form-v7-ts-seterror-nfxxu) • [Video](https://www.youtube.com/watch?v=raMqvE0YyIY)
 *
 * @param name - the path name to the form field value.
 * @param error - an error object which contains type and optional message
 * @param options - whether or not to focus on the field
 *
 * @example
 * ```tsx
 * // when the error is not associated with any fields, `clearError` will need to invoke to clear the error
 * const onSubmit = () => setError("serverError", { type: "server", message: "Error occurred"})
 *
 * <button onClick={() => setError("name", { type: "min" })} />
 *
 * // focus on the input after setting the error
 * <button onClick={() => setError("name", { type: "max" }, { shouldFocus: true })} />
 * ```
 */
export type UseFormSetError<TFieldValues extends FieldValues> = (name: FieldPath<TFieldValues> | `root.${string}` | 'root', error: ErrorOption, options?: {
    shouldFocus: boolean;
}) => void;
/**
 * Unregister a field reference and remove its value.
 *
 * @remarks
 * [API](https://react-hook-form.com/docs/useform/unregister) • [Demo](https://codesandbox.io/s/react-hook-form-unregister-4k2ey) • [Video](https://www.youtube.com/watch?v=TM99g_NW5Gk&feature=emb_imp_woyt)
 *
 * @param name - the path name to the form field value.
 * @param options - keep form state options
 *
 * @example
 * ```tsx
 * register("name", { required: true })
 *
 * <button onClick={() => unregister("name")} />
 * // there are various keep options to retain formState
 * <button onClick={() => unregister("name", { keepErrors: true })} />
 * ```
 */
export type UseFormUnregister<TFieldValues extends FieldValues> = (name?: FieldPath<TFieldValues> | FieldPath<TFieldValues>[] | readonly FieldPath<TFieldValues>[], options?: Omit<KeepStateOptions, 'keepIsSubmitted' | 'keepSubmitCount' | 'keepValues' | 'keepDefaultValues' | 'keepErrors'> & {
    keepValue?: boolean;
    keepDefaultValue?: boolean;
    keepError?: boolean;
}) => void;
/**
 * Validate the entire form. Handle submit and error callback.
 *
 * @remarks
 * [API](https://react-hook-form.com/docs/useform/handlesubmit) • [Demo](https://codesandbox.io/s/react-hook-form-handlesubmit-ts-v7-lcrtu) • [Video](https://www.youtube.com/watch?v=KzcPKB9SOEk)
 *
 * @param onValid - callback function invoked after form pass validation
 * @param onInvalid - callback function invoked when form failed validation
 *
 * @returns callback - return callback function
 *
 * @example
 * ```tsx
 * const onSubmit = (data) => console.log(data);
 * const onError = (error) => console.log(error);
 *
 * <form onSubmit={handleSubmit(onSubmit, onError)} />
 * ```
 */
export type UseFormHandleSubmit<TFieldValues extends FieldValues, TTransformedValues = TFieldValues> = (onValid: SubmitHandler<TTransformedValues>, onInvalid?: SubmitErrorHandler<TFieldValues>) => (e?: React.BaseSyntheticEvent) => Promise<void>;
/**
 * Reset a field state and reference.
 *
 * @remarks
 * [API](https://react-hook-form.com/docs/useform/resetfield) • [Demo](https://codesandbox.io/s/priceless-firefly-d0kuv) • [Video](https://www.youtube.com/watch?v=IdLFcNaEFEo)
 *
 * @param name - the path name to the form field value.
 * @param options - keep form state options
 *
 * @example
 * ```tsx
 * <input {...register("firstName", { required: true })} />
 * <button type="button" onClick={() => resetField("firstName"))}>Reset</button>
 * ```
 */
export type UseFormResetField<TFieldValues extends FieldValues> = <TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>>(name: TFieldName, options?: ResetFieldConfig<TFieldValues, TFieldName>) => void;
type ResetAction<TFieldValues> = (formValues: TFieldValues) => TFieldValues;
/**
 * Reset at the entire form state.
 *
 * @remarks
 * [API](https://react-hook-form.com/docs/useform/reset) • [Demo](https://codesandbox.io/s/react-hook-form-reset-v7-ts-pu901) • [Video](https://www.youtube.com/watch?v=qmCLBjyPwVk)
 *
 * @param values - the entire form values to be reset
 * @param keepStateOptions - keep form state options
 *
 * @example
 * ```tsx
 * useEffect(() => {
 *   // reset the entire form after component mount or form defaultValues is ready
 *   reset({
 *     fieldA: "test"
 *     fieldB: "test"
 *   });
 * }, [reset])
 *
 * // reset by combine with existing form values
 * reset({
 *   ...getValues(),
 *  fieldB: "test"
 *});
 *
 * // reset and keep form state
 * reset({
 *   ...getValues(),
 *}, {
 *   keepErrors: true,
 *   keepDirty: true
 *});
 * ```
 */
export type UseFormReset<TFieldValues extends FieldValues> = (values?: DefaultValues<TFieldValues> | TFieldValues | ResetAction<TFieldValues>, keepStateOptions?: KeepStateOptions) => void;
export type WatchInternal<TFieldValues> = (fieldNames?: InternalFieldName | InternalFieldName[], defaultValue?: DeepPartial<TFieldValues>, isMounted?: boolean, isGlobal?: boolean) => FieldPathValue<FieldValues, InternalFieldName> | FieldPathValues<FieldValues, InternalFieldName[]>;
export type GetIsDirty = <TName extends InternalFieldName, TData>(name?: TName, data?: TData) => boolean;
export type FormStateSubjectRef<TFieldValues extends FieldValues> = Subject<Partial<FormState<TFieldValues>> & {
    name?: InternalFieldName;
    values?: TFieldValues;
    type?: EventType;
}>;
export type Subjects<TFieldValues extends FieldValues = FieldValues> = {
    array: Subject<{
        name?: InternalFieldName;
        values?: FieldValues;
    }>;
    state: FormStateSubjectRef<TFieldValues>;
};
export type Names = {
    mount: InternalNameSet;
    unMount: InternalNameSet;
    disabled: InternalNameSet;
    array: InternalNameSet;
    watch: InternalNameSet;
    focus?: InternalFieldName;
    watchAll?: boolean;
};
export type BatchFieldArrayUpdate = <T extends Function, TFieldValues extends FieldValues, TFieldArrayName extends FieldArrayPath<TFieldValues> = FieldArrayPath<TFieldValues>>(name: InternalFieldName, updatedFieldArrayValues?: Partial<FieldArray<TFieldValues, TFieldArrayName>>[], method?: T, args?: Partial<{
    argA: unknown;
    argB: unknown;
}>, shouldSetValue?: boolean, shouldUpdateFieldsAndErrors?: boolean) => void;
export type FromSubscribe<TFieldValues extends FieldValues> = <TFieldNames extends readonly FieldPath<TFieldValues>[]>(payload: {
    name?: readonly [...TFieldNames] | TFieldNames[number];
    formState?: Partial<ReadFormState>;
    callback: (data: Partial<FormState<TFieldValues>> & {
        values: TFieldValues;
        name?: InternalFieldName;
    }) => void;
    exact?: boolean;
    reRenderRoot?: boolean;
}) => () => void;
export type Control<TFieldValues extends FieldValues = FieldValues, TContext = any, TTransformedValues = TFieldValues> = {
    _subjects: Subjects<TFieldValues>;
    _removeUnmounted: Noop;
    _names: Names;
    _state: {
        mount: boolean;
        action: boolean;
        watch: boolean;
    };
    _reset: UseFormReset<TFieldValues>;
    _options: UseFormProps<TFieldValues, TContext, TTransformedValues>;
    _getDirty: GetIsDirty;
    _resetDefaultValues: Noop;
    _formState: FormState<TFieldValues>;
    _setValid: (shouldUpdateValid?: boolean) => void;
    _fields: FieldRefs;
    _formValues: FieldValues;
    _proxyFormState: ReadFormState;
    _defaultValues: Partial<DefaultValues<TFieldValues>>;
    _getWatch: WatchInternal<TFieldValues>;
    _setFieldArray: BatchFieldArrayUpdate;
    _getFieldArray: <TFieldArrayValues>(name: InternalFieldName) => Partial<TFieldArrayValues>[];
    _setErrors: (errors: FieldErrors<TFieldValues>) => void;
    _setDisabledField: (props: {
        disabled?: boolean;
        name: FieldName<any>;
    }) => void;
    _runSchema: (names: InternalFieldName[]) => Promise<{
        errors: FieldErrors;
    }>;
    _focusError: () => boolean | undefined;
    _disableForm: (disabled?: boolean) => void;
    _subscribe: FromSubscribe<TFieldValues>;
    register: UseFormRegister<TFieldValues>;
    handleSubmit: UseFormHandleSubmit<TFieldValues, TTransformedValues>;
    unregister: UseFormUnregister<TFieldValues>;
    getFieldState: UseFormGetFieldState<TFieldValues>;
    setError: UseFormSetError<TFieldValues>;
};
export type WatchObserver<TFieldValues extends FieldValues> = (value: DeepPartial<TFieldValues>, info: {
    name?: FieldPath<TFieldValues>;
    type?: EventType;
    values?: unknown;
}) => void;
export type UseFormReturn<TFieldValues extends FieldValues = FieldValues, TContext = any, TTransformedValues = TFieldValues> = {
    watch: UseFormWatch<TFieldValues>;
    getValues: UseFormGetValues<TFieldValues>;
    getFieldState: UseFormGetFieldState<TFieldValues>;
    setError: UseFormSetError<TFieldValues>;
    clearErrors: UseFormClearErrors<TFieldValues>;
    setValue: UseFormSetValue<TFieldValues>;
    trigger: UseFormTrigger<TFieldValues>;
    formState: FormState<TFieldValues>;
    resetField: UseFormResetField<TFieldValues>;
    reset: UseFormReset<TFieldValues>;
    handleSubmit: UseFormHandleSubmit<TFieldValues, TTransformedValues>;
    unregister: UseFormUnregister<TFieldValues>;
    control: Control<TFieldValues, TContext, TTransformedValues>;
    register: UseFormRegister<TFieldValues>;
    setFocus: UseFormSetFocus<TFieldValues>;
    subscribe: UseFormSubscribe<TFieldValues>;
};
export type UseFormStateProps<TFieldValues extends FieldValues, TTransformedValues = TFieldValues> = Partial<{
    control?: Control<TFieldValues, any, TTransformedValues>;
    disabled?: boolean;
    name?: FieldPath<TFieldValues> | FieldPath<TFieldValues>[] | readonly FieldPath<TFieldValues>[];
    exact?: boolean;
}>;
export type UseFormStateReturn<TFieldValues extends FieldValues> = FormState<TFieldValues>;
export type UseWatchProps<TFieldValues extends FieldValues = FieldValues> = {
    defaultValue?: unknown;
    disabled?: boolean;
    name?: FieldPath<TFieldValues> | FieldPath<TFieldValues>[] | readonly FieldPath<TFieldValues>[];
    control?: Control<TFieldValues>;
    exact?: boolean;
    compute?: (formValues: any) => any;
};
export type FormProviderProps<TFieldValues extends FieldValues = FieldValues, TContext = any, TTransformedValues = TFieldValues> = {
    children: React.ReactNode | React.ReactNode[];
} & UseFormReturn<TFieldValues, TContext, TTransformedValues>;
export type FormProps<TFieldValues extends FieldValues, TTransformedValues = TFieldValues> = Omit<React.FormHTMLAttributes<HTMLFormElement>, 'onError' | 'onSubmit'> & Partial<{
    control: Control<TFieldValues, any, TTransformedValues>;
    headers: Record<string, string>;
    validateStatus: (status: number) => boolean;
    onError: ({ response, error, }: {
        response: Response;
        error?: undefined;
    } | {
        response?: undefined;
        error: unknown;
    }) => void;
    onSuccess: ({ response }: {
        response: Response;
    }) => void;
    onSubmit: FormSubmitHandler<TTransformedValues>;
    method: 'post' | 'put' | 'delete';
    children: React.ReactNode | React.ReactNode[];
    render: (props: {
        submit: (e?: React.FormEvent) => void;
    }) => React.ReactNode | React.ReactNode[];
    encType: 'application/x-www-form-urlencoded' | 'multipart/form-data' | 'text/plain' | 'application/json';
}>;
export {};
//# sourceMappingURL=form.d.ts.map