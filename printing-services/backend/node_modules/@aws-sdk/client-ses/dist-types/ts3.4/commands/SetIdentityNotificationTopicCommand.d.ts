import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  SetIdentityNotificationTopicRequest,
  SetIdentityNotificationTopicResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface SetIdentityNotificationTopicCommandInput
  extends SetIdentityNotificationTopicRequest {}
export interface SetIdentityNotificationTopicCommandOutput
  extends SetIdentityNotificationTopicResponse,
    __MetadataBearer {}
declare const SetIdentityNotificationTopicCommand_base: {
  new (
    input: SetIdentityNotificationTopicCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SetIdentityNotificationTopicCommandInput,
    SetIdentityNotificationTopicCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: SetIdentityNotificationTopicCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SetIdentityNotificationTopicCommandInput,
    SetIdentityNotificationTopicCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class SetIdentityNotificationTopicCommand extends SetIdentityNotificationTopicCommand_base {
  protected static __types: {
    api: {
      input: SetIdentityNotificationTopicRequest;
      output: {};
    };
    sdk: {
      input: SetIdentityNotificationTopicCommandInput;
      output: SetIdentityNotificationTopicCommandOutput;
    };
  };
}
