import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  CreateConfigurationSetEventDestinationRequest,
  CreateConfigurationSetEventDestinationResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface CreateConfigurationSetEventDestinationCommandInput
  extends CreateConfigurationSetEventDestinationRequest {}
export interface CreateConfigurationSetEventDestinationCommandOutput
  extends CreateConfigurationSetEventDestinationResponse,
    __MetadataBearer {}
declare const CreateConfigurationSetEventDestinationCommand_base: {
  new (
    input: CreateConfigurationSetEventDestinationCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateConfigurationSetEventDestinationCommandInput,
    CreateConfigurationSetEventDestinationCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: CreateConfigurationSetEventDestinationCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateConfigurationSetEventDestinationCommandInput,
    CreateConfigurationSetEventDestinationCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class CreateConfigurationSetEventDestinationCommand extends CreateConfigurationSetEventDestinationCommand_base {
  protected static __types: {
    api: {
      input: CreateConfigurationSetEventDestinationRequest;
      output: {};
    };
    sdk: {
      input: CreateConfigurationSetEventDestinationCommandInput;
      output: CreateConfigurationSetEventDestinationCommandOutput;
    };
  };
}
