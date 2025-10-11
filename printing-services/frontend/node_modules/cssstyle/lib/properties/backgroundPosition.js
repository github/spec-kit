"use strict";

const parsers = require("../parsers");

const property = "background-position";
const shorthand = "background";
const keyX = ["left", "right"];
const keyY = ["top", "bottom"];
const keywordsX = ["center", ...keyX];
const keywordsY = ["center", ...keyY];
const keywords = ["center", ...keyX, ...keyY];

module.exports.parse = function parse(v, opt = {}) {
  const { globalObject } = opt;
  if (v === "") {
    return v;
  }
  const values = parsers.splitValue(v, {
    delimiter: ","
  });
  const parsedValues = [];
  for (const val of values) {
    const value = parsers.parsePropertyValue(property, val, {
      globalObject,
      inArray: true
    });
    if (Array.isArray(value) && value.length) {
      let parsedValue = "";
      switch (value.length) {
        case 1: {
          const [part1] = value;
          const val1 =
            part1.type === "Identifier" ? part1.name : parsers.parseLengthPercentage([part1]);
          if (val1) {
            if (val1 === "center") {
              parsedValue = `${val1} ${val1}`;
            } else if (val1 === "top" || val1 === "bottom") {
              parsedValue = `center ${val1}`;
            } else {
              parsedValue = `${val1} center`;
            }
          }
          break;
        }
        case 2: {
          const [part1, part2] = value;
          const val1 =
            part1.type === "Identifier" ? part1.name : parsers.parseLengthPercentage([part1]);
          const val2 =
            part2.type === "Identifier" ? part2.name : parsers.parseLengthPercentage([part2]);
          if (val1 && val2) {
            if (keywordsX.includes(val1) && keywordsY.includes(val2)) {
              parsedValue = `${val1} ${val2}`;
            } else if (keywordsY.includes(val1) && keywordsX.includes(val2)) {
              parsedValue = `${val2} ${val1}`;
            } else if (keywordsX.includes(val1)) {
              if (val2 === "center" || !keywordsX.includes(val2)) {
                parsedValue = `${val1} ${val2}`;
              }
            } else if (keywordsY.includes(val2)) {
              if (!keywordsY.includes(val1)) {
                parsedValue = `${val1} ${val2}`;
              }
            } else if (!keywordsY.includes(val1) && !keywordsX.includes(val2)) {
              parsedValue = `${val1} ${val2}`;
            }
          }
          break;
        }
        case 3: {
          const [part1, part2, part3] = value;
          const val1 = part1.type === "Identifier" && part1.name;
          const val2 =
            part2.type === "Identifier" ? part2.name : parsers.parseLengthPercentage([part2]);
          const val3 =
            part3.type === "Identifier" ? part3.name : parsers.parseLengthPercentage([part3]);
          if (val1 && val2 && val3) {
            let posX = "";
            let offX = "";
            let posY = "";
            let offY = "";
            if (keywordsX.includes(val1)) {
              if (keyY.includes(val2)) {
                if (!keywords.includes(val3)) {
                  posX = val1;
                  posY = val2;
                  offY = val3;
                }
              } else if (keyY.includes(val3)) {
                if (!keywords.includes(val2)) {
                  posX = val1;
                  offX = val2;
                  posY = val3;
                }
              }
            } else if (keywordsY.includes(val1)) {
              if (keyX.includes(val2)) {
                if (!keywords.includes(val3)) {
                  posX = val2;
                  offX = val3;
                  posY = val1;
                }
              } else if (keyX.includes(val3)) {
                if (!keywords.includes(val2)) {
                  posX = val3;
                  posY = val1;
                  offY = val2;
                }
              }
            }
            if (posX && posY) {
              if (offX) {
                parsedValue = `${posX} ${offX} ${posY}`;
              } else if (offY) {
                parsedValue = `${posX} ${posY} ${offY}`;
              }
            }
          }
          break;
        }
        case 4: {
          const [part1, part2, part3, part4] = value;
          const val1 = part1.type === "Identifier" && part1.name;
          const val2 = parsers.parseLengthPercentage([part2]);
          const val3 = part3.type === "Identifier" && part3.name;
          const val4 = parsers.parseLengthPercentage([part4]);
          if (val1 && val2 && val3 && val4) {
            let posX = "";
            let offX = "";
            let posY = "";
            let offY = "";
            if (keywordsX.includes(val1) && keyY.includes(val3)) {
              posX = val1;
              offX = val2;
              posY = val3;
              offY = val4;
            } else if (keyX.includes(val1) && keywordsY.includes(val3)) {
              posX = val1;
              offX = val2;
              posY = val3;
              offY = val4;
            } else if (keyY.includes(val1) && keywordsX.includes(val3)) {
              posX = val3;
              offX = val4;
              posY = val1;
              offY = val2;
            }
            if (posX && offX && posY && offY) {
              parsedValue = `${posX} ${offX} ${posY} ${offY}`;
            }
          }
          break;
        }
        default:
      }
      if (parsedValue) {
        parsedValues.push(parsedValue);
      } else {
        return;
      }
    } else if (typeof value === "string") {
      parsedValues.push(value);
    }
  }
  if (parsedValues.length) {
    return parsedValues.join(", ");
  }
};

module.exports.definition = {
  set(v) {
    v = parsers.prepareValue(v, this._global);
    if (parsers.hasVarFunc(v)) {
      this._setProperty(shorthand, "");
      this._setProperty(property, v);
    } else {
      const val = module.exports.parse(v, {
        globalObject: this._global
      });
      if (typeof val === "string") {
        const shorthandPriority = this._priorities.get(shorthand);
        const prior = this._priorities.get(property) ?? "";
        const priority = shorthandPriority && prior ? "" : prior;
        this._setProperty(property, val, priority);
      }
    }
  },
  get() {
    return this.getPropertyValue(property);
  },
  enumerable: true,
  configurable: true
};
