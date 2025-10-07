"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;
var _helperPluginUtils = require("@babel/helper-plugin-utils");
var _core = require("@babel/core");
const TRACE_ID = "__self";
function getThisFunctionParent(path) {
  let scope = path.scope;
  do {
    const {
      path
    } = scope;
    if (path.isFunctionParent() && !path.isArrowFunctionExpression()) {
      return path;
    }
  } while (scope = scope.parent);
  return null;
}
function isDerivedClass(classPath) {
  return classPath.node.superClass !== null;
}
function isThisAllowed(path) {
  const parentMethodOrFunction = getThisFunctionParent(path);
  if (parentMethodOrFunction === null) {
    return true;
  }
  if (!parentMethodOrFunction.isMethod()) {
    return true;
  }
  if (parentMethodOrFunction.node.kind !== "constructor") {
    return true;
  }
  return !isDerivedClass(parentMethodOrFunction.parentPath.parentPath);
}
var _default = exports.default = (0, _helperPluginUtils.declare)(api => {
  api.assertVersion(7);
  const visitor = {
    JSXOpeningElement(path) {
      if (!isThisAllowed(path)) {
        return;
      }
      const node = path.node;
      const id = _core.types.jsxIdentifier(TRACE_ID);
      const trace = _core.types.thisExpression();
      node.attributes.push(_core.types.jsxAttribute(id, _core.types.jsxExpressionContainer(trace)));
    }
  };
  return {
    name: "transform-react-jsx-self",
    visitor: {
      Program(path) {
        path.traverse(visitor);
      }
    }
  };
});

//# sourceMappingURL=index.js.map
