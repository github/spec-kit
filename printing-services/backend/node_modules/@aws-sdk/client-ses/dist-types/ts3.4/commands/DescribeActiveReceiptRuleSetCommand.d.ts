import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  DescribeActiveReceiptRuleSetRequest,
  DescribeActiveReceiptRuleSetResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface DescribeActiveReceiptRuleSetCommandInput
  extends DescribeActiveReceiptRuleSetRequest {}
export interface DescribeActiveReceiptRuleSetCommandOutput
  extends DescribeActiveReceiptRuleSetResponse,
    __MetadataBearer {}
declare const DescribeActiveReceiptRuleSetCommand_base: {
  new (
    input: DescribeActiveReceiptRuleSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DescribeActiveReceiptRuleSetCommandInput,
    DescribeActiveReceiptRuleSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    ...[input]: [] | [DescribeActiveReceiptRuleSetCommandInput]
  ): import("@smithy/smithy-client").CommandImpl<
    DescribeActiveReceiptRuleSetCommandInput,
    DescribeActiveReceiptRuleSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class DescribeActiveReceiptRuleSetCommand extends DescribeActiveReceiptRuleSetCommand_base {
  protected static __types: {
    api: {
      input: {};
      output: DescribeActiveReceiptRuleSetResponse;
    };
    sdk: {
      input: DescribeActiveReceiptRuleSetCommandInput;
      output: DescribeActiveReceiptRuleSetCommandOutput;
    };
  };
}
