import type { BlockParams, LogParams, TransactionReceiptParams, TransactionResponseParams } from "./formatting.js";
export type FormatFunc = (value: any) => any;
export declare function allowNull(format: FormatFunc, nullValue?: any): FormatFunc;
export declare function arrayOf(format: FormatFunc, allowNull?: boolean): FormatFunc;
export declare function object(format: Record<string, FormatFunc>, altNames?: Record<string, Array<string>>): FormatFunc;
export declare function formatBoolean(value: any): boolean;
export declare function formatData(value: string): string;
export declare function formatHash(value: any): string;
export declare function formatUint256(value: any): string;
export declare function formatLog(value: any): LogParams;
export declare function formatBlock(value: any): BlockParams;
export declare function formatReceiptLog(value: any): LogParams;
export declare function formatTransactionReceipt(value: any): TransactionReceiptParams;
export declare function formatTransactionResponse(value: any): TransactionResponseParams;
//# sourceMappingURL=format.d.ts.map