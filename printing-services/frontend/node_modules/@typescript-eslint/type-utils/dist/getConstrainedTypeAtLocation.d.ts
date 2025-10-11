import type { ParserServicesWithTypeInformation, TSESTree } from '@typescript-eslint/typescript-estree';
import type * as ts from 'typescript';
/**
 * Resolves the given node's type. Will resolve to the type's generic constraint, if it has one.
 */
export declare function getConstrainedTypeAtLocation(services: ParserServicesWithTypeInformation, node: TSESTree.Node): ts.Type;
//# sourceMappingURL=getConstrainedTypeAtLocation.d.ts.map