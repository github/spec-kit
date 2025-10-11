import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  UpdateConfigurationSetTrackingOptionsRequest,
  UpdateConfigurationSetTrackingOptionsResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface UpdateConfigurationSetTrackingOptionsCommandInput
  extends UpdateConfigurationSetTrackingOptionsRequest {}
export interface UpdateConfigurationSetTrackingOptionsCommandOutput
  extends UpdateConfigurationSetTrackingOptionsResponse,
    __MetadataBearer {}
declare const UpdateConfigurationSetTrackingOptionsCommand_base: {
  new (
    input: UpdateConfigurationSetTrackingOptionsCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateConfigurationSetTrackingOptionsCommandInput,
    UpdateConfigurationSetTrackingOptionsCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: UpdateConfigurationSetTrackingOptionsCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateConfigurationSetTrackingOptionsCommandInput,
    UpdateConfigurationSetTrackingOptionsCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class UpdateConfigurationSetTrackingOptionsCommand extends UpdateConfigurationSetTrackingOptionsCommand_base {
  protected static __types: {
    api: {
      input: UpdateConfigurationSetTrackingOptionsRequest;
      output: {};
    };
    sdk: {
      input: UpdateConfigurationSetTrackingOptionsCommandInput;
      output: UpdateConfigurationSetTrackingOptionsCommandOutput;
    };
  };
}
