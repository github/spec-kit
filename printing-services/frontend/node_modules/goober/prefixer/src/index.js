import { cssPropertyAlias, cssPropertyPrefixFlags, cssValuePrefixFlags } from 'style-vendorizer';

export function prefix(property, value) {
    let cssText = '';

    /* Resolve aliases, e.g. `gap` -> `grid-gap` */
    const propertyAlias = cssPropertyAlias(property);
    if (propertyAlias) cssText += `${propertyAlias}:${value};`;

    /* Prefix properties, e.g. `backdrop-filter` -> `-webkit-backdrop-filter` */
    const propertyFlags = cssPropertyPrefixFlags(property);
    if (propertyFlags & 0b001) cssText += `-webkit-${property}:${value};`;
    if (propertyFlags & 0b010) cssText += `-moz-${property}:${value};`;
    if (propertyFlags & 0b100) cssText += `-ms-${property}:${value};`;

    /* Prefix values, e.g. `position: "sticky"` -> `position: "-webkit-sticky"` */
    /* Notice that flags don't overlap and property prefixing isn't needed here */
    const valueFlags = cssValuePrefixFlags(property, value);
    if (valueFlags & 0b001) cssText += `${property}:-webkit-${value};`;
    else if (valueFlags & 0b010) cssText += `${property}:-moz-${value};`;
    else if (valueFlags & 0b100) cssText += `${property}:-ms-${value};`;

    /* Include the standardized declaration last */
    /* https://css-tricks.com/ordering-css3-properties/ */
    cssText += `${property}:${value};`;

    return cssText;
}
