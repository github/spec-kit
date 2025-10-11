import type { ScopeManager } from '@typescript-eslint/scope-manager';
import type { TSESTree } from '@typescript-eslint/types';
import { ParserOptions } from '@typescript-eslint/types';
import type { ParserServices } from '@typescript-eslint/typescript-estree';
import { visitorKeys } from '@typescript-eslint/visitor-keys';
import type * as ts from 'typescript';
interface ParseForESLintResult {
    ast: TSESTree.Program & {
        range?: [number, number];
        tokens?: TSESTree.Token[];
        comments?: TSESTree.Comment[];
    };
    services: ParserServices;
    visitorKeys: typeof visitorKeys;
    scopeManager: ScopeManager;
}
declare function parse(code: ts.SourceFile | string, options?: ParserOptions): ParseForESLintResult['ast'];
declare function parseForESLint(code: ts.SourceFile | string, options?: ParserOptions | null): ParseForESLintResult;
export { parse, parseForESLint, ParserOptions };
//# sourceMappingURL=parser.d.ts.map