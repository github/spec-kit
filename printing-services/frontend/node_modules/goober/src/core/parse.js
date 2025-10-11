/**
 * Parses the object into css, scoped, blocks
 * @param {Object} obj
 * @param {String} selector
 * @param {String} wrapper
 */
export let parse = (obj, selector) => {
    let outer = '';
    let blocks = '';
    let current = '';

    for (let key in obj) {
        let val = obj[key];

        if (key[0] == '@') {
            // If these are the `@` rule
            if (key[1] == 'i') {
                // Handling the `@import`
                outer = key + ' ' + val + ';';
            } else if (key[1] == 'f') {
                // Handling the `@font-face` where the
                // block doesn't need the brackets wrapped
                blocks += parse(val, key);
            } else {
                // Regular at rule block
                blocks += key + '{' + parse(val, key[1] == 'k' ? '' : selector) + '}';
            }
        } else if (typeof val == 'object') {
            // Call the parse for this block
            blocks += parse(
                val,
                selector
                    ? // Go over the selector and replace the matching multiple selectors if any
                      selector.replace(/([^,])+/g, (sel) => {
                          // Return the current selector with the key matching multiple selectors if any
                          return key.replace(/([^,]*:\S+\([^)]*\))|([^,])+/g, (k) => {
                              // If the current `k`(key) has a nested selector replace it
                              if (/&/.test(k)) return k.replace(/&/g, sel);

                              // If there's a current selector concat it
                              return sel ? sel + ' ' + k : k;
                          });
                      })
                    : key
            );
        } else if (val != undefined) {
            // Convert all but CSS variables
            key = /^--/.test(key) ? key : key.replace(/[A-Z]/g, '-$&').toLowerCase();
            // Push the line for this property
            current += parse.p
                ? // We have a prefixer and we need to run this through that
                  parse.p(key, val)
                : // Nope no prefixer just append it
                  key + ':' + val + ';';
        }
    }

    // If we have properties apply standard rule composition
    return outer + (selector && current ? selector + '{' + current + '}' : current) + blocks;
};
