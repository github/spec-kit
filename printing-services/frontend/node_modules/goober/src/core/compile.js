import { parse } from './parse';

/**
 * Can parse a compiled string, from a tagged template
 * @param {String} value
 * @param {Object} [props]
 */
export let compile = (str, defs, data) => {
    return str.reduce((out, next, i) => {
        let tail = defs[i];

        // If this is a function we need to:
        if (tail && tail.call) {
            // 1. Call it with `data`
            let res = tail(data);

            // 2. Grab the className
            let className = res && res.props && res.props.className;

            // 3. If there's none, see if this is basically a
            // previously styled className by checking the prefix
            let end = className || (/^go/.test(res) && res);

            if (end) {
                // If the `end` is defined means it's a className
                tail = '.' + end;
            } else if (res && typeof res == 'object') {
                // If `res` it's an object, we're either dealing with a vnode
                // or an object returned from a function interpolation
                tail = res.props ? '' : parse(res, '');
            } else {
                // Regular value returned. Can be falsy as well.
                // Here we check if this is strictly a boolean with false value
                // define it as `''` to be picked up as empty, otherwise use
                // res value
                tail = res === false ? '' : res;
            }
        }
        return out + next + (tail == null ? '' : tail);
    }, '');
};
