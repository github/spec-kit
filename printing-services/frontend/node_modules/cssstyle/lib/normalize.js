"use strict";

const implementedProperties = require("./generated/implementedProperties");
const { hasVarFunc, isGlobalKeyword, isValidPropertyValue, splitValue } = require("./parsers");
const background = require("./properties/background");
const border = require("./properties/border");
const borderWidth = require("./properties/borderWidth");
const borderStyle = require("./properties/borderStyle");
const borderColor = require("./properties/borderColor");
const borderTop = require("./properties/borderTop");
const borderRight = require("./properties/borderRight");
const borderBottom = require("./properties/borderBottom");
const borderLeft = require("./properties/borderLeft");
const flex = require("./properties/flex");
const font = require("./properties/font");
const margin = require("./properties/margin");
const padding = require("./properties/padding");

const borderImageProperty = "border-image";

exports.shorthandProperties = new Map([
  ["background", background],
  [
    "border",
    {
      definition: border.definition,
      parse: border.parse,
      shorthandFor: new Map([
        ...border.shorthandFor,
        ...border.positionShorthandFor,
        [borderImageProperty, null]
      ])
    }
  ],
  ["border-width", borderWidth],
  ["border-style", borderStyle],
  ["border-color", borderColor],
  ["border-top", borderTop],
  ["border-right", borderRight],
  ["border-bottom", borderBottom],
  ["border-left", borderLeft],
  ["flex", flex],
  ["font", font],
  ["margin", margin],
  ["padding", padding]
]);

exports.borderProperties = new Set([
  "border",
  borderImageProperty,
  ...border.shorthandFor.keys(),
  ...border.positionShorthandFor.keys(),
  ...borderTop.shorthandFor.keys(),
  ...borderRight.shorthandFor.keys(),
  ...borderBottom.shorthandFor.keys(),
  ...borderLeft.shorthandFor.keys()
]);

exports.getPositionValue = (positionValues, position) => {
  switch (positionValues.length) {
    case 1: {
      const [val1] = positionValues;
      return val1;
    }
    case 2: {
      const [val1, val2] = positionValues;
      switch (position) {
        case "top": {
          return val1;
        }
        case "right": {
          return val2;
        }
        case "bottom": {
          return val1;
        }
        case "left": {
          return val2;
        }
        default: {
          if (val1 === val2) {
            return val1;
          }
          return `${val1} ${val2}`;
        }
      }
    }
    case 3: {
      const [val1, val2, val3] = positionValues;
      switch (position) {
        case "top": {
          return val1;
        }
        case "right": {
          return val2;
        }
        case "bottom": {
          return val3;
        }
        case "left": {
          return val2;
        }
        default: {
          if (val1 === val3) {
            if (val1 === val2) {
              return val1;
            }
            return `${val1} ${val2}`;
          }
          return `${val1} ${val2} ${val3}`;
        }
      }
    }
    case 4: {
      const [val1, val2, val3, val4] = positionValues;
      switch (position) {
        case "top": {
          return val1;
        }
        case "right": {
          return val2;
        }
        case "bottom": {
          return val3;
        }
        case "left": {
          return val4;
        }
        default: {
          if (val2 === val4) {
            if (val1 === val3) {
              if (val1 === val2) {
                return val1;
              }
              return `${val1} ${val2}`;
            }
            return `${val1} ${val2} ${val3}`;
          }
          return `${val1} ${val2} ${val3} ${val4}`;
        }
      }
    }
    default:
  }
};

const borderElements = {
  name: "border",
  positions: ["top", "right", "bottom", "left"],
  lines: ["width", "style", "color"]
};

const getPropertyItem = (property, properties) => {
  const propertyItem = properties.get(property) ?? {
    property,
    value: "",
    priority: ""
  };
  return propertyItem;
};

const matchesBorderShorthandValue = (property, value, shorthandValue, opt = {}) => {
  const { globalObject } = opt;
  const obj = border.parse(shorthandValue, {
    globalObject
  });
  if (Object.hasOwn(obj, property)) {
    return value === obj[property];
  }
  return value === border.initialValues.get(property);
};

const replaceBorderShorthandValue = (value, shorthandValue, opt = {}) => {
  const { globalObject } = opt;
  const borderFirstInitialKey = border.initialValues.keys().next().value;
  const borderFirstInitialValue = border.initialValues.get(borderFirstInitialKey);
  const valueObj = border.parse(value, {
    globalObject
  });
  const shorthandObj = shorthandValue
    ? border.parse(shorthandValue, {
        globalObject
      })
    : {
        [borderFirstInitialKey]: borderFirstInitialValue
      };
  const keys = border.shorthandFor.keys();
  for (const key of keys) {
    const initialValue = border.initialValues.get(key);
    let parsedValue = initialValue;
    if (Object.hasOwn(valueObj, key)) {
      parsedValue = valueObj[key];
    }
    if (parsedValue === initialValue) {
      if (key === borderFirstInitialKey) {
        if (!Object.hasOwn(shorthandObj, key)) {
          shorthandObj[key] = parsedValue;
        }
      } else {
        delete shorthandObj[key];
      }
    } else {
      shorthandObj[key] = parsedValue;
      if (
        shorthandObj[borderFirstInitialKey] &&
        shorthandObj[borderFirstInitialKey] === borderFirstInitialValue
      ) {
        delete shorthandObj[borderFirstInitialKey];
      }
    }
  }
  return Object.values(shorthandObj).join(" ");
};

