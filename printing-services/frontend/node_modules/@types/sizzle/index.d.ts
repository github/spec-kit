export as namespace Sizzle;

declare const Sizzle: SizzleStatic;
export = Sizzle;

// For users who don't have "dom" types
// See: https://github.com/DefinitelyTyped/DefinitelyTyped/pull/73082
type Element = typeof globalThis extends { Element: { new(): infer T } } ? T : never;
type Document = typeof globalThis extends { Document: { new(): infer T } } ? T : never;
type DocumentFragment = typeof globalThis extends { DocumentFragment: { new(): infer T } } ? T : never;

interface SizzleStatic {
    selectors: Sizzle.Selectors;
    <TArrayLike extends ArrayLike<Element>>(
        selector: string,
        context: Element | Document | DocumentFragment,
        results: TArrayLike,
    ): TArrayLike;
    (selector: string, context?: Element | Document | DocumentFragment): Element[];
    // eslint-disable-next-line @typescript-eslint/no-unsafe-function-type
    compile(selector: string): Function;
    matchesSelector(element: Element, selector: string): boolean;
    matches(selector: string, elements: Element[]): Element[];
}

declare namespace Sizzle {
    interface Selectors {
        cacheLength: number;
        match: Selectors.Matches;
        find: Selectors.FindFunctions;
        preFilter: Selectors.PreFilterFunctions;
        filter: Selectors.FilterFunctions;
        attrHandle: Selectors.AttrHandleFunctions;
        pseudos: Selectors.PseudoFunctions;
        setFilters: Selectors.SetFilterFunctions;
        createPseudo(fn: Selectors.CreatePseudoFunction): Selectors.PseudoFunction;
    }

    namespace Selectors {
        interface Matches {
            [name: string]: RegExp;
        }

        interface FindFunction {
            // eslint-disable-next-line @typescript-eslint/no-invalid-void-type
            (match: RegExpMatchArray, context: Element | Document, isXML: boolean): Element[] | void;
        }

        interface FindFunctions {
            [name: string]: FindFunction;
        }

        interface PreFilterFunction {
            (match: RegExpMatchArray): string[];
        }

        interface PreFilterFunctions {
            [name: string]: PreFilterFunction;
        }

        interface FilterFunction {
            (element: string, ...matches: string[]): boolean;
        }

        interface FilterFunctions {
            [name: string]: FilterFunction;
        }

        interface AttrHandleFunction {
            (elem: any, casePreservedName: string, isXML: boolean): string;
        }

        interface AttrHandleFunctions {
            [name: string]: AttrHandleFunction;
        }

        interface PseudoFunction {
            (elem: Element): boolean;
        }

        interface PseudoFunctions {
            [name: string]: PseudoFunction;
        }

        interface SetFilterFunction {
            (elements: Element[], argument: number, not: boolean): Element[];
        }

        interface SetFilterFunctions {
            [name: string]: SetFilterFunction;
        }

        interface CreatePseudoFunction {
            (...args: any[]): PseudoFunction;
        }
    }
}
