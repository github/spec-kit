import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  SetIdentityHeadersInNotificationsEnabledRequest,
  SetIdentityHeadersInNotificationsEnabledResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface SetIdentityHeadersInNotificationsEnabledCommandInput
  extends SetIdentityHeadersInNotificationsEnabledRequest {}
export interface SetIdentityHeadersInNotificationsEnabledCommandOutput
  extends SetIdentityHeadersInNotificationsEnabledResponse,
    __MetadataBearer {}
declare const SetIdentityHeadersInNotificationsEnabledCommand_base: {
  new (
    input: SetIdentityHeadersInNotificationsEnabledCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SetIdentityHeadersInNotificationsEnabledCommandInput,
    SetIdentityHeadersInNotificationsEnabledCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: SetIdentityHeadersInNotificationsEnabledCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SetIdentityHeadersInNotificationsEnabledCommandInput,
    SetIdentityHeadersInNotificationsEnabledCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class SetIdentityHeadersInNotificationsEnabledCommand extends SetIdentityHeadersInNotificationsEnabledCommand_base {
  protected static __types: {
    api: {
      input: SetIdentityHeadersInNotificationsEnabledRequest;
      output: {};
    };
    sdk: {
      input: SetIdentityHeadersInNotificationsEnabledCommandInput;
      output: SetIdentityHeadersInNotificationsEnabledCommandOutput;
    };
  };
}
