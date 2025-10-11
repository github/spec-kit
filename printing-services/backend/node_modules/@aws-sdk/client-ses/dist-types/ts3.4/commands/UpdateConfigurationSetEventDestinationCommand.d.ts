import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  UpdateConfigurationSetEventDestinationRequest,
  UpdateConfigurationSetEventDestinationResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface UpdateConfigurationSetEventDestinationCommandInput
  extends UpdateConfigurationSetEventDestinationRequest {}
export interface UpdateConfigurationSetEventDestinationCommandOutput
  extends UpdateConfigurationSetEventDestinationResponse,
    __MetadataBearer {}
declare const UpdateConfigurationSetEventDestinationCommand_base: {
  new (
    input: UpdateConfigurationSetEventDestinationCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateConfigurationSetEventDestinationCommandInput,
    UpdateConfigurationSetEventDestinationCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: UpdateConfigurationSetEventDestinationCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateConfigurationSetEventDestinationCommandInput,
    UpdateConfigurationSetEventDestinationCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class UpdateConfigurationSetEventDestinationCommand extends UpdateConfigurationSetEventDestinationCommand_base {
  protected static __types: {
    api: {
      input: UpdateConfigurationSetEventDestinationRequest;
      output: {};
    };
    sdk: {
      input: UpdateConfigurationSetEventDestinationCommandInput;
      output: UpdateConfigurationSetEventDestinationCommandOutput;
    };
  };
}
