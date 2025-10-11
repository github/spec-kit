import type { IsFlatObject, Noop } from './utils';
import type { RegisterOptions } from './validator';
export type InternalFieldName = string;
export type FieldName<TFieldValues extends FieldValues> = IsFlatObject<TFieldValues> extends true ? Extract<keyof TFieldValues, string> : string;
export type CustomElement<TFieldValues extends FieldValues> = Partial<HTMLElement> & {
    name: FieldName<TFieldValues>;
    type?: string;
    value?: any;
    disabled?: boolean;
    checked?: boolean;
    options?: HTMLOptionsCollection;
    files?: FileList | null;
    focus?: Noop;
};
export type FieldValue<TFieldValues extends FieldValues> = TFieldValues[InternalFieldName];
export type FieldValues = Record<string, any>;
export type NativeFieldValue = string | number | boolean | null | undefined | unknown[];
export type FieldElement<TFieldValues extends FieldValues = FieldValues> = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement | CustomElement<TFieldValues>;
export type Ref = FieldElement;
export type Field = {
    _f: {
        ref: Ref;
        name: InternalFieldName;
        refs?: HTMLInputElement[];
        mount?: boolean;
    } & RegisterOptions;
};
export type FieldRefs = Partial<{
    [key: InternalFieldName]: Field | FieldRefs;
}>;
//# sourceMappingURL=fields.d.ts.map