const replacePositionValue = (value, positionValues, position) => {
  switch (positionValues.length) {
    case 1: {
      const [val1] = positionValues;
      if (val1 === value) {
        return positionValues.join(" ");
      }
      switch (position) {
        case "top": {
          return [value, val1, val1].join(" ");
        }
        case "right": {
          return [val1, value, val1, val1].join(" ");
        }
        case "bottom": {
          return [val1, val1, value].join(" ");
        }
        case "left": {
          return [val1, val1, val1, value].join(" ");
        }
        default:
      }
      break;
    }
    case 2: {
      const [val1, val2] = positionValues;
      if (val1 === val2) {
        return replacePositionValue(value, [val1], position);
      }
      switch (position) {
        case "top": {
          if (val1 === value) {
            return positionValues.join(" ");
          }
          return [value, val2, val1].join(" ");
        }
        case "right": {
          if (val2 === value) {
            return positionValues.join(" ");
          }
          return [val1, value, val1, val2].join(" ");
        }
        case "bottom": {
          if (val1 === value) {
            return positionValues.join(" ");
          }
          return [val1, val2, value].join(" ");
        }
        case "left": {
          if (val2 === value) {
            return positionValues.join(" ");
          }
          return [val1, val2, val1, value].join(" ");
        }
        default:
      }
      break;
    }
    case 3: {
      const [val1, val2, val3] = positionValues;
      if (val1 === val3) {
        return replacePositionValue(value, [val1, val2], position);
      }
      switch (position) {
        case "top": {
          if (val1 === value) {
            return positionValues.join(" ");
          } else if (val3 === value) {
            return [value, val2].join(" ");
          }
          return [value, val2, val3].join(" ");
        }
        case "right": {
          if (val2 === value) {
            return positionValues.join(" ");
          }
          return [val1, value, val3, val2].join(" ");
        }
        case "bottom": {
          if (val3 === value) {
            return positionValues.join(" ");
          } else if (val1 === value) {
            return [val1, val2].join(" ");
          }
          return [val1, val2, value].join(" ");
        }
        case "left": {
          if (val2 === value) {
            return positionValues.join(" ");
          }
          return [val1, val2, val3, value].join(" ");
        }
        default:
      }
      break;
    }
    case 4: {
      const [val1, val2, val3, val4] = positionValues;
      if (val2 === val4) {
        return replacePositionValue(value, [val1, val2, val3], position);
      }
      switch (position) {
        case "top": {
          if (val1 === value) {
            return positionValues.join(" ");
          }
          return [value, val2, val3, val4].join(" ");
        }
        case "right": {
          if (val2 === value) {
            return positionValues.join(" ");
          } else if (val4 === value) {
            return [val1, value, val3].join(" ");
          }
          return [val1, value, val3, val4].join(" ");
        }
        case "bottom": {
          if (val3 === value) {
            return positionValues.join(" ");
          }
          return [val1, val2, value, val4].join(" ");
        }
        case "left": {
          if (val4 === value) {
            return positionValues.join(" ");
          } else if (val2 === value) {
            return [val1, val2, val3].join(" ");
          }
          return [val1, val2, val3, value].join(" ");
        }
        default:
      }
      break;
    }
    default:
  }
};

