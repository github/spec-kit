"use strict";

const parsers = require("../parsers");
const backgroundImage = require("./backgroundImage");
const backgroundPosition = require("./backgroundPosition");
const backgroundSize = require("./backgroundSize");
const backgroundRepeat = require("./backgroundRepeat");
const backgroundOrigin = require("./backgroundOrigin");
const backgroundClip = require("./backgroundClip");
const backgroundAttachment = require("./backgroundAttachment");
const backgroundColor = require("./backgroundColor");

const property = "background";
const initialValues = new Map([
  ["background-image", "none"],
  ["background-position", "0% 0%"],
  ["background-size", "auto"],
  ["background-repeat", "repeat"],
  ["background-origin", "padding-box"],
  ["background-clip", "border-box"],
  ["background-attachment", "scroll"],
  ["background-color", "transparent"]
]);

module.exports.shorthandFor = new Map([
  ["background-image", backgroundImage],
  ["background-position", backgroundPosition],
  ["background-size", backgroundSize],
  ["background-repeat", backgroundRepeat],
  ["background-origin", backgroundOrigin],
  ["background-clip", backgroundClip],
  ["background-attachment", backgroundAttachment],
  ["background-color", backgroundColor]
]);

module.exports.parse = function parse(v, opt = {}) {
  const { globalObject } = opt;
  if (v === "") {
    return v;
  } else if (parsers.hasCalcFunc(v)) {
    v = parsers.resolveCalc(v);
  }
  if (!parsers.isValidPropertyValue(property, v)) {
    return;
  }
  const values = parsers.splitValue(v, {
    delimiter: ","
  });
  const bgValues = [];
  const l = values.length;
  for (let i = 0; i < l; i++) {
    let bg = {
      "background-image": initialValues.get("background-image"),
      "background-position": initialValues.get("background-position"),
      "background-size": initialValues.get("background-size"),
      "background-repeat": initialValues.get("background-repeat"),
      "background-origin": initialValues.get("background-origin"),
      "background-clip": initialValues.get("background-clip"),
      "background-attachment": initialValues.get("background-attachment"),
      "background-color": initialValues.get("background-color")
    };
    if (l > 1 && i !== l - 1) {
      bg = {
        "background-image": initialValues.get("background-image"),
        "background-position": initialValues.get("background-position"),
        "background-size": initialValues.get("background-size"),
        "background-repeat": initialValues.get("background-repeat"),
        "background-origin": initialValues.get("background-origin"),
        "background-clip": initialValues.get("background-clip"),
        "background-attachment": initialValues.get("background-attachment")
      };
    }
    const bgPosition = [];
    const bgSize = [];
    const bgRepeat = [];
    const bgBox = [];
    const bgParts = parsers.splitValue(values[i], {
      delimiter: "/"
    });
    if (!bgParts.length || bgParts.length > 2) {
      return;
    }
    const [bgPart1, bgPart2 = ""] = bgParts;
    const parts1 = parsers.splitValue(bgPart1);
    for (const part of parts1) {
      let partValid = false;
      for (const [longhand, value] of module.exports.shorthandFor) {
        if (parsers.isValidPropertyValue(longhand, part)) {
          partValid = true;
          switch (longhand) {
            case "background-clip":
            case "background-origin": {
              const parsedValue = value.parse(part, { globalObject });
              if (parsedValue) {
                bgBox.push(parsedValue);
              }
              break;
            }
            case "background-color": {
              if (i !== values.length - 1) {
                return;
              }
              const parsedValue = value.parse(part, { globalObject });
              if (parsedValue) {
                bg[longhand] = parsedValue;
              }
              break;
            }
            case "background-position": {
              const parsedValue = value.parse(part, { globalObject });
              if (parsedValue) {
                bgPosition.push(parsedValue);
              }
              break;
            }
            case "background-repeat": {
              const parsedValue = value.parse(part, { globalObject });
              if (parsedValue) {
                bgRepeat.push(parsedValue);
              }
              break;
            }
            case "background-size": {
              break;
            }
            default: {
              const parsedValue = value.parse(part, { globalObject });
              if (parsedValue) {
                bg[longhand] = parsedValue;
              }
            }
          }
        }
      }
      if (!partValid) {
        return;
      }
    }
    if (bgPart2) {
      const parts2 = parsers.splitValue(bgPart2);
      for (const part of parts2) {
        let partValid = false;
        for (const [longhand, value] of module.exports.shorthandFor) {
          if (parsers.isValidPropertyValue(longhand, part)) {
            partValid = true;
            switch (longhand) {
              case "background-clip":
              case "background-origin": {
                const parsedValue = value.parse(part, { globalObject });
                if (parsedValue) {
                  bgBox.push(parsedValue);
                }
                break;
              }
              case "background-color": {
                if (i !== l - 1) {
                  return;
                }
                const parsedValue = value.parse(part, { globalObject });
                if (parsedValue) {
                  bg[longhand] = parsedValue;
                }
                break;
              }
              case "background-position": {
                break;
              }
              case "background-repeat": {
                const parsedValue = value.parse(part, { globalObject });
                if (parsedValue) {
                  bgRepeat.push(parsedValue);
                }
                break;
              }
              case "background-size": {
                const parsedValue = value.parse(part, { globalObject });
                if (parsedValue) {
                  bgSize.push(parsedValue);
                }
                break;
              }
              default: {
                const parsedValue = value.parse(part, { globalObject });
                if (parsedValue) {
                  bg[longhand] = parsedValue;
                }
              }
            }
          }
        }
        if (!partValid) {
          return;
        }
      }
    }
    if (bgPosition.length) {
      const { parse: parser } = module.exports.shorthandFor.get("background-position");
      const value = parser(bgPosition.join(" "), { globalObject });
      if (value) {
        bg["background-position"] = value;
      }
    }
    if (bgSize.length) {
      const { parse: parser } = module.exports.shorthandFor.get("background-size");
      const value = parser(bgSize.join(" "), { globalObject });
      if (value) {
        bg["background-size"] = value;
      }
    }
    if (bgRepeat.length) {
      const { parse: parser } = module.exports.shorthandFor.get("background-repeat");
      const value = parser(bgRepeat.join(" "), { globalObject });
      if (value) {
        bg["background-repeat"] = value;
      }
    }
    if (bgBox.length) {
      switch (bgBox.length) {
        case 1: {
          const [value] = bgBox;
          bg["background-origin"] = value;
          bg["background-clip"] = value;
          break;
        }
        case 2: {
          const [value1, value2] = bgBox;
          bg["background-origin"] = value1;
          bg["background-clip"] = value2;
          break;
        }
        default: {
          return;
        }
      }
    }
    bgValues.push(bg);
  }
  return bgValues;
};

