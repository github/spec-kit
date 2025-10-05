import type { INPUT_VALIDATION_RULES } from '../constants';
import type { Message } from './errors';
import type { FieldValues } from './fields';
import type { FieldPath, FieldPathValue } from './path';
export type ValidationValue = boolean | number | string | RegExp;
export type ValidationRule<TValidationValue extends ValidationValue = ValidationValue> = TValidationValue | ValidationValueMessage<TValidationValue>;
export type ValidationValueMessage<TValidationValue extends ValidationValue = ValidationValue> = {
    value: TValidationValue;
    message: Message;
};
export type ValidateResult = Message | Message[] | boolean | undefined;
export type Validate<TFieldValue, TFormValues> = (value: TFieldValue, formValues: TFormValues) => ValidateResult | Promise<ValidateResult>;
export type RegisterOptions<TFieldValues extends FieldValues = FieldValues, TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>> = Partial<{
    required: Message | ValidationRule<boolean>;
    min: ValidationRule<number | string>;
    max: ValidationRule<number | string>;
    maxLength: ValidationRule<number>;
    minLength: ValidationRule<number>;
    validate: Validate<FieldPathValue<TFieldValues, TFieldName>, TFieldValues> | Record<string, Validate<FieldPathValue<TFieldValues, TFieldName>, TFieldValues>>;
    value: FieldPathValue<TFieldValues, TFieldName>;
    setValueAs: (value: any) => any;
    shouldUnregister?: boolean;
    onChange?: (event: any) => void;
    onBlur?: (event: any) => void;
    disabled: boolean;
    deps: FieldPath<TFieldValues> | FieldPath<TFieldValues>[];
}> & ({
    pattern?: ValidationRule<RegExp>;
    valueAsNumber?: false;
    valueAsDate?: false;
} | {
    pattern?: undefined;
    valueAsNumber?: false;
    valueAsDate?: true;
} | {
    pattern?: undefined;
    valueAsNumber?: true;
    valueAsDate?: false;
});
export type InputValidationRules = typeof INPUT_VALIDATION_RULES;
export type MaxType = InputValidationRules['max'] | InputValidationRules['maxLength'];
export type MinType = InputValidationRules['min'] | InputValidationRules['minLength'];
//# sourceMappingURL=validator.d.ts.map