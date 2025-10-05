export class Finder {
    constructor(window: object);
    onError(e: Error, opt?: {
        noexcept?: boolean;
    }): void;
    setup(selector: string, node: object, opt?: {
        check?: boolean;
        domSymbolTree?: object;
        noexcept?: boolean;
        warn?: boolean;
    }): object;
    private _registerEventListeners;
    private _correspond;
    private _createTreeWalker;
    private _prepareQuerySelectorWalker;
    private _collectNthChild;
    private _collectNthOfType;
    private _matchAnPlusB;
    private _matchHasPseudoFunc;
    private _matchLogicalPseudoFunc;
    private _matchPseudoClassSelector;
    private _matchShadowHostPseudoClass;
    private _matchSelector;
    private _matchLeaves;
    private _findDescendantNodes;
    private _matchCombinator;
    private _findPrecede;
    private _findNodeWalker;
    private _matchSelf;
    private _findLineal;
    private _findEntryNodes;
    private _collectNodes;
    private _getCombinedNodes;
    private _matchNodeNext;
    private _matchNodePrev;
    find(targetType: string): Set<object>;
    #private;
}
