export function matchPseudoElementSelector(astName: string, astType: string, opt?: {
    forgive?: boolean;
    warn?: boolean;
}): void;
export function matchDirectionPseudoClass(ast: object, node: object): boolean;
export function matchLanguagePseudoClass(ast: object, node: object): boolean;
export function matchAttributeSelector(ast: object, node: object, opt?: {
    check?: boolean;
    forgive?: boolean;
}): boolean;
export function matchTypeSelector(ast: object, node: object, opt?: {
    check?: boolean;
    forgive?: boolean;
}): boolean;
