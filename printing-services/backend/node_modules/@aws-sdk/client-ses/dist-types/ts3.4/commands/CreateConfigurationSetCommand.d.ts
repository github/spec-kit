import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  CreateConfigurationSetRequest,
  CreateConfigurationSetResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface CreateConfigurationSetCommandInput
  extends CreateConfigurationSetRequest {}
export interface CreateConfigurationSetCommandOutput
  extends CreateConfigurationSetResponse,
    __MetadataBearer {}
declare const CreateConfigurationSetCommand_base: {
  new (
    input: CreateConfigurationSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateConfigurationSetCommandInput,
    CreateConfigurationSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: CreateConfigurationSetCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    CreateConfigurationSetCommandInput,
    CreateConfigurationSetCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class CreateConfigurationSetCommand extends CreateConfigurationSetCommand_base {
  protected static __types: {
    api: {
      input: CreateConfigurationSetRequest;
      output: {};
    };
    sdk: {
      input: CreateConfigurationSetCommandInput;
      output: CreateConfigurationSetCommandOutput;
    };
  };
}
