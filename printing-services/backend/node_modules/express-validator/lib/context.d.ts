import { FieldInstance, FieldValidationError, Location, Meta, Request, UnknownFieldInstance, ValidationError } from './base';
import { ContextItem } from './context-items';
/**
 * Defines which kind of value makes a field optional.
 *
 * - `undefined`: only `undefined` values; equivalent to `value === undefined`
 * - `null`: only `undefined` and `null` values; equivalent to `value == null`
 * - `falsy`: all falsy values; equivalent to `!value`
 * - `false`: not optional.
 */
export type Optional = 'undefined' | 'null' | 'falsy' | false;
export type AddErrorOptions = {
    type: 'field';
    message?: any;
    value: any;
    meta: Meta;
} | {
    type: 'unknown_fields';
    req: Request;
    message?: any;
    fields: UnknownFieldInstance[];
} | {
    type: 'alternative';
    req: Request;
    message?: any;
    nestedErrors: FieldValidationError[];
} | {
    type: 'alternative_grouped';
    req: Request;
    message?: any;
    nestedErrors: FieldValidationError[][];
};
export type ValueVisibility = {
    type: 'visible';
} | {
    type: 'hidden';
} | {
    type: 'redacted';
    value: string;
};
export declare class Context {
    readonly fields: string[];
    readonly locations: Location[];
    readonly stack: ReadonlyArray<ContextItem>;
    readonly optional: Optional;
    readonly bail: boolean;
    readonly visibility: ValueVisibility;
    readonly message?: any | undefined;
    private readonly _errors;
    get errors(): ReadonlyArray<ValidationError>;
    private readonly dataMap;
    constructor(fields: string[], locations: Location[], stack: ReadonlyArray<ContextItem>, optional: Optional, bail: boolean, visibility?: ValueVisibility, message?: any | undefined);
    getData(options?: {
        requiredOnly: boolean;
    }): FieldInstance[];
    addFieldInstances(instances: FieldInstance[]): void;
    setData(path: string, value: any, location: Location): void;
    addError(opts: AddErrorOptions): void;
    private updateVisibility;
}
export type ReadonlyContext = Pick<Context, Exclude<keyof Context, 'setData' | 'addFieldInstances' | 'addError'>>;
