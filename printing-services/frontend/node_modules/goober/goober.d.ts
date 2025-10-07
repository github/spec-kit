import { Properties as CSSProperties } from 'csstype';

export = goober;

export as namespace goober;

declare namespace goober {
    interface DefaultTheme {}

    type Theme<T extends object> = keyof T extends never ? T : { theme: T };

    interface StyledFunction {
        // used when creating a styled component from a native HTML element
        <T extends keyof React.JSX.IntrinsicElements, P extends Object = {}>(
            tag: T,
            forwardRef?: ForwardRefFunction
        ): Tagged<
            React.JSX.LibraryManagedAttributes<T, React.JSX.IntrinsicElements[T]> &
                P &
                Theme<DefaultTheme>
        >;

        // used to extend other styled components. Inherits props from the extended component
        <PP extends Object = {}, P extends Object = {}>(
            tag: StyledVNode<PP>,
            forwardRef?: ForwardRefFunction
        ): Tagged<PP & P & Theme<DefaultTheme>>;

        // used when creating a component from a string (html native) but using a non HTML standard
        // component, such as when you want to style web components
        <P extends Object = {}>(tag: string): Tagged<
            P & Partial<React.JSX.ElementChildrenAttribute>
        >;

        // used to create a styled component from a JSX element (both functional and class-based)
        <T extends React.JSX.Element | React.JSX.ElementClass, P extends Object = {}>(
            tag: T,
            forwardRef?: ForwardRefFunction
        ): Tagged<P>;
    }

    // used when creating a styled component from a native HTML element with the babel-plugin-transform-goober parser
    type BabelPluginTransformGooberStyledFunction = {
        [T in keyof React.JSX.IntrinsicElements]: Tagged<
            React.JSX.LibraryManagedAttributes<T, React.JSX.IntrinsicElements[T]> &
                Theme<DefaultTheme>
        >;
    };

    type ForwardRefFunction = {
        (props: any, ref: any): any;
    };

    type ForwardPropsFunction = (props: object) => void;

    const styled: StyledFunction & BabelPluginTransformGooberStyledFunction;
    function setup<T>(
        val: T,
        prefixer?: (key: string, val: any) => string,
        theme?: Function,
        forwardProps?: ForwardPropsFunction
    ): void;
    function extractCss(target?: Element): string;
    function glob(
        tag: CSSAttribute | TemplateStringsArray | string,
        ...props: Array<string | number>
    ): void;
    function css(
        tag: CSSAttribute | TemplateStringsArray | string,
        ...props: Array<string | number>
    ): string;
    function keyframes(
        tag: CSSAttribute | TemplateStringsArray | string,
        ...props: Array<string | number>
    ): string;

    type StyledVNode<T> = ((props: T, ...args: any[]) => any) & {
        defaultProps?: T;
        displayName?: string;
    };

    type StylesGenerator<P extends Object = {}> = (props: P) => CSSAttribute | string;

    type Tagged<P extends Object = {}> = <PP extends Object = { as?: any }>(
        tag:
            | CSSAttribute
            | (CSSAttribute | StylesGenerator<P & PP>)[]
            | TemplateStringsArray
            | string
            | StylesGenerator<P & PP>,
        ...props: Array<
            | string
            | number
            | ((props: P & PP) => CSSAttribute | string | number | false | undefined)
        >
    ) => StyledVNode<Omit<P & PP, keyof Theme<DefaultTheme>>>;

    interface CSSAttribute extends CSSProperties {
        [key: string]: CSSAttribute | string | number | undefined | null;
    }
}
