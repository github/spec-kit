"use client";

// src/IsRestoringProvider.ts
import * as React from "react";
var IsRestoringContext = React.createContext(false);
var useIsRestoring = () => React.useContext(IsRestoringContext);
var IsRestoringProvider = IsRestoringContext.Provider;
export {
  IsRestoringProvider,
  useIsRestoring
};
//# sourceMappingURL=IsRestoringProvider.js.map