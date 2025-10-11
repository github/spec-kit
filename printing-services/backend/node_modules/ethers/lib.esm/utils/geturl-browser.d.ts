import type { FetchGetUrlFunc, FetchRequest, FetchCancelSignal, GetUrlResponse } from "./fetch.js";
export declare function createGetUrl(options?: Record<string, any>): FetchGetUrlFunc;
export declare function getUrl(req: FetchRequest, _signal?: FetchCancelSignal): Promise<GetUrlResponse>;
//# sourceMappingURL=geturl-browser.d.ts.map