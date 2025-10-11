export interface PaginationResult<R> extends Array<R> {
    next(): Promise<PaginationResult<R>>;
    totalResults: null | number;
    done: boolean;
}
//# sourceMappingURL=pagination.d.ts.map