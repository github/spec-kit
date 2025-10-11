/**
 * Should forward prop utility function
 * @param {Function} filterPropFunction The flter function
 */
export function shouldForwardProp(filterPropFunction) {
    /**
     * The forward props function passed to `setup`
     * @param {object} props
     */
    function forwardProp(props) {
        for (let p in props) {
            if (!filterPropFunction(p)) {
                delete props[p];
            }
        }
    }

    return forwardProp;
}