exports.prepareBorderProperties = (property, value, priority, properties, opt = {}) => {
  if (typeof property !== "string" || value === null) {
    return;
  }
  const { globalObject } = opt;
  const { lines, name, positions } = borderElements;
  const [prop1, prop2, prop3] = property.split("-");
  if (prop1 !== name) {
    return;
  } else if (positions.includes(prop2)) {
    if (prop3) {
      if (!lines.includes(prop3)) {
        return;
      }
    }
  } else if (lines.includes(prop2)) {
    if (prop3) {
      return;
    }
  }
  const borderItems = new Map();
  const nameProperty = prop1;
  // Empty string, global keywords, var(), value of longhands.
  if (typeof value === "string") {
    // longhand properties
    if (prop3) {
      const nameItem = getPropertyItem(nameProperty, properties);
      const imageItem = getPropertyItem(borderImageProperty, properties);
      const lineProperty = `${prop1}-${prop3}`;
      const lineItem = getPropertyItem(lineProperty, properties);
      const positionProperty = `${prop1}-${prop2}`;
      const positionItem = getPropertyItem(positionProperty, properties);
      const longhandProperty = `${prop1}-${prop2}-${prop3}`;
      const longhandItem = getPropertyItem(longhandProperty, properties);
      longhandItem.value = value;
      longhandItem.priority = priority;
      const propertyValue = hasVarFunc(value) ? "" : value;
      if (propertyValue === "") {
        nameItem.value = "";
        lineItem.value = "";
        positionItem.value = "";
      } else if (isGlobalKeyword(propertyValue)) {
        if (nameItem.value !== propertyValue) {
          nameItem.value = "";
        }
        if (lineItem.value !== propertyValue) {
          lineItem.value = "";
        }
        if (positionItem.value !== propertyValue) {
          positionItem.value = "";
        }
      } else {
        if (
          nameItem.value &&
          !matchesBorderShorthandValue(lineProperty, propertyValue, nameItem.value, {
            globalObject
          })
        ) {
          nameItem.value = "";
        }
        if (lineItem.value) {
          lineItem.value = replacePositionValue(propertyValue, splitValue(lineItem.value), prop2);
        }
        if (
          positionItem.value &&
          !matchesBorderShorthandValue(lineProperty, propertyValue, positionItem.value, {
            globalObject
          })
        ) {
          positionItem.value = "";
        }
      }
      borderItems.set(nameProperty, nameItem);
      borderItems.set(borderImageProperty, imageItem);
      borderItems.set(lineProperty, lineItem);
      borderItems.set(positionProperty, positionItem);
      borderItems.set(longhandProperty, longhandItem);
      // border-top, border-right, border-bottom, border-left shorthands
    } else if (prop2 && positions.includes(prop2)) {
      const nameItem = getPropertyItem(nameProperty, properties);
      const imageItem = getPropertyItem(borderImageProperty, properties);
      const lineWidthProperty = `${prop1}-width`;
      const lineWidthItem = getPropertyItem(lineWidthProperty, properties);
      const lineStyleProperty = `${prop1}-style`;
      const lineStyleItem = getPropertyItem(lineStyleProperty, properties);
      const lineColorProperty = `${prop1}-color`;
      const lineColorItem = getPropertyItem(lineColorProperty, properties);
      const positionProperty = `${prop1}-${prop2}`;
      const positionItem = getPropertyItem(positionProperty, properties);
      positionItem.value = value;
      positionItem.priority = priority;
      const propertyValue = hasVarFunc(value) ? "" : value;
      if (propertyValue === "") {
        nameItem.value = "";
        lineWidthItem.value = "";
        lineStyleItem.value = "";
        lineColorItem.value = "";
      } else if (isGlobalKeyword(propertyValue)) {
        if (nameItem.value !== propertyValue) {
          nameItem.value = "";
        }
        if (lineWidthItem.value !== propertyValue) {
          lineWidthItem.value = "";
        }
        if (lineStyleItem.value !== propertyValue) {
          lineStyleItem.value = "";
        }
        if (lineColorItem.value !== propertyValue) {
          lineColorItem.value = "";
        }
      } else {
        if (
          nameItem.value &&
          !matchesBorderShorthandValue(property, propertyValue, nameItem.value, {
            globalObject
          })
        ) {
          nameItem.value = "";
        }
        if (lineWidthItem.value && isValidPropertyValue(lineWidthProperty, propertyValue)) {
          lineWidthItem.value = propertyValue;
        }
        if (lineStyleItem.value && isValidPropertyValue(lineStyleProperty, propertyValue)) {
          lineStyleItem.value = propertyValue;
        }
        if (lineColorItem.value && isValidPropertyValue(lineColorProperty, propertyValue)) {
          lineColorItem.value = propertyValue;
        }
      }
      for (const line of lines) {
        const longhandProperty = `${prop1}-${prop2}-${line}`;
        const longhandItem = getPropertyItem(longhandProperty, properties);
        longhandItem.value = propertyValue;
        longhandItem.priority = priority;
        borderItems.set(longhandProperty, longhandItem);
      }
      borderItems.set(nameProperty, nameItem);
      borderItems.set(borderImageProperty, imageItem);
      borderItems.set(lineWidthProperty, lineWidthItem);
      borderItems.set(lineStyleProperty, lineStyleItem);
      borderItems.set(lineColorProperty, lineColorItem);
      borderItems.set(positionProperty, positionItem);
      // border-width, border-style, border-color
    } else if (prop2 && lines.includes(prop2)) {
      const nameItem = getPropertyItem(nameProperty, properties);
      const imageItem = getPropertyItem(borderImageProperty, properties);
      const lineProperty = `${prop1}-${prop2}`;
      const lineItem = getPropertyItem(lineProperty, properties);
      lineItem.value = value;
      lineItem.priority = priority;
      const propertyValue = hasVarFunc(value) ? "" : value;
      if (propertyValue === "") {
        nameItem.value = "";
      } else if (isGlobalKeyword(propertyValue)) {
        if (nameItem.value !== propertyValue) {
          nameItem.value = "";
        }
      }
      for (const position of positions) {
        const positionProperty = `${prop1}-${position}`;
        const positionItem = getPropertyItem(positionProperty, properties);
        const longhandProperty = `${prop1}-${position}-${prop2}`;
        const longhandItem = getPropertyItem(longhandProperty, properties);
        if (propertyValue) {
          positionItem.value = replaceBorderShorthandValue(propertyValue, positionItem.value, {
            globalObject
          });
        } else {
          positionItem.value = "";
        }
        longhandItem.value = propertyValue;
        longhandItem.priority = priority;
        borderItems.set(positionProperty, positionItem);
        borderItems.set(longhandProperty, longhandItem);
      }
      borderItems.set(nameProperty, nameItem);
      borderItems.set(borderImageProperty, imageItem);
      borderItems.set(lineProperty, lineItem);
      // border shorthand
    } else {
      const nameItem = getPropertyItem(nameProperty, properties);
      const imageItem = getPropertyItem(borderImageProperty, properties);
      const propertyValue = hasVarFunc(value) ? "" : value;
      imageItem.value = propertyValue ? "none" : "";
      for (const line of lines) {
        const lineProperty = `${prop1}-${line}`;
        const lineItem = getPropertyItem(lineProperty, properties);
        lineItem.value = propertyValue;
        lineItem.priority = priority;
        borderItems.set(lineProperty, lineItem);
      }
      for (const position of positions) {
        const positionProperty = `${prop1}-${position}`;
        const positionItem = getPropertyItem(positionProperty, properties);
        positionItem.value = propertyValue;
        positionItem.priority = priority;
        borderItems.set(positionProperty, positionItem);
        for (const line of lines) {
          const longhandProperty = `${positionProperty}-${line}`;
          const longhandItem = getPropertyItem(longhandProperty, properties);
          longhandItem.value = propertyValue;
          longhandItem.priority = priority;
          borderItems.set(longhandProperty, longhandItem);
        }
      }
      borderItems.set(property, nameItem);
      borderItems.set(borderImageProperty, imageItem);
    }
    // Values of border-width, border-style, border-color
  } else if (Array.isArray(value)) {
    if (!value.length || !lines.includes(prop2)) {
      return;
    }
    const nameItem = getPropertyItem(nameProperty, properties);
    const imageItem = getPropertyItem(borderImageProperty, properties);
    const lineProperty = `${prop1}-${prop2}`;
    const lineItem = getPropertyItem(lineProperty, properties);
    if (value.length === 1) {
      const [propertyValue] = value;
      if (nameItem.value && propertyValue) {
        nameItem.value = replaceBorderShorthandValue(propertyValue, nameItem.value, {
          globalObject
        });
      }
    } else {
      nameItem.value = "";
    }
    lineItem.value = value.join(" ");
    lineItem.priority = priority;
    const positionValues = {};
    switch (value.length) {
      case 1: {
        const [val1] = value;
        positionValues.top = val1;
        positionValues.right = val1;
        positionValues.bottom = val1;
        positionValues.left = val1;
        break;
      }
      case 2: {
        const [val1, val2] = value;
        positionValues.top = val1;
        positionValues.right = val2;
        positionValues.bottom = val1;
        positionValues.left = val2;
        break;
      }
      case 3: {
        const [val1, val2, val3] = value;
        positionValues.top = val1;
        positionValues.right = val2;
        positionValues.bottom = val3;
        positionValues.left = val2;
        break;
      }
      case 4: {
        const [val1, val2, val3, val4] = value;
        positionValues.top = val1;
        positionValues.right = val2;
        positionValues.bottom = val3;
        positionValues.left = val4;
        break;
      }
      default: {
        return;
      }
    }
    for (const position of positions) {
      const positionProperty = `${prop1}-${position}`;
      const positionItem = getPropertyItem(positionProperty, properties);
      if (positionItem.value && positionValues[position]) {
        positionItem.value = replaceBorderShorthandValue(
          positionValues[position],
          positionItem.value,
          {
            globalObject
          }
        );
      }
      const longhandProperty = `${positionProperty}-${prop2}`;
      const longhandItem = getPropertyItem(longhandProperty, properties);
      longhandItem.value = positionValues[position];
      longhandItem.priority = priority;
      borderItems.set(positionProperty, positionItem);
      borderItems.set(longhandProperty, longhandItem);
    }
    borderItems.set(nameProperty, nameItem);
    borderItems.set(borderImageProperty, imageItem);
    borderItems.set(lineProperty, lineItem);
    // Values of border, border-top, border-right, border-bottom, border-top.
  } else if (value && typeof value === "object") {
    // position shorthands
    if (prop2) {
      if (!positions.includes(prop2)) {
        return;
      }
      const nameItem = getPropertyItem(nameProperty, properties);
      const imageItem = getPropertyItem(borderImageProperty, properties);
      const lineWidthProperty = `${prop1}-width`;
      const lineWidthItem = getPropertyItem(lineWidthProperty, properties);
      const lineStyleProperty = `${prop1}-style`;
      const lineStyleItem = getPropertyItem(lineStyleProperty, properties);
      const lineColorProperty = `${prop1}-color`;
      const lineColorItem = getPropertyItem(lineColorProperty, properties);
      const positionProperty = `${prop1}-${prop2}`;
      const positionItem = getPropertyItem(positionProperty, properties);
      if (nameItem.value) {
        for (const positionValue of Object.values(value)) {
          if (
            !matchesBorderShorthandValue(property, positionValue, nameItem.value, {
              globalObject
            })
          ) {
            nameItem.value = "";
            break;
          }
        }
      }
      positionItem.value = Object.values(value).join(" ");
      positionItem.priority = priority;
      for (const line of lines) {
        const longhandProperty = `${prop1}-${prop2}-${line}`;
        const longhandItem = getPropertyItem(longhandProperty, properties);
        if (Object.hasOwn(value, longhandProperty)) {
          const itemValue = value[longhandProperty];
          if (line === "width") {
            if (lineWidthItem.value) {
              lineWidthItem.value = replacePositionValue(
                itemValue,
                splitValue(lineWidthItem.value),
                prop2
              );
            }
          } else if (line === "style") {
            if (lineStyleItem.value) {
              lineStyleItem.value = replacePositionValue(
                itemValue,
                splitValue(lineStyleItem.value),
                prop2
              );
            }
          } else if (line === "color") {
            if (lineColorItem.value) {
              lineColorItem.value = replacePositionValue(
                itemValue,
                splitValue(lineColorItem.value),
                prop2
              );
            }
          }
          longhandItem.value = itemValue;
          longhandItem.priority = priority;
        } else {
          const itemValue = border.initialValues.get(`${prop1}-${line}`);
          if (line === "width") {
            if (lineWidthItem.value) {
              lineWidthItem.value = replacePositionValue(
                itemValue,
                splitValue(lineWidthItem.value),
                prop2
              );
            }
          } else if (line === "style") {
            if (lineStyleItem.value) {
              lineStyleItem.value = replacePositionValue(
                itemValue,
                splitValue(lineStyleItem.value),
                prop2
              );
            }
          } else if (line === "color") {
            if (lineColorItem.value) {
              lineColorItem.value = replacePositionValue(
                itemValue,
                splitValue(lineColorItem.value),
                prop2
              );
            }
          }
          longhandItem.value = itemValue;
          longhandItem.priority = priority;
        }
        borderItems.set(longhandProperty, longhandItem);
      }
      borderItems.set(nameProperty, nameItem);
      borderItems.set(borderImageProperty, imageItem);
      borderItems.set(lineWidthProperty, lineWidthItem);
      borderItems.set(lineStyleProperty, lineStyleItem);
      borderItems.set(lineColorProperty, lineColorItem);
      borderItems.set(positionProperty, positionItem);
      // border shorthand
    } else {
      const nameItem = getPropertyItem(prop1, properties);
      const imageItem = getPropertyItem(borderImageProperty, properties);
      const lineWidthProperty = `${prop1}-width`;
      const lineWidthItem = getPropertyItem(lineWidthProperty, properties);
      const lineStyleProperty = `${prop1}-style`;
      const lineStyleItem = getPropertyItem(lineStyleProperty, properties);
      const lineColorProperty = `${prop1}-color`;
      const lineColorItem = getPropertyItem(lineColorProperty, properties);
      const propertyValue = Object.values(value).join(" ");
      nameItem.value = propertyValue;
      nameItem.priority = priority;
      imageItem.value = propertyValue ? "none" : "";
      if (Object.hasOwn(value, lineWidthProperty)) {
        lineWidthItem.value = value[lineWidthProperty];
      } else {
        lineWidthItem.value = border.initialValues.get(lineWidthProperty);
      }
      lineWidthItem.priority = priority;
      if (Object.hasOwn(value, lineStyleProperty)) {
        lineStyleItem.value = value[lineStyleProperty];
      } else {
        lineStyleItem.value = border.initialValues.get(lineStyleProperty);
      }
      lineStyleItem.priority = priority;
      if (Object.hasOwn(value, lineColorProperty)) {
        lineColorItem.value = value[lineColorProperty];
      } else {
        lineColorItem.value = border.initialValues.get(lineColorProperty);
      }
      lineColorItem.priority = priority;
      for (const position of positions) {
        const positionProperty = `${prop1}-${position}`;
        const positionItem = getPropertyItem(positionProperty, properties);
        positionItem.value = propertyValue;
        positionItem.priority = priority;
        for (const line of lines) {
          const longhandProperty = `${positionProperty}-${line}`;
          const longhandItem = getPropertyItem(longhandProperty, properties);
          const lineProperty = `${prop1}-${line}`;
          if (Object.hasOwn(value, lineProperty)) {
            longhandItem.value = value[lineProperty];
          } else {
            longhandItem.value = border.initialValues.get(lineProperty);
          }
          longhandItem.priority = priority;
          borderItems.set(longhandProperty, longhandItem);
        }
        borderItems.set(positionProperty, positionItem);
      }
      borderItems.set(property, nameItem);
      borderItems.set(borderImageProperty, imageItem);
      borderItems.set(lineWidthProperty, lineWidthItem);
      borderItems.set(lineStyleProperty, lineStyleItem);
      borderItems.set(lineColorProperty, lineColorItem);
    }
  } else {
    return;
  }
  if (!borderItems.has(name)) {
    return;
  }
  const borderProperties = new Map([[name, borderItems.get(name)]]);
  for (const line of lines) {
    const lineProperty = `${name}-${line}`;
    const lineItem = borderItems.get(lineProperty) ??
      properties.get(lineProperty) ?? {
        property: lineProperty,
        value: "",
        priority: ""
      };
    borderProperties.set(lineProperty, lineItem);
  }
  for (const position of positions) {
    const positionProperty = `${name}-${position}`;
    const positionItem = borderItems.get(positionProperty) ??
      properties.get(positionProperty) ?? {
        property: positionProperty,
        value: "",
        priority: ""
      };
    borderProperties.set(positionProperty, positionItem);
    for (const line of lines) {
      const longhandProperty = `${name}-${position}-${line}`;
      const longhandItem = borderItems.get(longhandProperty) ??
        properties.get(longhandProperty) ?? {
          property: longhandProperty,
          value: "",
          priority: ""
        };
      borderProperties.set(longhandProperty, longhandItem);
    }
  }
  const borderImageItem = borderItems.get(borderImageProperty) ?? {
    property: borderImageProperty,
    value: "",
    priority: ""
  };
  borderProperties.set(borderImageProperty, borderImageItem);
  return borderProperties;
};

