import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { UpdateConfigurationSetSendingEnabledRequest } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface UpdateConfigurationSetSendingEnabledCommandInput
  extends UpdateConfigurationSetSendingEnabledRequest {}
export interface UpdateConfigurationSetSendingEnabledCommandOutput
  extends __MetadataBearer {}
declare const UpdateConfigurationSetSendingEnabledCommand_base: {
  new (
    input: UpdateConfigurationSetSendingEnabledCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateConfigurationSetSendingEnabledCommandInput,
    UpdateConfigurationSetSendingEnabledCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: UpdateConfigurationSetSendingEnabledCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateConfigurationSetSendingEnabledCommandInput,
    UpdateConfigurationSetSendingEnabledCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class UpdateConfigurationSetSendingEnabledCommand extends UpdateConfigurationSetSendingEnabledCommand_base {
  protected static __types: {
    api: {
      input: UpdateConfigurationSetSendingEnabledRequest;
      output: {};
    };
    sdk: {
      input: UpdateConfigurationSetSendingEnabledCommandInput;
      output: UpdateConfigurationSetSendingEnabledCommandOutput;
    };
  };
}
