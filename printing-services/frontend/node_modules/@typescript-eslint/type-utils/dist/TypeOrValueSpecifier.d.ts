import type { JSONSchema4 } from '@typescript-eslint/utils/json-schema';
import type * as ts from 'typescript';
interface FileSpecifier {
    from: 'file';
    name: string[] | string;
    path?: string;
}
interface LibSpecifier {
    from: 'lib';
    name: string[] | string;
}
interface PackageSpecifier {
    from: 'package';
    name: string[] | string;
    package: string;
}
export type TypeOrValueSpecifier = FileSpecifier | LibSpecifier | PackageSpecifier | string;
export declare const typeOrValueSpecifierSchema: JSONSchema4;
export declare function typeMatchesSpecifier(type: ts.Type, specifier: TypeOrValueSpecifier, program: ts.Program): boolean;
export {};
//# sourceMappingURL=TypeOrValueSpecifier.d.ts.map