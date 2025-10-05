import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  DescribeReceiptRuleRequest,
  DescribeReceiptRuleResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface DescribeReceiptRuleCommandInput
  extends DescribeReceiptRuleRequest {}
export interface DescribeReceiptRuleCommandOutput
  extends DescribeReceiptRuleResponse,
    __MetadataBearer {}
declare const DescribeReceiptRuleCommand_base: {
  new (
    input: DescribeReceiptRuleCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DescribeReceiptRuleCommandInput,
    DescribeReceiptRuleCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: DescribeReceiptRuleCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DescribeReceiptRuleCommandInput,
    DescribeReceiptRuleCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class DescribeReceiptRuleCommand extends DescribeReceiptRuleCommand_base {
  protected static __types: {
    api: {
      input: DescribeReceiptRuleRequest;
      output: DescribeReceiptRuleResponse;
    };
    sdk: {
      input: DescribeReceiptRuleCommandInput;
      output: DescribeReceiptRuleCommandOutput;
    };
  };
}
