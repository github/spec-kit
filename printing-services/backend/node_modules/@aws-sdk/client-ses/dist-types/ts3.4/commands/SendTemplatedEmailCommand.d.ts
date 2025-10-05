import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  SendTemplatedEmailRequest,
  SendTemplatedEmailResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface SendTemplatedEmailCommandInput
  extends SendTemplatedEmailRequest {}
export interface SendTemplatedEmailCommandOutput
  extends SendTemplatedEmailResponse,
    __MetadataBearer {}
declare const SendTemplatedEmailCommand_base: {
  new (
    input: SendTemplatedEmailCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SendTemplatedEmailCommandInput,
    SendTemplatedEmailCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: SendTemplatedEmailCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SendTemplatedEmailCommandInput,
    SendTemplatedEmailCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class SendTemplatedEmailCommand extends SendTemplatedEmailCommand_base {
  protected static __types: {
    api: {
      input: SendTemplatedEmailRequest;
      output: SendTemplatedEmailResponse;
    };
    sdk: {
      input: SendTemplatedEmailCommandInput;
      output: SendTemplatedEmailCommandOutput;
    };
  };
}
