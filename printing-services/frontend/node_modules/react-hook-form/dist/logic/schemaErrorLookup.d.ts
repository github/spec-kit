import type { FieldError, FieldErrors, FieldValues } from '../types';
export default function schemaErrorLookup<T extends FieldValues = FieldValues>(errors: FieldErrors<T>, _fields: FieldValues, name: string): {
    error?: FieldError;
    name: string;
};
//# sourceMappingURL=schemaErrorLookup.d.ts.map