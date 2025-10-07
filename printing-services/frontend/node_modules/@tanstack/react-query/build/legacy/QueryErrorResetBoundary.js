"use client";

// src/QueryErrorResetBoundary.tsx
import * as React from "react";
import { jsx } from "react/jsx-runtime";
function createValue() {
  let isReset = false;
  return {
    clearReset: () => {
      isReset = false;
    },
    reset: () => {
      isReset = true;
    },
    isReset: () => {
      return isReset;
    }
  };
}
var QueryErrorResetBoundaryContext = React.createContext(createValue());
var useQueryErrorResetBoundary = () => React.useContext(QueryErrorResetBoundaryContext);
var QueryErrorResetBoundary = ({
  children
}) => {
  const [value] = React.useState(() => createValue());
  return /* @__PURE__ */ jsx(QueryErrorResetBoundaryContext.Provider, { value, children: typeof children === "function" ? children(value) : children });
};
export {
  QueryErrorResetBoundary,
  useQueryErrorResetBoundary
};
//# sourceMappingURL=QueryErrorResetBoundary.js.map