const generateBorderLineShorthand = (items, property, prior) => {
  const values = [];
  for (const [, item] of items) {
    const { value: itemValue } = item;
    values.push(itemValue);
  }
  const value = exports.getPositionValue(values);
  const priority = prior ? prior : "";
  return [property, { property, value, priority }];
};

const generateBorderPositionShorthand = (items, property, prior) => {
  const values = [];
  for (const [, item] of items) {
    const { value: itemValue } = item;
    values.push(itemValue);
  }
  const value = values.join(" ");
  const priority = prior ? prior : "";
  return [property, { property, value, priority }];
};

const generateBorderNameShorthand = (items, property, prior) => {
  const values = new Set(items);
  if (values.size === 1) {
    const value = values.keys().next().value;
    const priority = prior ? prior : "";
    return [property, { property, value, priority }];
  }
};

const prepareBorderShorthands = (properties) => {
  const lineWidthItems = new Map();
  const lineWidthPriorItems = new Map();
  const lineStyleItems = new Map();
  const lineStylePriorItems = new Map();
  const lineColorItems = new Map();
  const lineColorPriorItems = new Map();
  const positionTopItems = new Map();
  const positionTopPriorItems = new Map();
  const positionRightItems = new Map();
  const positionRightPriorItems = new Map();
  const positionBottomItems = new Map();
  const positionBottomPriorItems = new Map();
  const positionLeftItems = new Map();
  const positionLeftPriorItems = new Map();
  for (const [property, { priority, value }] of properties) {
    const [, positionPart, linePart] = property.split("-");
    switch (linePart) {
      case "width": {
        if (priority) {
          lineWidthPriorItems.set(property, { property, value, priority });
        } else {
          lineWidthItems.set(property, { property, value, priority });
        }
        break;
      }
      case "style": {
        if (priority) {
          lineStylePriorItems.set(property, { property, value, priority });
        } else {
          lineStyleItems.set(property, { property, value, priority });
        }
        break;
      }
      case "color": {
        if (priority) {
          lineColorPriorItems.set(property, { property, value, priority });
        } else {
          lineColorItems.set(property, { property, value, priority });
        }
        break;
      }
      default:
    }
    switch (positionPart) {
      case "top": {
        if (priority) {
          positionTopPriorItems.set(property, { property, value, priority });
        } else {
          positionTopItems.set(property, { property, value, priority });
        }
        break;
      }
      case "right": {
        if (priority) {
          positionRightPriorItems.set(property, { property, value, priority });
        } else {
          positionRightItems.set(property, { property, value, priority });
        }
        break;
      }
      case "bottom": {
        if (priority) {
          positionBottomPriorItems.set(property, { property, value, priority });
        } else {
          positionBottomItems.set(property, { property, value, priority });
        }
        break;
      }
      case "left": {
        if (priority) {
          positionLeftPriorItems.set(property, { property, value, priority });
        } else {
          positionLeftItems.set(property, { property, value, priority });
        }
        break;
      }
      default:
    }
  }
  if (lineWidthItems.size === 4) {
    const [property, item] = generateBorderLineShorthand(lineWidthItems, "border-width") ?? [];
    if (property && item) {
      properties.set(property, item);
    }
  } else if (lineWidthPriorItems.size === 4) {
    const [property, item] =
      generateBorderLineShorthand(lineWidthPriorItems, "border-width", "important") ?? [];
    if (property && item) {
      properties.set(property, item);
    }
  }
  if (lineStyleItems.size === 4) {
    const [property, item] = generateBorderLineShorthand(lineStyleItems, "border-style") ?? [];
    if (property && item) {
      properties.set(property, item);
    }
  } else if (lineStylePriorItems.size === 4) {
    const [property, item] =
      generateBorderLineShorthand(lineStylePriorItems, "border-style", "important") ?? [];
    if (property && item) {
      properties.set(property, item);
    }
  }
  if (lineColorItems.size === 4) {
    const [property, item] = generateBorderLineShorthand(lineColorItems, "border-color") ?? [];
    if (property && item) {
      properties.set(property, item);
    }
  } else if (lineColorPriorItems.size === 4) {
    const [property, item] =
      generateBorderLineShorthand(lineColorPriorItems, "border-color", "important") ?? [];
    if (property && item) {
      properties.set(property, item);
    }
  }
  const nameItems = [];
  const namePriorItems = [];
  if (positionTopItems.size === 3) {
    const [property, item] = generateBorderPositionShorthand(positionTopItems, "border-top") ?? [];
    if (property && item) {
      properties.set(property, item);
      if (properties.has(borderImageProperty)) {
        const { value: imageValue } = properties.get(borderImageProperty);
        if (imageValue === "none") {
          const { value: itemValue } = item;
          nameItems.push(itemValue);
        }
      }
    }
  } else if (positionTopPriorItems.size === 3) {
    const [property, item] =
      generateBorderPositionShorthand(positionTopPriorItems, "border-top", "important") ?? [];
    if (property && item) {
      properties.set(property, item);
      if (properties.has(borderImageProperty)) {
        const { value: imageValue } = properties.get(borderImageProperty);
        if (imageValue === "none") {
          const { value: itemValue } = item;
          namePriorItems.push(itemValue);
        }
      }
    }
  }
  if (positionRightItems.size === 3) {
    const [property, item] =
      generateBorderPositionShorthand(positionRightItems, "border-right") ?? [];
    if (property && item) {
      properties.set(property, item);
      if (properties.has(borderImageProperty)) {
        const { value: imageValue } = properties.get(borderImageProperty);
        if (imageValue === "none") {
          const { value: itemValue } = item;
          nameItems.push(itemValue);
        }
      }
    }
  } else if (positionRightPriorItems.size === 3) {
    const [property, item] =
      generateBorderPositionShorthand(positionRightPriorItems, "border-right", "important") ?? [];
    if (property && item) {
      properties.set(property, item);
      if (properties.has(borderImageProperty)) {
        const { value: imageValue } = properties.get(borderImageProperty);
        if (imageValue === "none") {
          const { value: itemValue } = item;
          nameItems.push(itemValue);
        }
      }
    }
  }
  if (positionBottomItems.size === 3) {
    const [property, item] =
      generateBorderPositionShorthand(positionBottomItems, "border-bottom") ?? [];
    if (property && item) {
      properties.set(property, item);
      if (properties.has(borderImageProperty)) {
        const { value: imageValue } = properties.get(borderImageProperty);
        if (imageValue === "none") {
          const { value: itemValue } = item;
          nameItems.push(itemValue);
        }
      }
    }
  } else if (positionBottomPriorItems.size === 3) {
    const [property, item] =
      generateBorderPositionShorthand(positionBottomPriorItems, "border-bottom", "important") ?? [];
    if (property && item) {
      properties.set(property, item);
      if (properties.has(borderImageProperty)) {
        const { value: imageValue } = properties.get(borderImageProperty);
        if (imageValue === "none") {
          const { value: itemValue } = item;
          nameItems.push(itemValue);
        }
      }
    }
  }
  if (positionLeftItems.size === 3) {
    const [property, item] =
      generateBorderPositionShorthand(positionLeftItems, "border-left") ?? [];
    if (property && item) {
      properties.set(property, item);
      if (properties.has(borderImageProperty)) {
        const { value: imageValue } = properties.get(borderImageProperty);
        if (imageValue === "none") {
          const { value: itemValue } = item;
          nameItems.push(itemValue);
        }
      }
    }
  } else if (positionLeftPriorItems.size === 3) {
    const [property, item] =
      generateBorderPositionShorthand(positionLeftPriorItems, "border-left", "important") ?? [];
    if (property && item) {
      properties.set(property, item);
      if (properties.has(borderImageProperty)) {
        const { value: imageValue } = properties.get(borderImageProperty);
        if (imageValue === "none") {
          const { value: itemValue } = item;
          nameItems.push(itemValue);
        }
      }
    }
  }
  const mixedPriorities = nameItems.length && namePriorItems.length;
  const imageItem = {
    property: borderImageProperty,
    value: "none",
    priority: ""
  };
  if (nameItems.length === 4) {
    const [property, item] = generateBorderNameShorthand(nameItems, "border") ?? [];
    if (property && item) {
      properties.set(property, item);
      properties.delete(borderImageProperty);
      properties.set(borderImageProperty, imageItem);
    }
  } else if (namePriorItems.length === 4) {
    const [property, item] =
      generateBorderNameShorthand(namePriorItems, "border", "important") ?? [];
    if (property && item) {
      properties.set(property, item);
      properties.delete(borderImageProperty);
      properties.set(borderImageProperty, imageItem);
    }
  } else if (properties.has(borderImageProperty)) {
    const { value: imageValue } = properties.get(borderImageProperty);
    if (imageValue === "none") {
      if (mixedPriorities) {
        properties.delete(borderImageProperty);
        properties.set(borderImageProperty, imageItem);
      } else {
        properties.delete(borderImageProperty);
      }
    }
  }
  if (mixedPriorities) {
    const items = [];
    const priorItems = [];
    for (const item of properties) {
      const [, { priority }] = item;
      if (priority) {
        priorItems.push(item);
      } else {
        items.push(item);
      }
    }
    const firstPropertyKey = properties.keys().next().value;
    const { priority: firstPropertyPriority } = properties.get(firstPropertyKey);
    if (firstPropertyPriority) {
      return new Map([...priorItems, ...items]);
    }
    return new Map([...items, ...priorItems]);
  }
  if (properties.has(borderImageProperty)) {
    properties.delete(borderImageProperty);
    properties.set(borderImageProperty, imageItem);
  }
  return properties;
};

