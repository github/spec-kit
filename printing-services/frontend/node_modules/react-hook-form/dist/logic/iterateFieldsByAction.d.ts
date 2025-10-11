import type { FieldRefs, InternalFieldName, Ref } from '../types';
declare const iterateFieldsByAction: (fields: FieldRefs, action: (ref: Ref, name: string) => 1 | undefined | void, fieldsNames?: Set<InternalFieldName> | InternalFieldName[] | 0, abortEarly?: boolean) => true | undefined;
export default iterateFieldsByAction;
//# sourceMappingURL=iterateFieldsByAction.d.ts.map