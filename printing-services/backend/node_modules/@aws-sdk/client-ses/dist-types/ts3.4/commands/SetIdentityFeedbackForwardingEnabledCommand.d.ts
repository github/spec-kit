import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  SetIdentityFeedbackForwardingEnabledRequest,
  SetIdentityFeedbackForwardingEnabledResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface SetIdentityFeedbackForwardingEnabledCommandInput
  extends SetIdentityFeedbackForwardingEnabledRequest {}
export interface SetIdentityFeedbackForwardingEnabledCommandOutput
  extends SetIdentityFeedbackForwardingEnabledResponse,
    __MetadataBearer {}
declare const SetIdentityFeedbackForwardingEnabledCommand_base: {
  new (
    input: SetIdentityFeedbackForwardingEnabledCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SetIdentityFeedbackForwardingEnabledCommandInput,
    SetIdentityFeedbackForwardingEnabledCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: SetIdentityFeedbackForwardingEnabledCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SetIdentityFeedbackForwardingEnabledCommandInput,
    SetIdentityFeedbackForwardingEnabledCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class SetIdentityFeedbackForwardingEnabledCommand extends SetIdentityFeedbackForwardingEnabledCommand_base {
  protected static __types: {
    api: {
      input: SetIdentityFeedbackForwardingEnabledRequest;
      output: {};
    };
    sdk: {
      input: SetIdentityFeedbackForwardingEnabledCommandInput;
      output: SetIdentityFeedbackForwardingEnabledCommandOutput;
    };
  };
}
