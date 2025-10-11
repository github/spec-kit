export = gooberShouldForwardProp;

export as namespace shouldForwardProp;

declare namespace gooberShouldForwardProp {
    type ForwardPropFunction = (prop: string) => boolean;

    function shouldForwardProp(fwdProp: ForwardPropFunction): (props: object) => undefined;
}
