import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  ReorderReceiptRuleSetRequest,
  ReorderReceiptRuleSetResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface ReorderReceiptRuleSetCommandInput
  extends ReorderReceiptRuleSetRequest {}
export interface ReorderReceiptRuleSetCommandOutput
  extends ReorderReceiptRuleSetResponse,
    __MetadataBearer {}
declare const ReorderReceiptRuleSetCommand_base: {
  new (
    input: ReorderReceiptRuleSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    ReorderReceiptRuleSetCommandInput,
    ReorderReceiptRuleSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: ReorderReceiptRuleSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    ReorderReceiptRuleSetCommandInput,
    ReorderReceiptRuleSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class ReorderReceiptRuleSetCommand extends ReorderReceiptRuleSetCommand_base {
  protected static __types: {
    api: {
      input: ReorderReceiptRuleSetRequest;
      output: {};
    };
    sdk: {
      input: ReorderReceiptRuleSetCommandInput;
      output: ReorderReceiptRuleSetCommandOutput;
    };
  };
}