exports.prepareProperties = (properties, opt = {}) => {
  const { globalObject } = opt;
  const { positions } = borderElements;
  const parsedProperties = new Map();
  const prepareShorthands = new Map();
  const borderProperties = new Map();
  for (const [property, item] of properties) {
    const { value, priority } = item;
    const { logicalPropertyGroup: shorthandProperty } = implementedProperties.get(property) ?? {};
    if (exports.borderProperties.has(property)) {
      borderProperties.set(property, { property, value, priority });
    } else if (exports.shorthandProperties.has(shorthandProperty)) {
      if (!prepareShorthands.has(shorthandProperty)) {
        prepareShorthands.set(shorthandProperty, new Map());
      }
      const longhandItems = prepareShorthands.get(shorthandProperty);
      if (longhandItems.size) {
        const firstPropertyKey = longhandItems.keys().next().value;
        const { priority: firstPropertyPriority } = longhandItems.get(firstPropertyKey);
        if (priority === firstPropertyPriority) {
          longhandItems.set(property, { property, value, priority });
          prepareShorthands.set(shorthandProperty, longhandItems);
        } else {
          parsedProperties.delete(shorthandProperty);
        }
      } else {
        longhandItems.set(property, { property, value, priority });
        prepareShorthands.set(shorthandProperty, longhandItems);
      }
      parsedProperties.set(property, item);
    } else if (exports.shorthandProperties.has(property)) {
      const shorthandItem = exports.shorthandProperties.get(property);
      const parsedValues = shorthandItem.parse(value, {
        globalObject
      });
      let omitShorthandProperty = false;
      if (Array.isArray(parsedValues)) {
        const [parsedValue] = parsedValues;
        if (typeof parsedValue === "string") {
          for (const [longhandProperty, longhandItem] of shorthandItem.shorthandFor) {
            if (!priority && properties.has(longhandProperty)) {
              const { priority: longhandPriority } = properties.get(longhandProperty);
              if (longhandPriority) {
                omitShorthandProperty = true;
                continue;
              }
            }
            const { position } = longhandItem;
            const longhandValue = exports.getPositionValue([parsedValue], position);
            parsedProperties.set(longhandProperty, {
              property: longhandProperty,
              value: longhandValue,
              priority
            });
          }
        } else if (parsedValue) {
          for (const longhandProperty of Object.keys(parsedValue)) {
            const longhandValue = parsedValue[longhandProperty];
            parsedProperties.set(longhandProperty, {
              property: longhandProperty,
              value: longhandValue,
              priority
            });
          }
        }
      } else if (parsedValues) {
        for (const longhandProperty of Object.keys(parsedValues)) {
          const longhandValue = parsedValues[longhandProperty];
          parsedProperties.set(longhandProperty, {
            property: longhandProperty,
            value: longhandValue,
            priority
          });
        }
      }
      if (!omitShorthandProperty) {
        parsedProperties.set(property, { property, value, priority });
      }
    } else {
      parsedProperties.set(property, { property, value, priority });
    }
  }
  if (prepareShorthands.size) {
    for (const [property, item] of prepareShorthands) {
      const shorthandItem = exports.shorthandProperties.get(property);
      if (item.size === shorthandItem.shorthandFor.size) {
        if (shorthandItem.position) {
          const positionValues = [];
          let priority = "";
          for (const { value: longhandValue, priority: longhandPriority } of item.values()) {
            positionValues.push(longhandValue);
            if (longhandPriority) {
              priority = longhandPriority;
            }
          }
          const value = exports.getPositionValue(positionValues, shorthandItem.position);
          parsedProperties.set(property, {
            property,
            value,
            priority
          });
        }
      }
    }
  }
  if (borderProperties.size) {
    const longhandProperties = new Map();
    for (const [property, item] of borderProperties) {
      if (exports.shorthandProperties.has(property)) {
        const { value, priority } = item;
        if (property === "border") {
          const lineItems = border.parse(value, {
            globalObject
          });
          for (const [key, initialValue] of border.initialValues) {
            if (!Object.hasOwn(lineItems, key)) {
              lineItems[key] = initialValue;
            }
          }
          for (const lineProperty of Object.keys(lineItems)) {
            const [namePart, linePart] = lineProperty.split("-");
            const lineValue = lineItems[lineProperty];
            for (const position of positions) {
              const longhandProperty = `${namePart}-${position}-${linePart}`;
              const longhandItem = {
                property: longhandProperty,
                value: lineValue,
                priority
              };
              if (longhandProperties.has(longhandProperty)) {
                const { priority: longhandPriority } = longhandProperties.get(longhandProperty);
                if (!longhandPriority) {
                  longhandProperties.delete(longhandProperty);
                  longhandProperties.set(longhandProperty, longhandItem);
                }
              } else {
                longhandProperties.set(longhandProperty, longhandItem);
              }
            }
          }
          if (value) {
            longhandProperties.set(borderImageProperty, {
              property: borderImageProperty,
              value: "none",
              priority
            });
          }
        } else {
          const shorthandItem = exports.shorthandProperties.get(property);
          const parsedItem = shorthandItem.parse(value, {
            globalObject
          });
          if (Array.isArray(parsedItem)) {
            const [namePart, linePart] = property.split("-");
            for (const position of positions) {
              const longhandProperty = `${namePart}-${position}-${linePart}`;
              const longhandValue = exports.getPositionValue(parsedItem, position);
              const longhandItem = {
                property: longhandProperty,
                value: longhandValue,
                priority
              };
              if (longhandProperties.has(longhandProperty)) {
                const { priority: longhandPriority } = longhandProperties.get(longhandProperty);
                if (!longhandPriority) {
                  longhandProperties.delete(longhandProperty);
                  longhandProperties.set(longhandProperty, longhandItem);
                }
              } else {
                longhandProperties.set(longhandProperty, longhandItem);
              }
            }
          } else if (parsedItem) {
            for (const [key, initialValue] of shorthandItem.initialValues) {
              if (!Object.hasOwn(parsedItem, key)) {
                parsedItem[key] = initialValue;
              }
            }
            for (const longhandProperty of Object.keys(parsedItem)) {
              const longhandValue = parsedItem[longhandProperty];
              const longhandItem = {
                property: longhandProperty,
                value: longhandValue,
                priority
              };
              if (longhandProperties.has(longhandProperty)) {
                const { priority: longhandPriority } = longhandProperties.get(longhandProperty);
                if (!longhandPriority) {
                  longhandProperties.delete(longhandProperty);
                  longhandProperties.set(longhandProperty, longhandItem);
                }
              } else {
                longhandProperties.set(longhandProperty, longhandItem);
              }
            }
          }
        }
      } else if (longhandProperties.has(property)) {
        const { priority } = longhandProperties.get(property);
        if (!priority) {
          longhandProperties.delete(property);
          longhandProperties.set(property, item);
        }
      } else {
        longhandProperties.set(property, item);
      }
    }
    const normalizedProperties = prepareBorderShorthands(longhandProperties);
    for (const [property, item] of normalizedProperties) {
      parsedProperties.set(property, item);
    }
  }
  return parsedProperties;
};

