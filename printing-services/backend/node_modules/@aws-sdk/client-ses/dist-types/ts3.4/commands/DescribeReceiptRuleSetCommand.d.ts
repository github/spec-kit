import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  DescribeReceiptRuleSetRequest,
  DescribeReceiptRuleSetResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface DescribeReceiptRuleSetCommandInput
  extends DescribeReceiptRuleSetRequest {}
export interface DescribeReceiptRuleSetCommandOutput
  extends DescribeReceiptRuleSetResponse,
    __MetadataBearer {}
declare const DescribeReceiptRuleSetCommand_base: {
  new (
    input: DescribeReceiptRuleSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DescribeReceiptRuleSetCommandInput,
    DescribeReceiptRuleSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: DescribeReceiptRuleSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DescribeReceiptRuleSetCommandInput,
    DescribeReceiptRuleSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class DescribeReceiptRuleSetCommand extends DescribeReceiptRuleSetCommand_base {
  protected static __types: {
    api: {
      input: DescribeReceiptRuleSetRequest;
      output: DescribeReceiptRuleSetResponse;
    };
    sdk: {
      input: DescribeReceiptRuleSetCommandInput;
      output: DescribeReceiptRuleSetCommandOutput;
    };
  };
}
