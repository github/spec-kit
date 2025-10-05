import trimParser from "../valueParsers/trim";
import booleanParser from "../valueParsers/booleanParser";
import currencyParser from "../valueParsers/currency";
import numberParser from "../valueParsers/number";

const defaultOptions={
  nameFor:{
    text: "#text",
    comment: "",
    cdata: "",
  },
  // onTagClose: () => {},
  // onAttribute: () => {},
  piTag: false,
  declaration: false, //"?xml"
  tags: {
    valueParsers: [
      // "trim",
      // "boolean",
      // "number",
      // "currency",
      // "date",
    ]
  },
  attributes:{
    prefix: "@_",
    suffix: "",
    groupBy: "",
    
    valueParsers: [
      // "trim",
      // "boolean",
      // "number",
      // "currency",
      // "date",
    ]
  },
  dataType:{

  }
}

//TODO
const withJoin = ["trim","join", /*"entities",*/"number","boolean","currency"/*, "date"*/]
const withoutJoin = ["trim", /*"entities",*/"number","boolean","currency"/*, "date"*/]

export function buildOptions(options){
  //clone
  const finalOptions = { ... defaultOptions};

  //add config missed in cloning
  finalOptions.tags.valueParsers.push(...withJoin)
  if(!this.preserveOrder)
    finalOptions.tags.valueParsers.push(...withoutJoin);

  //add config missed in cloning
  finalOptions.attributes.valueParsers.push(...withJoin)

  //override configuration
  copyProperties(finalOptions,options);
  return finalOptions;
}

function copyProperties(target, source) {
  for (let key in source) {
    if (source.hasOwnProperty(key)) {
      if (typeof source[key] === 'object' && !Array.isArray(source[key])) {
        // Recursively copy nested properties
        if (typeof target[key] === 'undefined') {
          target[key] = {};
        }
        copyProperties(target[key], source[key]);
      } else {
        // Copy non-nested properties
        target[key] = source[key];
      }
    }
  }
}

export function registerCommonValueParsers(options){
  return {
    "trim": new trimParser(),
    // "join": this.entityParser.parse,
    "boolean": new booleanParser(),
    "number": new numberParser({
          hex: true,
          leadingZeros: true,
          eNotation: true
        }),
    "currency": new currencyParser(),
    // "date": this.entityParser.parse,
  }
}