exports.normalizeBorderProperties = (properties) => {
  const { lines, name, positions } = borderElements;
  if (properties.has(name)) {
    for (const line of lines) {
      properties.delete(`${name}-${line}`);
    }
    for (const position of positions) {
      properties.delete(`${name}-${position}`);
      for (const line of lines) {
        properties.delete(`${name}-${position}-${line}`);
      }
    }
    properties.delete(`${name}-image`);
  }
  for (const line of lines) {
    const lineProperty = `${name}-${line}`;
    if (properties.has(lineProperty)) {
      for (const position of positions) {
        const positionProperty = `${name}-${position}`;
        const longhandProperty = `${name}-${position}-${line}`;
        properties.delete(positionProperty);
        properties.delete(longhandProperty);
      }
    }
  }
  for (const position of positions) {
    const positionProperty = `${name}-${position}`;
    if (properties.has(positionProperty)) {
      const longhandProperties = [];
      for (const line of lines) {
        const longhandProperty = `${name}-${position}-${line}`;
        longhandProperties.push(longhandProperty);
      }
      if (longhandProperties.length === 3) {
        for (const longhandProperty of longhandProperties) {
          properties.delete(longhandProperty);
        }
      } else {
        properties.delete(positionProperty);
      }
    }
  }
  return properties;
};
