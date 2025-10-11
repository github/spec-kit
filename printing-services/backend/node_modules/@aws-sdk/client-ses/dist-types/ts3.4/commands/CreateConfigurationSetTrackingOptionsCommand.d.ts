import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  CreateConfigurationSetTrackingOptionsRequest,
  CreateConfigurationSetTrackingOptionsResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface CreateConfigurationSetTrackingOptionsCommandInput
  extends CreateConfigurationSetTrackingOptionsRequest {}
export interface CreateConfigurationSetTrackingOptionsCommandOutput
  extends CreateConfigurationSetTrackingOptionsResponse,
    __MetadataBearer {}
declare const CreateConfigurationSetTrackingOptionsCommand_base: {
  new (
    input: CreateConfigurationSetTrackingOptionsCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateConfigurationSetTrackingOptionsCommandInput,
    CreateConfigurationSetTrackingOptionsCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: CreateConfigurationSetTrackingOptionsCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateConfigurationSetTrackingOptionsCommandInput,
    CreateConfigurationSetTrackingOptionsCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class CreateConfigurationSetTrackingOptionsCommand extends CreateConfigurationSetTrackingOptionsCommand_base {
  protected static __types: {
    api: {
      input: CreateConfigurationSetTrackingOptionsRequest;
      output: {};
    };
    sdk: {
      input: CreateConfigurationSetTrackingOptionsCommandInput;
      output: CreateConfigurationSetTrackingOptionsCommandOutput;
    };
  };
}
