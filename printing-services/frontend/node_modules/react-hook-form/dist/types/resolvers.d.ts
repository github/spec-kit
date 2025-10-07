import type { FieldErrors } from './errors';
import type { Field, FieldName, FieldValues, InternalFieldName } from './fields';
import type { CriteriaMode } from './form';
export type ResolverSuccess<TTransformedValues> = {
    values: TTransformedValues;
    errors: Record<string, never>;
};
export type ResolverError<TFieldValues extends FieldValues = FieldValues> = {
    values: Record<string, never>;
    errors: FieldErrors<TFieldValues>;
};
export type ResolverResult<TFieldValues extends FieldValues = FieldValues, TTransformedValues = TFieldValues> = ResolverSuccess<TTransformedValues> | ResolverError<TFieldValues>;
export interface ResolverOptions<TFieldValues extends FieldValues> {
    criteriaMode?: CriteriaMode;
    fields: Record<InternalFieldName, Field['_f']>;
    names?: FieldName<TFieldValues>[];
    shouldUseNativeValidation: boolean | undefined;
}
export type Resolver<TFieldValues extends FieldValues = FieldValues, TContext = any, TTransformedValues = TFieldValues> = (values: TFieldValues, context: TContext | undefined, options: ResolverOptions<TFieldValues>) => Promise<ResolverResult<TFieldValues, TTransformedValues>> | ResolverResult<TFieldValues, TTransformedValues>;
//# sourceMappingURL=resolvers.d.ts.map