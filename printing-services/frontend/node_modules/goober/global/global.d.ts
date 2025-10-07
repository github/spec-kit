import { Properties as CSSProperties } from 'csstype';
import { Theme, DefaultTheme } from 'goober';

export = gooberGlobal;

export as namespace gooberGlobal;

declare namespace gooberGlobal {
    interface CSSAttribute extends CSSProperties {
        [key: string]: CSSAttribute | string | number | undefined;
    }

    function createGlobalStyles(
        tag: CSSAttribute | TemplateStringsArray | string,
        ...props: Array<
            | string
            | number
            | ((props: Theme<DefaultTheme>) => CSSAttribute | string | number | false | undefined)
        >
    ): Function;
    function glob(
        tag: CSSAttribute | TemplateStringsArray | string,
        ...props: Array<string | number>
    ): void;
}
