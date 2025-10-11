import type { CriteriaMode, FieldName, FieldRefs, FieldValues, InternalFieldName } from '../types';
declare const _default: <TFieldValues extends FieldValues>(fieldsNames: Set<InternalFieldName> | InternalFieldName[], _fields: FieldRefs, criteriaMode?: CriteriaMode, shouldUseNativeValidation?: boolean | undefined) => {
    criteriaMode: CriteriaMode | undefined;
    names: FieldName<TFieldValues>[];
    fields: Record<string, {
        ref: import("../types").Ref;
        name: InternalFieldName;
        refs?: HTMLInputElement[];
        mount?: boolean;
    } & import("../types").RegisterOptions>;
    shouldUseNativeValidation: boolean | undefined;
};
export default _default;
//# sourceMappingURL=getResolverOptions.d.ts.map