let newRule = /(?:([\u0080-\uFFFF\w-%@]+) *:? *([^{;]+?);|([^;}{]*?) *{)|(}\s*)/g;
let ruleClean = /\/\*[^]*?\*\/|  +/g;
let ruleNewline = /\n+/g;
let empty = ' ';

/**
 * Convert a css style string into a object
 * @param {String} val
 * @returns {Object}
 */
export let astish = (val) => {
    let tree = [{}];
    let block, left;

    while ((block = newRule.exec(val.replace(ruleClean, '')))) {
        // Remove the current entry
        if (block[4]) {
            tree.shift();
        } else if (block[3]) {
            left = block[3].replace(ruleNewline, empty).trim();
            tree.unshift((tree[0][left] = tree[0][left] || {}));
        } else {
            tree[0][block[1]] = block[2].replace(ruleNewline, empty).trim();
        }
    }

    return tree[0];
};
