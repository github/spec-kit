import type { FetchGetUrlFunc, FetchRequest, FetchCancelSignal, GetUrlResponse } from "./fetch.js";
/**
 *  @_ignore:
 */
export declare function createGetUrl(options?: Record<string, any>): FetchGetUrlFunc;
/**
 *  @_ignore:
 */
export declare function getUrl(req: FetchRequest, signal?: FetchCancelSignal): Promise<GetUrlResponse>;
//# sourceMappingURL=geturl.d.ts.map