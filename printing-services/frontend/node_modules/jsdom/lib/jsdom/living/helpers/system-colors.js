"use strict";

// https://drafts.csswg.org/css-color-4/#css-system-colors
module.exports.systemColors = new Map([
  [
    "accentcolor", {
      light: "rgb(0, 153, 255)",
      dark: "rgb(0, 51, 255)"
    }
  ],
  [
    "accentcolortext", {
      light: "rgb(0, 0, 0)",
      dark: "rgb(255, 255, 255)"
    }
  ],
  [
    "activetext", {
      light: "rgb(255, 0, 0)",
      dark: "rgb(255, 102, 102)"
    }
  ],
  [
    "buttonborder", {
      light: "rgb(51, 51, 51)",
      dark: "rgb(204, 204, 204)"
    }
  ],
  [
    "buttonface", {
      light: "rgb(204, 204, 204)",
      dark: "rgb(51, 51, 51)"
    }
  ],
  [
    "buttontext", {
      light: "rgb(0, 0, 0)",
      dark: "rgb(255, 255, 155)"
    }
  ],
  [
    "canvas", {
      light: "rgb(255, 255, 255)",
      dark: "rgb(0, 0, 0)"
    }
  ],
  [
    "canvastext", {
      light: "rgb(0, 0, 0)",
      dark: "rgb(255, 255, 255)"
    }
  ],
  [
    "field", {
      light: "rgb(255, 255, 255)",
      dark: "rgb(0, 0, 0)"
    }
  ],
  [
    "fieldtext", {
      light: "rgb(0, 0, 0)",
      dark: "rgb(255, 255, 255)"
    }
  ],
  [
    "graytext", {
      light: "rgb(102, 102, 102)",
      dark: "rgb(153, 153, 153)"
    }
  ],
  [
    "highlight", {
      light: "rgb(0, 153, 255)",
      dark: "rgb(0, 51, 255)"
    }
  ],
  [
    "highlighttext", {
      light: "rgb(255, 255, 255)",
      dark: "rgb(0, 0, 0)"
    }
  ],
  [
    "linktext", {
      light: "rgb(0, 0, 255)",
      dark: "rgb(0, 204, 255)"
    }
  ],
  [
    "mark", {
      light: "rgb(255, 255, 0)",
      dark: "rgb(204, 0, 153)"
    }
  ],
  [
    "marktext", {
      light: "rgb(0, 0, 0)",
      dark: "rgb(255, 255, 255)"
    }
  ],
  [
    "selecteditem", {
      light: "rgb(0, 153, 255)",
      dark: "rgb(0, 51, 255)"
    }
  ],
  [
    "selecteditemtext", {
      light: "rgb(255, 255, 255)",
      dark: "rgb(0, 0, 0)"
    }
  ],
  [
    "visitedtext", {
      light: "rgb(128, 0, 128)",
      dark: "rgb(255, 51, 255)"
    }
  ]
]);

// Deprecated system colors
// https://drafts.csswg.org/css-color-4/#deprecated-system-colors
module.exports.deprecatedAliases = new Map([
  ["activeborder", "buttonborder"],
  ["activecaption", "canvas"],
  ["appworkspace", "canvas"],
  ["background", "canvas"],
  ["buttonhighlight", "buttonface"],
  ["buttonshadow", "buttonface"],
  ["captiontext", "canvastext"],
  ["inactiveborder", "buttonborder"],
  ["inactivecaption", "canvas"],
  ["inactivecaptiontext", "graytext"],
  ["infobackground", "canvas"],
  ["infotext", "canvastext"],
  ["menu", "canvas"],
  ["menutext", "canvastext"],
  ["scrollbar", "canvas"],
  ["threeddarkshadow", "buttonborder"],
  ["threedface", "buttonface"],
  ["threedhighlight", "buttonborder"],
  ["threedlightshadow", "buttonborder"],
  ["threedshadow", "buttonborder"],
  ["window", "canvas"],
  ["windowframe", "buttonborder"],
  ["windowtext", "canvastext"]
]);