module.exports.definition = {
  set(v) {
    v = parsers.prepareValue(v, this._global);
    if (v === "" || parsers.hasVarFunc(v)) {
      for (const [key] of module.exports.shorthandFor) {
        this._setProperty(key, "");
      }
      this._setProperty(property, v);
    } else {
      const bgValues = module.exports.parse(v, {
        globalObject: this._global
      });
      if (!Array.isArray(bgValues)) {
        return;
      }
      const bgMap = new Map([
        ["background-image", []],
        ["background-position", []],
        ["background-size", []],
        ["background-repeat", []],
        ["background-origin", []],
        ["background-clip", []],
        ["background-attachment", []],
        ["background-color", []]
      ]);
      const backgrounds = [];
      for (const bgValue of bgValues) {
        const bg = [];
        for (const [longhand, value] of Object.entries(bgValue)) {
          if (value) {
            const arr = bgMap.get(longhand);
            arr.push(value);
            bgMap.set(longhand, arr);
            if (value !== initialValues.get(longhand)) {
              if (longhand === "background-size") {
                bg.push(`/ ${value}`);
              } else {
                bg.push(value);
              }
            } else if (longhand === "background-image") {
              if (v === "none") {
                bg.push(value);
              }
            } else if (longhand === "background-color") {
              if (v === "transparent") {
                bg.push(value);
              }
            }
          }
        }
        backgrounds.push(bg.join(" "));
      }
      const priority = this._priorities.get(property) ?? "";
      for (const [longhand, value] of bgMap) {
        this._setProperty(longhand, value.join(", "), priority);
      }
      this._setProperty(property, backgrounds.join(", "), priority);
    }
  },
  get() {
    const v = this.getPropertyValue(property);
    if (parsers.hasVarFunc(v)) {
      return v;
    }
    const bgMap = new Map();
    let l = 0;
    for (const [longhand] of module.exports.shorthandFor) {
      const val = this.getPropertyValue(longhand);
      if (longhand === "background-image") {
        if (
          val === "none" &&
          v === "none" &&
          this.getPropertyValue("background-color") === "transparent"
        ) {
          return val;
        }
        if (val !== initialValues.get(longhand)) {
          const imgValues = parsers.splitValue(val, {
            delimiter: ","
          });
          l = imgValues.length;
          bgMap.set(longhand, imgValues);
        }
      } else if (longhand === "background-color") {
        if (val !== initialValues.get(longhand) || v.includes(val)) {
          bgMap.set(longhand, [val]);
        }
      } else if (val !== initialValues.get(longhand)) {
        bgMap.set(
          longhand,
          parsers.splitValue(val, {
            delimiter: ","
          })
        );
      }
    }
    if (l === 0) {
      const [background] = bgMap.get("background-color");
      if (background) {
        return background;
      }
      return "";
    }
    const bgValues = [];
    for (let i = 0; i < l; i++) {
      bgValues[i] = [];
    }
    for (const [longhand, values] of bgMap) {
      for (let i = 0; i < l; i++) {
        switch (longhand) {
          case "background-color": {
            if (i === l - 1) {
              const value = values[0];
              if (parsers.hasVarFunc(value)) {
                return "";
              }
              if (value && value !== initialValues.get(longhand)) {
                const bgValue = bgValues[i];
                bgValue.push(value);
              }
            }
            break;
          }
          case "background-size": {
            const value = values[i];
            if (parsers.hasVarFunc(value)) {
              return "";
            }
            if (value && value !== initialValues.get(longhand)) {
              const bgValue = bgValues[i];
              bgValue.push(`/ ${value}`);
            }
            break;
          }
          default: {
            const value = values[i];
            if (parsers.hasVarFunc(value)) {
              return "";
            }
            if (value && value !== initialValues.get(longhand)) {
              const bgValue = bgValues[i];
              bgValue.push(value);
            }
          }
        }
      }
    }
    const backgrounds = [];
    for (const bgValue of bgValues) {
      backgrounds.push(bgValue.join(" "));
    }
    return backgrounds.join(", ");
  },
  enumerable: true,
  configurable: true
};
