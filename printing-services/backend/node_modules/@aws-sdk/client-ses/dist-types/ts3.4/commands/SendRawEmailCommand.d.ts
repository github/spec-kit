import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { SendRawEmailRequest, SendRawEmailResponse } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface SendRawEmailCommandInput extends SendRawEmailRequest {}
export interface SendRawEmailCommandOutput
  extends SendRawEmailResponse,
    __MetadataBearer {}
declare const SendRawEmailCommand_base: {
  new (
    input: SendRawEmailCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SendRawEmailCommandInput,
    SendRawEmailCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: SendRawEmailCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SendRawEmailCommandInput,
    SendRawEmailCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class SendRawEmailCommand extends SendRawEmailCommand_base {
  protected static __types: {
    api: {
      input: SendRawEmailRequest;
      output: SendRawEmailResponse;
    };
    sdk: {
      input: SendRawEmailCommandInput;
      output: SendRawEmailCommandOutput;
    };
  };
}
