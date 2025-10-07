import type { JSONSchema4 } from '@typescript-eslint/utils/json-schema';
import * as ts from 'typescript';
import type { TypeOrValueSpecifier } from './TypeOrValueSpecifier';
export interface ReadonlynessOptions {
    readonly treatMethodsAsReadonly?: boolean;
    readonly allow?: TypeOrValueSpecifier[];
}
export declare const readonlynessOptionsSchema: {
    type: "object";
    additionalProperties: false;
    properties: {
        treatMethodsAsReadonly: {
            type: "boolean";
        };
        allow: {
            type: "array";
            items: JSONSchema4;
        };
    };
};
export declare const readonlynessOptionsDefaults: ReadonlynessOptions;
/**
 * Checks if the given type is readonly
 */
declare function isTypeReadonly(program: ts.Program, type: ts.Type, options?: ReadonlynessOptions): boolean;
export { isTypeReadonly };
//# sourceMappingURL=isTypeReadonly.d.ts.map