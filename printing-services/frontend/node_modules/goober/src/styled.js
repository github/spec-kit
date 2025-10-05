import { css } from './css';
import { parse } from './core/parse';

let h, useTheme, fwdProp;
function setup(pragma, prefix, theme, forwardProps) {
    // This one needs to stay in here, so we won't have cyclic dependencies
    parse.p = prefix;

    // These are scope to this context
    h = pragma;
    useTheme = theme;
    fwdProp = forwardProps;
}

/**
 * styled function
 * @param {string} tag
 * @param {function} forwardRef
 */
function styled(tag, forwardRef) {
    let _ctx = this || {};

    return function wrapper() {
        let _args = arguments;

        function Styled(props, ref) {
            // Grab a shallow copy of the props
            let _props = Object.assign({}, props);

            // Keep a local reference to the previous className
            let _previousClassName = _props.className || Styled.className;

            // _ctx.p: is the props sent to the context
            _ctx.p = Object.assign({ theme: useTheme && useTheme() }, _props);

            // Set a flag if the current components had a previous className
            // similar to goober. This is the append/prepend flag
            // The _empty_ space compresses better than `\s`
            _ctx.o = / *go\d+/.test(_previousClassName);

            _props.className =
                // Define the new className
                css.apply(_ctx, _args) + (_previousClassName ? ' ' + _previousClassName : '');

            // If the forwardRef fun is defined we have the ref
            if (forwardRef) {
                _props.ref = ref;
            }

            // Assign the _as with the provided `tag` value
            let _as = tag;

            // If this is a string -- checking that is has a first valid char
            if (tag[0]) {
                // Try to assign the _as with the given _as value if any
                _as = _props.as || tag;
                // And remove it
                delete _props.as;
            }

            // Handle the forward props filter if defined and _as is a string
            if (fwdProp && _as[0]) {
                fwdProp(_props);
            }

            return h(_as, _props);
        }

        return forwardRef ? forwardRef(Styled) : Styled;
    };
}

export { styled, setup };
