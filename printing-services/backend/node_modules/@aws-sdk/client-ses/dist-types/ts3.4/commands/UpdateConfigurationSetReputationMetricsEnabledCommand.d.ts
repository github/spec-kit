import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { UpdateConfigurationSetReputationMetricsEnabledRequest } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface UpdateConfigurationSetReputationMetricsEnabledCommandInput
  extends UpdateConfigurationSetReputationMetricsEnabledRequest {}
export interface UpdateConfigurationSetReputationMetricsEnabledCommandOutput
  extends __MetadataBearer {}
declare const UpdateConfigurationSetReputationMetricsEnabledCommand_base: {
  new (
    input: UpdateConfigurationSetReputationMetricsEnabledCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateConfigurationSetReputationMetricsEnabledCommandInput,
    UpdateConfigurationSetReputationMetricsEnabledCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: UpdateConfigurationSetReputationMetricsEnabledCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateConfigurationSetReputationMetricsEnabledCommandInput,
    UpdateConfigurationSetReputationMetricsEnabledCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class UpdateConfigurationSetReputationMetricsEnabledCommand extends UpdateConfigurationSetReputationMetricsEnabledCommand_base {
  protected static __types: {
    api: {
      input: UpdateConfigurationSetReputationMetricsEnabledRequest;
      output: {};
    };
    sdk: {
      input: UpdateConfigurationSetReputationMetricsEnabledCommandInput;
      output: UpdateConfigurationSetReputationMetricsEnabledCommandOutput;
    };
  };
}
