"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;
var _helperPluginUtils = require("@babel/helper-plugin-utils");
var _core = require("@babel/core");
const TRACE_ID = "__source";
const FILE_NAME_VAR = "_jsxFileName";
const createNodeFromNullish = (val, fn) => val == null ? _core.types.nullLiteral() : fn(val);
var _default = exports.default = (0, _helperPluginUtils.declare)(api => {
  api.assertVersion(7);
  function makeTrace(fileNameIdentifier, {
    line,
    column
  }) {
    const fileLineLiteral = createNodeFromNullish(line, _core.types.numericLiteral);
    const fileColumnLiteral = createNodeFromNullish(column, c => _core.types.numericLiteral(c + 1));
    return _core.template.expression.ast`{
      fileName: ${fileNameIdentifier},
      lineNumber: ${fileLineLiteral},
      columnNumber: ${fileColumnLiteral},
    }`;
  }
  const isSourceAttr = attr => _core.types.isJSXAttribute(attr) && attr.name.name === TRACE_ID;
  return {
    name: "transform-react-jsx-source",
    visitor: {
      JSXOpeningElement(path, state) {
        const {
          node
        } = path;
        if (!node.loc || path.node.attributes.some(isSourceAttr)) {
          return;
        }
        if (!state.fileNameIdentifier) {
          const fileNameId = path.scope.generateUidIdentifier(FILE_NAME_VAR);
          state.fileNameIdentifier = fileNameId;
          path.scope.getProgramParent().push({
            id: fileNameId,
            init: _core.types.stringLiteral(state.filename || "")
          });
        }
        node.attributes.push(_core.types.jsxAttribute(_core.types.jsxIdentifier(TRACE_ID), _core.types.jsxExpressionContainer(makeTrace(_core.types.cloneNode(state.fileNameIdentifier), node.loc.start))));
      }
    }
  };
});

//# sourceMappingURL=index.js.map
