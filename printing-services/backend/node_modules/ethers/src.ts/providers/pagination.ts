export interface PaginationResult<R> extends Array<R> {
    next(): Promise<PaginationResult<R>>;

    // The total number of results available or null if unknown
    totalResults: null | number;

    done: boolean;
}
