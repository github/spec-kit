import type { FieldValues, UseFormProps, UseFormReturn } from '../types';
export declare function createFormControl<TFieldValues extends FieldValues = FieldValues, TContext = any, TTransformedValues = TFieldValues>(props?: UseFormProps<TFieldValues, TContext, TTransformedValues>): Omit<UseFormReturn<TFieldValues, TContext, TTransformedValues>, 'formState'> & {
    formControl: Omit<UseFormReturn<TFieldValues, TContext, TTransformedValues>, 'formState'>;
};
//# sourceMappingURL=createFormControl.d.ts.map