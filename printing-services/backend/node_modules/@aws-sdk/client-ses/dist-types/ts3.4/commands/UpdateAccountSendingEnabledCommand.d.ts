import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { UpdateAccountSendingEnabledRequest } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface UpdateAccountSendingEnabledCommandInput
  extends UpdateAccountSendingEnabledRequest {}
export interface UpdateAccountSendingEnabledCommandOutput
  extends __MetadataBearer {}
declare const UpdateAccountSendingEnabledCommand_base: {
  new (
    input: UpdateAccountSendingEnabledCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateAccountSendingEnabledCommandInput,
    UpdateAccountSendingEnabledCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    ...[input]: [] | [UpdateAccountSendingEnabledCommandInput]
  ): import("@smithy/smithy-client").CommandImpl<
    UpdateAccountSendingEnabledCommandInput,
    UpdateAccountSendingEnabledCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class UpdateAccountSendingEnabledCommand extends UpdateAccountSendingEnabledCommand_base {
  protected static __types: {
    api: {
      input: UpdateAccountSendingEnabledRequest;
      output: {};
    };
    sdk: {
      input: UpdateAccountSendingEnabledCommandInput;
      output: UpdateAccountSendingEnabledCommandOutput;
    };
  };
}
