import { Location, Request } from './base';
export type MatchedDataOptions = {
    /**
     * Whether the value returned by `matchedData()` should include data deemed optional.
     * @default false
     */
    includeOptionals: boolean;
    /**
     * An array of locations in the request to extract the data from.
     */
    locations: Location[];
    /**
     * Whether the value returned by `matchedData()` should include only values that have passed
     * validation.
     * @default true
     */
    onlyValidData: boolean;
};
/**
 * Extracts data validated or sanitized from the request, and builds an object with them.
 *
 * @param req the express request object
 * @param options
 * @returns an object of data that's been validated or sanitized in the passed request
 */
export declare function matchedData<T extends object = Record<string, any>>(req: Request, options?: Partial<MatchedDataOptions>): T;
