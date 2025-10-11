import type { FutureConfig as RouterFutureConfig } from "@remix-run/router";
import type { FutureConfig as RenderFutureConfig } from "./components";
export declare function warnOnce(key: string, message: string): void;
export declare function logV6DeprecationWarnings(renderFuture: Partial<RenderFutureConfig> | undefined, routerFuture?: Omit<RouterFutureConfig, "v7_prependBasename">): void;
