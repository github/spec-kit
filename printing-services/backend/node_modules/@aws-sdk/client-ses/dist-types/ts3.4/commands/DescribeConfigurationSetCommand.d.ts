import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  DescribeConfigurationSetRequest,
  DescribeConfigurationSetResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface DescribeConfigurationSetCommandInput
  extends DescribeConfigurationSetRequest {}
export interface DescribeConfigurationSetCommandOutput
  extends DescribeConfigurationSetResponse,
    __MetadataBearer {}
declare const DescribeConfigurationSetCommand_base: {
  new (
    input: DescribeConfigurationSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DescribeConfigurationSetCommandInput,
    DescribeConfigurationSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: DescribeConfigurationSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DescribeConfigurationSetCommandInput,
    DescribeConfigurationSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class DescribeConfigurationSetCommand extends DescribeConfigurationSetCommand_base {
  protected static __types: {
    api: {
      input: DescribeConfigurationSetRequest;
      output: DescribeConfigurationSetResponse;
    };
    sdk: {
      input: DescribeConfigurationSetCommandInput;
      output: DescribeConfigurationSetCommandOutput;
    };
  };
}
