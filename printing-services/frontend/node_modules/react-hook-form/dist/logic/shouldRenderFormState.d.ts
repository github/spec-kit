import type { FieldValues, FormState, InternalFieldName, ReadFormState } from '../types';
declare const _default: <T extends FieldValues, K extends ReadFormState>(formStateData: Partial<FormState<T>> & {
    name?: InternalFieldName;
    values?: T;
}, _proxyFormState: K, updateFormState: (formState: Partial<FormState<T>>) => void, isRoot?: boolean) => string | true | undefined;
export default _default;
//# sourceMappingURL=shouldRenderFormState.d.ts.map