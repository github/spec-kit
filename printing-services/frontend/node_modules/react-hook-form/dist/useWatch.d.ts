import type { Control, DeepPartialSkipArrayKey, FieldPath, FieldPathValue, FieldPathValues, FieldValues } from './types';
/**
 * Subscribe to the entire form values change and re-render at the hook level.
 *
 * @remarks
 *
 * [API](https://react-hook-form.com/docs/usewatch) • [Demo](https://codesandbox.io/s/react-hook-form-v7-ts-usewatch-h9i5e)
 *
 * @param props - defaultValue, disable subscription and match exact name.
 *
 * @example
 * ```tsx
 * const { control } = useForm();
 * const values = useWatch({
 *   control,
 *   defaultValue: {
 *     name: "data"
 *   },
 *   exact: false,
 * })
 * ```
 */
export declare function useWatch<TFieldValues extends FieldValues = FieldValues, TTransformedValues = TFieldValues>(props: {
    name?: undefined;
    defaultValue?: DeepPartialSkipArrayKey<TFieldValues>;
    control?: Control<TFieldValues, any, TTransformedValues>;
    disabled?: boolean;
    exact?: boolean;
    compute?: undefined;
}): DeepPartialSkipArrayKey<TFieldValues>;
/**
 * Custom hook to subscribe to field change and isolate re-rendering at the component level.
 *
 * @remarks
 *
 * [API](https://react-hook-form.com/docs/usewatch) • [Demo](https://codesandbox.io/s/react-hook-form-v7-ts-usewatch-h9i5e)
 *
 * @param props - defaultValue, disable subscription and match exact name.
 *
 * @example
 * ```tsx
 * const { control } = useForm();
 * const values = useWatch({
 *   control,
 *   name: "fieldA",
 *   defaultValue: "default value",
 *   exact: false,
 * })
 * ```
 */
export declare function useWatch<TFieldValues extends FieldValues = FieldValues, TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>, TTransformedValues = TFieldValues>(props: {
    name: TFieldName;
    defaultValue?: FieldPathValue<TFieldValues, TFieldName>;
    control?: Control<TFieldValues, any, TTransformedValues>;
    disabled?: boolean;
    exact?: boolean;
    compute?: undefined;
}): FieldPathValue<TFieldValues, TFieldName>;
/**
 * Custom hook to subscribe to field change and compute function to produce state update
 *
 * @remarks
 *
 * [API](https://react-hook-form.com/docs/usewatch)
 *
 * @param props - defaultValue, disable subscription and match exact name.
 *
 * @example
 * ```tsx
 * const { control } = useForm();
 * const values = useWatch({
 *   control,
 *   compute: (formValues) => formValues.fieldA
 * })
 * ```
 */
export declare function useWatch<TFieldValues extends FieldValues = FieldValues, TTransformedValues = TFieldValues, TComputeValue = unknown>(props: {
    name?: undefined;
    defaultValue?: DeepPartialSkipArrayKey<TFieldValues>;
    control?: Control<TFieldValues, any, TTransformedValues>;
    disabled?: boolean;
    exact?: boolean;
    compute: (formValues: TFieldValues) => TComputeValue;
}): TComputeValue;
/**
 * Custom hook to subscribe to field change and compute function to produce state update
 *
 * @remarks
 *
 * [API](https://react-hook-form.com/docs/usewatch)
 *
 * @param props - defaultValue, disable subscription and match exact name.
 *
 * @example
 * ```tsx
 * const { control } = useForm();
 * const values = useWatch({
 *   control,
 *   name: "fieldA",
 *   defaultValue: "default value",
 *   exact: false,
 *   compute: (fieldValue) => fieldValue === "data" ? fieldValue : null,
 * })
 * ```
 */
export declare function useWatch<TFieldValues extends FieldValues = FieldValues, TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>, TTransformedValues = TFieldValues, TComputeValue = unknown>(props: {
    name: TFieldName;
    defaultValue?: FieldPathValue<TFieldValues, TFieldName>;
    control?: Control<TFieldValues, any, TTransformedValues>;
    disabled?: boolean;
    exact?: boolean;
    compute: (fieldValue: FieldPathValue<TFieldValues, TFieldName>) => TComputeValue;
}): TComputeValue;
/**
 * Custom hook to subscribe to field change and isolate re-rendering at the component level.
 *
 * @remarks
 *
 * [API](https://react-hook-form.com/docs/usewatch) • [Demo](https://codesandbox.io/s/react-hook-form-v7-ts-usewatch-h9i5e)
 *
 * @param props - defaultValue, disable subscription and match exact name.
 *
 * @example
 * ```tsx
 * const { control } = useForm();
 * const values = useWatch({
 *   control,
 *   name: ["fieldA", "fieldB"],
 *   defaultValue: {
 *     fieldA: "data",
 *     fieldB: "data"
 *   },
 *   exact: false,
 * })
 * ```
 */
export declare function useWatch<TFieldValues extends FieldValues = FieldValues, TFieldNames extends readonly FieldPath<TFieldValues>[] = readonly FieldPath<TFieldValues>[], TTransformedValues = TFieldValues>(props: {
    name: readonly [...TFieldNames];
    defaultValue?: DeepPartialSkipArrayKey<TFieldValues>;
    control?: Control<TFieldValues, any, TTransformedValues>;
    disabled?: boolean;
    exact?: boolean;
    compute?: undefined;
}): FieldPathValues<TFieldValues, TFieldNames>;
/**
 * Custom hook to subscribe to field change and compute function to produce state update
 *
 * @remarks
 *
 * [API](https://react-hook-form.com/docs/usewatch)
 *
 * @param props - defaultValue, disable subscription and match exact name.
 *
 * @example
 * ```tsx
 * const { control } = useForm();
 * const values = useWatch({
 *   control,
 *   name: ["fieldA", "fieldB"],
 *   defaultValue: {
 *     fieldA: "data",
 *     fieldB: 0
 *   },
 *   compute: ([fieldAValue, fieldBValue]) => fieldB === 2 ? fieldA : null,
 *   exact: false,
 * })
 * ```
 */
export declare function useWatch<TFieldValues extends FieldValues = FieldValues, TFieldNames extends readonly FieldPath<TFieldValues>[] = readonly FieldPath<TFieldValues>[], TTransformedValues = TFieldValues, TComputeValue = unknown>(props: {
    name: readonly [...TFieldNames];
    defaultValue?: DeepPartialSkipArrayKey<TFieldValues>;
    control?: Control<TFieldValues, any, TTransformedValues>;
    disabled?: boolean;
    exact?: boolean;
    compute: (fieldValue: FieldPathValues<TFieldValues, TFieldNames>) => TComputeValue;
}): TComputeValue;
/**
 * Custom hook to subscribe to field change and isolate re-rendering at the component level.
 *
 * @remarks
 *
 * [API](https://react-hook-form.com/docs/usewatch) • [Demo](https://codesandbox.io/s/react-hook-form-v7-ts-usewatch-h9i5e)
 *
 * @example
 * ```tsx
 * // can skip passing down the control into useWatch if the form is wrapped with the FormProvider
 * const values = useWatch()
 * ```
 */
export declare function useWatch<TFieldValues extends FieldValues = FieldValues>(): DeepPartialSkipArrayKey<TFieldValues>;
//# sourceMappingURL=useWatch.d.ts.map